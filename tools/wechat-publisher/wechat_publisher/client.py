from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import requests

from .config import WeChatConfig, assert_credentials
from .http_safe import request


BASE_URL = "https://api.weixin.qq.com"


class WeChatApiError(RuntimeError):
    pass


@dataclass
class WeChatClient:
    config: WeChatConfig
    timeout: int = 30

    def get_access_token(self) -> str:
        assert_credentials(self.config)
        if self.config.access_token:
            return self.config.access_token
        response = request('GET',
            f"{BASE_URL}/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": self.config.app_id,
                "secret": self.config.app_secret,
            },
            timeout=self.timeout,
        )
        data = self._parse_response(response)
        token = data.get("access_token")
        if not token:
            raise WeChatApiError('WeChat token response is missing access_token')
        return str(token)

    def upload_news_image(self, image_path: str | Path, access_token: str) -> str:
        path = Path(image_path)
        with path.open("rb") as file_obj:
            response = request('POST',
                f"{BASE_URL}/cgi-bin/media/uploadimg",
                params={"access_token": access_token},
                files={"media": (path.name, file_obj)},
                timeout=self.timeout,
            )
        data = self._parse_response(response)
        url = data.get("url")
        if not url:
            raise WeChatApiError('WeChat image response is missing a URL')
        return str(url)

    def upload_thumb_material(self, image_path: str | Path, access_token: str) -> str:
        return self.upload_permanent_material(image_path, access_token, "thumb")

    def upload_permanent_material(
        self,
        image_path: str | Path,
        access_token: str,
        material_type: str = "image",
    ) -> str:
        path = Path(image_path)
        with path.open("rb") as file_obj:
            response = request('POST',
                f"{BASE_URL}/cgi-bin/material/add_material",
                params={"access_token": access_token, "type": material_type},
                files={"media": (path.name, file_obj)},
                timeout=self.timeout,
            )
        data = self._parse_response(response)
        media_id = data.get("media_id")
        if not media_id:
            raise WeChatApiError('WeChat material response is missing media_id')
        return str(media_id)

    def add_draft(self, payload: dict[str, Any], access_token: str) -> dict[str, Any]:
        response = request('POST',
            f"{BASE_URL}/cgi-bin/draft/add",
            params={"access_token": access_token},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=self.timeout,
        )
        return self._parse_response(response)

    def update_draft(
        self, media_id: str, article: dict[str, Any], access_token: str
    ) -> dict[str, Any]:
        response = request('POST',
            f"{BASE_URL}/cgi-bin/draft/update",
            params={"access_token": access_token},
            data=json.dumps(
                {"media_id": media_id, "index": 0, "articles": article},
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=self.timeout,
        )
        return self._parse_response(response)

    def post_json(self, endpoint: str, body: dict[str, Any], access_token: str) -> dict[str, Any]:
        if endpoint not in {'draft/get', 'draft/batchget'}:
            raise ValueError('Read-back transport only supports draft/get and draft/batchget')
        response = request('POST', f'{BASE_URL}/cgi-bin/{endpoint}',
            params={'access_token': access_token},
            data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=self.timeout)
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: requests.Response) -> dict[str, Any]:
        if not response.encoding or response.encoding.lower() in {"iso-8859-1", "latin-1"}:
            response.encoding = "utf-8"
        try:
            data = response.json()
        except ValueError:
            raise WeChatApiError('WeChat API returned non-JSON data; response details withheld') from None
        if not isinstance(data, dict):
            raise WeChatApiError('WeChat API returned an unexpected response shape')
        errcode = data.get("errcode")
        if errcode is not None and (not isinstance(errcode, int) or isinstance(errcode, bool)):
            raise WeChatApiError('WeChat API returned an invalid error code; response details withheld')
        if errcode not in (None, 0):
            if errcode == 40164:
                # Only the refused IP is useful for whitelist recovery; do not echo the service message.
                import re
                ips = re.findall(r'(?<![0-9])(?:[0-9]{1,3}[.]){3}[0-9]{1,3}(?![0-9])', str(data.get('errmsg', '')))
                raise WeChatApiError('WeChat API error 40164: invalid ip ' + ', '.join(ips))
            raise WeChatApiError(f'WeChat API error {errcode}; response details withheld')
        return data
