# SPDX-License-Identifier: AGPL-3.0-only
"""Build a source-only, independently scanned release archive from a whitelist."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from release_check import ROOT, check, release_files


def build(root: Path = ROOT) -> dict:
    root = root.resolve()
    initial = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in release_files(root)}
    result = check(root)
    if not result['passed']:
        raise ValueError('Release is blocked by the local secret scan; run release_check.py for sanitized findings')
    destination = root / 'dist/Light-WeChat-1.0.0.zip'
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'name': 'Light-WeChat', 'skill': 'light-wechat', 'version': '1.0.0', 'license': 'AGPL-3.0-only',
                'files': [{'path': path, 'sha256': digest} for path, digest in initial.items()],
                'private_configuration_included': False, 'git_metadata_included': False}
    # Stage beside the destination so the final atomic replace works even when
    # the OS temporary directory and this checkout are on different drives.
    with tempfile.TemporaryDirectory(prefix='.build-', dir=destination.parent) as scratch:
        staged = Path(scratch) / 'release.zip'
        with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for relative, expected in initial.items():
                content = (root / relative).read_bytes()
                if hashlib.sha256(content).hexdigest() != expected:
                    raise ValueError('Source changed during release verification; rerun after edits finish')
                info = zipfile.ZipInfo('light-wechat/' + relative, date_time=(2026, 11, 6, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                package.writestr(info, content)
            info = zipfile.ZipInfo('light-wechat/RELEASE_FILES.json', date_time=(2026, 11, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            package.writestr(info, json.dumps(manifest, ensure_ascii=False, indent=2))
        staged.replace(destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    (destination.parent / (destination.name + '.sha256')).write_text(digest + '  ' + destination.name + '\n', encoding='ascii')
    return {'archive': str(destination), 'sha256': digest, 'source_files': len(initial), 'scanned': True}


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
