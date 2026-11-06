from __future__ import annotations

import re
from dataclasses import dataclass

from wechat_publisher.markdown_wechat import ALLOWED_CHUAN_BLOCKS, CUSTOM_BLOCK_RE, extract_comment_metadata


INTERNAL_PUBLIC_COPY_PATTERNS = [
    "公众号这版",
    "上一版",
    "上面那张",
    "素材：",
    "素材建议：",
    "副标题：",
    "目标读者：",
    "预计阅读时间：",
    "封面图方向：",
    "资料来源：",
    "参考资料：",
    "sources.md",
    "image-ledger",
    "editor-brief",
]

PUBLIC_PRODUCTION_NOTE_PATTERNS = [
    (re.compile(r"\bimagegen\b", re.I), "imagegen"),
    (re.compile(r"由\s*(?:AI|人工智能).{0,24}(?:生成|制作)", re.I), "由 AI 生成/制作"),
    (re.compile(r"(?:本文|本篇|这张|该张)(?:封面|插图|图片|装饰图).{0,24}(?:imagegen|AI|人工智能)", re.I), "公开图片制作说明"),
    (re.compile(r"生成提示词", re.I), "生成提示词"),
    (re.compile(r"它是叙事转场", re.I), "叙事转场制作说明"),
    (re.compile(r"不是产品界面或测试结果", re.I), "非证据制作说明"),
    (re.compile(r"不包含实测数据", re.I), "非实测制作说明"),
]

PUBLIC_SOURCE_DUMP_PATTERNS = [
    re.compile(r"(?:核查|参考|资料)链接\s*[：:]", re.I),
    re.compile(r"(?:延伸阅读|相关链接)\s*[：:]", re.I),
]

GENERIC_AI_PHRASES = [
    "随着人工智能的快速发展",
    "在当今时代",
    "近年来",
    "不难看出",
    "值得注意的是",
    "总的来说",
    "综上所述",
    "具有重要意义",
    "带来了新的机遇和挑战",
    "本文将从",
]

NON_EVIDENCE_IMAGE_MARKERS = (
    "chuan-lab-opener",
    "chuan-lab-contact-card",
    "chuan-lab-end-mark",
    "chuan-lab-signal-divider",
    "ornament-",
    "transition-",
    "texture-",
)
IMAGE_RE = re.compile(
    r"!\[[^\]]*\]\(([^)]+)\)|<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']",
    re.I,
)
BLOCK_SPAN_RE = re.compile(
    r"^:::([A-Za-z][A-Za-z0-9_-]*)\s*$[\s\S]*?^:::\s*$",
    re.M,
)
LOW_SURFACE_BLOCKS = {
    "brand",
    "byline",
    "contact",
    "image-note",
    "source-note",
    "sep",
    "pillar-ai",
    "pillar-llm",
    "pillar-paper",
    "pillar-career",
}
LEGACY_TEMPLATE_BLOCKS = {
    "brand",
    "pillar-ai",
    "pillar-llm",
    "pillar-paper",
    "pillar-career",
    "lead",
    "claim",
    "takeaway",
}
OPENING_TEXT_BLOCKS = {
    "brand",
    "byline",
    "brief",
    "keyline",
    "lead",
    "claim",
    "signal",
    "stat",
    "pullquote",
    "quote",
    "pillar-ai",
    "pillar-llm",
    "pillar-paper",
    "pillar-career",
}
STRUCTURAL_BREAK_RE = re.compile(
    r"!\[[^\]]*\]\([^)]+\)|"
    r"^#{2,3}\s+.+$|"
    r"^```|"
    r"^\|.+\|\s*$|"
    r"^:::(?:brief|keyline|stat|pullquote|data|compare|quote|method|timeline|steps|aside|warning|checklist)\s*$",
    re.M,
)


@dataclass(frozen=True)
class LayoutIssue:
    severity: str
    code: str
    message: str


def chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def find_component_names(markdown_text: str) -> list[str]:
    names: list[str] = []
    for line in markdown_text.splitlines():
        match = CUSTOM_BLOCK_RE.fullmatch(line.strip())
        if match:
            names.append(match.group(1))
    return names


def image_matches(markdown_text: str) -> list[tuple[re.Match[str], str]]:
    matches: list[tuple[re.Match[str], str]] = []
    for match in IMAGE_RE.finditer(markdown_text):
        source = (match.group(1) or match.group(2) or "").strip()
        matches.append((match, source))
    return matches


def is_evidence_image(source: str) -> bool:
    lowered = source.lower()
    return not any(marker in lowered for marker in NON_EVIDENCE_IMAGE_MARKERS)


