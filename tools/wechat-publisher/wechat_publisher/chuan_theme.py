from __future__ import annotations

from dataclasses import dataclass


COLORS = {
    "ink": "#101820",
    "body": "#20242a",
    "muted": "#667085",
    "faint": "#8a97a5",
    "soft": "#f7f7f7",
    "soft_cyan": "#f3fafb",
    "soft_green": "#f4f8f6",
    "soft_yellow": "#fff9e8",
    "soft_indigo": "#f6f6fb",
    "indigo": "#596bd8",
    "line": "#d9dfe4",
    "green": "#0d6e5b",
    "accent": "#087b6e",
    "cyan": "#00a7c8",
    "yellow": "#d9a400",
    "white": "#ffffff",
}


BODY_P_STYLE = (
    "margin:0;"
    "line-height:1.75;"
    "font-size:17px;"
    f"color:{COLORS['body']};"
    "letter-spacing:0;"
    "text-indent:2em;"
)

MEDIA_P_STYLE = BODY_P_STYLE.replace("text-indent:2em;", "text-indent:0;")

H2_WRAP_STYLE = (
    "margin:18px 0 6px;"
    "padding:0;"
)
H2_STYLE = (
    "font-size:21px;"
    "line-height:1.45;"
    "margin:0;"
    "font-weight:800;"
    f"color:{COLORS['ink']};"
    "letter-spacing:0;"
)
H3_STYLE = (
    "font-size:18px;"
    "line-height:1.55;"
    "margin:14px 0 4px;"
    "padding:0;"
    "font-weight:800;"
    f"color:{COLORS['ink']};"
    "letter-spacing:0;"
)

STRONG_STYLE = f"font-weight:750;color:{COLORS['accent']};"
INLINE_CODE_STYLE = (
    "font-family:Menlo,Consolas,monospace;"
    "font-size:0.92em;"
    f"background:{COLORS['soft']};"
    f"color:{COLORS['green']};"
    "padding:1px 4px;border-radius:2px;"
)
PRE_STYLE = (
    f"background:{COLORS['ink']};"
    "color:#f5fbff;"
    "border-radius:2px;"
    "padding:14px 16px;"
    "margin:14px 0;"
    "overflow-x:auto;"
    "line-height:1.7;"
    "font-size:13.5px;"
)
PRE_CODE_STYLE = (
    "font-family:Menlo,Consolas,monospace;"
    "white-space:pre-wrap;"
    "word-break:break-word;"
)

BLOCKQUOTE_STYLE = (
    "margin:0 0 10px;"
    "padding:0 0 0 14px;"
    f"border-left:3px solid {COLORS['line']};"
    "background:transparent;"
    f"color:{COLORS['muted']};"
)
BLOCKQUOTE_P_STYLE = (
    "margin:0;"
    "line-height:1.8;"
    "font-size:15px;"
    f"color:{COLORS['muted']};"
    "letter-spacing:0;"
)

UL_STYLE = "margin:0 0 10px 1.2em;padding:0;line-height:1.85;"
OL_STYLE = "margin:0 0 10px 1.2em;padding:0;line-height:1.85;"
LI_STYLE = "margin:3px 0;"

TABLE_STYLE = (
    "width:100%;"
    "border-collapse:collapse;"
    "margin:14px 0;"
    "font-size:15px;"
    "line-height:1.65;"
)
TH_STYLE = (
    f"border:1px solid {COLORS['line']};"
    f"background:{COLORS['soft']};"
    "padding:10px 8px;"
    "text-align:left;"
    f"color:{COLORS['ink']};"
    "font-weight:800;"
)
TD_STYLE = (
    f"border:1px solid {COLORS['line']};"
    "padding:10px 8px;"
    "vertical-align:top;"
    f"color:{COLORS['body']};"
)

IMAGE_STYLE = "max-width:100%;height:auto;display:block;margin:10px auto 4px;border-radius:0;"
ORNAMENT_IMAGE_STYLE = (
    "max-width:100%;height:auto;display:block;"
    "margin:14px auto 10px;border-radius:0;"
)
SEP_STYLE = (
    "margin:18px auto;"
    "width:44px;"
    "height:1px;"
    f"background:{COLORS['line']};"
    "line-height:1;"
    "font-size:0;"
)


@dataclass(frozen=True)
class ComponentTheme:
    label: str
    container_style: str
    label_style: str


