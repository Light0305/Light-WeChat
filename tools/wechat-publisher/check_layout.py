from __future__ import annotations

import argparse
import json
from pathlib import Path

from wechat_publisher.layout_qa import check_layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Chuan Lab WeChat layout readiness.")
    parser.add_argument("markdown", type=Path, help="Public article Markdown path.")
    parser.add_argument("--json", action="store_true", help="Print issues as JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on warnings as well as errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = args.markdown.read_text(encoding="utf-8")
    issues = check_layout(text)

    if args.json:
        print(json.dumps([issue.__dict__ for issue in issues], ensure_ascii=False, indent=2))
    else:
        print(f"Chuan Lab layout QA: {args.markdown}")
        print(f"Issues: {len(issues)}")
        for issue in issues:
            print(f"- [{issue.severity}] {issue.code}: {issue.message}")

    has_error = any(issue.severity == "error" for issue in issues)
    has_warning = any(issue.severity == "warning" for issue in issues)
    return 1 if has_error or (args.strict and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())

