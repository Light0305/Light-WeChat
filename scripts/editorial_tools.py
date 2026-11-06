#!/usr/bin/env python3
"""Run the original WeWrite editorial evaluator and advisory style-risk checks."""
import argparse
import json
import sys
from pathlib import Path

from upstream_modules import editorial_report, style_signals
from v9_support import input_manifest, load_article, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    article, _, _ = load_article(args.article)
    signals = style_signals((article / "draft.md").read_text(encoding="utf-8"))
    write_json(article / "reviews/wewrite-style-signals.json", signals)
    result = editorial_report(article)
    result["input_sha256"] = input_manifest(article)["sha256"]
    result["source"] = "vendor/wewrite/src/wewrite/commands/content_eval.py"
    write_json(article / "reviews/wewrite-editorial-eval.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["publishable"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
