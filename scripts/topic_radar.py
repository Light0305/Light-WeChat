#!/usr/bin/env python3
"""Collect RSS/Atom or supplied entries as unverified editorial leads, never facts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def date_value(value: str) -> datetime | None:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            result = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    return result.astimezone(timezone.utc) if result.tzinfo else result.replace(tzinfo=timezone.utc)


def canonical(url: str) -> str:
    p = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urlencode(sorted(query)), ""))


def event_key(entry: dict) -> str:
    if entry.get("event_key"):
        return "explicit:" + str(entry["event_key"])
    url = canonical(entry["url"])
    arxiv = re.search(r"arxiv\.org/(?:abs|pdf)/((?:\d{4}\.\d{4,5}|[a-z-]+/\d{7}))(?:v\d+)?", url)
    if arxiv:
        return "arxiv:" + arxiv.group(1)
    if entry.get("doi"):
        return "doi:" + entry["doi"].lower().removeprefix("https://doi.org/")
    if "doi.org/" in url:
        return "doi:" + url.split("doi.org/", 1)[1].lower()
    return "url:" + url


def parse_feed(data: bytes, source: str) -> list[dict]:
    root = ET.fromstring(data)
    entries = []
    atom = "{http://www.w3.org/2005/Atom}"
    def text(node, paths):
        for path in paths:
            value = node.findtext(path)
            if value:
                return value.strip()
        return ""
    nodes = root.findall("./channel/item") if root.tag != atom + "feed" else root.findall(atom + "entry")
    for node in nodes:
        if node.tag == atom + "entry":
            link = next((n.get("href", "") for n in node.findall(atom + "link")
                         if n.get("rel", "alternate") == "alternate"), "")
            published = text(node, [atom + "published"])
            updated = text(node, [atom + "updated"])
            title = text(node, [atom + "title"])
        else:
            link = text(node, ["link", "guid"])
            published = text(node, ["pubDate", "{http://purl.org/dc/elements/1.1/}date"])
            updated, title = "", text(node, ["title"])
        if link.startswith(("http://", "https://")) and title:
            entries.append({"title": re.sub(r"\s+", " ", title), "url": link,
                            "published_at": published, "updated_at": updated, "source": source})
    return entries


def collect(source: dict, raw_dir: Path) -> tuple[list[dict], dict]:
    sid = source["id"]
    health = {"id": sid, "url": source["url"], "collected_at": datetime.now(timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(source["url"], headers={"User-Agent": "ChuanLab-Radar/9.0 (+editorial research)",
                                                              "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml"})
        with urllib.request.urlopen(req, timeout=18) as response:
            data = response.read(4_000_001)
        if len(data) > 4_000_000:
            raise ValueError("Feed exceeds 4 MB collection bound")
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", sid)
        raw_path = raw_dir / (safe_id + ".xml")
        raw_path.write_bytes(data)
        entries = parse_feed(data, sid)
        health.update({"status": "ok" if entries else "ok-empty", "entries": len(entries), "raw_sha256": hashlib.sha256(data).hexdigest(),
                       "raw_file": raw_path.name})
        return entries, health
    except Exception as exc:
        health.update({"status": "failed", "error": str(exc)[:250]})
        return [], health


def normalize(entries: list[dict], as_of: datetime, days: int) -> dict:
    selected, excluded, groups = [], [], {}
    cutoff = as_of - timedelta(days=days)
    for raw in entries:
        e = dict(raw)
        if not isinstance(e.get("url"), str) or not e["url"].startswith(("http://", "https://")) or not e.get("title"):
            excluded.append({**e, "reason": "missing title or valid URL"})
            continue
        e["url"] = canonical(e["url"])
        published = date_value(e.get("published_at", ""))
        updated = date_value(e.get("updated_at", ""))
        # Updated-only is useful but must never be relabeled as publication time.
        e["date_status"] = "published" if published else "updated-only" if updated else "unknown"
        e["published_at"] = published.isoformat() if published else None
        e["updated_at"] = updated.isoformat() if updated else None
        e["verification"] = "unverified-discovery"
        active_date = published or updated
        if active_date and active_date > as_of + timedelta(minutes=5):
            excluded.append({**e, "reason": "future timestamp; verify source timezone"})
            continue
        if active_date and active_date < cutoff:
            excluded.append({**e, "reason": "outside requested collection window"})
            continue
        key = event_key(e)
        if key in groups:
            groups[key]["related_entries"].append(e)
            continue
        e["event_key"] = key
        e["related_entries"] = []
        groups[key] = e
        selected.append(e)
    selected.sort(key=lambda e: e["published_at"] or e["updated_at"] or "", reverse=True)
    return {"entries": selected, "excluded": excluded}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "assets/source-registry.json")
    p.add_argument("--input", type=Path, help="JSON array or object with entries from other discovery tools")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--as-of", help="ISO timestamp; otherwise current UTC time")
    args = p.parse_args(argv)
    if args.days < 1:
        p.error("--days must be positive")
    as_of = date_value(args.as_of) if args.as_of else datetime.now(timezone.utc)
    if as_of is None:
        p.error("Invalid --as-of timestamp")
    args.out.mkdir(parents=True, exist_ok=True)
    health, entries = [], []
    if args.input:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        entries = data if isinstance(data, list) else data["entries"]
        health.append({"id": "supplied-input", "status": "read", "entries": len(entries)})
    else:
        config = json.loads(args.config.read_text(encoding="utf-8-sig"))
        feeds = [s for s in config["sources"] if s.get("kind") == "rss" and s.get("enabled", True)]
        raw_dir = args.out / "raw"
        raw_dir.mkdir(exist_ok=True)
        with ThreadPoolExecutor(max_workers=5) as pool:
            for rows, status in pool.map(lambda s: collect(s, raw_dir), feeds):
                entries.extend(rows)
                health.append(status)
    result = {"as_of": as_of.isoformat(), "days": args.days, "source_health": health,
              "scope": "Unverified leads; requires original-source reading and manual editorial selection",
              **normalize(entries, as_of, args.days)}
    (args.out / "radar.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Chuan Lab 选题线索", "", f"截至：{as_of.isoformat()}", "",
             "线索未经事实认证；日期未知或仅更新时间不视为新发布。", "", "## 来源健康", ""]
    lines.extend(f"- {h['id']}: {h['status']}" + (" — " + h["error"] if h.get("error") else "") for h in health)
    lines.extend(["", "## 候选线索", ""])
    for e in result["entries"]:
        title = str(e["title"]).replace("[", "(").replace("]", ")")
        lines.append(f"- [{title}]({e['url']}) · {e['date_status']} · {e.get('published_at') or e.get('updated_at') or '日期待核'}")
    (args.out / "topic-candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "leads": len(result["entries"]),
                      "failed_sources": sum(h["status"] == "failed" for h in health)}, ensure_ascii=False))
    return 0 if result["entries"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
