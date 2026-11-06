#!/usr/bin/env python3
"""Flag formulaic and AI-like prose patterns in a Chuan Lab draft."""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


CONTRAST_RE = re.compile(
    r"(?:不是|并非|不只是|不止|并不是)[^。！？\n]{0,42}(?:而是|更是)"
)
IMPORTANCE_RE = re.compile(r"真正(?:的|地|值得|重要|改变|变化|问题|关键|决定|卡住|需要|能|让|把|揭开)?")
TRANSITION_RE = re.compile(
    r"这意味着|换句话说|更准确地说|从这个角度看|说到底|归根结底|"
    r"值得注意的是|需要注意的是|问题在于|关键在于"
)
STANCE_RE = re.compile(r"我的(?:核心)?判断是|本文的核心判断|核心判断是|先说结论")
SCAFFOLD_RE = re.compile(
    r"本文将|接下来(?:我们)?|下面(?:我们)?|从以下(?:几个)?|"
    r"可以看出|不难发现|不难看出|首先[^。！？]{0,160}其次"
)
GENERIC_RE = re.compile(
    r"随着人工智能的快速发展|在当今时代|带来了新的机遇和挑战|"
    r"具有重要意义|未来已来|赋能千行百业|颠覆(?:了)?传统|全新的范式"
)
ABSTRACTION_RE = re.compile(
    r"底层逻辑|范式转变|重新定义|核心在于|更重要的是|"
    r"背后(?:是|意味着)|从本质上看|本质上(?:是|意味着)"
)


@dataclass(frozen=True)
class ProseIssue:
    code: str
    count: int
    limit: int
    message: str


def chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def clean_public_text(markdown_text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", markdown_text)
    text = re.sub(r"<!--([\s\S]*?)-->", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^#\s+.*$", " ", text, count=1, flags=re.M)
    text = re.sub(r"^:::[A-Za-z][A-Za-z0-9_-]*\s*$|^:::\s*$", " ", text, flags=re.M)
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.M)
    text = re.sub(r"[*_`>#]", "", text)
    return text


def prose_paragraphs(markdown_text: str) -> list[str]:
    plain_markdown = re.sub(
        r"^:::[A-Za-z][A-Za-z0-9_-]*\s*$[\s\S]*?^:::\s*$",
        " ",
        markdown_text,
        flags=re.M,
    )
    cleaned = clean_public_text(plain_markdown)
    paragraphs: list[str] = []
    for raw in re.split(r"\n\s*\n", cleaned):
        paragraph = re.sub(r"\s+", "", raw)
        if chinese_chars(paragraph) >= 8:
            paragraphs.append(paragraph)
    return paragraphs


def sentence_count(paragraph: str) -> int:
    parts = [part for part in re.split(r"[。！？!?]+", paragraph) if chinese_chars(part) >= 2]
    return max(1, len(parts))


def repeated_paragraph_starter(paragraphs: list[str]) -> tuple[str, int]:
    starters: list[str] = []
    for paragraph in paragraphs:
        match = re.search(r"[\u4e00-\u9fff]{2,4}", paragraph)
        if match:
            starters.append(match.group(0)[:2])
    if not starters:
        return "", 0
    starter, count = Counter(starters).most_common(1)[0]
    return starter, count


def analyse_prose(markdown_text: str) -> tuple[dict[str, float | int | str], list[ProseIssue]]:
    text = clean_public_text(markdown_text)
    cjk = chinese_chars(text)
    paragraphs = prose_paragraphs(markdown_text)
    counts = {
        "contrast_pivots": len(CONTRAST_RE.findall(text)),
        "importance_markers": len(IMPORTANCE_RE.findall(text)),
        "formulaic_transitions": len(TRANSITION_RE.findall(text)),
        "stance_labels": len(STANCE_RE.findall(text)),
        "meta_scaffolding": len(SCAFFOLD_RE.findall(text)),
        "generic_claims": len(GENERIC_RE.findall(text)),
        "abstraction_markers": len(ABSTRACTION_RE.findall(text)),
    }
    limits = {
        "contrast_pivots": max(1, 1 + cjk // 2500),
        "importance_markers": max(2, math.ceil(cjk / 1800)),
        "formulaic_transitions": max(2, math.ceil(cjk / 1600)),
        "stance_labels": 1,
        "meta_scaffolding": 0,
        "generic_claims": 0,
        "abstraction_markers": max(1, math.ceil(cjk / 2400)),
    }
    labels = {
        "contrast_pivots": "corrective 'not X but Y' pivots",
        "importance_markers": "uses of 真正",
        "formulaic_transitions": "formulaic transition markers",
        "stance_labels": "announced stance labels",
        "meta_scaffolding": "meta-explanatory scaffolds",
        "generic_claims": "generic AI-era claims",
        "abstraction_markers": "abstract importance/mechanism labels",
    }
    issues: list[ProseIssue] = []
    for code, count in counts.items():
        limit = limits[code]
        if count > limit:
            issues.append(
                ProseIssue(
                    code=code,
                    count=count,
                    limit=limit,
                    message=(
                        f"Found {count} {labels[code]} (budget {limit}); rebuild the flagged "
                        "sentences from concrete evidence instead of swapping synonyms."
                    ),
                )
            )

    one_sentence = sum(sentence_count(paragraph) == 1 for paragraph in paragraphs)
    one_sentence_ratio = one_sentence / len(paragraphs) if paragraphs else 0.0
    if len(paragraphs) >= 10 and one_sentence_ratio > 0.68:
        issues.append(
            ProseIssue(
                code="one_sentence_rhythm",
                count=one_sentence,
                limit=math.floor(len(paragraphs) * 0.68),
                message=(
                    f"{one_sentence}/{len(paragraphs)} prose paragraphs contain one sentence; "
                    "merge related thoughts and reserve isolated lines for earned emphasis."
                ),
            )
        )

    starter, starter_count = repeated_paragraph_starter(paragraphs)
    if len(paragraphs) >= 10 and starter_count >= 4 and starter_count / len(paragraphs) >= 0.18:
        issues.append(
            ProseIssue(
                code="repeated_paragraph_starter",
                count=starter_count,
                limit=3,
                message=(
                    f"{starter_count} paragraphs begin with '{starter}'; vary the syntax only "
                    "after checking whether the paragraphs are doing duplicate work."
                ),
            )
        )

    metrics: dict[str, float | int | str] = {
        "chinese_chars": cjk,
        "paragraphs": len(paragraphs),
        "one_sentence_paragraph_ratio": round(one_sentence_ratio, 3),
        "most_repeated_starter": starter,
        "most_repeated_starter_count": starter_count,
        **counts,
    }
    return metrics, issues


def resolve_draft(path: Path) -> Path:
    if path.is_dir():
        return path / "draft.md"
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Article folder or Markdown draft")
    args = parser.parse_args()
    draft_path = resolve_draft(args.path)
    if not draft_path.exists():
        print(f"FAIL: draft not found: {draft_path}")
        return 2
    metrics, issues = analyse_prose(draft_path.read_text(encoding="utf-8"))
    print(f"Chuan Lab prose lint: {draft_path}")
    for key, value in metrics.items():
        print(f"- {key}: {value}")
    print(f"Issues: {len(issues)}")
    for issue in issues:
        print(f"- [{issue.code}] {issue.message}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
