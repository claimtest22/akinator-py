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

import logging
import re
import warnings
from typing import Any, Optional, TypeVar, Union, overload

from .enums import Answer, Language, Theme
from .errors import InvalidAnswer

try:
    from loguru import logger as _loguru_logger

    _HAS_LOGURU = True
except ImportError:  # pragma: no cover
    _HAS_LOGURU = False
    _loguru_logger = None  # type: ignore

T = TypeVar("T")
MISSING: Any = object()

_SESSION_RE = re.compile(r"localStorage\.setItem\(\s*['\"]session['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
_IDENT_RE = re.compile(r"localStorage\.setItem\(\s*['\"]identifiant['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
_CF_MARKERS = (
    "Just a moment",
    "cf-mitigated",
    "challenge-platform",
    "Verify you are human",
    "Attention Required",
)

_ANSWER_ALIASES: dict[str, Answer] = {
    "y": Answer.yes,
    "yes": Answer.yes,
    "0": Answer.yes,
    "n": Answer.no,
    "no": Answer.no,
    "1": Answer.no,
    "i": Answer.idk,
    "idk": Answer.idk,
    "dont know": Answer.idk,
    "don't know": Answer.idk,
    "2": Answer.idk,
    "p": Answer.probably,
    "probably": Answer.probably,
    "3": Answer.probably,
    "pn": Answer.probably_not,
    "probably not": Answer.probably_not,
    "probably_not": Answer.probably_not,
    "4": Answer.probably_not,
}


def _stdlib_logger() -> logging.Logger:
    return logging.getLogger("akinator")


class _LoggerProxy:
    """Thin facade over loguru (preferred) or stdlib logging."""

    __slots__ = ("_stdlib",)

    def __init__(self) -> None:
        self._stdlib = _stdlib_logger()

    def _loguru(self):
        if not _HAS_LOGURU:
            return None
        return _loguru_logger.opt(depth=1)

    @staticmethod
    def _format(msg: str, args: tuple[Any, ...]) -> str:
        if not args:
            return msg
        try:
            return msg % args
        except Exception:
            return f"{msg} {args}"

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        loguru = self._loguru()
        if loguru is not None:
            loguru.opt(depth=2).debug(self._format(msg, args), **kwargs)
            return
        self._stdlib.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        loguru = self._loguru()
        if loguru is not None:
            loguru.opt(depth=2).info(self._format(msg, args), **kwargs)
            return
        self._stdlib.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        loguru = self._loguru()
        if loguru is not None:
            loguru.opt(depth=2).warning(self._format(msg, args), **kwargs)
            return
        self._stdlib.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        loguru = self._loguru()
        if loguru is not None:
            loguru.opt(depth=2).error(self._format(msg, args), **kwargs)
            return
        self._stdlib.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        loguru = self._loguru()
        if loguru is not None:
            loguru.opt(depth=2).exception(self._format(msg, args), **kwargs)
            return
        self._stdlib.exception(msg, *args, **kwargs)


log = _LoggerProxy()


def setup_logging(*, level: int | str = logging.INFO, colorize: bool = True) -> None:
    """Optional convenience setup for loguru-based library logging."""

    if _HAS_LOGURU:
        import sys

        _loguru_logger.remove()
        _loguru_logger.add(
            sys.stderr,
            level=level if isinstance(level, str) else logging.getLevelName(level),
            colorize=colorize,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>akinator</cyan> | "
                "<level>{message}</level>"
            ),
            filter=lambda r: r["name"] is None or "akinator" in (r["name"] or ""),
        )
        return

    logger = _stdlib_logger()
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(levelname)s] akinator: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)


def parse_session_token(html: str) -> Optional[str]:
    """Extract the game ``session`` token from a ``/game`` HTML page."""

    match = _SESSION_RE.search(html)
    return match.group(1) if match else None


def parse_identifiant(html: str) -> Optional[str]:
    """Extract the optional ``identifiant`` token from a ``/game`` HTML page."""

    match = _IDENT_RE.search(html)
    return match.group(1) if match else None


def looks_like_cloudflare(text: str, *, status: Optional[int] = None) -> bool:
    """Return ``True`` if a response body/status looks like a Cloudflare challenge."""

    if status in {403, 503} and text:
        lowered = text[:4000]
        return any(marker in lowered for marker in _CF_MARKERS)
    if not text:
        return False
    head = text[:2000]
    return "Just a moment" in head or "cf-mitigated" in head


def coerce_language(value: Union[Language, str]) -> Language:
    if isinstance(value, Language):
        return value
    key = str(value).strip().lower()
    for lang in Language:
        if lang.value == key or lang.name == key:
            return lang
    raise ValueError(f"unknown language {value!r}")


def coerce_theme(value: Union[Theme, int, str]) -> Theme:
    if isinstance(value, Theme):
        return value
    if isinstance(value, int):
        for theme in Theme:
            if theme.value == value:
                return theme
        raise ValueError(f"unknown theme id {value!r}")
    key = str(value).strip().lower()
    for theme in Theme:
        if theme.name == key or str(theme.value) == key:
            return theme
    raise ValueError(f"unknown theme {value!r}")


def coerce_answer(value: Union[Answer, int, str]) -> Answer:
    """Normalize user input into an :class:`Answer`."""

    if isinstance(value, Answer):
        return value
    if isinstance(value, int):
        try:
            return Answer(value)
        except ValueError as exc:
            raise InvalidAnswer(f"answer must be 0–4, got {value!r}") from exc
    key = str(value).strip().lower()
    if key in _ANSWER_ALIASES:
        return _ANSWER_ALIASES[key]
    try:
        return Answer(int(key))
    except (ValueError, KeyError) as exc:
        raise InvalidAnswer(f"cannot interpret answer {value!r}") from exc


def warn_once(message: str, *, category: type[Warning] = UserWarning, stacklevel: int = 3) -> None:
    """Emit a library warning without spamming identical messages."""

    warnings.warn(message, category=category, stacklevel=stacklevel)


@overload
def _get(mapping: dict[str, Any], key: str, default: T) -> Union[Any, T]:
    ...


@overload
def _get(mapping: dict[str, Any], key: str) -> Any:
    ...


def _get(mapping: dict[str, Any], key: str, default: Any = None) -> Any:
    return mapping[key] if key in mapping else default
