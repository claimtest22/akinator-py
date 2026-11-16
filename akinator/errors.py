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

from typing import Any, Optional


class AkinatorException(Exception):
    """Base exception for all library errors."""


class HTTPException(AkinatorException):
    """Raised when an HTTP request fails at the transport layer.

    Attributes
    ----------
    status: Optional[int]
        HTTP status code if available.
    response: Any
        Raw response object when present.
    """

    def __init__(self, message: str, *, status: Optional[int] = None, response: Any = None) -> None:
        self.status: Optional[int] = status
        self.response: Any = response
        super().__init__(message)


class CloudflareException(HTTPException):
    """Raised when Cloudflare challenges the client instead of serving the game."""


class InvalidResponse(AkinatorException):
    """Raised when the server returns HTML/JSON that cannot be parsed as a game state."""


class SessionClosed(AkinatorException):
    """Raised when an action is attempted after :meth:`Akinator.close`."""


class GameNotStarted(AkinatorException):
    """Raised when an action requires an active game that was never started."""


class InvalidAnswer(AkinatorException):
    """Raised when an answer value is outside the accepted ``0``–``4`` range."""


class CannotGoBack(AkinatorException):
    """Raised when :meth:`Akinator.back` is called on the first question."""


class ServerKO(AkinatorException):
    """Raised when Akinator returns ``completion == "KO"`` (expired/invalid session)."""


class AntiBotBlocked(AkinatorException):
    """Raised when ``/exclude`` (or similar) is blocked by anti-bot HTML instead of JSON."""
