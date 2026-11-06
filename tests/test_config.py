from pathlib import Path
import json

from dotenv import dotenv_values
from PIL import Image
import pytest

import configure
import create_article_workspace as creator
import settings
from wechat_publisher import config as credentials
from workspace_guard import WorkspaceSafetyError, assert_within


def test_defaults_are_local(local_settings):
    value = settings.load_settings()
    assert not value.wechat_enabled and not value.image_enabled
    assert value.author == value.brand_name == ''
    assert value.contact_card is None


def test_no_parent_or_inherited_credentials(tmp_path, local_settings, monkeypatch):
    repo = tmp_path / 'isolated'
    repo.mkdir()
    (tmp_path / '.env').write_text('WECHAT_APP_ID=parent-account\nWECHAT_APP_SECRET=parent-secret\n')
    monkeypatch.setattr(credentials, 'REPOSITORY', repo)
    monkeypatch.setenv('WECHAT_APP_ID', 'inherited-account')
    monkeypatch.setenv('WECHAT_APP_SECRET', 'inherited-secret')
    value = credentials.load_config()
    assert value.app_id == value.app_secret == ''
    with pytest.raises(ValueError, match='Missing WeChat credentials'):
        credentials.assert_credentials(value)


def test_explicit_credentials_and_no_interpolation(tmp_path, local_settings):
    path = tmp_path / 'selected.env'
    path.write_text('WECHAT_APP_ID=test-account\nWECHAT_APP_SECRET="${UNRELATED_VALUE}"\n')
    value = credentials.load_config(path)
    assert value.app_id == 'test-account'
    assert value.app_secret == '${UNRELATED_VALUE}'


def test_masked_setup_roundtrip(tmp_path):
    values = {'WECHAT_APP_SECRET': 'contains-quote"and-backslash\\'}
    configure.save_credentials(values, tmp_path)
    assert dotenv_values(tmp_path / '.env', interpolate=False) == values
    with pytest.raises(ValueError, match='single-line'):
        configure.save_credentials({'IMAGE_API_KEY': 'bad\nvalue'}, tmp_path)


def test_template_init_never_overwrites(tmp_path):
    for source in ('chuanlab.example.toml', '.env.example'):
        (tmp_path / source).write_text('template')
    assert len(configure.create_templates(tmp_path)) == 2
    (tmp_path / '.env').write_text('keep-me')
    assert configure.create_templates(tmp_path) == []
    assert (tmp_path / '.env').read_text() == 'keep-me'


def test_creator_idempotence_and_no_late_contact_injection(article, local_settings):
    config, root = local_settings
    original = {p.relative_to(article): p.read_bytes() for p in article.rglob('*') if p.is_file()}
    card = config.parent / 'own-card.png'
    Image.new('RGB', (200, 200)).save(card)
    config.write_text('[publication]\ncontact_card = ' + json.dumps(card.as_posix()) + '\n')
    creator.create(article.name, root, column='ai')
    assert original == {p.relative_to(article): p.read_bytes() for p in article.rglob('*') if p.is_file()}
    fresh = creator.create('新文章', root)
    assert json.loads((fresh / 'article.json').read_text())['contact_card'] == 'images/contact-card.png'


@pytest.mark.parametrize('title', ['../outside', 'CON', 'a/b', 'a\\b'])
def test_bad_article_names(local_settings, title):
    with pytest.raises(WorkspaceSafetyError):
        creator.create(title, local_settings[1])


def test_path_escape_refused(tmp_path):
    with pytest.raises(WorkspaceSafetyError):
        assert_within(tmp_path / '../outside', tmp_path)


def test_test_workspace_cannot_enable_live(local_settings, monkeypatch):
    local_settings[0].write_text('[wechat]\nenabled = true\n')
    monkeypatch.setenv('CHUANLAB_ALLOW_TEST_ROOT', '1')
    with pytest.raises(ValueError, match='isolated test'):
        settings.require_wechat_enabled()
