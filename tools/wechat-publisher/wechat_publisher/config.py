from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'shared'))
from settings import load_settings


@dataclass(frozen=True)
class WeChatConfig:
    app_id: str
    app_secret: str
    access_token: str | None = None
    default_author: str = ''
    default_need_open_comment: int = 0
    default_only_fans_can_comment: int = 0


def load_config(env_file: str | Path | None = None) -> WeChatConfig:
    # No dotenv ancestor search and no inherited account from another project.
    path = Path(env_file).expanduser() if env_file else REPOSITORY / '.env'
    if env_file and not path.is_file():
        raise ValueError('The explicitly selected credential file does not exist')
    values = dotenv_values(path, interpolate=False) if path.is_file() else {}
    def value(name: str, default: str = '') -> str:
        return str(values.get(name) or default).strip()
    return WeChatConfig(
        app_id=value('WECHAT_APP_ID'), app_secret=value('WECHAT_APP_SECRET'),
        access_token=value('WECHAT_ACCESS_TOKEN') or None,
        default_author=load_settings().author,
        default_need_open_comment=int(value('WECHAT_DEFAULT_NEED_OPEN_COMMENT', '0')),
        default_only_fans_can_comment=int(value('WECHAT_DEFAULT_ONLY_FANS_CAN_COMMENT', '0')),
    )


def assert_credentials(config: WeChatConfig) -> None:
    missing = []
    if not config.app_id:
        missing.append("WECHAT_APP_ID")
    if not config.app_secret and not config.access_token:
        missing.append('WECHAT_APP_SECRET or WECHAT_ACCESS_TOKEN')
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing WeChat credentials: {joined}")


def account_fingerprint(config: WeChatConfig) -> str:
    assert_credentials(config)
    return hashlib.sha256(config.app_id.encode('utf-8')).hexdigest()

