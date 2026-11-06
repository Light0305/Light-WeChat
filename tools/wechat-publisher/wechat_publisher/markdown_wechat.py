from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import markdown
from PIL import Image, UnidentifiedImageError

from wechat_publisher.chuan_theme import (
    BLOCKQUOTE_P_STYLE,
    BLOCKQUOTE_STYLE,
    BODY_P_STYLE,
    MEDIA_P_STYLE,
    CHUAN_COMPONENTS,
    H2_STYLE,
    H2_WRAP_STYLE,
    H3_STYLE,
    IMAGE_STYLE,
    INLINE_CODE_STYLE,
    LI_STYLE,
    OL_STYLE,
    ORNAMENT_IMAGE_STYLE,
    PRE_CODE_STYLE,
    PRE_STYLE,
    SEP_STYLE,
    STRONG_STYLE,
    TABLE_STYLE,
    TD_STYLE,
    TH_STYLE,
    UL_STYLE,
)


@dataclass(frozen=True)
class ArticleMetadata:
    title: str
    digest: str
    author: str


META_COMMENT_RE = re.compile(
    r"^\s*<!--\s*(title|digest|subtitle|deck|author|mode|pillar|image-count-rationale|layout)\s*:\s*(.*?)\s*-->\s*$",
    re.I,
)


def collapse_inline_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_comment_metadata(markdown_text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in markdown_text.splitlines():
        match = META_COMMENT_RE.match(line)
        if not match:
            continue
        key = match.group(1).lower()
        value = collapse_inline_text(match.group(2))
        if value:
            metadata[key] = value
    return metadata


def extract_title(markdown_text: str) -> str:
    metadata = extract_comment_metadata(markdown_text)
    if metadata.get("title"):
        return metadata["title"]
    for line in markdown_text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return collapse_inline_text(match.group(1))
    for line in markdown_text.splitlines():
        if line.strip():
            return collapse_inline_text(line.strip().lstrip("#"))
    raise ValueError("Cannot infer title from empty markdown.")


def extract_digest(markdown_text: str, title: str, max_len: int = 128) -> str:
    metadata = extract_comment_metadata(markdown_text)
    for key in ("digest", "subtitle", "deck"):
        if metadata.get(key):
            return metadata[key][:max_len]
    clean_lines: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if META_COMMENT_RE.match(stripped):
            continue
        if stripped.startswith("!["):
            continue
        if stripped.startswith("副标题"):
            stripped = stripped.split("：", 1)[-1].strip()
        clean_lines.append(collapse_inline_text(re.sub(r"[*_`>]+", "", stripped)))
        if clean_lines:
            break
    digest = clean_lines[0] if clean_lines else title
    return digest[:max_len]


def trim_utf8_bytes(value: str, max_bytes: int) -> str:
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive.")
    clean = collapse_inline_text(value)
    if len(clean.encode("utf-8")) <= max_bytes:
        return clean

    output: list[str] = []
    used = 0
    for char in clean:
        size = len(char.encode("utf-8"))
        if used + size > max_bytes:
            break
        output.append(char)
        used += size
    return "".join(output).rstrip(" \t\r\n，。；、：:;,.!?！？")


def trim_characters(value: str, max_chars: int) -> str:
    if max_chars < 1:
        raise ValueError("max_chars must be positive.")
    clean = collapse_inline_text(value)
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip(" \t\r\n，。；、：:;,.!?！？")


def strip_frontmatter_like_metadata(markdown_text: str) -> str:
    forbidden_prefixes = (
        "栏目：",
        "目标读者：",
        "目标用户：",
        "预计阅读时间：",
        "封面图方向：",
        "素材：",
        "素材建议：",
        "资料来源：",
        "参考资料：",
        "Source：",
        "Sources：",
    )
    lines = []
    dropped_leading_title = False
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if META_COMMENT_RE.match(stripped):
            continue
        if not dropped_leading_title and re.match(r"^#\s+.+", stripped):
            dropped_leading_title = True
            continue
        if (
            stripped.startswith("副标题")
            or stripped.startswith("摘要：")
            or stripped.startswith("导语：")
        ):
            continue
        if any(stripped.startswith(prefix) for prefix in forbidden_prefixes):
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


CUSTOM_BLOCK_RE = re.compile(r"^:::([A-Za-z][A-Za-z0-9_-]*)\s*$")
ALLOWED_CHUAN_BLOCKS = set(CHUAN_COMPONENTS) | {"sep"}


def format_component_inline(text: str) -> str:
    escaped = html.escape(text.strip(), quote=True)
    escaped = re.sub(
        r"`([^`]+)`",
        rf'<code style="{INLINE_CODE_STYLE}">\1</code>',
        escaped,
    )
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong style="font-weight:800;color:inherit;">\1</strong>',
        escaped,
        flags=re.S,
    )
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" style="color:#0d6e5b;text-decoration:none;">\1</a>',
        escaped,
    )
    return escaped


