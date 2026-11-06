#!/usr/bin/env python3
"""Check v9 package integrity; editorial truth still requires real source review."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

from v9_support import (KINDS, LAYOUTS, PUBLISHER_ROOT, input_manifest, inside, load_article,
                        now, preview_fingerprint, read_json, sha, valid_preview, write_json)


def image_paths(text: str) -> list[str]:
    paths = re.findall(r'!\[[^\]]*\]\(([^)]+)\)|<img\b[^>]*\bsrc=["\']([^"\']+)', text, re.I)
    return list(dict.fromkeys((a or b).strip().strip("<>") for a, b in paths))


def public_text(text: str) -> str:
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    return text


def audit_covers(article: Path, config: dict, assets: dict) -> list[str]:
    """Validate delivered formats and their common source; visual identity needs review."""
    errors = []
    fields = [("cover", "cover", 900 / 383), ("square_cover", "square-cover", 1)]
    profile = config.get("cover_profile")
    shared = profile == "shared-master-v1"
    if profile and not shared:
        errors.append(f"Unknown cover profile: {profile}")
    if shared:
        master = config.get("cover_master", "")
        if not master or assets.get(master, {}).get("role") != "cover-master":
            errors.append("Shared cover master is missing from config or asset ledger")
        try:
            with Image.open(inside(article, master)) as im:
                if im.width < 900 or im.height < 383:
                    errors.append("Shared cover master resolution is too small")
                im.verify()
        except (OSError, ValueError) as exc:
            errors.append(f"Unusable cover master: {exc}")
        paths = [master] + [config.get(field, "") for field, _, _ in fields]
        if len(set(paths)) != len(paths):
            errors.append("Keep the cover master and each delivered format at distinct paths")
        for field, _, _ in fields:
            if not master or assets.get(config.get(field, ""), {}).get("derived_from") != master:
                errors.append(f"Cover must reference the shared master with derived_from: {field}")
    for field, role, expected in fields:
        name = config.get(field, "")
        if assets.get(name, {}).get("role") != role:
            errors.append(f"Cover ledger role missing: {field}")
        try:
            with Image.open(inside(article, name)) as im:
                w, h = im.size
                if w < 900 or h <= 0 or abs(w / h - expected) / expected > .025:
                    errors.append(f"Incorrect cover resolution/ratio: {name} {w}x{h}")
                im.verify()
        except (OSError, ValueError) as exc:
            errors.append(f"Unusable cover {field}: {exc}")
    return errors


def audit(article: Path, delivery: bool = False) -> dict:
    errors, warnings = [], []
    try:
        article, config, evidence = load_article(article)
        current = input_manifest(article)
    except (OSError, ValueError, TypeError) as exc:
        return {"passed": False, "errors": [str(exc)], "warnings": [], "checked_at": now()}
    if config.get("kind") not in KINDS:
        errors.append("Unknown article kind")
    if config.get("layout") not in LAYOUTS:
        errors.append("Unknown layout")
    if config.get("delivery") not in {"wechat-draft", "local-only"}:
        errors.append("delivery must be wechat-draft or local-only")
    for name in ("draft.md", "editor-brief.md", "sources.md", "image-ledger.md", "cover-brief.md"):
        p = inside(article, name)
        if not p.is_file() or not p.read_text(encoding="utf-8-sig").strip():
            errors.append(f"Required document missing or empty: {name}")
    draft_path = inside(article, "draft.md")
    draft = draft_path.read_text(encoding="utf-8-sig") if draft_path.is_file() else ""
    layout = re.search(r"<!--\s*layout:\s*(\S+)\s*-->", draft)
    if not layout or layout.group(1) != config.get("layout"):
        errors.append("Draft layout metadata must match article.json")
    title_match = re.search(r"^#\s+(.+)$", draft, re.M)
    title = title_match.group(1).strip() if title_match else ""
    title_override = re.search(r"<!--\s*title:\s*(.*?)\s*-->", draft)
    if title_override and title_override.group(1).strip() != title:
        errors.append("Public title override differs from H1; keep a single reviewed title")
    digest_match = re.search(r"<!--\s*digest:\s*(.*?)\s*-->", draft)
    digest = digest_match.group(1).strip() if digest_match else ""
    sys.path.insert(0, str(PUBLISHER_ROOT))
    from wechat_publisher.payload import MAX_DIGEST_CHARS, MAX_TITLE_CHARS
    if not title or len(title) > MAX_TITLE_CHARS:
        errors.append(f"Title missing or exceeds backend limit of {MAX_TITLE_CHARS} characters")
    if not digest or len(digest) > MAX_DIGEST_CHARS:
        errors.append(f"Digest missing or exceeds backend limit of {MAX_DIGEST_CHARS} characters")
    visible = public_text(draft)
    if re.search(r"\{\{.+?\}\}|【(?:插入|待补)[^】]*】", visible):
        errors.append("Unresolved production placeholders in public copy")
    if re.search(r"<\s*(?:script|iframe|form|input|style)\b|\son\w+\s*=|javascript:", draft, re.I):
        errors.append("Public copy contains active or unsupported HTML")
    if re.search(r"```(?:mermaid|latex)|\$\$", draft, re.I):
        errors.append("Render equations/diagrams before delivery; raw syntax remains")
    body = re.sub(r"^#\s+.+$", "", visible, flags=re.M)
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", body).strip()
    if not body:
        errors.append("Public body is empty")
    if re.search(r"震惊|吊打|封神|史诗级|一文读懂", title):
        warnings.append("Review title specificity and evidence strength; rhetoric is advisory")
    if any(len(p) > 500 for p in visible.split("\n\n")):
        warnings.append("Some paragraphs are long; inspect mobile reading rhythm")

    sources = {}
    source_list = evidence.get("sources", [])
    claim_list = evidence.get("claims", [])
    asset_list = evidence.get("assets", [])
    if not all(isinstance(v, list) for v in (source_list, claim_list, asset_list)):
        errors.append("evidence sources/claims/assets must be arrays")
        source_list, claim_list, asset_list = [], [], []
    for s in source_list:
        if not isinstance(s, dict):
            errors.append("Invalid source record")
            continue
        sid = s.get("id")
        if not sid or sid in sources:
            errors.append(f"Missing or duplicate source ID: {sid}")
        sources[sid] = s
        if s.get("type") not in {"primary", "secondary", "community", "user"}:
            errors.append(f"Unknown source type: {sid}")
        if s.get("status") == "verified":
            required = ("title", "accessed_at", "locator")
            if not all(str(s.get(k, "")).strip() for k in required):
                errors.append(f"Verified source lacks title/access time/locator: {sid}")
            if s.get("type") != "user":
                u = urlparse(s.get("url", ""))
                if u.scheme not in {"http", "https"} or not u.hostname or u.hostname in {"example.com", "example.org"}:
                    errors.append(f"Verified source lacks real original URL: {sid}")
    used_claims, ids = [], set()
    for c in claim_list:
        if not isinstance(c, dict):
            errors.append("Invalid claim record")
            continue
        cid = c.get("id")
        if not cid or cid in ids:
            errors.append(f"Missing or duplicate claim ID: {cid}")
        ids.add(cid)
        if c.get("used", True) is False:
            continue
        used_claims.append(c)
        kind = c.get("kind")
        if not c.get("text") or kind not in {"fact", "inference", "opinion"}:
            errors.append(f"Claim lacks text or valid kind: {cid}")
        refs = c.get("sources", [])
        if not isinstance(refs, list):
            refs = []
            errors.append(f"Claim sources must be an array: {cid}")
        if kind in {"fact", "inference"} and (not refs or c.get("status") != "verified" or not c.get("locator")):
            errors.append(f"Used claim lacks verified evidence and locator: {cid}")
        if kind == "inference" and not c.get("reasoning"):
            errors.append(f"Inference needs reasoning: {cid}")
        for ref in refs:
            if ref not in sources or sources[ref].get("status") != "verified":
                errors.append(f"Claim {cid} points to unverified/missing source {ref}")
    if not used_claims:
        errors.append("No used claims recorded; editorial review cannot be traced")
    assets = {}
    for a in asset_list:
        if not isinstance(a, dict) or not a.get("path"):
            errors.append("Invalid asset record")
            continue
        name = a["path"]
        if name in assets:
            errors.append(f"Duplicate asset: {name}")
        assets[name] = a
        try:
            if not inside(article, name).is_file():
                errors.append(f"Asset missing: {name}")
        except ValueError as exc:
            errors.append(str(exc))
        if not a.get("origin") or not a.get("rights"):
            errors.append(f"Asset provenance/use basis missing: {name}")
        if a.get("generated") is True:
            if not a.get("generator") or not isinstance(a.get("prompt"), str) or not a.get("prompt"):
                errors.append(f"Generated asset needs actual generator and saved prompt: {name}")
            else:
                try:
                    if not inside(article, a["prompt"]).is_file():
                        errors.append(f"Generated asset prompt is missing: {name}")
                except ValueError as exc:
                    errors.append(str(exc))
        role = a.get("role")
        if role not in {"evidence", "explanation", "editorial", "cover-master", "cover", "square-cover", "brand"}:
            errors.append(f"Invalid asset role: {name}")
        refs = a.get("source_ids", [])
        if role == "evidence" and (a.get("generated") is not False or not refs):
            errors.append(f"Evidence image must be real and traceable: {name}")
        for ref in refs:
            if ref not in sources or sources[ref].get("status") != "verified":
                errors.append(f"Asset points to missing/unverified source: {name} -> {ref}")
    used_images = image_paths(draft)
    for name in used_images:
        if name not in assets:
            errors.append(f"Public image not in evidence asset ledger: {name}")
        try:
            p = inside(article, name)
            with Image.open(p) as im:
                im.verify()
        except (OSError, ValueError) as exc:
            errors.append(f"Unusable public image {name}: {exc}")
    if not any(assets.get(p, {}).get("role") in {"evidence", "explanation"} for p in used_images):
        warnings.append("No evidence/explanation visual in body; justify this editorial choice in review")
    errors.extend(audit_covers(article, config, assets))
    contact = config.get('contact_card', False)
    if contact and (not isinstance(contact, str) or not used_images or used_images[-1] != contact):
        errors.append('Configured optional contact card must be the final body image')
    try:
        from wechat_publisher.markdown_wechat import audit_rendered_layout, markdown_to_wechat_html
        rendered = markdown_to_wechat_html(draft)
        audit_rendered_layout(rendered)
        if config.get("layout", "").startswith("gzh-"):
            from upstream_modules import validate_body
            upstream_errors, upstream_warnings, leaf_count = validate_body(rendered)
            errors.extend("gzh-design: " + item for item in upstream_errors)
            warnings.extend("gzh-design: " + item for item in upstream_warnings)
        if re.search(r"<p\b[^>]*>\s*(?:&nbsp;|<br\s*/?>)?\s*</p>", rendered, re.I):
            errors.append("Empty spacer paragraph in rendered public copy")
    except (ValueError, KeyError) as exc:
        errors.append(f"Rendered HTML failed: {exc}")
    if delivery:
        if config.get("layout", "").startswith("gzh-"):
            try:
                from upstream_modules import editorial_report
                assessment = editorial_report(article)
                if not assessment["publishable"]:
                    errors.append("WeWrite editorial gate failed: average >= 4, minimum >= 3, no blockers required")
            except (OSError, ValueError, TypeError) as exc:
                errors.append("WeWrite editorial assessment missing/invalid: " + str(exc))
        errors.extend(valid_preview(article, current["sha256"]))
        try:
            reviews = read_json(inside(article, "review-state.json"))
        except (OSError, ValueError):
            reviews = {}
        for role in ("factual", "editorial", "visual"):
            r = reviews.get(role, {})
            if r.get("decision") != "pass" or r.get("input_sha256") != current["sha256"]:
                errors.append(f"Current {role} review missing/stale")
                continue
            try:
                if sha(inside(article, r["report"])) != r.get("report_sha256"):
                    errors.append(f"{role} review report changed")
                if role == "visual" and r.get("preview_sha256") != preview_fingerprint(article):
                    errors.append("Visual review refers to a different preview")
            except (KeyError, OSError, ValueError):
                errors.append(f"{role} report missing/unsafe")
    return {"passed": not errors, "mode": "delivery" if delivery else "structural",
            "input_sha256": current["sha256"], "checked_at": now(), "errors": errors,
            "warnings": warnings, "counts": {"sources": len(sources), "claims": len(used_claims),
                                              "body_images": len(used_images)}}


def save_report(article: Path, result: dict) -> None:
    lines = ["# Quality Gate · v9", "", f"Result: {'PASS' if result['passed'] else 'FAIL'}",
             f"Mode: {result.get('mode', 'invalid-package')}", f"Checked: {result['checked_at']}", "",
             "机器检查不代替事实、编辑、视觉审阅；PASS 不等于人工批准。", "", "## Blocking issues", ""]
    lines.extend("- " + s for s in result["errors"])
    if not result["errors"]:
        lines.append("None.")
    lines.extend(["", "## Advisory observations", ""])
    lines.extend("- " + s for s in result["warnings"])
    if not result["warnings"]:
        lines.append("None.")
    inside(article, "quality-gate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(inside(article, "publishing/quality-result.json"), result)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", type=Path)
    parser.add_argument("--delivery", action="store_true")
    args = parser.parse_args(argv)
    from workspace_guard import assert_article_root
    article = assert_article_root(args.article)
    result = audit(article, args.delivery)
    save_report(article, result)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
