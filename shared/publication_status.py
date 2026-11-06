"""Deterministic publication state storage for Chuan Lab articles."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from workspace_guard import assert_article_root, assert_within

STATES = [
    "idea",
    "researched",
    "drafted",
    "qa-passed",
    "user-approved",
    "uploaded",
    "verified",
    "published",
]


class StatusTransitionError(ValueError):
    """Raised for invalid publication-state transitions."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status_path(article_root: Path, *, root: Path | None = None) -> Path:
    article = assert_article_root(article_root, root)
    return assert_within(article / "publication-status.yaml", article)


def initial_status(article_root: Path, *, root: Path | None = None) -> dict:
    article_root = assert_article_root(article_root, root)
    now = _now()
    return {
        "version": 1,
        "article": article_root.name,
        "state": "idea",
        "updated_at": now,
        "approval": None,
        "wechat": {},
        "history": [
            {
                "from": None,
                "to": "idea",
                "at": now,
                "actor": "workspace",
                "reason": "Article workspace created",
            }
        ],
    }


def save_status(
    article_root: Path,
    data: dict,
    *,
    root: Path | None = None,
) -> Path:
    path = status_path(article_root, root=root)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_status(
    article_root: Path,
    create: bool = False,
    *,
    root: Path | None = None,
) -> dict:
    path = status_path(article_root, root=root)
    if not path.exists():
        if not create:
            raise FileNotFoundError(f"Missing publication status: {path}")
        data = initial_status(article_root, root=root)
        save_status(article_root, data, root=root)
        return data
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("state") not in STATES:
        raise StatusTransitionError(f"Unknown publication state: {data.get('state')}")
    return data


def transition(
    article_root: Path,
    target: str,
    *,
    actor: str,
    reason: str,
    rollback: bool = False,
    metadata: dict | None = None,
    root: Path | None = None,
) -> dict:
    if target not in STATES:
        raise StatusTransitionError(f"Unknown target state: {target}")
    if not actor.strip() or not reason.strip():
        raise StatusTransitionError("Transitions require non-empty actor and reason.")
    data = load_status(article_root, create=True, root=root)
    current = data["state"]
    current_index = STATES.index(current)
    target_index = STATES.index(target)
    if rollback:
        if target_index >= current_index:
            raise StatusTransitionError("Rollback target must precede the current state.")
    elif target_index != current_index + 1:
        expected = STATES[current_index + 1] if current_index + 1 < len(STATES) else "none"
        raise StatusTransitionError(
            f"Forward transition must be {current} -> {expected}."
        )
    now = _now()
    event = {
        "from": current,
        "to": target,
        "at": now,
        "actor": actor.strip(),
        "reason": reason.strip(),
    }
    if metadata:
        event["metadata"] = metadata
    data["state"] = target
    data["updated_at"] = now
    data.setdefault("history", []).append(event)
    if target == "user-approved":
        data["approval"] = {
            "approved_by": actor.strip(),
            "approved_at": now,
            "reason": reason.strip(),
        }
        if metadata:
            data["approval"]["metadata"] = metadata
    if rollback and target_index < STATES.index("user-approved"):
        data["approval"] = None
    save_status(article_root, data, root=root)
    return data


def is_user_approved(data: dict) -> bool:
    return (
        data.get("state") in STATES[STATES.index("user-approved") :]
        and bool(data.get("approval"))
    )
