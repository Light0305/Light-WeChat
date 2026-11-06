from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / 'shared'))
from settings import load_settings, require_wechat_enabled
from workspace_guard import production_articles_root

from wechat_publisher.client import WeChatClient
from wechat_publisher.config import WeChatConfig, account_fingerprint, load_config
from wechat_publisher.markdown_wechat import (
    add_local_image_metadata,
    audit_rendered_layout,
    build_metadata,
    drop_local_image_sources,
    find_local_image_sources,
    html_package_preview_document,
    html_preview_document,
    markdown_to_wechat_html,
    read_markdown,
    replace_local_image_sources,
    trim_characters,
)
from wechat_publisher.payload import MAX_DIGEST_CHARS, MAX_TITLE_CHARS
from wechat_publisher.payload import DraftArticle, build_draft_payload

ARTICLES_ROOT = production_articles_root()
LIVE_CONFIRMATION = "UPLOAD_APPROVED_DRAFT"
APPROVED_STATES = {'user-approved', 'uploaded', 'verified'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a Markdown article to WeChat draft box.")
    parser.add_argument("--markdown", required=True, type=Path, help="Public article Markdown path.")
    parser.add_argument("--thumb", type=Path, help="Cover image path for thumb material upload.")
    parser.add_argument("--thumb-media-id", help="Existing WeChat thumb_media_id. Skips thumb upload.")
    parser.add_argument("--update-media-id", help="Update this existing draft in place instead of adding a duplicate.")
    parser.add_argument("--title", help="Override the article title sent to WeChat.")
    parser.add_argument("--digest", help="Override the article digest sent to WeChat.")
    parser.add_argument("--author", help="Article author. Defaults to env WECHAT_DEFAULT_AUTHOR.")
    parser.add_argument("--source-url", default="", help="Optional original/content source URL.")
    parser.add_argument("--env-file", type=Path, help="Optional .env file path.")
    parser.add_argument("--out-dir", type=Path, default=Path("wechat-out"), help="Output directory.")
    parser.add_argument(
        "--article-root",
        type=Path,
        help='Direct article folder under the configured workspace/articles directory. Required in live mode.',
    )
    parser.add_argument(
        "--confirm-live-upload",
        default="",
        help=f"Live mode requires the exact value {LIVE_CONFIRMATION}.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Generate HTML and payload without API calls.")
    parser.add_argument(
        "--title-max-chars",
        "--title-max-bytes",
        dest="title_max_chars",
        type=int,
        default=MAX_TITLE_CHARS,
        help=f"Maximum characters for title before trimming. Defaults to {MAX_TITLE_CHARS}; --title-max-bytes is a deprecated alias.",
    )
    parser.add_argument(
        "--no-trim-title",
        action="store_true",
        help="Disable automatic title trimming and fail validation instead.",
    )
    parser.add_argument(
        "--digest-max-chars",
        "--digest-max-bytes",
        dest="digest_max_chars",
        type=int,
        default=MAX_DIGEST_CHARS,
        help=f"Maximum characters for digest before trimming. Defaults to {MAX_DIGEST_CHARS}; --digest-max-bytes is a deprecated alias.",
    )
    parser.add_argument(
        "--no-trim-digest",
        action="store_true",
        help="Disable automatic digest trimming and fail validation instead.",
    )
    parser.add_argument(
        "--skip-body-image",
        action="append",
        default=[],
        help="Local Markdown image src to leave unchanged in live mode. Repeatable.",
    )
    parser.add_argument(
        "--drop-body-image",
        action="append",
        default=[],
        help="Local Markdown image src to remove from article body before upload. Repeatable.",
    )
    parser.add_argument(
        "--drop-thumb-in-body",
        action="store_true",
        help="Remove the cover image from the article body when --thumb lives under the Markdown folder.",
    )
    return parser.parse_args()


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, FileNotFoundError, OSError):
        return False


def _assert_within(path: Path, root: Path, label: str) -> Path:
    root_resolved = root.resolve(strict=False)
    path_resolved = path.resolve(strict=False)
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"{label} must stay under {root_resolved}: {path}") from exc
    for candidate in [path, *path.parents]:
        if candidate.exists() and _is_reparse_point(candidate):
            raise ValueError(f"{label} must not traverse a reparse point: {candidate}")
        if candidate.resolve(strict=False) == root_resolved:
            break
    return path_resolved


def validate_upload_gate(args: argparse.Namespace) -> None:
    thumb = getattr(args, "thumb", None)
    if thumb and not thumb.is_file():
        raise ValueError(f"Cover image does not exist: {thumb}")
    if args.dry_run and args.article_root is None:
        return
    if args.article_root is None:
        raise ValueError("Live mode requires --article-root.")
    article = _assert_within(args.article_root, ARTICLES_ROOT, "article root")
    if article.parent != ARTICLES_ROOT.resolve(strict=False):
        raise ValueError('Article root must be a direct child of the configured articles directory')
    _assert_within(args.markdown, article, "markdown")
    _assert_within(args.out_dir, article / "publishing", "output directory")
    if args.thumb:
        _assert_within(args.thumb, article, "thumb")
    if args.dry_run:
        return
    require_wechat_enabled()
    if args.confirm_live_upload != LIVE_CONFIRMATION:
        raise ValueError(
            f"Live mode requires --confirm-live-upload {LIVE_CONFIRMATION}."
        )
    status_path = article / "publication-status.yaml"
    if not status_path.exists():
        raise ValueError(f"Live mode requires publication status: {status_path}")
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid publication status file: {status_path}") from exc
    if status.get("state") not in APPROVED_STATES or not status.get("approval"):
        raise ValueError("Live mode requires a recorded user-approved state.")
    sys.path.insert(0, str(REPOSITORY / 'scripts'))
    from article_workflow import assert_frozen
    lock = assert_frozen(article)
    approved = (status.get('approval') or {}).get('metadata', {})
    credentials = load_config(getattr(args, 'env_file', None))
    if (approved.get('package_sha256') != lock['sha256'] or approved.get('approval_scope') != 'draft-upload-only'
            or approved.get('account_sha256') != account_fingerprint(credentials)):
        raise ValueError('Upload approval must bind this frozen package and configured account')
    if getattr(args, "update_media_id", None):
        if status.get("state") == "published":
            raise ValueError("A published article cannot be updated as a draft.")
        if args.update_media_id != (status.get("wechat") or {}).get("media_id"):
            raise ValueError("Update media ID must match this article's recorded draft.")