def line_label_style(color: str, *, border: str | None = None) -> str:
    border_color = border or color
    return (
        "display:inline-block;"
        "margin:0 0 9px;"
        "padding:0 0 3px;"
        "font-size:12px;"
        "line-height:1.2;"
        "font-weight:800;"
        f"color:{color};"
        f"border-bottom:1px solid {border_color};"
        "letter-spacing:0;"
    )


def quiet_label_style(color: str) -> str:
    return (
        "display:inline-block;"
        "margin:0 0 7px;"
        "font-size:11px;"
        "line-height:1.2;"
        "font-weight:800;"
        f"color:{color};"
        "letter-spacing:0;"
    )


def legacy_pillar(label: str, accent: str, ink: str) -> ComponentTheme:
    return ComponentTheme(
        label=label,
        container_style=(
            "margin:4px 0 12px;"
            "padding:2px 0 2px 11px;"
            f"border-left:2px solid {accent};"
            "background:#ffffff;"
            f"color:{COLORS['muted']};"
            "font-size:13px;line-height:1.65;letter-spacing:0;"
        ),
        label_style=line_label_style(ink, border=accent),
    )


CHUAN_COMPONENTS: dict[str, ComponentTheme] = {
    # Legacy public orientation blocks remain renderable for existing articles.
    "pillar-ai": legacy_pillar("AI 前沿", "#16b8c4", "#087b86"),
    "pillar-llm": legacy_pillar("大模型", "#28c792", COLORS["green"]),
    "pillar-paper": legacy_pillar("论文", "#7c8cf8", "#5364d8"),
    "pillar-career": legacy_pillar("程序员就业", "#e0a11a", "#8a6200"),
    "brand": ComponentTheme(
        label="",
        container_style=(
            "margin:12px 0 14px;padding:12px 14px;"
            f"border:1px solid {COLORS['line']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15px;line-height:1.8;letter-spacing:0;"
        ),
        label_style="",
    ),
    "byline": ComponentTheme(
        label="",
        container_style=(
            "margin:0 0 12px;padding:10px;"
            f"background:{COLORS['soft']};color:#515151;"
            "font-size:14px;line-height:1.8;font-weight:400;letter-spacing:0;"
        ),
        label_style="",
    ),
    "brief": ComponentTheme(
        label="导读",
        container_style=(
            "margin:0 0 14px;padding:15px 16px;"
            f"background:{COLORS['soft']};"
            f"color:{COLORS['body']};"
            "font-size:16px;line-height:1.75;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["ink"]),
    ),
    "keyline": ComponentTheme(
        label="",
        container_style=(
            "margin:14px 0;padding:17px 18px;"
            f"border-left:4px solid {COLORS['green']};background:{COLORS['soft_green']};"
            f"color:{COLORS['ink']};font-size:19px;line-height:1.72;"
            "font-weight:750;letter-spacing:0;"
        ),
        label_style="",
    ),
    "lead": ComponentTheme(
        label="",
        container_style=(
            "margin:0 0 12px;padding:0 0 0 14px;"
            f"border-left:3px solid {COLORS['line']};background:#ffffff;"
            f"color:{COLORS['muted']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style="",
    ),
    "claim": ComponentTheme(
        label="",
        container_style=(
            "margin:14px 0;padding:14px 0;"
            f"border-top:1px solid {COLORS['line']};border-bottom:1px solid {COLORS['line']};"
            f"background:#ffffff;color:{COLORS['ink']};"
            "font-size:17px;line-height:1.78;font-weight:750;letter-spacing:0;"
        ),
        label_style="",
    ),
    "signal": ComponentTheme(
        label="快讯",
        container_style=(
            "margin:12px 0;padding:0 0 0 14px;"
            f"border-left:2px solid {COLORS['cyan']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["cyan"]),
    ),
    "stat": ComponentTheme(
        label="数据",
        container_style=(
            "margin:14px 0;padding:17px 18px;"
            f"background:{COLORS['ink']};border-radius:2px;color:#f7fbfc;"
            "font-size:18px;line-height:1.7;font-weight:750;letter-spacing:0;"
        ),
        label_style=line_label_style("#9ee9d8", border="#25c79a"),
    ),
    "pullquote": ComponentTheme(
        label="",
        container_style=(
            "margin:14px 0;padding:0 0 0 16px;"
            f"border-left:3px solid {COLORS['green']};background:#ffffff;"
            f"color:{COLORS['ink']};font-size:18px;line-height:1.75;"
            "font-weight:750;letter-spacing:0;"
        ),
        label_style="",
    ),
    "data": ComponentTheme(
        label="证据",
        container_style=(
            "margin:12px 0;padding:13px 14px;"
            f"background:{COLORS['soft_green']};border-left:3px solid {COLORS['green']};"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["green"]),
    ),
    "compare": ComponentTheme(
        label="对照",
        container_style=(
            "margin:14px 0;padding:14px 0;"
            f"border-top:1px solid {COLORS['line']};border-bottom:1px solid {COLORS['line']};"
            f"background:#ffffff;color:{COLORS['body']};"
            "font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["green"]),
    ),
    "quote": ComponentTheme(
        label="原文",
        container_style=(
            "margin:12px 0;padding:0 0 0 14px;"
            f"border-left:3px solid {COLORS['line']};background:#ffffff;"
            f"color:{COLORS['muted']};font-size:15px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["faint"]),
    ),
    "method": ComponentTheme(
        label="方法",
        container_style=(
            "margin:14px 0;padding:13px 0 0;"
            f"border-top:2px solid {COLORS['green']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["green"]),
    ),
    "timeline": ComponentTheme(
        label="时间线",
        container_style=(
            "margin:14px 0;padding:0 0 0 15px;"
            "border-left:2px solid #7c8cf8;background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["indigo"]),
    ),
    "steps": ComponentTheme(
        label="步骤",
        container_style=(
            "margin:14px 0;padding:13px 0 0;"
            f"border-top:2px solid {COLORS['green']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["green"]),
    ),
    "aside": ComponentTheme(
        label="",
        container_style=(
            "margin:12px 0;padding:11px 13px;"
            f"background:{COLORS['soft']};color:{COLORS['muted']};"
            "font-size:14.5px;line-height:1.75;letter-spacing:0;"
        ),
        label_style="",
    ),
    "warning": ComponentTheme(
        label="边界",
        container_style=(
            "margin:12px 0;padding:0 0 0 14px;"
            f"border-left:2px solid {COLORS['yellow']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style("#8a6200"),
    ),
    "takeaway": ComponentTheme(
        label="",
        container_style=(
            "margin:16px 0 12px;padding:15px 0 0;"
            f"border-top:2px solid {COLORS['ink']};background:#ffffff;"
            f"color:{COLORS['ink']};font-size:16px;line-height:1.85;letter-spacing:0;"
        ),
        label_style="",
    ),
    "note": ComponentTheme(
        label="注记",
        container_style=(
            "margin:12px 0;padding:11px 13px;"
            f"background:{COLORS['soft']};color:{COLORS['muted']};"
            "font-size:14.5px;line-height:1.75;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["faint"]),
    ),
    "point": ComponentTheme(
        label="要点",
        container_style=(
            "margin:10px 0;padding:0 0 0 14px;"
            f"border-left:2px solid {COLORS['green']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["green"]),
    ),
    "checklist": ComponentTheme(
        label="检查",
        container_style=(
            "margin:14px 0;padding:13px 0 0;"
            f"border-top:2px solid {COLORS['green']};background:#ffffff;"
            f"color:{COLORS['body']};font-size:15.5px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=quiet_label_style(COLORS["green"]),
    ),
    "contact": ComponentTheme(
        label="联系 Chuan",
        container_style=(
            "margin:18px 0 4px;padding:15px 16px;"
            f"background:{COLORS['soft']};border:1px solid {COLORS['line']};"
            "border-radius:2px;"
            f"color:{COLORS['body']};font-size:15px;line-height:1.8;letter-spacing:0;"
        ),
        label_style=line_label_style(COLORS["ink"], border=COLORS["green"]),
    ),
    "image-note": ComponentTheme(
        label="",
        container_style=(
            "margin:0 auto 10px;padding:0 8px;text-align:center;"
            f"color:{COLORS['muted']};font-size:13px;line-height:1.7;letter-spacing:0;"
        ),
        label_style="",
    ),
    "source-note": ComponentTheme(
        label="",
        container_style=(
            "margin:4px 0 10px;"
            f"color:{COLORS['faint']};font-size:12px;line-height:1.65;letter-spacing:0;"
        ),
        label_style="",
    ),
}
