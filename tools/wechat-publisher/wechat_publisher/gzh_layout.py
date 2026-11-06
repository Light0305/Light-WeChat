"""Chuan Lab adapter for actual isjiamu/gzh-design-skill component templates.

Template markup is extracted verbatim in gzh_components.json; attribution, pinned
source and AGPL license accompany the project-local skill's vendor/gzh-design.
This adapter adds Markdown assembly, arbitrary-size tables and copyable code.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from settings import load_settings

DATA = Path(__file__).with_name("gzh_components.json")
NAMES = {"moyu-green", "graphite-minimal", "red-white", "moyu-ticket", "olive-journal", "zen-whitespace"}
ACCENTS = {"moyu-green": "#059669", "graphite-minimal": "#52525B", "red-white": "#DC2626",
           "moyu-ticket": "#059669", "olive-journal": "#ed7b2f", "zen-whitespace": "#4A5D52"}
UNDERLINES = {"moyu-green": "border-bottom:2px solid #A7F3D0;font-weight:600;",
              "moyu-ticket": "border-bottom:2px solid #A7F3D0;font-weight:600;",
              "graphite-minimal": "border-bottom:2px solid #52525B;font-weight:600;",
              "red-white": "border-bottom:2px solid #FECACA;font-weight:600;",
              "olive-journal": "border-bottom:2px solid #ed7b2f;font-weight:600;",
              "zen-whitespace": "border-bottom:1.5px solid #B5C8BC;font-weight:500;"}


def fragment(text):
    return BeautifulSoup(text, "html.parser")


def leaf(text):
    return '<span leaf="">' + html.escape(text, quote=False) + '</span>'


class Assembler:
    def __init__(self, name):
        self.name = name.removeprefix("gzh-")
        if self.name not in NAMES:
            raise ValueError(f"Unknown gzh-design theme: {name}")
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.components = data["themes"][self.name]["components"]
        self.common = data["common"]
        self.number = 0
        self.accent = ACCENTS[self.name]

    def template(self, key):
        return self.components[key]["html"]

    def filled(self, key, content, values=None):
        template = self.template(key)
        values = values or {}
        def replace(match):
            field = match.group(1)
            return values.get(field, content)
        return re.sub(r"\{\{(.*?)\}\}", replace, template)

    def inline(self, node):
        if isinstance(node, Comment):
            return ""
        if isinstance(node, NavigableString):
            return leaf(str(node)) if str(node).strip() else str(node)
        inner = "".join(self.inline(child) for child in node.children)
        if node.name == "strong":
            template = fragment(self.template("strong"))
            target = template.select_one("span[leaf]")
            target.clear()
            target.append(fragment(inner))
            return str(template)
        if node.name == "code":
            code = fragment(self.common[2].replace("#DC2626", self.accent))
            target = code.select_one("span[leaf]")
            target.clear()
            target.append(fragment(leaf(node.get_text())))
            return str(code)
        if node.name == "a":
            return f'<a href="{html.escape(node.get("href", ""), quote=True)}" style="color:{self.accent};text-decoration:underline;overflow-wrap:anywhere;">{inner}</a>'
        if node.name == "br":
            return "<br>"
        if node.name == "u":
            return f'<span style="{UNDERLINES[self.name]}">{inner}</span>'
        if node.name in {"em", "s", "del", "sup", "sub"}:
            return f'<{node.name}>{inner}</{node.name}>'
        if node.name == "span":
            style = html.escape(node.get("style", ""), quote=True)
            return f'<span style="{style}">{inner}</span>'
        return inner

    def image(self, node):
        src, alt = node.get("src", ""), node.get("alt", "")
        # The original complete frame is shipped; generic assembly uses common 2a
        # to preserve arbitrary image attributes and only emits a real caption.
        template = fragment(self.common[3])
        image = template.find("img")
        image["src"] = src
        image["alt"] = alt
        caption = template.find_all("p")[-1]
        if alt:
            caption.clear()
            caption.append(fragment(leaf(alt)))
        else:
            caption.decompose()
        return str(template)

    def chapter(self, node):
        self.number += 1
        title = "".join(self.inline(c) for c in node.children)
        number = f"{self.number:02d}"
        publication = html.escape(load_settings().brand_name or 'SECTION')
        values = {"01": number, "编号": number, "ENGLISH TAG": publication,
                  "ENGLISH · 英文副标题": publication, "副标题": publication}
        result = self.filled("chapter", title, values)
        # Some upstream samples encode these as demo literals, not slots.
        if self.name == "zen-whitespace":
            result = result.replace('01 · CHAPTER ONE', number + ' · ' + publication)
            result = result.replace("中文章节大标题", title)
        else:
            result = re.sub(r'(<span leaf="">)01(</span>)', rf'\g<1>{number}\2', result)
        return result.replace('<section ', f'<section data-cl-section="{number}" ', 1)

    def table(self, node):
        base = fragment(self.template("table")) if "table" in self.components else None
        th = base.find("th") if base else None
        td = base.find("td") if base else None
        table_style = base.find("table").get("style", "") if base else "border-collapse:collapse;font-size:13px;line-height:1.8;"
        table_style += "width:100%;table-layout:fixed;margin:18px 0;"
        table = fragment(str(node)).find("table")
        table["style"] = table_style
        for cell in table.find_all(["td", "th"]):
            prototype = th if cell.name == "th" else td
            style = prototype.get("style", "") if prototype else f"padding:10px 8px;border-bottom:1px solid #dddddd;color:{self.accent};"
            style += "overflow-wrap:anywhere;vertical-align:top;"
            alignment = re.search(r"text-align\s*:\s*(left|right|center)", cell.get("style", ""))
            if alignment:
                style += f"text-align:{alignment.group(1)};"
            content = self.inline(cell)
            cell.clear()
            cell["style"] = style
            cell.append(fragment(content))
        return str(table)

    def code(self, node):
        code = node.find("code")
        text = code.get_text() if code else node.get_text()
        language = " ".join(code.get("class", [])) if code else ""
        language = language.removeprefix("language-") or "CODE"
        template = fragment(self.common[1].replace("#DC2626", self.accent))
        template.select_one("span[leaf]").string = language
        inner = template.find_all("section")[-1]
        inner.clear()
        # Keep exact spaces/newlines for runnable code. Full-width space
        # substitution in upstream's paste sample would change Python/SQL.
        inner.append(fragment('<pre style="margin:0;font:13px/1.7 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;">'
                              '<code style="font-family:Consolas,monospace;white-space:pre-wrap;">' + leaf(text) + '</code></pre>'))
        return str(template)

    def block(self, node):
        if isinstance(node, Comment):
            return ""
        if isinstance(node, NavigableString):
            return leaf(str(node)) if str(node).strip() else ""
        if node.name == "h2":
            return self.chapter(node)
        if node.name in {"h3", "h4"}:
            inner = self.inline(node)
            if "subheading" in self.components:
                return self.filled("subheading", inner)
            return self.common[6].replace("#DC2626", self.accent).replace("小标题文字", inner)
        if node.name == "p":
            if node.find("img"):
                # Preserve any adjacent text, not only the first image.
                return "".join(self.image(c) if isinstance(c, Tag) and c.name == "img" else self.inline(c) for c in node.children)
            inner = self.inline(node)
            result = self.filled("paragraph", inner)
            if self.name == "zen-whitespace":
                result = re.sub(r'(<span leaf="">).*?(</span>)', lambda m: m[1] + inner + m[2], result, count=1, flags=re.S)
            return result
        if node.name == "blockquote":
            template = fragment(self.template("quote"))
            paras = template.find_all("p")
            target = paras[-1] if paras else template.find("section")
            target.clear()
            target.append(fragment("<br>".join(self.inline(c) for c in node.children if not isinstance(c, NavigableString) or str(c).strip())))
            # Remove upstream label/metadata slots; they aren't article content.
            for tag in template.find_all(string=re.compile(r"\{\{")):
                tag.replace_with("")
            return str(template)
        if node.name == "table":
            return self.table(node)
        if node.name == "pre":
            return self.code(node)
        if node.name == "img":
            return self.image(node)
        if node.name in {"ul", "ol"}:
            start = f' start="{html.escape(str(node["start"]), quote=True)}"' if node.name == "ol" and "start" in node.attrs else ""
            return f'<{node.name}{start} style="padding-left:1.5em;margin:16px 0;line-height:1.9;font-size:15px;">' + "".join(self.block(c) for c in node.children) + f'</{node.name}>'
        if node.name == "li":
            return '<li style="margin:8px 0;">' + "".join(self.block(c) if isinstance(c, Tag) and c.name in {"p", "ul", "ol", "pre"} else self.inline(c) for c in node.children) + '</li>'
        if node.name == "hr":
            return '<section style="border-top:1px solid #dddddd;margin:28px 0;"><span leaf=""><br></span></section>'
        if node.name in {"script", "style", "iframe", "object", "embed"}:
            raise ValueError(f"Active HTML not permitted in article: {node.name}")
        if node.name == "section" and node.get("style"):
            # Advanced components assembled directly from the shipped theme:
            # preserve their real markup. The upstream validator checks them.
            return str(node)
        return "".join(self.block(c) for c in node.children)

    def render(self, body):
        content = "".join(self.block(n) for n in fragment(body).contents)
        container = fragment(self.template("container"))
        root = container.find("section")
        root.clear()
        root["data-gzh-theme"] = self.name
        root.append(fragment(content))
        result = str(container)
        if re.search(r"\{\{.*?\}\}", result):
            raise ValueError("Unfilled gzh-design template slots")
        return result


class ChuanEditorial(Assembler):
    """Article composition, using gzh's Zen editorial grammar with new art direction.

    Original theme libraries remain untouched. This is an explicitly attributed
    adaptation: hierarchy comes from type, rhythm and media, not nested UI cards.
    """

    def __init__(self):
        super().__init__("zen-whitespace")
        self.name = "chuan-editorial"
        self.accent = "#285447"

    def inline(self, node):
        if isinstance(node, Tag):
            inner = "".join(self.inline(c) for c in node.children)
            if node.name == "strong":
                return '<strong style="font-weight:650;color:#173f34;">' + inner + '</strong>'
            if node.name == "code":
                return '<code style="font:13px/1.7 Consolas,monospace;color:#285447;background:#f3f4f0;padding:1px 4px;">' + leaf(node.get_text()) + '</code>'
            if node.name == "span":
                return inner
            if node.name == "u":
                return '<span style="border-bottom:1px solid #a9bdb2;">' + inner + '</span>'
        return super().inline(node)

    def chapter(self, node):
        self.number += 1
        title = "".join(self.inline(c) for c in node.children)
        return (f'<section data-cl-section="{self.number:02d}" style="margin:52px 0 22px;padding:18px 0 0;border-top:1px solid #d9dfda;">'
                f'<p style="font:11px/1.5 Georgia,serif;color:#7b8c80;letter-spacing:2px;margin:0 0 10px;">{leaf(f"{self.number:02d}")}</p>'
                '<h2 style="font-family:\'Noto Serif SC\',\'Songti SC\',SimSun,serif;font-size:22px;font-weight:700;line-height:1.55;letter-spacing:.3px;color:#173b30;margin:0;">'
                + title + '</h2></section>')

    def image(self, node):
        # No shadows, rounding, badges or synthetic device frames on evidence.
        attrs = 'src="' + html.escape(node.get("src", ""), quote=True) + '" alt="' + html.escape(node.get("alt", ""), quote=True) + '"'
        return '<section style="margin:28px 0 12px;"><img ' + attrs + ' style="display:block;width:100%;height:auto;margin:0;border:0;"/></section>'

    def table(self, node):
        table = fragment(str(node)).find("table")
        table["style"] = "border-collapse:collapse;width:100%;table-layout:fixed;margin:28px 0;font-size:13px;line-height:1.85;letter-spacing:0;"
        for cell in table.find_all(["th", "td"]):
            alignment = re.search(r"text-align\s*:\s*(left|right|center)", cell.get("style", ""))
            head = cell.name == "th"
            style = ("padding:12px 7px;border-bottom:1px solid #d9dfda;vertical-align:top;overflow-wrap:anywhere;"
                     + ("color:#285447;font-weight:650;background:#f4f5f1;" if head else "color:#414844;font-weight:400;")
                     + "text-align:" + (alignment.group(1) if alignment else "left") + ";")
            inner = self.inline(cell)
            cell.clear()
            cell["style"] = style
            cell.append(fragment(inner))
        return str(table)

    def code(self, node):
        code = node.find("code")
        text = code.get_text() if code else node.get_text()
        language = " ".join(code.get("class", [])) if code else ""
        label = language.removeprefix("language-") or "CODE"
        return ('<section style="margin:28px 0;padding:16px;background:#f5f5f1;border-top:1px solid #d9dfda;border-bottom:1px solid #d9dfda;">'
                '<p style="font:10px/1.6 Consolas,monospace;letter-spacing:1.5px;color:#7b8c80;margin:0 0 12px;">' + leaf(label.upper()) + '</p>'
                '<pre style="margin:0;font:13px/1.8 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;color:#293d33;">'
                '<code style="font-family:Consolas,monospace;white-space:pre-wrap;">' + leaf(text) + '</code></pre></section>')

    def block(self, node):
        if isinstance(node, Tag):
            if node.name == "p" and not node.find("img"):
                return '<p style="margin:0 0 22px;font-size:16px;line-height:1.95;letter-spacing:.3px;text-align:justify;">' + self.inline(node) + '</p>'
            if node.name in {"h3", "h4"}:
                return '<h3 style="font-size:17px;line-height:1.65;font-weight:650;color:#173b30;margin:30px 0 14px;">' + self.inline(node) + '</h3>'
            if node.name == "blockquote":
                return ('<section style="margin:34px 0;padding:22px 0;border-top:1px solid #d9dfda;border-bottom:1px solid #d9dfda;">'
                        '<p style="font-family:\'Noto Serif SC\',\'Songti SC\',SimSun,serif;font-size:20px;line-height:1.85;color:#285447;margin:0;">'
                        + '<br>'.join(self.inline(c) for c in node.children if isinstance(c, Tag)) + '</p></section>')
            if node.name in {"ul", "ol"}:
                start = f' start="{html.escape(str(node["start"]), quote=True)}"' if node.name == "ol" and "start" in node.attrs else ""
                return f'<{node.name}{start} style="padding-left:1.4em;margin:20px 0 26px;font-size:16px;line-height:1.95;">' + ''.join(self.block(c) for c in node.children) + f'</{node.name}>'
            if node.name == "section":
                classes = node.get("class", [])
                kind = next((c[3:] for c in classes if c.startswith("cl-")), None)
                if kind:
                    inner = ''.join(self.inline(c) for c in node.children)
                    if kind == "byline":
                        style = "margin:0 0 24px;padding:12px 0;border-bottom:1px solid #d9dfda;font-size:11px;line-height:1.7;letter-spacing:1.5px;color:#65756b;"
                    elif kind == "lead":
                        style = "margin:0 0 28px;font-family:'Noto Serif SC','Songti SC',SimSun,serif;font-size:23px;line-height:1.75;letter-spacing:.5px;color:#173b30;"
                    elif kind in {"image-note", "source-note"}:
                        style = "margin:8px 0 30px;padding:0;font-size:12px;line-height:1.85;color:#79847c;letter-spacing:0;"
                    elif kind == "sep":
                        return '<section style="margin:36px 0;border-top:1px solid #d9dfda;"><span leaf=""><br></span></section>'
                    else:
                        style = "margin:26px 0;padding:18px 0;border-top:1px solid #d9dfda;border-bottom:1px solid #d9dfda;line-height:1.9;"
                    return '<section style="' + style + '">' + inner + '</section>'
        return super().block(node)

    def render(self, body):
        content = ''.join(self.block(n) for n in fragment(body).contents)
        return ('<section data-gzh-theme="chuan-editorial" style="max-width:677px;margin:0 auto;padding:0 0 28px;background:#ffffff;'
                'font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;'
                'font-size:16px;line-height:1.95;letter-spacing:.3px;color:#303a34;overflow-wrap:break-word;">' + content + '</section>')


def apply_gzh_layout(body, name):
    return (ChuanEditorial() if name == "gzh-chuan-editorial" else Assembler(name)).render(body)
