# SPDX-License-Identifier: AGPL-3.0-only
"""Local high-confidence credential checks; reports locations, never secret values."""
from __future__ import annotations

import math
from pathlib import Path
import re

RULES = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'openai-style-key': re.compile(r'\bsk-(?:proj-|svcacct-)?[a-zA-Z0-9_-]{24,}'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[a-zA-Z0-9]{30,}|github_pat_[a-zA-Z0-9_]{50,})'),
    'aws-access-key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'credential-url': re.compile(r'https?://[^/\s:@]+:[^/\s@]+@'),
}
ASSIGNMENT = re.compile(
    r'''(?i)(?:api[_-]?key|app[_-]?secret|access[_-]?token|refresh[_-]?token|password)'''
    r'''["'\s]*[:=][\s]*["']([a-zA-Z0-9_./+!?@#$%^&*=-]{16,})["']''')


def entropy(value: str) -> float:
    return -sum((value.count(c) / len(value)) * math.log2(value.count(c) / len(value)) for c in set(value))


def scan_bytes(content: bytes, name: str) -> list[dict]:
    text = content.decode('utf-8', errors='replace')
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in RULES.items():
            if pattern.search(line):
                findings.append({'file': name, 'line': number, 'rule': rule})
        for match in ASSIGNMENT.finditer(line):
            value = match.group(1)
            if entropy(value) >= 3.25 and not value.lower().startswith(('your_', 'example_', 'replace_')):
                findings.append({'file': name, 'line': number, 'rule': 'literal-high-entropy-credential'})
    return findings


def forbidden_path(relative: str) -> bool:
    path = Path(relative)
    lower = relative.lower()
    name = path.name.lower()
    if name == '.env.example':
        return False
    if name == '.env' or name.startswith('.env.') or name == 'chuanlab.toml':
        return True
    if {part.lower() for part in path.parts} & {'.local', '.imagegen-private', 'workspace', 'articles', 'publishing', 'backups', 'node_modules', '.venv'}:
        return True
    if any(lower.endswith(x) for x in ('.key', '.pem', '.pfx', '.p12', '.sqlite', '.sqlite3', '.db', '.enc')):
        return True
    return bool(re.search(r'(?:credentials?|cookies?|sessions?|tokens?)(?:[.-].*)?\.(?:json|txt|log|yaml|yml)$', name))