def format_component_text(text: str) -> str:
    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n+", text.strip())
        if block.strip()
    ]
    output: list[str] = []
    previous_was_heading = False
    for index, block in enumerate(blocks):
        heading = re.fullmatch(r"#{2,4}\s+(.+)", block, flags=re.S)
        if heading:
            margin_top = "0" if index == 0 else "12px"
            content = format_component_inline(heading.group(1))
            output.append(
                '<span style="display:block;'
                f"margin:{margin_top} 0 4px;"
                'font-size:1em;line-height:1.5;font-weight:800;color:inherit;">'
                f"{content}</span>"
            )
            previous_was_heading = True
            continue

        content = format_component_inline(block).replace("\n", "<br>")
        if index == 0:
            output.append(content)
        else:
            margin_top = "0" if previous_was_heading else "4px"
            output.append(
                f'<span style="display:block;margin-top:{margin_top};">'
                f"{content}</span>"
            )
        previous_was_heading = False
    return "".join(output)


def render_chuan_component(name: str, text: str) -> str:
    theme = CHUAN_COMPONENTS[name]
    content = format_component_text(text)
    if not theme.label:
        return f'<section class="cl-{name}">{content}</section>'
    return (
        f'<section class="cl-{name}">'
        f'<span style="{theme.label_style}">{theme.label}</span><br>{content}'
        "</section>"
    )


