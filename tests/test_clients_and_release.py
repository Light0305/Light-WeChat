import base64
import io
import json
from pathlib import Path
import secrets
from types import SimpleNamespace

from PIL import Image
import pytest
import requests

import generate_image
import build_release
import release_check
from scan_secrets import forbidden_path, scan_bytes
from verify_upstream import verify
from wechat_publisher.client import WeChatApiError, WeChatClient
from wechat_publisher.config import WeChatConfig
from wechat_publisher import http_safe


def response(status=200, body=None):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(body or {}).encode()
    return result


def test_network_errors_withhold_credentials(monkeypatch):
    sensitive = secrets.token_urlsafe(32)
    def failed(session, *args, **kwargs):
        assert session.trust_env is False
        raise requests.ConnectionError('secret=' + sensitive)
    monkeypatch.setattr(requests.sessions.Session, 'request', failed)
    with pytest.raises(RuntimeError) as caught:
        http_safe.request('GET', 'https://example.invalid')
    assert sensitive not in str(caught.value)


def test_redirect_is_refused(monkeypatch):
    def redirect(session, *args, **kwargs):
        assert session.trust_env is False
        assert kwargs['allow_redirects'] is False
        return response(302)
    monkeypatch.setattr(requests.sessions.Session, 'request', redirect)
    with pytest.raises(RuntimeError, match='redirects are refused'):
        http_safe.request('GET', 'https://example.invalid')


def test_api_errors_do_not_echo_messages():
    sensitive = secrets.token_urlsafe(32)
    for code in (40001, sensitive):
        with pytest.raises(WeChatApiError) as caught:
            WeChatClient._parse_response(response(body={'errcode': code, 'errmsg': sensitive}))
        assert sensitive not in str(caught.value)
    with pytest.raises(WeChatApiError) as caught:
        WeChatClient._parse_response(response(body={'errcode': 40164, 'errmsg': 'invalid ip 203.0.113.7 ' + sensitive}))
    assert '203.0.113.7' in str(caught.value) and sensitive not in str(caught.value)


def test_only_draft_readback_endpoints():
    client = WeChatClient(WeChatConfig('', ''))
    with pytest.raises(ValueError, match='only supports'):
        client.post_json('freepublish/submit', {}, '')


def test_secret_detectors_redact_values():
    token = 'sk-' + secrets.token_urlsafe(40)
    result = scan_bytes(('api_key="' + token + '"').encode(), 'injected.txt')
    assert any(row['rule'] == 'openai-style-key' for row in result)
    assert token not in json.dumps(result)


@pytest.mark.parametrize('name', ['.env', '.env.backup', 'chuanlab.toml', 'workspace/article.json',
                                  'saved/credentials.backup.json', 'private.key', 'credentials.json',
                                  'cookies.json', 'tokens.json', '.LOCAL/settings.json'])
def test_sensitive_files_refused(name):
    assert forbidden_path(name)


def test_release_whitelist_excludes_local_runtime(tmp_path):
    (tmp_path / '.env').write_text('not-a-real-key')
    (tmp_path / 'workspace').mkdir()
    (tmp_path / 'workspace' / 'article.md').write_text('private synthetic content')
    (tmp_path / 'README.md').write_text('public')
    assert [p.name for p in release_check.release_files(tmp_path)] == ['README.md']
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'scripts' / '.env').write_text('unwanted')
    with pytest.raises(ValueError, match='Sensitive/runtime'):
        release_check.release_files(tmp_path)


def test_archive_is_deterministic_and_source_only(tmp_path, monkeypatch):
    import zipfile
    (tmp_path / 'README.md').write_text('synthetic release fixture')
    (tmp_path / '.env').write_text('local-only-placeholder')
    monkeypatch.setattr(build_release, 'check', lambda root: {'passed': True})
    first = build_release.build(tmp_path)
    second = build_release.build(tmp_path)
    assert first['sha256'] == second['sha256']
    with zipfile.ZipFile(first['archive']) as package:
        assert set(package.namelist()) == {'light-wechat/README.md', 'light-wechat/RELEASE_FILES.json'}


def test_pinned_upstreams():
    result = verify()
    assert not result['errors']


def image_args(article, **overrides):
    prompt = article / 'prompts/test.txt'
    prompt.write_text('Synthetic offline image adapter test; never submit to a provider.')
    return SimpleNamespace(command='generate', out=article / 'images/new-output.png',
        prompt_file=prompt, image=[], dry_run=True, confirm_paid=False, response_cache=None,
        size='1024x1024', **overrides)


def test_images_dry_run_and_paid_gate(article):
    args = image_args(article)
    result = generate_image.run(args)
    assert not result['network_used'] and not result['paid_request_submitted']
    args.dry_run = False
    with pytest.raises(ValueError, match='confirm-paid'):
        generate_image.run(args)


def test_images_recover_base64_without_key_or_paid_call(article):
    args = image_args(article)
    args.command = 'recover'
    data = io.BytesIO()
    Image.new('RGB', (32, 32), 'blue').save(data, format='PNG')
    cache = article / '.imagegen-private/responses/synthetic.json'
    cache.parent.mkdir(parents=True)
    cache.write_text(json.dumps({'data': [{'b64_json': base64.b64encode(data.getvalue()).decode()}]}))
    args.response_cache = cache
    args.dry_run = False
    generate_image.run(args)
    assert Image.open(args.out).size == (32, 32)


@pytest.mark.parametrize('url', ['http://example.invalid/v1', 'https://' + 'a:b' + '@example.invalid/v1',
                               'https://example.invalid/v1?credential=value'])
def test_images_provider_url_rules(url):
    with pytest.raises(ValueError):
        generate_image.api_base(url)
