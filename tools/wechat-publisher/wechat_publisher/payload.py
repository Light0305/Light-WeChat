from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAX_TITLE_CHARS = 32
MAX_AUTHOR_CHARS = 16
MAX_DIGEST_CHARS = 128
MAX_CONTENT_CHARS = 20_000
MAX_CONTENT_BYTES = 1_000_000


@dataclass(frozen=True)
class DraftArticle:
    title: str
    author: str
    digest: str
    content: str
    thumb_media_id: str
    content_source_url: str = ""
    need_open_comment: int = 0
    only_fans_can_comment: int = 0


def utf8_len(value: str) -> int:
    return len(value.encode("utf-8"))


def validate_draft_article(article: DraftArticle) -> None:
    errors: list[str] = []
    if not article.title.strip():
        errors.append("title is required")
    elif len(article.title) > MAX_TITLE_CHARS:
        errors.append(f"title is {len(article.title)} characters; max is {MAX_TITLE_CHARS}")

    if article.author and len(article.author) > MAX_AUTHOR_CHARS:
        errors.append(f"author is {len(article.author)} characters; max is {MAX_AUTHOR_CHARS}")

    if len(article.digest) > MAX_DIGEST_CHARS:
        errors.append(f"digest is {len(article.digest)} characters; max is {MAX_DIGEST_CHARS}")
    if not article.content.strip():
        errors.append("content is required")
    elif len(article.content) > MAX_CONTENT_CHARS:
        errors.append(
            f"content is {len(article.content)} characters; max is {MAX_CONTENT_CHARS}"
        )
    elif utf8_len(article.content) > MAX_CONTENT_BYTES:
        errors.append(f"content is {utf8_len(article.content)} bytes; max is {MAX_CONTENT_BYTES}")

    if not article.thumb_media_id.strip():
        errors.append("thumb_media_id is required")

    if article.need_open_comment not in (0, 1):
        errors.append("need_open_comment must be 0 or 1")
    if article.only_fans_can_comment not in (0, 1):
        errors.append("only_fans_can_comment must be 0 or 1")

    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid WeChat draft article: {joined}")


def build_draft_payload(article: DraftArticle) -> dict[str, Any]:
    validate_draft_article(article)
    return {
        "articles": [
            {
                "title": article.title,
                "author": article.author,
                "digest": article.digest,
                "content": article.content,
                "content_source_url": article.content_source_url,
                "thumb_media_id": article.thumb_media_id,
                "need_open_comment": article.need_open_comment,
                "only_fans_can_comment": article.only_fans_can_comment,
            }
        ]
    }
