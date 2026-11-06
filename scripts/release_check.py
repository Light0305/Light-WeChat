# SPDX-License-Identifier: AGPL-3.0-only
"""Scan a release whitelist and independent Git history entirely on this machine."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from scan_secrets import forbidden_path, scan_bytes

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {'agents', 'assets', 'references', 'scripts', 'shared', 'tools', 'vendor', 'tests', '.github'}
FILES = {'SKILL.md', 'README.md', 'README.zh-CN.md', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'SECURITY.md',
    'AGENTS.md', 'RELEASE_AUDIT.md', '.gitignore', '.gitattributes', '.gitleaks.toml', '.env.example', 'chuanlab.example.toml',
    'pyproject.toml', 'requirements.in', 'requirements.txt', 'requirements-dev.txt', 'package.json', 'package-lock.json',
    'RELEASE_FILES.json'}
IGNORED_TOP_LEVEL = {'.git', '.venv', 'node_modules', '.tools', 'dist', 'workspace', 'articles', 'tmp', 'backups',
    '__pycache__', '.pytest_cache', '.ruff_cache', '.local', '.env', 'chuanlab.toml'}


def release_files(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    result = []
    for child in sorted(root.iterdir()):
        if child.name in IGNORED_TOP_LEVEL or child.name.endswith('.egg-info'):
            continue
        if child.is_symlink():
            raise ValueError('Symlinks are not permitted in a release: ' + child.name)
        if child.is_dir():
            if child.name not in DIRECTORIES:
                raise ValueError('Unrecognized release directory: ' + child.name)
            for path in sorted(child.rglob('*')):
                relative = path.relative_to(root)
                if any(x in {'__pycache__', '.pytest_cache', '.ruff_cache'} for x in relative.parts):
                    continue
                if path.is_symlink():
                    raise ValueError('Release entry must not be a symlink: ' + relative.as_posix())
                if path.is_file():
                    if forbidden_path(relative.as_posix()):
                        raise ValueError('Sensitive/runtime file in source directories: ' + relative.as_posix())
                    result.append(path)
        elif child.name in FILES:
            result.append(child)
        else:
            raise ValueError('Unrecognized top-level file: ' + child.name)
    return result


def scanner() -> str:
    name = 'gitleaks.exe' if os.name == 'nt' else 'gitleaks'
    bundled = ROOT / '.tools/bin' / name
    found = str(bundled) if bundled.is_file() else shutil.which('gitleaks')
    if not found:
        raise ValueError('Gitleaks is required for a release; run scripts/install_gitleaks.py first')
    return found


def own_git(root: Path) -> bool:
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(root), 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == root.resolve()


def gitleaks_scan(executable: str, mode: str, source: Path, output: Path) -> dict:
    command = [executable, mode, str(source), '--no-banner', '--redact=100', '--exit-code', '1',
        '--config', str(ROOT / '.gitleaks.toml'), '--report-format', 'json', '--report-path', str(output)]
    if mode == 'git':
        command += ['--log-opts=--all']
    completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    if completed.returncode not in (0, 1):
        return {'passed': False, 'scan_error': True, 'findings': [], 'exit_code': completed.returncode}
    data = json.loads(output.read_text(encoding='utf-8')) if output.is_file() else []
    findings = [{'file': row.get('File', ''), 'line': row.get('StartLine'), 'rule': row.get('RuleID'),
                 'commit': row.get('Commit', '')} for row in (data or [])]
    return {'passed': completed.returncode == 0 and not findings, 'scan_error': False, 'findings': findings}


def check(root: Path = ROOT) -> dict:
    root = root.resolve()
    files = release_files(root)
    required = FILES - {'RELEASE_FILES.json'}
    missing = sorted(required - {p.relative_to(root).as_posix() for p in files})
    if missing:
        raise ValueError('Required release files missing: ' + ', '.join(missing))
    inventory = root / 'RELEASE_FILES.json'
    if inventory.exists():
        entries = json.loads(inventory.read_text(encoding='utf-8'))['files']
        expected = {entry['path']: entry['sha256'] for entry in entries}
        if len(expected) != len(entries):
            raise ValueError('Duplicate paths in extracted release inventory')
        actual = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in files if p != inventory}
        if actual != expected:
            raise ValueError('Extracted release inventory does not match its SHA-256 manifest')
    local_findings = []
    for path in files:
        local_findings.extend(scan_bytes(path.read_bytes(), path.relative_to(root).as_posix()))
    git = own_git(root)
    tracked_sensitive = []
    commits = 0
    if git:
        tracked = subprocess.check_output(['git', '--no-optional-locks', '-C', str(root), 'ls-files', '-z'])
        tracked_sensitive = [p.decode('utf-8', errors='replace') for p in tracked.split(b'\0') if p and forbidden_path(p.decode('utf-8', errors='replace'))]
        count = subprocess.run(['git', '--no-optional-locks', '-C', str(root), 'rev-list', '--all', '--count'],
            capture_output=True, text=True, encoding='utf-8', errors='replace')
        if count.returncode:
            raise ValueError('Cannot enumerate independent Git history')
        commits = int(count.stdout.strip() or '0')
    executable = scanner()
    version = subprocess.check_output([executable, 'version'], text=True, encoding='utf-8', errors='replace').strip()
    with tempfile.TemporaryDirectory(prefix='chuan-public-scan-') as directory:
        temporary = Path(directory)
        stage = temporary / 'source'
        for path in files:
            target = stage / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        source_scan = gitleaks_scan(executable, 'dir', stage, temporary / 'source-report.json')
        for row in source_scan['findings']:
            try:
                row['file'] = Path(row['file']).relative_to(stage).as_posix()
            except ValueError:
                pass
        history = gitleaks_scan(executable, 'git', root, temporary / 'history-report.json') if commits else {
            'passed': True, 'findings': [], 'scope': 'no independent commits to scan'}
    return {'passed': not local_findings and not tracked_sensitive and source_scan['passed'] and history['passed'],
        'source_files': len(files), 'local_findings': local_findings, 'tracked_sensitive_files': tracked_sensitive,
        'gitleaks_version': version, 'gitleaks_source': source_scan, 'gitleaks_history': history,
        'independent_git': git, 'history_commits': commits, 'source_uploaded': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = check()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        # Only local policy messages are shown; scanner stdout/stderr is never forwarded.
        result = {'passed': False, 'error': str(error) if isinstance(error, ValueError) else 'Local scanner failed to complete'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
