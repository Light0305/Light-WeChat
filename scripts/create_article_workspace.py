#!/usr/bin/env python3
"""Create an idempotent, project-local v9 article workspace."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from v9_support import KINDS, PLUGIN_ROOT, now
from publication_status import load_status
from workspace_guard import article_directory, assert_within, production_articles_root
from settings import load_settings

CONTENT_TYPES = {"guide", "explainer", "analysis", "paper-reading", "project-case", "update"}


def write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def create(title: str, root: Path, kind: str = "technical", column: str = "",
           content_type: str = "", series_id: str = "", project_id: str = "") -> Path:
    settings = load_settings()
    if kind not in KINDS:
        raise ValueError("Unknown article kind: " + kind)
    if column and column not in settings.columns:
        raise ValueError("Unknown content column: " + column)
    if content_type and content_type not in CONTENT_TYPES:
        raise ValueError("Unknown content type: " + content_type)
    column = column or {"paper": "papers", "interdisciplinary": "papers", "career": "careers"}.get(kind, "")
    content_type = content_type or ("paper-reading" if kind in {"paper", "interdisciplinary"} else "explainer")
    folder = article_directory(title, root)
    folder.mkdir(parents=True, exist_ok=True)
    for child in ("images", "prompts", "publishing", "reviews"):
        assert_within(folder / child, folder).mkdir(exist_ok=True)
    # Never silently migrate an existing article into a new workflow.
    existing_legacy = (folder / "draft.md").exists() and not (folder / "article.json").exists()
    if existing_legacy:
        raise ValueError("Existing legacy article: back up and explicitly migrate before adopting v9")
    new_article = not (folder / 'article.json').exists()
    layout = "gzh-chuan-editorial"
    config = {"workflow_version": 9, "kind": kind, "layout": layout, "delivery": "local-only",
              "cover": "images/cover.png", "square_cover": "images/cover-square.png", "contact_card": False,
              "cover_profile": "shared-master-v1", "cover_master": "images/cover-master.png",
              "content_standard": "2026-11", "column": column or None, "content_type": content_type,
              "series_id": series_id or None, "project_id": project_id or None}
    # Use WeWrite's real task-book schema, not a locally invented substitute.
    upstream_brief = Path(__file__).resolve().parents[1] / "vendor/wewrite/skills/wewrite-write/references/article-brief.md"
    import re
    brief = re.search(r"```yaml\s*\n(.*?)```", upstream_brief.read_text(encoding="utf-8"), re.S).group(1)
    import yaml
    brief_data = yaml.safe_load(brief)
    brief_data["constraints"]["desired_length"] = "按读者任务与材料确定，不设统一字数；用完整解释兑现承诺"
    write_if_missing(folder / "brief.yaml", yaml.safe_dump(brief_data, allow_unicode=True, sort_keys=False))
    brand_assets = []
    brand_markdown = ''
    if new_article and settings.contact_card:
        if not settings.contact_card.is_file():
            raise ValueError('The configured optional contact card does not exist')
        contact = folder / 'images/contact-card.png'
        from PIL import Image
        if not contact.exists():
            with Image.open(settings.contact_card) as image:
                image.convert('RGB').save(contact, format='PNG')
        brand_assets.append({'path': 'images/contact-card.png', 'role': 'brand', 'source_ids': [],
            'origin': 'User-supplied optional contact card', 'generated': False,
            'rights': 'User-supplied asset; record verified usage rights in image-ledger.md'})
        brand_markdown = '\n![联系作者](images/contact-card.png)\n'
        config['contact_card'] = 'images/contact-card.png'
    write_if_missing(folder / 'article.json', json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    write_if_missing(folder / 'evidence.json', json.dumps({'sources': [], 'claims': [], 'assets': brand_assets},
        ensure_ascii=False, indent=2) + '\n')
    write_if_missing(folder / "draft.md", f"# {title}\n\n<!-- digest: -->\n<!-- layout: {layout} -->\n\n"
                     "<!-- 先完成简报、研究和证据，再写正文；删除内部编辑说明后交付。 -->\n\n"
                     + brand_markdown)
    write_if_missing(folder / "editor-brief.md", f"# Editor Brief · v9 / Content 2026-11\n\nTopic: {title}\nKind: {kind}\nColumn: {column or '待明确，不从技术类别猜栏目'}\n"
                     f"Content type: {content_type}\nSeries ID: {series_id}\nProject ID: {project_id}\n\n"
                     "## Reader Contract\n\n读者、真正问题与读后收获：\n\n"
                     "## Thesis and Boundary\n\n核心判断、成立条件与最强反证：\n\n"
                     "## Evidence Map\n\n按主张 ID 说明原始来源、定位与未解缺口：\n\n"
                     "## Original Contribution\n\n解释、比较、测试、计算或实用整理：\n\n"
                     "## Depth and Learning Path\n\n读者起点与终点、解释主线中不能跳过的一步：\n\n"
                     "贯穿案例/对象及其证据、反例、改变条件后的判断：\n\n"
                     "前置/本篇/下一步；独立篇可说明理由。按承诺确定篇幅，不沿用上游示例字数上限：\n\n"
                     "## Article Mode and Layout\n\n选择的叙事、主题和每张图的信息任务：\n\n"
                     "## Packaging Bundle\n\n标题、摘要、封面概念、开头及共同承诺：\n\n"
                     "## Packaging Options\n\n有实质差异的备选和取舍理由（按题目需要）：\n")
    write_if_missing(folder / "sources.md", "# Sources · v9\n\n记录真实读过的原文、核实日期、定位、数据口径、反证与缺口；机器字段在 evidence.json。\n")
    write_if_missing(folder / "image-ledger.md", "# Image Ledger · v9\n\n记录每张图的来源/作者、许可或授权依据、原文件、改动和用途；机器字段在 evidence.json。\n")
    write_if_missing(folder / "cover-brief.md", "# Cover Brief · v9\n\n## Promise\n\n"
                     "## Visual Direction\n\n画法、主体、主辅色、材质及本篇选择理由：\n\n"
                     "## Shared Master\n\n母图路径、准确短标题、两种画幅必须保持的视觉内容：\n\n"
                     "## WeChat Wide / Square\n\n宽图约2.35:1、方图1:1的布局与同母图关系：\n\n"
                     "## Source and Tool\n\n每张图的实际工具、提示词、改图输入与导出过程：\n\n"
                     "## Text and Crop Check\n\n两种画幅全尺寸、手机缩略图及宽图中心方裁切的目检结果：\n")
    write_if_missing(folder / "quality-gate.md", "# Quality Gate · v9\n\n尚未审核；先按内容深度标准复核正文，"
                     "在 reviews/editorial.md 留具体定位，再生成预览并运行交付检查。\n")
    write_if_missing(folder / "retrospective.md", "# Retrospective\n\nPublished:\n\n## Human Feedback\n\n## 24h / 72h / 7d Funnel\n\n## Next Experiment\n")
    status = load_status(folder, create=True, root=root)
    if status.get("version") == 1 and not status.get("workflow_version"):
        from publication_status import save_status
        status.update({"workflow_version": 9, "human_review": "pending", "created_at": now()})
        save_status(folder, status, root=root)
    return folder


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("title")
    p.add_argument("--root", type=Path, default=production_articles_root())
    p.add_argument("--kind", choices=sorted(KINDS), default="technical")
    p.add_argument("--column", choices=sorted(load_settings().columns), default="")
    p.add_argument("--content-type", choices=sorted(CONTENT_TYPES), default="")
    p.add_argument("--series-id", default="")
    p.add_argument("--project-id", default="")
    args = p.parse_args()
    print(create(args.title, args.root, args.kind, args.column, args.content_type, args.series_id, args.project_id))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
