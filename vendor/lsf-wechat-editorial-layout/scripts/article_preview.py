"""Load a local article and reuse the publication template's typography in Dinamo."""
import base64
import json
from html import escape
from html.parser import HTMLParser
from mimetypes import guess_type
from pathlib import Path


ARTICLE_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "article-template.html"
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


class ArticleStyles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.styles = {}

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if "data-layout" in fields:
            self.styles[fields["data-layout"]] = fields["style"]


def article_css():
    parser = ArticleStyles()
    parser.feed(ARTICLE_TEMPLATE.read_text(encoding="utf-8"))
    selectors = {
        "body": ".article-body",
        "paragraph": ".article-body .demo-text",
        "first": ".article-body .demo-text.is-first",
        "heading": ".article-body h2",
        "marker": ".article-body .chapter-heading",
        "glyph": ".article-body .chapter-heading img",
        "emphasis": ".article-body strong",
        "image": ".article-body .demo-image, .article-body .screenshot-frame",
        "caption": ".article-body .article-caption",
    }
    return "\n".join(f"{selector}{{{parser.styles[role]}}}" for role, selector in selectors.items())


def image_uri(path):
    mime, _ = guess_type(path.name)
    if mime not in IMAGE_TYPES:
        raise ValueError(f"不支持的配图格式：{path}")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def load_article(path):
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict) or not isinstance(raw.get("title"), str) or not raw["title"].strip():
        raise ValueError("稿件 JSON 必须包含非空的 title")

    def blocks(values, label):
        if not isinstance(values, list):
            raise ValueError(f"{label} 必须是数组")
        result = []
        for entry in values:
            if isinstance(entry, str) and entry.strip():
                result.append(entry)
                continue
            if not isinstance(entry, dict) or len({"image", "screenshot"} & entry.keys()) != 1:
                raise ValueError(f"{label} 的每项须是正文，或包含 image / screenshot 的图片对象")
            kind = "image" if "image" in entry else "screenshot"
            source = entry[kind]
            caption = entry.get("caption", "")
            if not isinstance(source, str) or not source.strip() or not isinstance(caption, str):
                raise ValueError(f"{label} 的图片路径和图注须是文字")
            source = path.parent / source
            if not source.is_file():
                raise ValueError(f"找不到本地配图：{source}")
            allowed = IMAGE_TYPES - {"image/gif"} if kind == "screenshot" else IMAGE_TYPES
            if guess_type(source.name)[0] not in allowed:
                raise ValueError(f"不支持的配图格式：{source}")
            result.append({kind: source, "caption": caption.strip().rstrip("。.")})
        return result

    intro = blocks(raw.get("intro", []), "intro")
    chapters = raw.get("chapters", [])
    if not isinstance(chapters, list):
        raise ValueError("chapters 必须是数组")
    sections = []
    for index, chapter in enumerate(chapters, 1):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("title"), str) or not chapter["title"].strip():
            raise ValueError(f"第 {index} 节须包含非空的 title")
        content = blocks(chapter.get("paragraphs"), f"第 {index} 节 paragraphs")
        if not any(isinstance(block, str) for block in content):
            raise ValueError(f"第 {index} 节须有至少一段正文")
        sections.append({"title": chapter["title"].strip(), "paragraphs": content})
    if not sections and not any(isinstance(block, str) for block in intro):
        raise ValueError("稿件须有至少一段正文")
    return {"title": raw["title"].strip(), "intro": intro, "chapters": sections}


def paragraph(text, first):
    # Restore only the supported emphasis tag after escaping the whole paragraph.
    text = escape(text).replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
    return f'<p class="demo-text{" is-first" if first else ""}">{text}</p>'


def render_image(path, caption):
    caption = escape(caption)
    return (
        f'<figure><img class="demo-image" src="{image_uri(path)}" alt="{caption}">'
        + (f'<figcaption class="article-caption">{caption}</figcaption>' if caption else "")
        + '</figure>'
    )


def render_article(article, intro, chapter_markers, screenshot, footer, sample):
    first_paragraph = True

    def render_blocks(blocks):
        nonlocal first_paragraph
        parts = []
        for block in blocks:
            if isinstance(block, str):
                parts.append(paragraph(block, first_paragraph))
                first_paragraph = False
            elif "screenshot" in block:
                parts.append(screenshot(block))
            else:
                parts.append(render_image(block["image"], block["caption"]))
        return "\n".join(parts)

    title = escape(article["title"])
    parts = [f'<header><h1>{title}</h1>',
             f'<p class="sample-meta">{"示例文章" if sample else "本篇稿件"}</p></header>',
             '<div class="article-body">', intro, render_blocks(article["intro"])]
    for index, chapter in enumerate(article["chapters"]):
        anchor = ' id="preview-chapters"' if index == 0 else ""
        markers = chapter_markers[index]
        parts.extend([f'<section class="demo-section"{anchor}>',
                      f'<div class="chapter-heading">{markers}</div>' if markers else "",
                      f'<h2>{escape(chapter["title"])}</h2>',
                      render_blocks(chapter["paragraphs"]), '</section>'])
    return "\n".join([*parts, footer, '</div>'])
