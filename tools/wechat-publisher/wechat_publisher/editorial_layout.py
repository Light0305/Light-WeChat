"""Chuan Lab v9 inline themes, written locally from editorial requirements."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

THEMES = {
    "editorial": {"accent": "#087b6e", "soft": "#f1f7f5", "line": "1.85", "gap": 14},
    "paper": {"accent": "#4657a6", "soft": "#f3f4fa", "line": "1.9", "gap": 14},
    "guide": {"accent": "#1769aa", "soft": "#f1f6fb", "line": "1.85", "gap": 12},
}


class _ThemeParser(HTMLParser):
    def __init__(self, name: str):
        super().__init__(convert_charrefs=False)
        self.name, self.theme = name, THEMES[name]
        self.out: list[str] = []
        self.stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = self.theme
        style = None
        if tag == "p":
            gap = 0 if "blockquote" in self.stack or "li" in self.stack else t["gap"]
            style = (f"margin:0 0 {gap}px;line-height:{t['line']};font-size:16px;"
                     "color:#242933;letter-spacing:0;text-indent:0;overflow-wrap:break-word;")
        elif tag == "h2":
            style = "margin:0;font-size:22px;line-height:1.5;font-weight:700;color:#151d29;"
        elif tag == "h3":
            style = "margin:22px 0 9px;font-size:18px;line-height:1.55;font-weight:700;color:#151d29;"
        elif tag == "section" and "margin:18px 0 6px" in a.get("style", ""):
            style = f"margin:30px 0 12px;padding:0 0 8px;border-bottom:1px solid {t['accent']};"
        elif tag == "strong":
            style = f"font-weight:700;color:{t['accent']};"
        elif tag == "a":
            style = f"color:{t['accent']};text-decoration:underline;overflow-wrap:anywhere;"
        elif tag == "blockquote":
            style = f"margin:18px 0;padding:12px 15px;border-left:3px solid {t['accent']};background:{t['soft']};"
        elif tag == "img":
            style = "display:block;width:100%;max-width:100%;height:auto;margin:18px auto 8px;"
        elif tag == "table":
            style = "width:100%;border-collapse:collapse;table-layout:fixed;margin:18px 0;font-size:14px;line-height:1.65;"
        elif tag in ("td", "th"):
            alignment = re.search(r"text-align\s*:\s*(left|center|right)", a.get("style", ""))
            style = ("border:1px solid #dce1e7;padding:9px 8px;vertical-align:top;overflow-wrap:anywhere;"
                     + (f"background:{t['soft']};font-weight:700;" if tag == "th" else "")
                     + (f"text-align:{alignment.group(1)};" if alignment else "text-align:left;"))
        elif tag in ("ul", "ol"):
            style = f"margin:0 0 {t['gap']}px;padding-left:1.4em;line-height:{t['line']};font-size:16px;color:#242933;"
        elif tag == "li":
            style = "margin:5px 0;overflow-wrap:break-word;"
        elif tag == "pre":
            style = "margin:18px 0;padding:14px;background:#18212f;color:#f3f6fb;border-radius:4px;font-size:13px;line-height:1.7;overflow-wrap:anywhere;"
        elif tag == "code" and "pre" in self.stack:
            style = "font-family:Consolas,Menlo,monospace;white-space:pre-wrap;word-break:break-word;color:inherit;background:transparent;"
        if style is not None:
            if tag not in ("pre", "code"):
                style += "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;"
            a["style"] = style
        if tag == "p":
            a["data-cl-layout"] = self.name
        attr_text = "".join(f' {key}="{html.escape(value or "", quote=True)}"' for key, value in a.items())
        self.out.append(f"<{tag}{attr_text}>")
        if tag not in ("img", "br", "hr", "input", "meta", "link", "source", "wbr"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        self.out.append(f"</{tag}>")
        if tag in self.stack:
            del self.stack[len(self.stack) - 1 - self.stack[::-1].index(tag):]

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1] == tag:
            self.handle_endtag(tag)

    def handle_data(self, data):
        self.out.append(data)

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_charref(self, name):
        self.out.append(f"&#{name};")


def apply_editorial_layout(content: str, name: str) -> str:
    if name not in THEMES:
        raise ValueError(f"Unknown Chuan Lab layout: {name}")
    parser = _ThemeParser(name)
    parser.feed(content)
    parser.close()
    return "".join(parser.out)
