#!/usr/bin/env python3
"""v9 check, real preview, version-bound review and WeChat draft-only delivery."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from article_quality import audit, save_report
from v9_support import (PUBLISHER_ROOT, input_manifest, inside, load_article, now,
                        preview_fingerprint, read_json, sha, valid_preview, write_json)
from publication_status import STATES, load_status, save_status, transition
from wechat_ip_wait import whitelist_refusal
from settings import load_settings, require_wechat_enabled
from workspace_guard import production_articles_root

CAPTURE = Path(__file__).with_name("capture_local_chrome.cjs")
PRODUCTION_ARTICLES_ROOT = production_articles_root()


def checked(article: Path, delivery=False) -> dict:
    result = audit(article, delivery)
    save_report(article, result)
    if not result["passed"]:
        raise ValueError("QA failed: " + "; ".join(result["errors"]))
    return result


def render(article: Path, markdown: Path, output: Path) -> dict:
    """Use the same renderer and metadata as the live backend, without network/config."""
    _, config, _ = load_article(article)
    sys.path.insert(0, str(PUBLISHER_ROOT))
    from wechat_publisher.markdown_wechat import (add_local_image_metadata, audit_rendered_layout,
        build_metadata, html_package_preview_document, html_preview_document, markdown_to_wechat_html)
    from wechat_publisher.payload import DraftArticle, build_draft_payload
    output.mkdir(parents=True, exist_ok=True)
    text = markdown.read_text(encoding="utf-8-sig")
    meta = build_metadata(text, load_settings().author)
    content = add_local_image_metadata(markdown_to_wechat_html(text), markdown)
    metrics = audit_rendered_layout(content)
    payload = build_draft_payload(DraftArticle(title=meta.title, author=meta.author, digest=meta.digest,
        content=content, thumb_media_id="DRY_RUN_THUMB_MEDIA_ID"))
    (output / "wechat-body.html").write_text(content, encoding="utf-8")
    (output / "preview.html").write_text(html_preview_document(content,
        base_href=article.as_uri().rstrip("/") + "/"), encoding="utf-8")
    cover = inside(article, config["cover"])
    (output / "package-preview.html").write_text(html_package_preview_document(
        title=meta.title, digest=meta.digest, author=meta.author, cover_src=cover.as_uri()), encoding="utf-8")
    square = inside(article, config["square_cover"])
    shared = config.get("cover_profile") == "shared-master-v1"
    square_label = "方形封面 · 同一母图" if shared else "方形封面 · 独立布局"
    # Internal packaging board, not an article evidence image or submitted body.
    pair = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>公众号封面预览</title>"
        "<body style='margin:0;padding:18px;box-sizing:border-box;background:#f5f5f2;"
        "font:15px/1.7 system-ui;color:#18212f;overflow-wrap:anywhere'>"
        f"<h1 style='font-size:23px'>{html.escape(meta.title)}</h1>"
        f"<p>{html.escape(meta.digest)}</p><h2>宽封面</h2>"
        f"<img style='display:block;width:100%;height:auto' src='{cover.as_uri()}'>"
        f"<h2>{square_label}</h2>"
        f"<img style='display:block;width:100%;height:auto' src='{square.as_uri()}'>"
        "<h2>宽封面 · 默认中心方裁切</h2>"
        f"<img style='display:block;width:120px;height:120px;object-fit:cover' src='{cover.as_uri()}'>"
        "<p>本地包装模拟；API 上传宽封面，最终客户端效果由人工审核。</p></body></html>")
    (output / "cover-pair-preview.html").write_text(pair, encoding="utf-8")
    write_json(output / "draft_payload.json", payload)
    result = {"mode": "dry-run", "title": meta.title, "digest": meta.digest,
              "rendered_layout": metrics, "input_sha256": input_manifest(article)["sha256"]}
    write_json(output / "result.json", result)
    return result


def run_capture(source: Path, out: Path, width: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    # Clear only known generated files in this exact output folder, no recursive delete.
    for p in out.iterdir():
        if p.is_file() and p.suffix in {".png", ".json"}:
            p.unlink()
    command = ['node', str(CAPTURE), '--input', str(source), '--out', str(out),
               '--width', str(width), '--height', '844']
    if load_settings().browser:
        command.extend(['--browser', load_settings().browser])
    completed = subprocess.run(command,
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=110)
    if completed.returncode:
        raise ValueError("Browser preview failed: " + completed.stderr[-1500:])


def preview(article: Path) -> dict:
    checked(article)
    current = input_manifest(article)
    out = inside(article, "publishing/preview")
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "preview-manifest.json"
    manifest_path.unlink(missing_ok=True)
    render(article, inside(article, "draft.md"), out)
    for width in (375, 390):
        run_capture(out / "preview.html", out / f"mobile-{width}", width)
        run_capture(out / "cover-pair-preview.html", out / f"covers-{width}", width)
        run_capture(out / "package-preview.html", out / f"package-{width}", width)
    if current != input_manifest(article):
        raise ValueError("Inputs changed while generating preview; regenerate after edits finish")
    files = {}
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "preview-manifest.json":
            files[p.relative_to(out).as_posix()] = sha(p)
    manifest = {"input_sha256": current["sha256"], "created_at": now(), "files": files,
                "scope": "local-browser-only; not a WeChat client visual acceptance"}
    write_json(manifest_path, manifest)
    return {"preview": str(out / "preview.html"), "covers": str(out / "cover-pair-preview.html"),
            "screenshots": [str(out / f"mobile-{w}") for w in (375, 390)],
            "next": "Open and inspect screenshots; then record actual reviews"}


def record_review(article: Path, role: str, report: str, reviewer: str) -> dict:
    checked(article)
    _, config, _ = load_article(article)
    if role == "editorial" and config.get("layout", "").startswith("gzh-"):
        from upstream_modules import editorial_report
        evaluation = editorial_report(article)
        if not evaluation["publishable"]:
            raise ValueError("WeWrite editorial assessment does not pass")
        write_json(inside(article, "reviews/wewrite-editorial-eval.json"), evaluation)
    p = inside(article, report)
    if not p.is_file() or len(p.read_text(encoding="utf-8").strip()) < 40:
        raise ValueError("Review report must contain specific findings, not an empty pass label")
    if not report.startswith("reviews/"):
        raise ValueError("Keep actual review reports under reviews/")
    if not reviewer.strip():
        raise ValueError("Reviewer identity is required")
    current = input_manifest(article)["sha256"]
    result = {"decision": "pass", "reviewer": reviewer, "at": now(), "input_sha256": current,
              "report": report, "report_sha256": sha(p)}
    if role == "visual":
        errors = valid_preview(article, current)
        if errors:
            raise ValueError("; ".join(errors))
        result["preview_sha256"] = preview_fingerprint(article)
    path = inside(article, "review-state.json")
    reviews = read_json(path) if path.exists() else {}
    reviews[role] = result
    write_json(path, reviews)
    return {role: result}


def freeze(article: Path) -> dict:
    checked(article, True)
    _, config, _ = load_article(article)
    attempt_path = inside(article, "publishing/upload-attempt.json")
    if attempt_path.exists() and read_json(attempt_path).get("outcome") in {"in-flight", "unknown"}:
        raise ValueError("Reconcile the uncertain prior upload before freezing another package")
    state = load_status(article, create=True)
    if state["state"] == "published":
        raise ValueError("Do not alter a published article through the draft workflow")
    public = inside(article, "public.md")
    lock_path = inside(article, "publishing/package-lock.json")
    if public.exists():
        revision = inside(article, "publishing/revisions/" + now().replace(":", "-").replace("+", "_"))
        revision.mkdir(parents=True, exist_ok=True)
        shutil.copy2(public, revision / "public.md")
        for src in (lock_path, inside(article, "publication-status.yaml"), inside(article, "review-state.json")):
            if src.exists():
                shutil.copy2(src, revision / src.name)
    public.write_bytes(inside(article, "draft.md").read_bytes())
    lock = {"workflow_version": 9, "created_at": now(), **input_manifest(article),
            "public_sha256": sha(public), "review_sha256": sha(inside(article, "review-state.json")),
            "preview_sha256": preview_fingerprint(article),
            "approval_scope": "draft-upload-only" if config["delivery"] == "wechat-draft" else "local-review"}
    write_json(lock_path, lock)
    if STATES.index(state["state"]) >= STATES.index("qa-passed"):
        state = transition(article, "drafted", actor="v9-freeze", reason="Revalidate revised package", rollback=True)
    # A successful review is not consent to use another person's account.
    target_state = 'qa-passed'
    while state["state"] != target_state:
        target = STATES[STATES.index(state["state"]) + 1]
        state = transition(article, target, actor='agent-editor',
            reason='Current evidence, editorial and visual package passed; upload is a separate explicit action',
            metadata={"approval_scope": "draft-upload-only", "sha256": lock["public_sha256"],
                      "cover_sha256": sha(inside(article, load_article(article)[1]["cover"])),
                      "package_sha256": lock["sha256"]})
    state.update({"workflow_version": 9, "approval_scope": "draft-upload-only" if target_state == "user-approved" else None,
                  "human_review": "pending"})
    save_status(article, state)
    return {"frozen": str(public), "package_sha256": lock["sha256"], "human_review": "pending"}


def assert_frozen(article: Path) -> dict:
    checked(article, True)
    lock = read_json(inside(article, "publishing/package-lock.json"))
    current = input_manifest(article)
    if (lock.get("sha256") != current["sha256"] or lock.get("files") != current["files"]
            or lock.get("public_sha256") != sha(inside(article, "public.md"))
            or lock.get("review_sha256") != sha(inside(article, "review-state.json"))
            or lock.get("preview_sha256") != preview_fingerprint(article)):
        raise ValueError("Frozen package changed; repeat affected review, preview and freeze")
    return lock


def upload(article: Path, env_file: Path | None = None, resume_after_whitelist: bool = False,
           confirm_upload: bool = False) -> dict:
    require_wechat_enabled()
    if not confirm_upload:
        raise ValueError('Upload requires --confirm-upload after the user authorizes this draft upload')
    _, config, _ = load_article(article)
    if config.get("delivery") != "wechat-draft":
        raise ValueError("This article is local-only; upload is disabled")
    if article.parent.resolve() != PRODUCTION_ARTICLES_ROOT.resolve():
        raise ValueError("Isolated test workspaces cannot upload to the real draft box")
    sys.path.insert(0, str(PUBLISHER_ROOT))
    from wechat_publisher.config import account_fingerprint, assert_credentials, load_config
    credentials = load_config(env_file)
    assert_credentials(credentials)
    account = account_fingerprint(credentials)
    lock = assert_frozen(article)
    state = load_status(article)
    if state["state"] == "published":
        raise ValueError("Published article cannot be changed as a draft")
    previous_account = state.get('wechat', {}).get('account_sha256')
    if state.get('wechat', {}).get('media_id') and not previous_account:
        raise ValueError('Imported draft state lacks an account binding; do not reuse its media ID')
    if previous_account and previous_account != account:
        raise ValueError('This draft belongs to a different configured account; do not update or reconcile it here')
    attempt_path = inside(article, "publishing/upload-attempt.json")
    if attempt_path.exists() and read_json(attempt_path).get("outcome") in {"in-flight", "unknown"}:
        raise ValueError("Prior upload has an unclear result; run reconcile-upload before retrying")
    if attempt_path.exists() and read_json(attempt_path).get("outcome") == "waiting-whitelist":
        waiting = read_json(attempt_path)
        if waiting.get('account_sha256') != account:
            raise ValueError('The waiting upload belongs to a different configured account')
        if not resume_after_whitelist:
            raise ValueError("Waiting for the user to add the WeChat IP whitelist; do not retry yet")
        if waiting.get("requires_reconcile"):
            raise ValueError("Whitelist restored; run reconcile-upload before resuming the uncertain draft request")
        if waiting.get("package_sha256") != lock["sha256"]:
            raise ValueError("The waiting frozen package changed; review the pending article version before resuming")
    wechat = state.get("wechat", {})
    if wechat.get("package_sha256") == lock["sha256"] and state["state"] in {"uploaded", "verified"}:
        return {"media_id": wechat.get("media_id"), "action": "already-uploaded; verify without duplicating"}
    if state['state'] == 'qa-passed':
        state = transition(article, 'user-approved', actor='user-explicit-draft-upload',
            reason='Explicit request to upload this frozen version to the configured account draft box',
            metadata={'approval_scope': 'draft-upload-only', 'package_sha256': lock['sha256'],
                      'account_sha256': account})
    if state['state'] not in {'user-approved', 'uploaded', 'verified'}:
        raise ValueError('A frozen, reviewed package is required before upload')
    render(article, inside(article, "public.md"), inside(article, "publishing/wechat-dry-run"))
    out = inside(article, "publishing/wechat-live")
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "result.json"
    result_path.unlink(missing_ok=True)
    (out / "draft_payload.json").unlink(missing_ok=True)
    command = [sys.executable, str(PUBLISHER_ROOT / "publish_to_draft.py"), "--markdown", str(article / "public.md"),
               "--article-root", str(article), "--thumb", str(inside(article, config["cover"])),
               "--out-dir", str(out), "--confirm-live-upload", "UPLOAD_APPROVED_DRAFT",
               "--no-trim-title", "--no-trim-digest"]
    if wechat.get("media_id"):
        command.extend(["--update-media-id", wechat["media_id"]])
    if env_file:
        command.extend(["--env-file", str(env_file)])
    attempt = {"at": now(), "package_sha256": lock["sha256"], "outcome": "in-flight", 'account_sha256': account,
               "operation": "update" if wechat.get("media_id") else "add", "media_id": wechat.get("media_id")}
    write_json(attempt_path, attempt)
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300)
        if completed.returncode or not result_path.exists():
            attempt.update({"outcome": "unknown", "exit_code": completed.returncode})
            write_json(attempt_path, attempt)
            # Keep local diagnostic text redacted; API exception strings may include query parameters.
            diagnostic = re.sub(r"(?i)((?:access_token|secret|appid)=)[^&\s'\"]+", r"\1[REDACTED]",
                                completed.stderr[-6000:])
            (out / "error-redacted.log").write_text(diagnostic, encoding="utf-8")
            refusal = whitelist_refusal(diagnostic, draft_payload_exists=(out / "draft_payload.json").exists())
            if refusal:
                attempt.update(refusal)
                write_json(attempt_path, attempt)
                return {**attempt, "next": "Wait for user whitelist confirmation; then resume the same frozen draft"}
            raise ValueError("Draft upload failed/uncertain; see redacted local error, reconcile before retry")
    except (subprocess.TimeoutExpired, OSError):
        attempt["outcome"] = "unknown"
        write_json(attempt_path, attempt)
        raise ValueError("Upload interrupted/uncertain; reconcile draft box before retry") from None
    result = read_json(result_path)
    media_id = (result.get("wechat_response") or {}).get("media_id") or result.get("updated_media_id")
    if not media_id:
        attempt["outcome"] = "unknown"
        write_json(attempt_path, attempt)
        raise ValueError("No confirmed media_id returned; reconcile before retry")
    state = mark_uploaded(article, media_id, lock["sha256"], str(result_path), account)
    attempt.update({"outcome": "confirmed", "media_id": media_id})
    write_json(attempt_path, attempt)
    return {"media_id": media_id, "state": state["state"], "human_review": "pending", "next": "verify"}


def mark_uploaded(article: Path, media_id: str, package_sha: str, result_path: str, account: str) -> dict:
    state = load_status(article)
    if state["state"] == "verified":
        state = transition(article, "user-approved", actor="v9-delivery", reason="Draft revision", rollback=True)
    if state["state"] == "user-approved":
        state = transition(article, "uploaded", actor="v9-delivery", reason="Draft upload receipt confirmed",
                           metadata={"media_id": media_id, "approval_scope": "draft-upload-only"})
    if state["state"] != "uploaded":
        raise ValueError("Unexpected state after draft upload")
    state["wechat"] = {**state.get("wechat", {}), "media_id": media_id,
                       "package_sha256": package_sha, "upload_result": result_path, 'account_sha256': account}
    payload = inside(article, "publishing/wechat-live/draft_payload.json")
    if not payload.is_file():
        raise ValueError("Cannot confirm upload without its exact submitted payload")
    state["wechat"]["payload_sha256"] = sha(payload)
    state.update({"human_review": "pending", "approval_scope": "draft-upload-only"})
    save_status(article, state)
    return state


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.code_depth = 0
        self.code_parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {"pre", "code"}:
            self.code_depth += 1
    def handle_endtag(self, tag):
        if tag in {"pre", "code"} and self.code_depth:
            self.code_depth -= 1
            if self.code_depth == 0:
                import hashlib
                text = "".join(self.code_parts).replace("\r\n", "\n").strip()
                self.parts.append("[CODE:" + hashlib.sha256(text.encode("utf-8")).hexdigest() + "]")
                self.code_parts = []
    def handle_data(self, data):
        (self.code_parts if self.code_depth else self.parts).append(data)


def normalized_text(content: str) -> str:
    parser = _Text()
    parser.feed(content)
    return re.sub(r"\s+", "", "".join(parser.parts))


def wechat_image_identity(src: str) -> tuple:
    """Accept only the observed WeChat HTTP/HTTPS and original/640 rewrites."""
    parsed = urlsplit(html.unescape(src))
    if (parsed.scheme in {"http", "https"} and parsed.netloc == "mmbiz.qpic.cn"
            and re.fullmatch(r"/(?:sz_)?mmbiz_(?:png|jpg|jpeg|gif|webp)/[^/]+/(?:0|640)", parsed.path)):
        return ("wechat-image", parsed.netloc, parsed.path.rsplit("/", 1)[0],
                parsed.query, parsed.fragment)
    return ("exact-url", src)


def compare_server(expected: dict, item: dict) -> list[str]:
    errors = []
    for key in ("title", "digest"):
        if expected.get(key) != item.get(key):
            errors.append(f"Server {key} differs from frozen upload")
    if normalized_text(expected.get("content", "")) != normalized_text(item.get("content", "")):
        errors.append("Server full text differs from frozen upload")
    expected_imgs = re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', expected.get("content", ""), re.I)
    actual_imgs = re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', item.get("content", ""), re.I)
    if list(map(wechat_image_identity, actual_imgs)) != list(map(wechat_image_identity, expected_imgs)):
        errors.append("Server image count/order/URLs differ from uploaded payload")
    if expected.get("thumb_media_id") and expected["thumb_media_id"] != item.get("thumb_media_id"):
        errors.append("Server cover differs from uploaded payload")
    return errors


def api_client(env_file=None):
    require_wechat_enabled()
    sys.path.insert(0, str(PUBLISHER_ROOT))
    from wechat_publisher.client import WeChatClient
    from wechat_publisher.config import load_config
    client = WeChatClient(load_config(env_file))
    return client, client.get_access_token()


def api_post(client, token: str, endpoint: str, body: dict) -> dict:
    return client.post_json(endpoint, body, token)


def assert_account(state: dict, env_file=None) -> str:
    require_wechat_enabled()
    sys.path.insert(0, str(PUBLISHER_ROOT))
    from wechat_publisher.config import account_fingerprint, assert_credentials, load_config
    config = load_config(env_file)
    assert_credentials(config)
    account = account_fingerprint(config)
    recorded = state.get('wechat', {}).get('account_sha256')
    if (recorded and recorded != account) or (state.get('wechat', {}).get('media_id') and not recorded):
        raise ValueError('Configured account differs from this recorded draft')
    return account


def verify(article: Path, env_file=None) -> dict:
    require_wechat_enabled()
    lock = assert_frozen(article)
    state = load_status(article)
    assert_account(state, env_file)
    media_id = state.get("wechat", {}).get("media_id")
    if not media_id or state["state"] not in {"uploaded", "verified"}:
        raise ValueError("No confirmed draft upload is available to verify")
    payload_path = inside(article, "publishing/wechat-live/draft_payload.json")
    if state.get("wechat", {}).get("payload_sha256") != sha(payload_path):
        raise ValueError("Submitted payload changed since upload; restore the recorded payload before verification")
    expected = read_json(payload_path)["articles"][0]
    # Read-back must match both the submitted payload and the actual frozen manuscript.
    sys.path.insert(0, str(PUBLISHER_ROOT))
    from wechat_publisher.markdown_wechat import build_metadata, markdown_to_wechat_html
    frozen_text = inside(article, "public.md").read_text(encoding="utf-8-sig")
    frozen_meta = build_metadata(frozen_text, expected.get('author', load_settings().author))
    frozen_body = markdown_to_wechat_html(frozen_text)
    if (frozen_meta.title != expected.get("title") or frozen_meta.digest != expected.get("digest")
            or normalized_text(frozen_body) != normalized_text(expected.get("content", ""))
            or len(re.findall(r"<img\b", frozen_body, re.I)) != len(re.findall(r"<img\b", expected.get("content", ""), re.I))):
        raise ValueError("Submitted payload differs from frozen manuscript; do not mark draft verified")
    client, token = api_client(env_file)
    data = api_post(client, token, "draft/get", {"media_id": media_id})
    out = inside(article, "publishing/wechat-verification")
    write_json(out / "draft-get.json", data)
    items = data.get("news_item") or []
    errors = compare_server(expected, items[0]) if len(items) == 1 else ["Expected exactly one draft article"]
    # Check the exact public image URLs actually saved by WeChat after its rewrites.
    import requests
    saved_content = items[0].get("content", "") if len(items) == 1 else ""
    for src in re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', saved_content, re.I):
        from urllib.parse import urlparse
        hostname = urlparse(src).hostname or ""
        if not (hostname == "mmbiz.qpic.cn" or hostname.endswith(".qpic.cn")):
            errors.append("Uploaded image URL is not a recognized WeChat image host")
            continue
        try:
            with requests.get(src, timeout=20, stream=True) as response:
                if response.status_code != 200 or not response.headers.get("Content-Type", "").startswith("image/"):
                    errors.append("Uploaded image unavailable or non-image")
        except requests.RequestException:
            errors.append("Uploaded image fetch failed")
    summary = {"passed": not errors, "media_id": media_id, "checked_at": now(),
               "package_sha256": lock["sha256"], "errors": errors, "human_review": "pending",
               "scope": "API content read-back; not client visual acceptance"}
    write_json(out / "summary.json", summary)
    if errors:
        raise ValueError("Draft verification failed: " + "; ".join(errors))
    if state["state"] == "uploaded":
        state = transition(article, "verified", actor="v9-readback", reason="Frozen content and images match API read-back")
    state["wechat"]["verification_summary"] = str(out / "summary.json")
    state["human_review"] = "pending"
    save_status(article, state)
    return summary


def reconcile(article: Path, env_file=None) -> dict:
    """Read-only recovery after an uncertain add/update; never blindly resend."""
    require_wechat_enabled()
    lock = assert_frozen(article)
    attempt_path = inside(article, "publishing/upload-attempt.json")
    attempt = read_json(attempt_path)
    account = assert_account(load_status(article), env_file)
    if attempt.get('account_sha256') != account:
        raise ValueError('Configured account differs from the uncertain upload')
    if attempt.get("outcome") == "waiting-whitelist" and not attempt.get("requires_reconcile"):
        return {"action": "Waiting for user whitelist confirmation; no draft request was sent", "scope": "wechat-draft-upload-only"}
    if attempt.get("outcome") not in {"unknown", "in-flight", "waiting-whitelist"}:
        return {"action": "no unresolved attempt"}
    if attempt.get("package_sha256") != lock["sha256"]:
        raise ValueError("Resolve the uncertain prior version before replacing its frozen package")
    payload_path = inside(article, "publishing/wechat-live/draft_payload.json")
    if not payload_path.exists():
        # Backend saves payload before draft/add; a missing payload means no add was reached.
        attempt["outcome"] = "not-sent"
        write_json(attempt_path, attempt)
        return {"action": "No draft request was sent; retry permitted"}
    expected = read_json(payload_path)["articles"][0]
    client, token = api_client(env_file)
    if attempt.get("media_id"):
        data = api_post(client, token, "draft/get", {"media_id": attempt["media_id"]})
        candidates = [{"media_id": attempt["media_id"], "content": data}]
        complete = True
    else:
        candidates, complete = [], False
        for offset in range(0, 500, 20):
            data = api_post(client, token, "draft/batchget", {"offset": offset, "count": 20, "no_content": 0})
            candidates.extend(data.get("item") or [])
            if offset + 20 >= data.get("total_count", 10**9):
                complete = True
                break
    matches = [c for c in candidates if len(c.get("content", {}).get("news_item", [])) == 1
               and not compare_server(expected, c["content"]["news_item"][0])]
    if len(matches) == 1:
        media_id = matches[0]["media_id"]
        mark_uploaded(article, media_id, lock["sha256"], "reconciled-via-draft-read", account)
        attempt.update({"outcome": "confirmed", "media_id": media_id})
    elif not matches and complete:
        attempt["outcome"] = "not-found-after-read"
    else:
        raise ValueError("Draft reconciliation inconclusive or ambiguous; do not resend")
    write_json(attempt_path, attempt)
    return {"outcome": attempt["outcome"], "media_id": attempt.get("media_id"), "human_review": "pending"}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["check", "preview", "record-review", "freeze", "upload", "verify", "reconcile-upload"])
    p.add_argument("--resume-after-whitelist", action="store_true", help="Use only after the user confirms the refused WeChat IP was added")
    p.add_argument('--confirm-upload', action='store_true', help='Use only for a user-authorized draft upload')
    p.add_argument("article", type=Path)
    p.add_argument("--delivery", action="store_true")
    p.add_argument("--role", choices=["factual", "editorial", "visual"])
    p.add_argument("--report")
    p.add_argument("--reviewer", default="agent-editor")
    p.add_argument("--env-file", type=Path)
    args = p.parse_args(argv)
    try:
        article, _, _ = load_article(args.article)
        if args.command == "check":
            result = audit(article, args.delivery)
            save_report(article, result)
        elif args.command == "preview":
            result = preview(article)
        elif args.command == "record-review":
            if not args.role or not args.report:
                p.error("record-review requires --role and --report")
            result = record_review(article, args.role, args.report, args.reviewer)
        elif args.command == "freeze":
            result = freeze(article)
        elif args.command == "upload":
            result = upload(article, args.env_file, args.resume_after_whitelist, args.confirm_upload)
        elif args.command == "verify":
            result = verify(article, args.env_file)
        else:
            result = reconcile(article, args.env_file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("passed") is False else 0
    except (ValueError, OSError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        # Avoid leaking request URLs with access tokens in an exception string.
        message = re.sub(r"(?i)((?:access_token|secret|appid)=)[^&\s'\"]+", r"\1[REDACTED]", str(exc))
        print(json.dumps({"passed": False, "error": message}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
