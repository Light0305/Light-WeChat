# SPDX-License-Identifier: AGPL-3.0-only
"""Check the local runtime without opening accounts or contacting services."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'shared'))
from settings import load_settings


def browser_path(explicit: str = '') -> str | None:
    candidates = [explicit, os.environ.get('CHUANLAB_BROWSER', ''),
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Chromium.app/Contents/MacOS/Chromium']
    candidates.extend(shutil.which(x) or '' for x in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge'))
    return next((x for x in candidates if x and Path(x).is_file()), None)


def check() -> dict:
    settings = load_settings()
    missing = [name for name in ('markdown', 'PIL', 'requests', 'dotenv', 'bs4', 'yaml')
               if importlib.util.find_spec(name) is None]
    issues = ['Missing Python module: ' + name for name in missing]
    if sys.version_info < (3, 11):
        issues.append('Python 3.11 or later is required')
    node = shutil.which('node')
    version = ''
    if node:
        version = subprocess.check_output([node, '--version'], text=True, timeout=10).strip()
        parts = tuple(map(int, re.findall(r'[0-9]+', version)[:3]))
        if parts < (22, 16, 0):
            issues.append('Node.js 22.16 or later is required')
    else:
        issues.append('Node.js is missing')
    browser = browser_path(settings.browser)
    if not browser:
        issues.append('Chrome/Edge/Chromium is missing; configure preview.browser')
    return {'ready': not issues, 'issues': issues, 'python': sys.version.split()[0], 'node': version,
        'browser_found': bool(browser), 'credentials_read': False, 'network_used': False,
        'wechat_enabled': settings.wechat_enabled, 'paid_images_enabled': settings.image_enabled,
        'publisher_bundled': (ROOT / 'tools/wechat-publisher/publish_to_draft.py').is_file()}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ready'] else 1)
