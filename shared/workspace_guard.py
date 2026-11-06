"""Path safety helpers shared by the Chuan Lab skills."""

from __future__ import annotations

import os
import re
import stat
import unicodedata
from pathlib import Path

from settings import load_settings

PROJECT_ROOT = load_settings().workspace
ARTICLES_ROOT = load_settings().articles
WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
ILLEGAL_TITLE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class WorkspaceSafetyError(ValueError):
    """Raised when an article path violates the workspace boundary."""


def normalize_title(value: str) -> str:
    title = unicodedata.normalize("NFC", value)
    title = re.sub(r"\s+", " ", title).strip()
    if not title or title in {".", ".."}:
        raise WorkspaceSafetyError("Article title must not be empty or a dot segment.")
    if ILLEGAL_TITLE.search(title):
        raise WorkspaceSafetyError("Article title contains a Windows-illegal character.")
    if title.endswith((" ", ".")):
        raise WorkspaceSafetyError("Article title must not end with a space or dot.")
    stem = title.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED:
        raise WorkspaceSafetyError(f"Article title uses reserved Windows name: {stem}")
    return title


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attrs = path.lstat().st_file_attributes
    except (AttributeError, FileNotFoundError, OSError):
        return False
    return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def ensure_no_reparse_points(path: Path, stop: Path | None = None) -> None:
    current = Path(path)
    stop_resolved = stop.resolve(strict=False) if stop else None
    for candidate in [current, *current.parents]:
        if candidate.exists() and _is_reparse_point(candidate):
            raise WorkspaceSafetyError(f"Reparse points are not allowed: {candidate}")
        if stop_resolved is not None and candidate.resolve(strict=False) == stop_resolved:
            break


def assert_within(candidate: Path, root: Path) -> Path:
    root = Path(root)
    candidate = Path(candidate)
    ensure_no_reparse_points(root)
    ensure_no_reparse_points(candidate, root)
    root_resolved = root.resolve(strict=False)
    candidate_resolved = candidate.resolve(strict=False)
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise WorkspaceSafetyError(
            f"Path escapes the allowed root: {candidate_resolved}"
        ) from exc
    return candidate_resolved


def production_articles_root(root: Path | None = None) -> Path:
    if root is None and os.environ.get("CHUANLAB_ALLOW_TEST_ROOT") == "1":
        test_root = os.environ.get("CHUANLAB_TEST_ARTICLES_ROOT")
        if test_root:
            root = Path(test_root)
    selected = Path(root) if root is not None else ARTICLES_ROOT
    if selected.resolve(strict=False) != ARTICLES_ROOT.resolve(strict=False):
        if os.environ.get("CHUANLAB_ALLOW_TEST_ROOT") != "1":
            raise WorkspaceSafetyError(
                f"Articles root must resolve to {ARTICLES_ROOT}; got {selected}"
            )
    ensure_no_reparse_points(selected)
    return selected.resolve(strict=False)


def article_directory(title: str, root: Path | None = None) -> Path:
    articles_root = production_articles_root(root)
    return assert_within(articles_root / normalize_title(title), articles_root)


def assert_article_root(path: Path, root: Path | None = None) -> Path:
    articles_root = production_articles_root(root)
    article = assert_within(path, articles_root)
    relative = article.relative_to(articles_root)
    if len(relative.parts) != 1:
        raise WorkspaceSafetyError(
            "Article root must be a direct child of the articles directory."
        )
    normalize_title(relative.name)
    return article


def safe_descendant(article_root: Path, *parts: str) -> Path:
    article_root = assert_article_root(article_root)
    for part in parts:
        path_part = Path(part)
        if path_part.is_absolute() or ".." in path_part.parts:
            raise WorkspaceSafetyError(f"Unsafe relative path component: {part}")
    return assert_within(article_root.joinpath(*parts), article_root)
