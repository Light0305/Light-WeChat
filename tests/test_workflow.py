import json
import os
from types import SimpleNamespace

import pytest

import article_workflow as workflow
from article_quality import audit, audit_covers
from publication_status import load_status, save_status
from v9_support import input_manifest, read_json, write_json
from wechat_publisher import config as credentials


def test_new_article_contract(article):
    config = read_json(article / 'article.json')
    assert config['delivery'] == 'local-only' and config['contact_card'] is False
    assert not any('website' in key or 'post_' in key for key in config)
    result = audit(article)
    assert result['passed'], result['errors']


def test_two_covers_and_master_suffice(article):
    config, evidence = read_json(article / 'article.json'), read_json(article / 'evidence.json')
    assets = {row['path']: row for row in evidence['assets']}
    assert audit_covers(article, config, assets) == []
    del assets['images/cover.png']['derived_from']
    assert any('derived_from' in error for error in audit_covers(article, config, assets))


def test_freeze_is_not_upload_approval(reviewed):
    workflow.freeze(reviewed)
    state = load_status(reviewed)
    assert state['state'] == 'qa-passed'
    assert not state.get('approval') and state['human_review'] == 'pending'
    workflow.assert_frozen(reviewed)


def test_changed_input_invalidates_reviews(reviewed):
    workflow.freeze(reviewed)
    with (reviewed / 'draft.md').open('a', encoding='utf-8') as stream:
        stream.write('\n\n新增一句，用于测试旧预览失效。\n')
    with pytest.raises(ValueError, match='stale'):
        workflow.assert_frozen(reviewed)


def test_public_metadata_invalidates_version(article, local_settings):
    before = input_manifest(article)['sha256']
    local_settings[0].write_text('[publication]\nauthor = "new-author"\n')
    assert input_manifest(article)['sha256'] != before


def test_upload_disabled_without_config(article):
    with pytest.raises(ValueError, match='WeChat is disabled'):
        workflow.upload(article, confirm_upload=True)


def test_upload_needs_explicit_action(article, monkeypatch):
    monkeypatch.setattr(workflow, 'require_wechat_enabled', lambda: None)
    with pytest.raises(ValueError, match='confirm-upload'):
        workflow.upload(article)
    with pytest.raises(ValueError, match='local-only'):
        workflow.upload(article, confirm_upload=True)


def test_account_switch_and_unbound_media_are_refused(local_settings, monkeypatch):
    monkeypatch.setattr(workflow, 'require_wechat_enabled', lambda: None)
    config = credentials.WeChatConfig('test-account', 'test-local-placeholder')
    monkeypatch.setattr(credentials, 'load_config', lambda *a: config)
    for state in ({'wechat': {'media_id': 'local-test'}},
                  {'wechat': {'media_id': 'local-test', 'account_sha256': 'different-account'}}):
        with pytest.raises(ValueError, match='Configured account differs'):
            workflow.assert_account(state)


def test_simulated_upload_binds_approval_and_avoids_duplicates(reviewed, monkeypatch):
    config = read_json(reviewed / 'article.json')
    config['delivery'] = 'wechat-draft'
    write_json(reviewed / 'article.json', config)
    # Updating delivery invalidates the prior review. Rebuild the synthetic review explicitly.
    from conftest import synthetic_preview
    synthetic_preview(reviewed)
    for role in ('factual', 'editorial', 'visual'):
        workflow.record_review(reviewed, role, f'reviews/{role}.md', 'offline-test')
    workflow.freeze(reviewed)
    monkeypatch.setattr(workflow, 'require_wechat_enabled', lambda: None)
    account = credentials.WeChatConfig('offline-test-account', 'offline-placeholder')
    monkeypatch.setattr(credentials, 'load_config', lambda *a: account)
    calls = []
    def fake_process(command, **kwargs):
        # Replace the child publisher completely; never execute a live upload process.
        calls.append(command)
        output = reviewed / 'publishing/wechat-live'
        write_json(output / 'result.json', {'wechat_response': {'media_id': 'synthetic-media-id'}})
        write_json(output / 'draft_payload.json', {'articles': [{'title': 'synthetic'}]})
        return SimpleNamespace(returncode=0, stderr='')
    monkeypatch.setattr(workflow.subprocess, 'run', fake_process)
    result = workflow.upload(reviewed, confirm_upload=True)
    assert result['state'] == 'uploaded' and len(calls) == 1
    state = load_status(reviewed)
    approval = state['approval']['metadata']
    assert approval['account_sha256'] == credentials.account_fingerprint(account)
    assert approval['package_sha256'] == workflow.assert_frozen(reviewed)['sha256']
    again = workflow.upload(reviewed, confirm_upload=True)
    assert 'already-uploaded' in again['action'] and len(calls) == 1
    changed = credentials.WeChatConfig('other-test-account', 'offline-placeholder')
    monkeypatch.setattr(credentials, 'load_config', lambda *a: changed)
    with pytest.raises(ValueError, match='different configured account'):
        workflow.upload(reviewed, confirm_upload=True)
    assert len(calls) == 1


def test_uncertain_upload_blocks_retry(reviewed, monkeypatch):
    config = read_json(reviewed / 'article.json')
    config['delivery'] = 'wechat-draft'
    write_json(reviewed / 'article.json', config)
    monkeypatch.setattr(workflow, 'require_wechat_enabled', lambda: None)
    monkeypatch.setattr(workflow, 'assert_frozen', lambda article: {'sha256': 'synthetic-package'})
    monkeypatch.setattr(credentials, 'load_config', lambda *a: credentials.WeChatConfig('test', 'placeholder'))
    write_json(reviewed / 'publishing/upload-attempt.json', {'outcome': 'unknown'})
    with pytest.raises(ValueError, match='unclear result'):
        workflow.upload(reviewed, confirm_upload=True)


def test_readback_text_comparison():
    assert workflow.normalized_text('<p>A&nbsp; B</p>') == workflow.normalized_text('<p>A B</p>')


@pytest.mark.browser
@pytest.mark.skipif(os.environ.get('RUN_BROWSER_QA') != '1', reason='Enable explicit local-browser QA')
def test_real_mobile_preview(article):
    result = workflow.preview(article)
    manifest = read_json(article / 'publishing/preview/preview-manifest.json')
    assert len(manifest['files']) >= 21
    assert result['screenshots']
    from v9_support import valid_preview
    assert valid_preview(article, input_manifest(article)['sha256']) == []
    # Retain a copy only when the caller explicitly chooses an audit directory.
    if os.environ.get('BROWSER_QA_OUTPUT'):
        from pathlib import Path
        import shutil
        output = Path(os.environ['BROWSER_QA_OUTPUT'])
        output.mkdir(parents=True, exist_ok=True)
        for width in (375, 390):
            source = article / f'publishing/preview/mobile-{width}/first-screen.png'
            shutil.copyfile(source, output / f'mobile-{width}.png')
