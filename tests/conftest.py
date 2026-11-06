"""Synthetic fixtures only. No live accounts, article archives or network access."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket

from PIL import Image, ImageDraw
import pytest
import requests

import article_workflow as workflow
import create_article_workspace as creator
import settings
import workspace_guard
from v9_support import input_manifest, sha, write_json


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError('Tests must not access live services')
    monkeypatch.setattr(requests.sessions.Session, 'request', blocked)
    monkeypatch.setattr(socket, 'create_connection', blocked)


@pytest.fixture
def local_settings(tmp_path, monkeypatch):
    config = tmp_path / 'config.toml'
    config.write_text('[publication]\ncolumns = ["ai", "papers", "careers", "projects"]\n', encoding='utf-8')
    root = tmp_path / 'workspace/articles'
    monkeypatch.setenv('CHUANLAB_CONFIG', str(config))
    monkeypatch.setenv('CHUANLAB_WORKSPACE', str(root.parent))
    monkeypatch.setattr(workspace_guard, 'ARTICLES_ROOT', root)
    monkeypatch.setattr(workflow, 'PRODUCTION_ARTICLES_ROOT', root)
    monkeypatch.delenv('CHUANLAB_ALLOW_TEST_ROOT', raising=False)
    return config, root


@pytest.fixture
def article(local_settings):
    _, root = local_settings
    folder = creator.create('排版与上传门禁测试', root, column='ai')
    write_json(folder / 'assessment.yaml', {'decision': 'pass', 'dimensions': {
        key: 4 for key in ('accuracy', 'viewpoint', 'usefulness', 'voice', 'readability')},
        'blockers': [], 'notes': 'Synthetic fixture; these scores are not an editorial endorsement.'})
    (folder / 'draft.md').write_text(
        '# 排版与上传门禁测试\n\n<!-- digest: 仅供离线测试，不应上传的合成样稿。 -->\n'
        '<!-- layout: gzh-chuan-editorial -->\n\n'
        '这是用于检查本地工作流的合成样稿，不是真实报道，也不包含账号信息。\n\n'
        '## 测试对象\n\n下面的图片由测试程序画出，只用于检查图片路径与移动阅读宽度。\n\n'
        '![合成测试图](images/example.png)\n\n'
        '## 测试边界\n\n脚本检查版本、文件和授权约束。内容是否可靠，仍需阅读原始材料并完成编辑判断。\n', encoding='utf-8')
    assets = []
    for name, size, role in [('cover-master.png', (1200, 1200), 'cover-master'),
                             ('cover.png', (900, 383), 'cover'),
                             ('cover-square.png', (900, 900), 'square-cover'),
                             ('example.png', (900, 480), 'explanation')]:
        image = Image.new('RGB', size, '#f5f2e9')
        draw = ImageDraw.Draw(image)
        draw.rectangle((40, 40, size[0] - 40, size[1] - 40), outline='#17324d', width=4)
        draw.text((60, 60), 'SYNTHETIC TEST / DO NOT UPLOAD', fill='#17324d')
        image.save(folder / 'images' / name)
        asset = {'path': 'images/' + name, 'role': role, 'origin': 'Synthetic offline test fixture',
                 'rights': 'Constructed by this test; no external asset', 'generated': False, 'source_ids': []}
        if role in {'cover', 'square-cover'}:
            asset['derived_from'] = 'images/cover-master.png'
        assets.append(asset)
    write_json(folder / 'evidence.json', {'sources': [], 'claims': [
        {'id': 'test-opinion', 'kind': 'opinion', 'text': 'Synthetic fixture for mechanical testing only.'}], 'assets': assets})
    return folder


def synthetic_preview(folder: Path):
    """Exercise manifest binding without pretending this is a real browser acceptance."""
    out = folder / 'publishing/preview'
    workflow.render(folder, folder / 'draft.md', out)
    for width in (375, 390):
        for kind in ('mobile', 'covers', 'package'):
            target = out / f'{kind}-{width}'
            target.mkdir(parents=True, exist_ok=True)
            for name in ('first-screen.png', 'ending-screen.png'):
                Image.new('RGB', (width, 844), 'white').save(target / name)
            write_json(target / 'visual-audit.json', {'viewportWidth': width, 'scrollWidth': width,
                'brokenImages': 0, 'visibleTextLength': 80, 'synthetic': True})
    files = {p.relative_to(out).as_posix(): sha(p) for p in out.rglob('*')
             if p.is_file() and p.name != 'preview-manifest.json'}
    write_json(out / 'preview-manifest.json', {'input_sha256': input_manifest(folder)['sha256'],
        'files': files, 'scope': 'synthetic test only'})


@pytest.fixture
def reviewed(article):
    synthetic_preview(article)
    for role in ('factual', 'editorial', 'visual'):
        report = article / f'reviews/{role}.md'
        report.write_text('Synthetic test report: verifies file contracts and version binding only; '
                          'this is not a production review, and no material is authorized for upload.', encoding='utf-8')
        workflow.record_review(article, role, f'reviews/{role}.md', 'offline-test')
    return article
