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

from typing import Any, List, Mapping, Optional, Union

from bs4 import BeautifulSoup

from .enums import ANSWER_LABELS, Answer, Language, Theme
from .errors import (
    CannotGoBack,
    GameNotStarted,
    InvalidResponse,
    ServerKO,
    SessionClosed,
)
from .http import DEFAULT_IMPERSONATE, DEFAULT_TIMEOUT, HTTPClient
from .models import GameState, Guess, Question
from .utils import (
    coerce_answer,
    coerce_language,
    coerce_theme,
    log,
    parse_identifiant,
    parse_session_token,
    warn_once,
)


class Akinator:
    """High-level client for Akinator's public web game API.

    This client drives the same HTML/XHR flow the website uses
    (``POST /game``, ``POST /answer``, ``POST /cancel_answer``,
    ``POST /exclude``, ``POST /choice``). It is intentionally
    framework-agnostic.

    Parameters
    ----------
    language: Union[Language, str]
        Locale subdomain, e.g. ``Language.english`` or ``"en"``.
    theme: Union[Theme, int, str]
        Game theme. Defaults to :attr:`Theme.characters`.
    child_mode: bool
        When ``True``, enables Akinator's child-safe mode.
    impersonate: str
        TLS fingerprint profile forwarded to :mod:`curl_cffi`.
    timeout: float
        Per-request timeout in seconds.
    proxy: Optional[str]
        Optional HTTP(S) proxy URL.
    """

    __slots__ = (
        "language",
        "theme",
        "child_mode",
        "_http",
        "_session_token",
        "_identifiant",
        "_step",
        "_progression",
        "_question",
        "_guess",
        "_finished",
        "_ko",
        "_started",
        "_history",
        "_closed",
    )

    def __init__(
        self,
        language: Union[Language, str] = Language.english,
        *,
        theme: Union[Theme, int, str] = Theme.characters,
        child_mode: bool = False,
        impersonate: str = DEFAULT_IMPERSONATE,
        timeout: float = DEFAULT_TIMEOUT,
        proxy: Optional[str] = None,
    ) -> None:
        self.language: Language = coerce_language(language)
        self.theme: Theme = coerce_theme(theme)
        self.child_mode: bool = bool(child_mode)

        base = f"https://{self.language.value}.akinator.com"
        self._http = HTTPClient(
            base,
            impersonate=impersonate,
            timeout=timeout,
            proxy=proxy,
        )

        self._session_token: Optional[str] = None
        self._identifiant: Optional[str] = None
        self._step: int = 0
        self._progression: float = 0.0
        self._question: Optional[str] = None
        self._guess: Optional[Guess] = None
        self._finished: bool = False
        self._ko: bool = False
        self._started: bool = False
        self._history: List[GameState] = []
        self._closed: bool = False

    def close(self) -> None:
        """Close the underlying HTTP session."""

        self._http.close()
        self._closed = True

    def __enter__(self) -> Akinator:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def __del__(self) -> None:  # pragma: no cover
        try:
            self.close()
        except Exception:
            pass

    def _ensure_open(self) -> None:
        if self._closed:
            raise SessionClosed("This Akinator client has been closed")

    def _ensure_started(self) -> None:
        self._ensure_open()
        if not self._started or not self._session_token:
            raise GameNotStarted("Call start() before interacting with the game")

    @property
    def started(self) -> bool:
        return self._started

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def ko(self) -> bool:
        return self._ko

    @property
    def won(self) -> bool:
        return self._guess is not None and not self._finished

    @property
    def question(self) -> Optional[str]:
        return self._question

    @property
    def progression(self) -> float:
        return self._progression

    @property
    def step(self) -> int:
        return self._step

    @property
    def guess(self) -> Optional[Guess]:
        return self._guess

    @property
    def session(self) -> Optional[str]:
        return self._session_token

    @property
    def answers(self) -> List[str]:
        """Human-readable labels for the five possible answers."""

        return [ANSWER_LABELS[a] for a in Answer]

    def state(self) -> GameState:
        """Return a :class:`GameState` snapshot of the current session."""

        self._ensure_started()
        q: Optional[Question] = None
        if self._question is not None:
            q = Question(
                text=self._question,
                step=self._step,
                progression=self._progression,
            )
        return GameState(
            session=self._session_token or "",
            step=self._step,
            progression=self._progression,
            question=q,
            guess=self._guess,
            finished=self._finished,
            ko=self._ko,
        )

    def start(self) -> str:
        """Start a new game and return the first question."""

        self._ensure_open()
        log.info(
            "Starting game lang=%s theme=%s child_mode=%s",
            self.language.value,
            self.theme.name,
            self.child_mode,
        )

        self._http.get_text("/")

        html = self._http.post_form(
            "/game",
            {
                "sid": str(self.theme.value),
                "cm": "true" if self.child_mode else "false",
            },
            allow_html=True,
        )

        token = parse_session_token(html)
        if not token:
            raise InvalidResponse("could not locate session token in /game response")

        soup = BeautifulSoup(html, "html.parser")
        label = soup.select_one("#question-label")
        question = label.get_text(strip=True) if label else None
        if not question:
            for sel in (".question-text", "#question", "h2"):
                node = soup.select_one(sel)
                if node and node.get_text(strip=True):
                    question = node.get_text(strip=True)
                    break
        if not question:
            raise InvalidResponse("could not locate first question in /game response")

        self._session_token = token
        self._identifiant = parse_identifiant(html)
        self._step = 1
        self._progression = 0.0
        self._question = question
        self._guess = None
        self._finished = False
        self._ko = False
        self._started = True
        self._history.clear()
        self._push_history()

        log.debug("First question: %s", question)
        return question

    def answer(self, value: Union[Answer, int, str]) -> Union[str, Guess]:
        """Submit an answer to the current question."""

        self._ensure_started()
        if self._guess is not None:
            warn_once(
                "answer() called while a guess is pending; "
                "use confirm() / decline() instead",
            )

        ans = coerce_answer(value)
        payload = self._base_payload()
        payload["answer"] = str(int(ans))

        data = self._http.post_json("/answer", payload)
        return self._apply_payload(data)

    def back(self) -> str:
        """Undo the previous answer and return the restored question."""

        self._ensure_started()
        if self._step <= 1 and len(self._history) <= 1:
            raise CannotGoBack("already at the first question")

        payload = self._base_payload()
        data = self._http.post_json("/cancel_answer", payload)
        result = self._apply_payload(data)
        if isinstance(result, Guess):
            return result.name
        return result

    def decline(self) -> Union[str, Guess]:
        """Reject the current guess and continue the game (``POST /exclude``)."""

        self._ensure_started()
        if self._guess is None:
            raise GameNotStarted("no active guess to decline")

        payload = {
            "step": str(self._step),
            "sid": str(self.theme.value),
            "cm": "true" if self.child_mode else "false",
            "progression": self._fmt_progression(self._progression),
            "session": self._session_token,
            "forward_answer": "1",
        }
        data = self._http.post_json("/exclude", payload)
        self._guess = None
        return self._apply_payload(data)

    def confirm(self) -> None:
        """Confirm that the current guess is correct (``POST /choice``)."""

        self._ensure_started()
        if self._guess is None:
            raise GameNotStarted("no active guess to confirm")

        form = {
            "sid": str(self.theme.value),
            "pid": str(self._guess.id),
            "session": self._session_token or "",
            "cm": "true" if self.child_mode else "false",
        }
        if self._identifiant:
            form["identifiant"] = self._identifiant
        try:
            self._http.post_form("/choice", form, allow_html=True)
        except Exception as exc:  # noqa: BLE001
            log.warning("confirm() HTTP call failed: %s", exc)
            warn_once(f"confirm() could not complete /choice: {exc}")

        self._finished = True
        self._question = None
        log.info("Guess confirmed: %s", self._guess)

    def _base_payload(self) -> dict[str, Any]:
        return {
            "step": str(self._step),
            "progression": self._fmt_progression(self._progression),
            "sid": str(self.theme.value),
            "cm": "true" if self.child_mode else "false",
            "session": self._session_token,
        }

    @staticmethod
    def _fmt_progression(value: float) -> str:
        return f"{float(value):.10g}"

    def _push_history(self) -> None:
        try:
            self._history.append(self.state())
        except GameNotStarted:
            return
        if len(self._history) > 64:
            self._history = self._history[-64:]

    def _apply_payload(self, data: Mapping[str, Any]) -> Union[str, Guess]:
        completion = str(data.get("completion", "OK")).upper()
        if completion == "KO":
            self._ko = True
            self._started = False
            raise ServerKO("Akinator returned completion=KO (session invalid or expired)")

        if "step" in data and data["step"] is not None:
            try:
                self._step = int(data["step"])
            except (TypeError, ValueError):
                pass
        if "progression" in data and data["progression"] is not None:
            try:
                self._progression = float(data["progression"])
            except (TypeError, ValueError):
                pass
        if data.get("session"):
            self._session_token = str(data["session"])

        if data.get("name_proposition") or data.get("id_proposition"):
            guess = Guess(
                id=int(data.get("id_proposition") or 0),
                base_id=int(data["id_base_proposition"])
                if data.get("id_base_proposition") is not None
                else None,
                name=str(data.get("name_proposition") or "Unknown"),
                description=(
                    str(data["description_proposition"])
                    if data.get("description_proposition")
                    else None
                ),
                photo=str(data["photo"]) if data.get("photo") else None,
                author=str(data["pseudo"]) if data.get("pseudo") else None,
                step=self._step,
                raw=dict(data),
            )
            self._guess = guess
            self._question = None
            self._push_history()
            log.info("Guess: %s", guess)
            return guess

        question = data.get("question")
        if not question:
            raise InvalidResponse(f"payload missing question/guess: {dict(data)!r}")

        self._question = str(question)
        self._guess = None
        self._push_history()
        log.debug("Question step=%s prog=%.2f: %s", self._step, self._progression, self._question)
        return self._question

    def __repr__(self) -> str:
        return (
            f"<Akinator lang={self.language.value!r} theme={self.theme.name!r} "
            f"started={self._started} step={self._step} progression={self._progression:.1f}>"
        )

    def __str__(self) -> str:
        if self._guess is not None:
            return str(self._guess)
        return self._question or ""
