"""
The MIT License (MIT)

Copyright (c) 2026 frat

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, Optional

from .errors import AntiBotBlocked, CloudflareException, HTTPException, InvalidResponse
from .utils import log, looks_like_cloudflare

try:
    from curl_cffi import requests as _curl_requests

    _HAS_CURL_CFFI = True
except ImportError:  # pragma: no cover
    _HAS_CURL_CFFI = False
    _curl_requests = None  # type: ignore


DEFAULT_IMPERSONATE = "safari17_0"
DEFAULT_TIMEOUT = 30.0


class HTTPClient:
    """Low-level HTTP transport for the Akinator web endpoints.

    Prefers :mod:`curl_cffi` with browser TLS impersonation so Cloudflare
    challenges are avoided in the common case. Falls back to a clear error
    if ``curl_cffi`` is not installed.

    Parameters
    ----------
    base_url: str
        Origin such as ``https://en.akinator.com``.
    impersonate: str
        ``curl_cffi`` impersonation profile. Defaults to ``safari17_0``,
        which currently clears Akinator's edge challenge more reliably
        than several Chrome profiles from datacenter IPs.
    timeout: float
        Request timeout in seconds.
    proxy: Optional[str]
        Optional HTTP(S) proxy URL.
    """

    __slots__ = (
        "base_url",
        "impersonate",
        "timeout",
        "proxy",
        "_session",
        "_closed",
    )

    def __init__(
        self,
        base_url: str,
        *,
        impersonate: str = DEFAULT_IMPERSONATE,
        timeout: float = DEFAULT_TIMEOUT,
        proxy: Optional[str] = None,
    ) -> None:
        if not _HAS_CURL_CFFI:
            raise RuntimeError(
                "curl_cffi is required for Akinator HTTP. "
                "Install it with: pip install curl_cffi"
            )

        self.base_url = base_url.rstrip("/")
        self.impersonate = impersonate
        self.timeout = timeout
        self.proxy = proxy
        self._session = _curl_requests.Session(impersonate=impersonate)
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._session.close()
        finally:
            self._closed = True

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        data: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        allow_html: bool = False,
    ) -> tuple[int, str, MutableMapping[str, str]]:
        """Perform an HTTP request and return ``(status, text, headers)``."""

        if self._closed:
            raise HTTPException("HTTP client is closed")

        url = self._url(path)
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "allow_redirects": True,
        }
        if self.proxy:
            kwargs["proxy"] = self.proxy
        if headers:
            kwargs["headers"] = dict(headers)
        if data is not None:
            kwargs["data"] = dict(data)

        log.debug("%s %s data=%s", method.upper(), url, data)
        try:
            response = self._session.request(method.upper(), url, **kwargs)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(f"request failed: {exc}") from exc

        text = response.text or ""
        status = int(response.status_code)
        hdrs = {k.lower(): v for k, v in dict(response.headers).items()}

        if looks_like_cloudflare(text, status=status):
            raise CloudflareException(
                "Cloudflare challenge received; try another impersonate profile or proxy",
                status=status,
                response=response,
            )

        if not allow_html and status >= 400:
            raise HTTPException(f"HTTP {status} for {path}", status=status, response=response)

        return status, text, hdrs

    def get_text(self, path: str = "/", *, allow_html: bool = True) -> str:
        _, text, _ = self.request("GET", path, allow_html=allow_html)
        return text

    def post_form(self, path: str, data: Mapping[str, Any], *, allow_html: bool = False) -> str:
        _, text, _ = self.request("POST", path, data=data, allow_html=allow_html)
        return text

    def post_json(self, path: str, data: Mapping[str, Any]) -> dict[str, Any]:
        status, text, _ = self.request("POST", path, data=data, allow_html=True)
        if not text:
            raise InvalidResponse(f"empty body from {path}")
        stripped = text.lstrip()
        if stripped.startswith("<") or "Vital API blocked" in text:
            raise AntiBotBlocked(
                f"endpoint {path!r} returned anti-bot HTML instead of JSON "
                f"(status={status}). A browser-like proxy may be required for /exclude."
            )
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidResponse(f"invalid JSON from {path}: {text[:180]!r}") from exc
        if not isinstance(payload, dict):
            raise InvalidResponse(f"expected JSON object from {path}")
        return payload