def main() -> int:
    args = parse_args()
    validate_upload_gate(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    config = WeChatConfig('', '', default_author=load_settings().author) if args.dry_run else load_config(args.env_file)
    markdown_text = read_markdown(args.markdown)
    metadata = build_metadata(markdown_text, args.author or config.default_author)
    title = args.title.strip() if args.title else metadata.title
    if not args.no_trim_title:
        title = trim_characters(title, args.title_max_chars)
    digest = args.digest.strip() if args.digest else metadata.digest
    if not args.no_trim_digest:
        digest = trim_characters(digest, args.digest_max_chars)
    content_html = markdown_to_wechat_html(markdown_text)
    rendered_layout = audit_rendered_layout(content_html)
    if any(tag in content_html.lower() for tag in ("<ul", "<ol", "<li")):
        result_warning = (
            "Content contains HTML list tags. WeChat may render bullets/numbers "
            "unstably; prefer paragraph-style lists for public-account drafts."
        )
    else:
        result_warning = ""
    local_images = find_local_image_sources(content_html)
    drop_body_images = set(args.drop_body_image)
    if args.drop_thumb_in_body and args.thumb:
        try:
            thumb_src = args.thumb.resolve().relative_to(args.markdown.resolve().parent).as_posix()
            drop_body_images.add(thumb_src)
        except ValueError:
            pass
    dropped_body_images: list[str] = []
    if drop_body_images:
        content_html, dropped_body_images = drop_local_image_sources(
            content_html,
            args.markdown,
            drop_body_images,
        )
        local_images = find_local_image_sources(content_html)

    content_html = add_local_image_metadata(content_html, args.markdown)
    preview_path = args.out_dir / "preview.html"
    preview_base = args.markdown.resolve().parent.as_uri().rstrip("/") + "/"
    preview_path.write_text(
        html_preview_document(content_html, base_href=preview_base),
        encoding="utf-8",
    )
    package_preview_path = args.out_dir / "package-preview.html"
    cover_src = args.thumb.resolve().as_uri() if args.thumb else None
    package_preview_path.write_text(
        html_package_preview_document(
            title=title,
            digest=digest,
            author=metadata.author,
            cover_src=cover_src,
        ),
        encoding="utf-8",
    )

    thumb_media_id = args.thumb_media_id or "DRY_RUN_THUMB_MEDIA_ID"
    result: dict[str, object] = {
        "mode": "dry-run" if args.dry_run else "live",
        "title": title,
        "title_chars": len(title),
        "title_bytes": len(title.encode("utf-8")),
        "digest": digest,
        "digest_chars": len(digest),
        "digest_bytes": len(digest.encode("utf-8")),
        "preview_html": str(preview_path),
        "package_preview_html": str(package_preview_path),
        "local_images": local_images,
        "dropped_body_images": dropped_body_images,
        "rendered_layout": rendered_layout,
    }
    if result_warning:
        result["warning"] = result_warning

    client: WeChatClient | None = None
    token: str | None = None
    if not args.dry_run:
        client = WeChatClient(config)
        token = client.get_access_token()
        skip_body_images = set(args.skip_body_image)

        def upload_body_image(path: Path) -> str:
            assert client is not None and token is not None
            local_src = path.relative_to(args.markdown.resolve().parent).as_posix()
            if local_src in skip_body_images:
                return local_src
            return client.upload_news_image(path, token)

        content_html, uploaded_images = replace_local_image_sources(
            content_html,
            args.markdown,
            upload_body_image,
        )
        result["uploaded_images"] = uploaded_images
        if not args.thumb_media_id:
            if not args.thumb:
                raise ValueError("Live mode requires --thumb or --thumb-media-id.")
            thumb_media_id = client.upload_thumb_material(args.thumb, token)

        preview_path.write_text(
            html_preview_document(content_html, base_href=preview_base),
            encoding="utf-8",
        )

    article = DraftArticle(
        title=title,
        author=metadata.author,
        digest=digest,
        content=content_html,
        thumb_media_id=thumb_media_id,
        content_source_url=args.source_url,
        need_open_comment=config.default_need_open_comment,
        only_fans_can_comment=config.default_only_fans_can_comment,
    )
    payload = build_draft_payload(article)
    payload_path = args.out_dir / "draft_payload.json"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    result["payload"] = str(payload_path)

    if not args.dry_run:
        assert client is not None and token is not None
        if args.update_media_id:
            result["wechat_response"] = client.update_draft(
                args.update_media_id, payload["articles"][0], token
            )
            result["updated_media_id"] = args.update_media_id
        else:
            result["wechat_response"] = client.add_draft(payload, token)

    result_path = args.out_dir / "result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
