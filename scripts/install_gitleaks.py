# SPDX-License-Identifier: AGPL-3.0-only
"""Install a checksum-verified, pinned Gitleaks binary inside this skill only."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import platform
import struct
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '8.30.1'
CHECKSUM_FILE_SHA256 = '061476c21adaf5441516f96f185c1a4706a83cd6329b9b38762271b3d4a52fae'
ORIGIN = f'https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}'


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'Chuan-Lab-Local-Setup'})
    with urllib.request.urlopen(request, timeout=90) as response:
        if not response.url.startswith('https://'):
            raise ValueError('Insecure download refused')
        return response.read()


def install() -> dict:
    system = {'Windows': 'windows', 'Linux': 'linux', 'Darwin': 'darwin'}.get(platform.system())
    machine = platform.machine() or os.environ.get('PROCESSOR_ARCHITECTURE') or ('x86_64' if struct.calcsize('P') == 8 else 'x86')
    arch = {'amd64': 'x64', 'x86_64': 'x64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(machine.lower())
    if not system or not arch:
        raise ValueError('Unsupported system; install the official Gitleaks CLI manually')
    suffix = 'zip' if system == 'windows' else 'tar.gz'
    name = f'gitleaks_{VERSION}_{system}_{arch}.{suffix}'
    checksums = download(f'{ORIGIN}/gitleaks_{VERSION}_checksums.txt')
    if hashlib.sha256(checksums).hexdigest() != CHECKSUM_FILE_SHA256:
        raise ValueError('Pinned checksum document verification failed')
    expected = next((line.split()[0] for line in checksums.decode('utf-8').splitlines()
                     if line.split()[-1].lstrip('*') == name), None)
    if not expected:
        raise ValueError('Requested platform is absent from the verified checksum document')
    archive = download(ORIGIN + '/' + name)
    if hashlib.sha256(archive).hexdigest() != expected:
        raise ValueError('Gitleaks archive checksum verification failed')
    executable = 'gitleaks.exe' if os.name == 'nt' else 'gitleaks'
    if suffix == 'zip':
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            members = [p for p in package.namelist() if Path(p).name == executable]
            if len(members) != 1:
                raise ValueError('Unexpected archive contents')
            content = package.read(members[0])
    else:
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as package:
            members = [p for p in package.getmembers() if p.isfile() and Path(p.name).name == executable]
            if len(members) != 1:
                raise ValueError('Unexpected archive contents')
            content = package.extractfile(members[0]).read()
    destination = ROOT / '.tools/bin' / executable
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    if os.name != 'nt':
        destination.chmod(0o755)
    result = {'version': VERSION, 'archive_sha256': expected, 'checksum_document_verified': True,
              'local_install_only': True, 'source': ORIGIN}
    (ROOT / '.tools/gitleaks-install.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    try:
        print(json.dumps(install(), indent=2))
    except Exception:
        # Redirect/download errors can contain signed URLs: never echo them.
        raise SystemExit('Pinned scanner setup failed. Check network access or install the official CLI locally; no source was uploaded.')
