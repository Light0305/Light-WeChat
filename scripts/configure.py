# SPDX-License-Identifier: AGPL-3.0-only
"""Create local templates and collect credentials with masked terminal input."""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import sys

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def create_templates(root: Path = ROOT) -> list[str]:
    created = []
    for source, target in [('chuanlab.example.toml', 'chuanlab.toml'), ('.env.example', '.env')]:
        destination = root / target
        if destination.is_symlink():
            raise ValueError('Local configuration must not be a symbolic link')
        if not destination.exists():
            with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
                stream.write((root / source).read_bytes())
            created.append(target)
    return created


def save_credentials(values: dict[str, str], root: Path = ROOT) -> None:
    path = root / '.env'
    if path.is_symlink():
        raise ValueError('Refusing a linked credential file')
    current = dict(dotenv_values(path, interpolate=False)) if path.exists() else {}
    current.update(values)
    lines = ['# Local credentials. Do not commit, screenshot or share this file.']
    for key, value in current.items():
        if not key.replace('_', '').isalnum() or not isinstance(value, (str, type(None))):
            raise ValueError('Invalid local environment entry')
        value = value or ''
        if any(c in value for c in '\r\n'):
            raise ValueError('Credential values must be single-line')
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(key + '="' + escaped + '"')
    temporary = root / '.env.write-tmp'
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as stream:
        stream.write('\n'.join(lines) + '\n')
    temporary.replace(path)
    if os.name != 'nt':
        path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'wechat', 'images'])
    args = parser.parse_args()
    created = create_templates()
    if args.command == 'wechat':
        app_id = input('Your WeChat AppID (local only): ').strip()
        secret = getpass.getpass('Your AppSecret (hidden): ').strip()
        if not app_id or not secret:
            raise ValueError('AppID and AppSecret are required; nothing has been saved')
        save_credentials({'WECHAT_APP_ID': app_id, 'WECHAT_APP_SECRET': secret, 'WECHAT_ACCESS_TOKEN': ''})
        print('Credentials saved locally. Upload remains disabled until you enable it in chuanlab.toml.')
    elif args.command == 'images':
        secret = getpass.getpass('Your Images API key (hidden): ').strip()
        if not secret:
            raise ValueError('No key entered; nothing has been saved')
        save_credentials({'IMAGE_API_KEY': secret})
        print('Key saved locally. Configure your provider and enable it in chuanlab.toml before use.')
    else:
        print('Created: ' + ', '.join(created) if created else 'Local templates already exist; no files changed.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyboardInterrupt, EOFError):
        print('Configuration was not completed. Check local files; no credential values are displayed.', file=sys.stderr)
        raise SystemExit(1)
