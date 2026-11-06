# SPDX-License-Identifier: AGPL-3.0-only
"""Installation-local configuration; never search parent projects or user profiles."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import tomllib

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    repository: Path
    workspace: Path
    articles: Path
    author: str
    brand_name: str
    contact_card: Path | None
    columns: tuple[str, ...]
    wechat_enabled: bool
    browser: str
    image_enabled: bool
    image_base_url: str
    image_model: str


def load_settings() -> Settings:
    explicit = os.environ.get('CHUANLAB_CONFIG', '')
    path = Path(explicit).expanduser() if explicit else REPOSITORY_ROOT / 'chuanlab.toml'
    if explicit and not path.is_file():
        raise ValueError('CHUANLAB_CONFIG must name an existing local TOML file')
    data = tomllib.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else {}
    paths, publication = data.get('paths', {}), data.get('publication', {})
    wechat, images = data.get('wechat', {}), data.get('images', {})
    preview = data.get('preview', {})
    workspace = Path(os.environ.get('CHUANLAB_WORKSPACE') or paths.get('workspace', 'workspace')).expanduser()
    if not workspace.is_absolute():
        workspace = REPOSITORY_ROOT / workspace
    workspace = workspace.resolve(strict=False)
    if workspace == REPOSITORY_ROOT or workspace in REPOSITORY_ROOT.parents:
        raise ValueError('Choose a separate workspace directory, not the source root or its ancestors')
    contact = publication.get('contact_card', '')
    contact_path = Path(contact).expanduser() if contact else None
    if contact_path and not contact_path.is_absolute():
        contact_path = REPOSITORY_ROOT / contact_path
    columns = publication.get('columns', ['ai', 'papers', 'careers', 'projects'])
    if not isinstance(columns, list) or not columns or not all(
            isinstance(c, str) and re.fullmatch(r'[a-z][a-z0-9-]{0,47}', c) for c in columns):
        raise ValueError('publication.columns must be a nonempty list of lowercase identifiers')
    for section in (wechat, images):
        if not isinstance(section.get('enabled', False), bool):
            raise ValueError('Integration enabled flags must be TOML booleans')
    return Settings(REPOSITORY_ROOT, workspace, workspace / 'articles',
        str(publication.get('author', '')), str(publication.get('name', '')),
        contact_path, tuple(columns), wechat.get('enabled', False),
        str(preview.get('browser', '')), images.get('enabled', False),
        str(images.get('base_url', '')), str(images.get('model', '')))


def require_wechat_enabled() -> Settings:
    settings = load_settings()
    if not settings.wechat_enabled:
        raise ValueError('WeChat is disabled. Configure your own account and set wechat.enabled = true first')
    if os.environ.get('CHUANLAB_ALLOW_TEST_ROOT') == '1':
        raise ValueError('Live WeChat access is disabled in isolated test workspaces')
    return settings