def check_layout(markdown_text: str) -> list[LayoutIssue]:
    issues: list[LayoutIssue] = []
    components = find_component_names(markdown_text)
    cjk_count = chinese_chars(markdown_text)
    images = image_matches(markdown_text)
    inline_images = [source for _, source in images]
    evidence_images = [(match, source) for match, source in images if is_evidence_image(source)]

    for name in components:
        if name not in ALLOWED_CHUAN_BLOCKS:
            issues.append(
                LayoutIssue("error", "unknown-component", f"Unknown Chuan Lab block: {name}")
            )

    for name in sorted(set(components)):
        count = components.count(name)
        if count >= 4 and name not in {"point", "image-note", "source-note"}:
            issues.append(
                LayoutIssue(
                    "warning",
                    "component-overuse",
                    f"Component '{name}' appears {count} times; vary the layout rhythm.",
                )
            )

    substantive_components = [
        name
        for name in components
        if name not in LOW_SURFACE_BLOCKS
    ]
    max_components = 3 if cjk_count <= 5000 else 4
    if cjk_count > 1200 and len(substantive_components) > max_components:
        issues.append(
            LayoutIssue(
                "warning",
                "component-density",
                f"{len(substantive_components)} substantive callout blocks exceed the "
                f"recommended maximum of {max_components}; use headings and plain paragraphs "
                "for the default flow.",
            )
        )

    block_spans = list(BLOCK_SPAN_RE.finditer(markdown_text))
    for left, right in zip(block_spans, block_spans[1:]):
        if (
            left.group(1) not in LOW_SURFACE_BLOCKS
            and right.group(1) not in LOW_SURFACE_BLOCKS
            and not markdown_text[left.end() : right.start()].strip()
        ):
            issues.append(
                LayoutIssue(
                    "warning",
                    "consecutive-components",
                    f"Consecutive '{left.group(1)}' and '{right.group(1)}' blocks create a component wall; put editorial prose or evidence between them.",
                )
            )
            break

    opening_end = len(markdown_text)
    heading_match = re.search(r"^##\s+", markdown_text, re.M)
    if heading_match:
        opening_end = heading_match.start()
    cjk_seen = 0
    for char_match in re.finditer(r"[\u4e00-\u9fff]", markdown_text):
        cjk_seen += 1
        if cjk_seen >= 500:
            opening_end = min(opening_end, char_match.end())
            break
    opening_text_blocks = [
        match.group(1)
        for match in block_spans
        if match.start() < opening_end and match.group(1) in OPENING_TEXT_BLOCKS
    ]
    if len(opening_text_blocks) > 1:
        issues.append(
            LayoutIssue(
                "warning",
                "stacked-opening-text",
                "Opening stacks multiple text surfaces ("
                + " + ".join(opening_text_blocks)
                + "); keep one digest/byline/quote/stat surface and let a documentary hero stand on its own.",
            )
        )

    opening_slice = markdown_text[:opening_end]
    if (
        cjk_count > 1200
        and chinese_chars(opening_slice) > 180
        and not image_matches(opening_slice)
        and not opening_text_blocks
    ):
        issues.append(
            LayoutIssue(
                "warning",
                "flat-opening",
                "The opening runs past 180 Chinese characters without an image or one intentional opening surface; design the first screen instead of starting with a plain text wall.",
            )
        )

    legacy_count = sum(name in LEGACY_TEMPLATE_BLOCKS for name in components)
    if legacy_count >= 2:
        issues.append(
            LayoutIssue(
                "warning",
                "legacy-template-sequence",
                "Two or more legacy orientation/claim blocks make the article resemble the old pillar + lead + claim + takeaway template.",
            )
        )

    for phrase in INTERNAL_PUBLIC_COPY_PATTERNS:
        if phrase in markdown_text:
            issues.append(
                LayoutIssue(
                    "error",
                    "public-metadata-leak",
                    f"Internal/editor-facing phrase appears in public draft: {phrase}",
                )
            )

    for pattern, label in PUBLIC_PRODUCTION_NOTE_PATTERNS:
        if pattern.search(markdown_text):
            issues.append(
                LayoutIssue(
                    "error",
                    "public-production-note",
                    f"Production/provenance note appears in public draft: {label}. "
                    "Keep tool, prompt, rights, and AI-generation details in image-ledger.md; "
                    "public captions should only explain the visual and cite documentary sources.",
                )
            )

    for pattern in PUBLIC_SOURCE_DUMP_PATTERNS:
        match = pattern.search(markdown_text)
        if match:
            issues.append(
                LayoutIssue(
                    "error",
                    "public-source-dump",
                    f"Generic source-link dump appears in public draft: {match.group(0)}. "
                    "Keep the complete source ledger in sources.md; link only a source that the "
                    "reader must open at the relevant claim or action.",
                )
            )

    for phrase in GENERIC_AI_PHRASES:
        if phrase in markdown_text:
            issues.append(
                LayoutIssue(
                    "warning",
                    "generic-ai-phrase",
                    f"Generic AI-like phrase found; rewrite with a concrete scene or claim: {phrase}",
                )
            )

    min_evidence_images = 0
    if cjk_count > 1800:
        min_evidence_images = 2
    if cjk_count > 3200:
        min_evidence_images = 3
    if cjk_count > 5000:
        min_evidence_images = 4
    # A documented editorial choice can prefer two useful originals over filler.
    # Retain the baseline evidence requirement and the independent rhythm checks.
    if extract_comment_metadata(markdown_text).get("image-count-rationale"):
        min_evidence_images = min(min_evidence_images, 2)
    if len(evidence_images) < min_evidence_images:
        issues.append(
            LayoutIssue(
                "warning",
                "too-few-images",
                f"Draft has {len(evidence_images)} evidence image(s); a draft of this length "
                f"should normally include at least {min_evidence_images}. Brand opener and "
                "contact assets do not count.",
            )
        )

    if cjk_count > 2400:
        structural_breaks = list(STRUCTURAL_BREAK_RE.finditer(markdown_text))
        segment_starts = [0] + [match.end() for match in structural_breaks]
        segment_ends = [match.start() for match in structural_breaks] + [len(markdown_text)]
        longest_visual_gap = max(
            chinese_chars(markdown_text[start:end])
            for start, end in zip(segment_starts, segment_ends)
        )
        if longest_visual_gap > 1200:
            issues.append(
                LayoutIssue(
                    "warning",
                    "structural-gap",
                    f"A body span of about {longest_visual_gap} Chinese characters has no image, heading, table, code sample, or essential callout. Review the reading rhythm.",
                )
            )

    generic_template_headings = sum(
        bool(re.search(pattern, markdown_text, re.M))
        for pattern in (
            r"^##\s+(?:一[、.]\s*)?发生了什么\s*$",
            r"^##\s+(?:二[、.]\s*)?真正的变化\s*$",
            r"^##\s+(?:三[、.]\s*)?对读者意味着什么\s*$",
        )
    )
    if generic_template_headings >= 2:
        issues.append(
            LayoutIssue(
                "warning",
                "canned-article-skeleton",
                "Draft reuses the old generic article skeleton; write headings that advance this article's specific argument.",
            )
        )

    markdown_list_lines = re.findall(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", markdown_text, re.M)
    if markdown_list_lines:
        issues.append(
            LayoutIssue(
                "warning",
                "markdown-list-risk",
                "Markdown bullets/numbers can be fragile in WeChat; prefer paragraphs, tables, or Chuan blocks.",
            )
        )

    table_blocks = re.findall(r"(?:^\|.*\|\s*$\n?){2,}", markdown_text, re.M)
    for table_index, table in enumerate(table_blocks, start=1):
        rows = [line for line in table.splitlines() if line.strip().startswith("|")]
        if not rows:
            continue
        column_count = max(len(line.strip().strip("|").split("|")) for line in rows)
        if column_count > 4:
            issues.append(
                LayoutIssue(
                    "warning",
                    "wide-mobile-table",
                    f"Table {table_index} has {column_count} columns; split it or use a source figure because five-column tables become unreadable on a 390 px screen.",
                )
            )
        data_cells = [
            cell.strip()
            for row in rows[2:]
            for cell in row.strip().strip("|").split("|")
        ]
        if any(chinese_chars(cell) > 28 for cell in data_cells):
            issues.append(
                LayoutIssue(
                    "warning",
                    "dense-mobile-table",
                    f"Table {table_index} contains prose-length cells; convert the decision text into steps, points, or short paragraphs for mobile reading.",
                )
            )

    long_paragraphs = []
    for para in re.split(r"\n\s*\n", markdown_text):
        clean = re.sub(r"\s+", "", para)
        if chinese_chars(clean) > 260:
            long_paragraphs.append(chinese_chars(clean))
    if long_paragraphs:
        issues.append(
            LayoutIssue(
                "warning",
                "long-paragraph",
                f"{len(long_paragraphs)} paragraph(s) exceed 260 Chinese characters.",
            )
        )

    bold_segments = re.findall(r"\*\*(.+?)\*\*", markdown_text, re.S)
    bold_chars = sum(chinese_chars(segment) for segment in bold_segments)
    if cjk_count > 1200 and bold_chars / max(cjk_count, 1) > 0.12:
        issues.append(
            LayoutIssue(
                "warning",
                "bold-heavy",
                "More than 12% of Chinese body text is bold; keep colored emphasis selective.",
            )
        )
    if any(chinese_chars(segment) > 80 for segment in bold_segments):
        issues.append(
            LayoutIssue(
                "warning",
                "bold-paragraph",
                "An ordinary bold span exceeds 80 Chinese characters; emphasize a phrase "
                "or sentence instead of a full paragraph.",
            )
        )

    repeated_biru = len(re.findall(r"^\s*比如", markdown_text, re.M))
    if repeated_biru >= 3:
        issues.append(
            LayoutIssue(
                "warning",
                "ai-short-rhythm",
                "Repeated line-initial '比如' creates AI-like short-line rhythm.",
            )
        )

    stacked_short_lines = 0
    current_stack = 0
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", "!", ":::", "---")):
            current_stack = 0
            continue
        if 4 <= chinese_chars(stripped) <= 24 and stripped.endswith(("。", "？", "！")):
            current_stack += 1
            stacked_short_lines = max(stacked_short_lines, current_stack)
        else:
            current_stack = 0
    if stacked_short_lines >= 4:
        issues.append(
            LayoutIssue(
                "warning",
                "stacked-short-lines",
                "Four or more consecutive short sentence lines found; merge into natural paragraphs.",
            )
        )

    return issues
