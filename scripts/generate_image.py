# SPDX-License-Identifier: AGPL-3.0-only
"""Opt-in compatible Images API adapter; no global credentials or automatic retries."""
from __future__ import annotations

import argparse
import base64
from contextlib import ExitStack
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
import uuid

from dotenv import dotenv_values
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'shared'))
from settings import load_settings
from workspace_guard import assert_article_root, assert_within


def output_target(output: Path) -> tuple[Path, Path]:
    settings = load_settings()
    output = assert_within(output, settings.articles)
    parts = output.relative_to(settings.articles).parts
    if len(parts) < 3 or parts[1] != 'images' or output.suffix.lower() != '.png':
        raise ValueError('Output must be a PNG under one configured article/images directory')
    article = assert_article_root(settings.articles / parts[0])
    if output.exists():
        raise ValueError('Output exists; choose a new versioned filename')
    return article, output


def api_base(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise ValueError('Configure an HTTPS Images API base URL without credentials, query or fragment')
    return value.rstrip('/') + ('/v1' if parsed.path in ('', '/') else '')


def image_bytes(data: dict, session: requests.Session) -> bytes:
    rows = data.get('data')
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError('Expected exactly one image in the cached provider response')
    row = rows[0]
    if row.get('b64_json'):
        return base64.b64decode(row['b64_json'], validate=True)
    url = row.get('url', '')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Image download URL must be HTTPS and must not contain login credentials')
    if parsed.hostname.lower() == 'localhost':
        raise ValueError('Local image download hosts are refused')
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ValueError('Private image download addresses are refused')
    # No API authorization header is forwarded to a returned image host.
    response = session.get(url, timeout=60, allow_redirects=False)
    if response.status_code != 200:
        raise ValueError('Image download failed; use the cached response to recover without another paid generation')
    return response.content


def run(args) -> dict:
    article, output = output_target(args.out)
    settings = load_settings()
    if args.command == 'recover':
        if not args.response_cache:
            raise ValueError('Recovery requires a saved --response-cache')
        cache = assert_within(args.response_cache, article / '.imagegen-private/responses')
        data = json.loads(cache.read_text(encoding='utf-8'))
        if args.dry_run:
            return {'network_used': False, 'paid_request_submitted': False, 'cached_response_found': True}
    else:
        if not args.prompt_file:
            raise ValueError('Save the actual prompt and pass --prompt-file')
        prompt_path = assert_within(args.prompt_file, article / 'prompts')
        prompt = prompt_path.read_text(encoding='utf-8').strip()
        if not prompt:
            raise ValueError('The saved prompt is empty')
        references = [assert_within(path, article / 'images') for path in args.image]
        if args.command == 'edit' and not references:
            raise ValueError('Edits require --image')
        if args.command == 'generate' and references:
            raise ValueError('Use edit when providing reference images')
        if args.dry_run:
            return {'network_used': False, 'paid_request_submitted': False, 'reference_images': len(references),
                    'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
                    'provider_enabled': settings.image_enabled, 'model_configured': bool(settings.image_model)}
        if not settings.image_enabled or not args.confirm_paid:
            raise ValueError('A configured enabled provider and explicit --confirm-paid authorization are required')
        if not settings.image_model:
            raise ValueError('Configure your own image model name')
        base = api_base(settings.image_base_url)
        values = dotenv_values(ROOT / '.env', interpolate=False) if (ROOT / '.env').is_file() else {}
        key = str(values.get('IMAGE_API_KEY') or '')
        if not key:
            raise ValueError('Configure IMAGE_API_KEY locally; never send it in chat')
        cache_dir = article / '.imagegen-private/responses'
        cache_dir.mkdir(parents=True, exist_ok=True)
        request_id = uuid.uuid4().hex
        attempt = cache_dir.parent / (request_id + '-attempt.json')
        attempt.write_text(json.dumps({'outcome': 'in-flight', 'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
            'output': output.relative_to(article).as_posix()}), encoding='utf-8')
        try:
            with requests.Session() as session, ExitStack() as opened:
                session.trust_env = False
                headers = {'Authorization': 'Bearer ' + key}
                fields = {'model': settings.image_model, 'prompt': prompt, 'n': 1, 'size': args.size}
                if args.command == 'edit':
                    files = [('image[]', (path.name, opened.enter_context(path.open('rb')), 'application/octet-stream')) for path in references]
                    response = session.post(base + '/images/edits', headers=headers, data=fields, files=files,
                                            timeout=180, allow_redirects=False)
                else:
                    response = session.post(base + '/images/generations', headers=headers, json=fields,
                                            timeout=180, allow_redirects=False)
                if response.status_code != 200:
                    attempt.write_text(json.dumps({'outcome': 'rejected', 'http_status': response.status_code}), encoding='utf-8')
                    raise ValueError('Provider request was rejected; no response details are logged and no retry is made')
                data = response.json()
                cache = cache_dir / (request_id + '.json')
                cache.write_text(json.dumps(data), encoding='utf-8')
                attempt.write_text(json.dumps({'outcome': 'response-cached', 'response_file': cache.name}), encoding='utf-8')
        except requests.RequestException:
            attempt.write_text(json.dumps({'outcome': 'unknown', 'next': 'Check provider records before considering a new paid request'}), encoding='utf-8')
            raise ValueError('Provider result is unknown; check records before retrying. No automatic retry was made') from None
    with requests.Session() as session:
        session.trust_env = False
        raw = image_bytes(data, session)
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(raw)) as generated:
        generated.load()
        generated.save(output, format='PNG')
    return {'saved': str(output), 'response_cache': str(cache), 'generator': 'user-configured-images-api',
            'model': settings.image_model, 'generated': True,
            'next': 'Inspect the actual image, then register its prompt, generator, provenance and usage rights'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate', 'edit', 'recover'])
    parser.add_argument('--prompt-file', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--image', type=Path, action='append', default=[])
    parser.add_argument('--response-cache', type=Path)
    parser.add_argument('--size', default='1536x1024')
    parser.add_argument('--confirm-paid', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
        return 0
    except Exception:
        # Provider URLs, responses and exception strings can contain credentials or signed URLs.
        print(json.dumps({'passed': False, 'error': 'Image operation did not complete. Check local configuration and private attempt/cache records; no automatic retry was made.'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