def convert_chuan_blocks(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: list[str] = []
    block: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal block, buffer
        if block is None:
            return
        text = "\n".join(buffer).strip()
        output.append(render_chuan_component(block, text))
        block = None
        buffer = []

    for line in lines:
        stripped = line.strip()
        match = CUSTOM_BLOCK_RE.fullmatch(stripped)
        if match:
            name = match.group(1)
            if name not in ALLOWED_CHUAN_BLOCKS:
                raise ValueError(f"Unknown Chuan Lab block: {name}")
            if name == "sep":
                flush()
                output.append('<section class="cl-sep"></section>')
                continue
            if block is not None:
                raise ValueError(f"Nested Chuan Lab block is not supported: {name}")
            flush()
            block = name
            buffer = []
            continue
        if stripped == ":::":
            if block is None:
                raise ValueError("Unexpected Chuan Lab block closing marker.")
            flush()
            continue
        if stripped.startswith(":::"):
            raise ValueError(f"Malformed Chuan Lab block marker: {stripped}")
        if block is not None:
            buffer.append(line)
        else:
            output.append(line)
    flush()
    return "\n".join(output).strip() + "\n"


def markdown_to_wechat_html(markdown_text: str) -> str:
    public_md = strip_frontmatter_like_metadata(markdown_text)
    public_md = convert_chuan_blocks(public_md)
    body = markdown.markdown(
        public_md,
        extensions=["extra", "sane_lists", "tables"],
        output_format="html5",
    )
    layout = extract_comment_metadata(markdown_text).get("layout")
    if layout and layout.startswith("gzh-"):
        from wechat_publisher.gzh_layout import apply_gzh_layout
        return apply_gzh_layout(body, layout)
    body = apply_wechat_inline_styles(body)
    if layout:
        from wechat_publisher.editorial_layout import apply_editorial_layout
        body = apply_editorial_layout(body, layout)
    return wrap_wechat_styles(body)


def audit_rendered_layout(content_html: str) -> dict[str, int]:
    # Native gzh-design components carry their own intentional spacing. Check
    # them with the upstream platform validator, not the legacy zero-gap rule.
    if 'data-gzh-theme="' in content_html:
        return {"double_breaks": 0, "raw_markdown_subheadings": 0,
                "unexpected_paragraph_spacing": 0}
    paragraph_tags = re.findall(r'<p\b[^>]*>', content_html, flags=re.I)
    unexpected_paragraph_spacing = 0
    for tag in paragraph_tags:
        style_match = re.search(r'\bstyle="([^"]*)"', tag, flags=re.I)
        if not style_match:
            continue
        style = style_match.group(1)
        margin = re.search(r"(?:^|;)\s*margin\s*:\s*([^;]+)", style, flags=re.I)
        if not margin:
            continue
        normalized = re.sub(r"\s+", " ", margin.group(1).strip().lower())
        theme_match = re.search(r'\bdata-cl-layout="(editorial|paper|guide)"', tag)
        allowed = {"0"}
        if theme_match:
            from wechat_publisher.editorial_layout import THEMES
            gap = THEMES[theme_match.group(1)]["gap"]
            allowed.update({"0 0 0px", f"0 0 {gap}px"})
        if normalized not in allowed:
            unexpected_paragraph_spacing += 1
    metrics = {
        "double_breaks": len(
            re.findall(r"<br[^>]*>\s*<br\b", content_html, flags=re.I)
        ),
        "raw_markdown_subheadings": len(
            re.findall(r"(?:^|>)\s*#{2,4}\s+", content_html)
        ),
        "unexpected_paragraph_spacing": unexpected_paragraph_spacing,
    }
    failures = [name for name, count in metrics.items() if count]
    if failures:
        details = ", ".join(f"{name}={metrics[name]}" for name in failures)
        raise ValueError(f"Rendered WeChat layout audit failed: {details}")
    return metrics


def apply_wechat_inline_styles(body_html: str) -> str:
    body_html = re.sub(
        r"<h2>(.*?)</h2>",
        rf'<section style="{H2_WRAP_STYLE}"><h2 style="{H2_STYLE}">\1</h2></section>',
        body_html,
        flags=re.S,
    )
    body_html = re.sub(
        r"<h3>(.*?)</h3>",
        rf'<h3 style="{H3_STYLE}">\1</h3>',
        body_html,
        flags=re.S,
    )
    def style_paragraph(match: re.Match[str]) -> str:
        inner = match.group(1)
        # Images and component wrappers are not running prose: never indent them.
        style = MEDIA_P_STYLE if re.search(r"<img\b|<section\b", inner, re.I) else BODY_P_STYLE
        return f'<p style="{style}">{inner}</p>'

    body_html = re.sub(r"<p>(.*?)</p>", style_paragraph, body_html, flags=re.S)
    body_html = re.sub(
        r'<p style="[^"]*"><section class="cl-([a-z-]+)">(.*?)</section></p>',
        r'<section class="cl-\1">\2</section>',
        body_html,
        flags=re.S,
    )
    body_html = re.sub(
        r'<p(?:\s+style="[^"]*")?\s+class="cl-sep">(.*?)</p>|<p style="[^"]*"><span class="cl-sep">(.*?)</span></p>|<p style="[^"]*">· · ·</p>|<section class="cl-sep"></section>',
        f'<section style="{SEP_STYLE}"></section>',
        body_html,
        flags=re.S,
    )
    for name, theme in CHUAN_COMPONENTS.items():
        body_html = re.sub(
            rf'<section class="cl-{re.escape(name)}">(.*?)</section>',
            rf'<section style="{theme.container_style}">\1</section>',
            body_html,
            flags=re.S,
        )
    body_html = re.sub(
        r"<blockquote>",
        f'<blockquote style="{BLOCKQUOTE_STYLE}">',
        body_html,
    )
    body_html = re.sub(
        r'(<blockquote style="[^"]*">\s*)<p style="[^"]*">(.*?)</p>(\s*</blockquote>)',
        rf'\1<p style="{BLOCKQUOTE_P_STYLE}">\2</p>\3',
        body_html,
        flags=re.S,
    )
    body_html = re.sub(
        r"<ul>",
        f'<ul style="{UL_STYLE}">',
        body_html,
    )
    body_html = re.sub(
        r"<ol>",
        f'<ol style="{OL_STYLE}">',
        body_html,
    )
    body_html = re.sub(
        r"<li>",
        f'<li style="{LI_STYLE}">',
        body_html,
    )
    body_html = re.sub(
        r"<table>",
        f'<table style="{TABLE_STYLE}">',
        body_html,
    )
    def style_table_cell(match: re.Match[str]) -> str:
        tag, existing = match.group(1), match.group(2) or ""
        base = TH_STYLE if tag == "th" else TD_STYLE
        return f'<{tag} style="{base}{existing}">'

    body_html = re.sub(
        r'<(th|td)(?:\s+style="([^"]*)")?>',
        style_table_cell,
        body_html,
    )
    body_html = re.sub(
        r"<pre><code>(.*?)</code></pre>",
        rf'<pre style="{PRE_STYLE}"><code style="{PRE_CODE_STYLE}">\1</code></pre>',
        body_html,
        flags=re.S,
    )
    body_html = re.sub(
        r"<code>(.*?)</code>",
        rf'<code style="{INLINE_CODE_STYLE}">\1</code>',
        body_html,
        flags=re.S,
    )
    body_html = re.sub(
        r"<strong>(.*?)</strong>",
        rf'<strong style="{STRONG_STYLE}">\1</strong>',
        body_html,
        flags=re.S,
    )
    body_html = re.sub(
        r"<img\b(?![^>]*\bstyle=)([^>]*)>",
        rf'<img style="{IMAGE_STYLE}"\1>',
        body_html,
        flags=re.I,
    )
    body_html = re.sub(
        r'<img style="[^"]*"([^>]*src="[^"]*(?:ornament-|transition-|texture-)[^"]*"[^>]*)>',
        rf'<img style="{ORNAMENT_IMAGE_STYLE}"\1>',
        body_html,
        flags=re.I,
    )
    return body_html


def wrap_wechat_styles(body_html: str) -> str:
    # Keep the submitted draft body flat. WeChat's editor/API can be fussy with
    # one giant wrapper around a full article, especially when images and tables
    # are mixed in the same payload.
    return body_html.strip()


def build_metadata(markdown_text: str, author: str) -> ArticleMetadata:
    title = extract_title(markdown_text)
    digest = extract_digest(markdown_text, title)
    return ArticleMetadata(title=title, digest=digest, author=author)


def read_markdown(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def html_preview_document(content_html: str, base_href: str | None = None) -> str:
    base = f'\n  <base href="{html.escape(base_href, quote=True)}">' if base_href else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">{base}
  <title>WeChat Preview</title>
</head>
<body style="max-width:720px;margin:32px auto;padding:0 18px;background:#fff;">
{content_html}
</body>
</html>
"""


def html_package_preview_document(
    *,
    title: str,
    digest: str,
    author: str,
    cover_src: str | None,
) -> str:
    safe_title = html.escape(title, quote=True)
    safe_digest = html.escape(digest, quote=True)
    safe_author = html.escape(author, quote=True)
    feed_cover = (
        f'<img src="{html.escape(cover_src, quote=True)}" alt="封面" '
        'style="display:block;width:100%;aspect-ratio:2.35/1;object-fit:cover;">'
        if cover_src
        else '<section style="width:100%;aspect-ratio:2.35/1;background:#eef1f3;"></section>'
    )
    share_cover = (
        f'<img src="{html.escape(cover_src, quote=True)}" alt="分享缩略图" '
        'style="display:block;width:90px;height:90px;object-fit:cover;">'
        if cover_src
        else '<section style="width:90px;height:90px;background:#eef1f3;"></section>'
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WeChat Package Preview</title>
</head>
<body style="margin:0;background:#f3f4f5;color:#111;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;">
  <main style="max-width:390px;margin:0 auto;padding:18px 14px 34px;box-sizing:border-box;">
    <section style="margin:0 0 12px;color:#7a7f86;font-size:12px;">订阅号消息 · 模拟预览</section>
    <article style="background:#fff;padding:14px;border-radius:4px;box-shadow:0 1px 4px rgba(16,24,32,.08);">
      <h1 style="margin:0 0 12px;font-size:20px;line-height:1.42;font-weight:700;">{safe_title}</h1>
      {feed_cover}
      <p style="margin:12px 0 0;font-size:14px;line-height:1.65;color:#60666d;">{safe_digest}</p>
      <p style="margin:9px 0 0;font-size:12px;line-height:1.5;color:#9a9fa5;">{safe_author}</p>
    </article>
    <section style="margin:18px 0 8px;color:#7a7f86;font-size:12px;">分享卡片 · 缩略预览</section>
    <article style="display:flex;gap:10px;background:#fff;padding:12px;border-radius:4px;box-shadow:0 1px 4px rgba(16,24,32,.08);">
      <section style="flex:1;min-width:0;">
        <h2 style="margin:0;font-size:16px;line-height:1.45;font-weight:650;">{safe_title}</h2>
        <p style="margin:8px 0 0;font-size:12px;color:#8a8f95;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{safe_author}</p>
      </section>
      <section style="width:90px;height:90px;flex:0 0 90px;overflow:hidden;">{share_cover}</section>
    </article>
  </main>
</body>
</html>
"""


def escape_text(value: str) -> str:
    return html.escape(value, quote=True)


IMG_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=")([^"]+)("[^>]*>)', re.I)


def add_local_image_metadata(content_html: str, markdown_path: str | Path) -> str:
    """Preserve the dimensions and display width required by WeChat's editor."""
    base_dir = Path(markdown_path).resolve().parent

    def repl(match: re.Match[str]) -> str:
        src = match.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        local_path = (base_dir / html.unescape(src)).resolve()
        try:
            with Image.open(local_path) as picture:
                width, height = picture.size
                image_type = (picture.format or "").lower()
        except UnidentifiedImageError:
            # Non-raster preview assets, such as SVG, have no PIL dimensions.
            return match.group(0)
        tag = match.group(0)

        def set_attr(name: str, value: str) -> None:
            nonlocal tag
            pattern = re.compile(r'\s' + re.escape(name) + r'="[^"]*"', re.I)
            tag = pattern.sub("", tag)
            tag = re.sub(r'\s*/?>$', lambda _: f' {name}="{html.escape(value, quote=True)}">', tag)

        style_match = re.search(r'\sstyle="([^"]*)"', tag, re.I)
        style = style_match.group(1) if style_match else ""
        style = re.sub(r'(?<![-\w])width\s*:[^;]*;?', "", style, flags=re.I)
        set_attr("style", "width:100%;" + style)
        class_match = re.search(r'\sclass="([^"]*)"', tag, re.I)
        classes = (class_match.group(1).split() if class_match else [])
        for name in ("rich_pages", "wxw-img", "js_insertlocal"):
            if name not in classes:
                classes.append(name)
        set_attr("class", " ".join(classes))
        for name, value in {
            "width": "100%", "data-w": str(width), "data-h": str(height),
            "data-ratio": str(height / width), "data-type": image_type,
            "data-s": "300,640",
        }.items():
            set_attr(name, value)
        return tag

    return IMG_SRC_RE.sub(repl, content_html)


def find_local_image_sources(content_html: str) -> list[str]:
    sources: list[str] = []
    for _, src, _ in IMG_SRC_RE.findall(content_html):
        if src.startswith(("http://", "https://", "data:")):
            continue
        if src not in sources:
            sources.append(src)
    return sources


def replace_local_image_sources(
    content_html: str,
    markdown_path: str | Path,
    uploader: Callable[[Path], str],
) -> tuple[str, dict[str, str]]:
    md_path = Path(markdown_path).resolve()
    base_dir = md_path.parent
    replacements: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        local_path = (base_dir / src).resolve()
        if not local_path.exists():
            raise FileNotFoundError(f"Local image not found: {local_path}")
        if src not in replacements:
            replacements[src] = uploader(local_path)
        return f"{prefix}{replacements[src]}{suffix}"

    return IMG_SRC_RE.sub(repl, content_html), replacements


def drop_local_image_sources(
    content_html: str,
    markdown_path: str | Path,
    local_sources: set[str],
) -> tuple[str, list[str]]:
    md_path = Path(markdown_path).resolve()
    base_dir = md_path.parent
    dropped: list[str] = []

    def repl(match: re.Match[str]) -> str:
        src = match.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        local_path = (base_dir / src).resolve()
        if src in local_sources:
            if not local_path.exists():
                raise FileNotFoundError(f"Local image not found: {local_path}")
            dropped.append(src)
            return ""
        return match.group(0)

    return IMG_SRC_RE.sub(repl, content_html), dropped
