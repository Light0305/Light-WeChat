"""Shared, deterministic version binding for the v9 editorial pipeline."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "shared"))
from workspace_guard import assert_article_root, assert_within
from settings import load_settings

PUBLISHER_ROOT = PLUGIN_ROOT / 'tools/wechat-publisher'
KINDS = {"news", "technical", "software", "career", "paper", "interdisciplinary"}
LAYOUTS = {"editorial", "paper", "guide", "gzh-chuan-editorial", "gzh-moyu-green", "gzh-graphite-minimal",
           "gzh-red-white", "gzh-moyu-ticket", "gzh-olive-journal", "gzh-zen-whitespace"}
INPUT_DOCS = ("article.json", "draft.md", "evidence.json", "editor-brief.md", "sources.md",
              "image-ledger.md", "cover-brief.md", "brief.yaml", "assessment.yaml")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(data) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def inside(article: Path, relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts or ":" in relative or "\\" in relative:
        raise ValueError(f"Use an article-relative forward-slash path: {relative}")
    return assert_within(article / p, article)


def load_article(article: Path) -> tuple[Path, dict, dict]:
    article = assert_article_root(article)
    config = read_json(article / "article.json")
    if not isinstance(config, dict):
        raise ValueError("article.json must be an object")
    if config.get("workflow_version") != 9:
        raise ValueError("This command requires article.json workflow_version: 9")
    evidence = read_json(article / "evidence.json")
    if not isinstance(evidence, dict):
        raise ValueError("evidence.json must be an object")
    return article, config, evidence


def input_manifest(article: Path) -> dict:
    files = {}
    for name in INPUT_DOCS:
        p = inside(article, name)
        files[name] = sha(p) if p.is_file() else None
    for directory in ("images", "prompts"):
        assets = inside(article, directory)
        if not assets.exists():
            continue
        for candidate in sorted(assets.rglob("*")):
            p = assert_within(candidate, article)
            if p.is_file():
                if p.name.startswith(".") or p.suffix.lower() in {".env", ".key", ".pem"}:
                    raise ValueError("Do not keep hidden files or credentials in article assets")
                files[p.relative_to(article).as_posix()] = sha(p)
    # Bind both the render implementation and publishing implementation.
    for name in ("publish_to_draft.py", "wechat_publisher/markdown_wechat.py",
                 "wechat_publisher/editorial_layout.py", "wechat_publisher/gzh_layout.py",
                 "wechat_publisher/gzh_components.json", "wechat_publisher/chuan_theme.py",
                 "wechat_publisher/payload.py", 'wechat_publisher/config.py',
                 'wechat_publisher/client.py', 'wechat_publisher/http_safe.py'):
        p = PUBLISHER_ROOT / name
        files["@publisher/" + name] = sha(p) if p.is_file() else None
    for name in ("article_workflow.py", "wechat_ip_wait.py", "v9_support.py", "article_quality.py", "upstream_modules.py", "capture_local_chrome.cjs"):
        files["@pipeline/" + name] = sha(Path(__file__).with_name(name))
    for name in ('settings.py', 'workspace_guard.py', 'publication_status.py'):
        files['@shared/' + name] = sha(PLUGIN_ROOT / 'shared' / name)
    # Non-secret publication metadata affects preview and must invalidate a frozen package.
    settings = load_settings()
    files['@publication'] = object_sha({'author': settings.author, 'name': settings.brand_name})
    for name in ("vendor/wewrite/src/wewrite/commands/content_eval.py",
                 "vendor/gzh-design/scripts/validate_gzh_html.py"):
        path = Path(__file__).resolve().parents[1] / name
        files["@upstream/" + name] = sha(path)
    return {"files": files, "sha256": object_sha(files)}


def preview_fingerprint(article: Path) -> str:
    return sha(inside(article, "publishing/preview/preview-manifest.json"))


def valid_preview(article: Path, current: str) -> list[str]:
    errors = []
    try:
        manifest = read_json(inside(article, "publishing/preview/preview-manifest.json"))
        if manifest.get("input_sha256") != current:
            errors.append("Preview is stale; regenerate it for the current package")
        files = manifest.get("files", {})
        required = {"preview.html", "package-preview.html", "cover-pair-preview.html"}
        for width in (375, 390):
            for kind in ("mobile", "covers", "package"):
                required.update({f"{kind}-{width}/first-screen.png", f"{kind}-{width}/ending-screen.png",
                                 f"{kind}-{width}/visual-audit.json"})
        if not required.issubset(files):
            errors.append("Preview lacks required HTML or 375/390 screenshots")
        for name, expected in files.items():
            p = inside(article, "publishing/preview/" + name)
            if not p.is_file() or sha(p) != expected:
                errors.append(f"Preview artifact changed or missing: {name}")
        for width in (375, 390):
            for kind in ("mobile", "covers", "package"):
                metrics = read_json(inside(article, f"publishing/preview/{kind}-{width}/visual-audit.json"))
                if (metrics.get("viewportWidth") != width or metrics.get("scrollWidth", width + 1) > width
                        or metrics.get("brokenImages", 1) or not metrics.get("visibleTextLength")):
                    errors.append(f"{kind} preview failed at {width}px")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"Valid preview missing: {exc}")
    return errors
