# SPDX-License-Identifier: AGPL-3.0-only
"""Small credential-safe transport for the draft-only WeChat client."""
from __future__ import annotations

import requests


def request(method: str, url: str, **kwargs) -> requests.Response:
    try:
        with requests.Session() as session:
            # Do not borrow netrc authentication or proxy credentials from the
            # maintainer's or another project's environment.
            session.trust_env = False
            response = session.request(method, url, allow_redirects=False, **kwargs)
    except requests.RequestException:
        raise RuntimeError('WeChat connection failed; no request URL or credential is logged') from None
    if 300 <= response.status_code < 400:
        raise RuntimeError('WeChat redirects are refused to protect account credentials')
    if response.status_code >= 400:
        raise RuntimeError(f'WeChat HTTP {response.status_code}; response details withheld')
    return response
