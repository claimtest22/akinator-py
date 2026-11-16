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

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


@dataclass(slots=True)
class Question:
    """A question posed by Akinator.

    Attributes
    ----------
    text: str
        Question text shown to the player.
    step: int
        Opaque server step counter.
    progression: float
        Confidence / progress in the range roughly ``0``–``100``.
    question_id: Optional[str]
        Server-side question identifier when provided.
    akitude: Optional[str]
        Expression asset name or URL fragment when provided.
    """

    text: str
    step: int
    progression: float
    question_id: Optional[str] = None
    akitude: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __str__(self) -> str:
        return self.text


@dataclass(slots=True)
class Guess:
    """A character / object / animal proposition from Akinator.

    Attributes
    ----------
    id: int
        Proposition id (``id_proposition``).
    base_id: Optional[int]
        Base proposition id when present.
    name: str
        Display name of the guess.
    description: Optional[str]
        Short description or franchise line.
    photo: Optional[str]
        Absolute URL to a portrait image.
    author: Optional[str]
        Contributor / pseudo field from the API.
    step: int
        Server step carried by the win payload (needed for ``/exclude``).
    """

    id: int
    name: str
    step: int
    base_id: Optional[int] = None
    description: Optional[str] = None
    photo: Optional[str] = None
    author: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __str__(self) -> str:
        if self.description:
            return f"{self.name} ({self.description})"
        return self.name


@dataclass(slots=True)
class GameState:
    """Snapshot of a running (or finished) game.

    Attributes
    ----------
    session: str
        Server session token.
    step: int
        Current step.
    progression: float
        Current progression.
    question: Optional[Question]
        Active question, or ``None`` when a guess is pending.
    guess: Optional[Guess]
        Active guess, or ``None`` while questioning.
    finished: bool
        Whether the player confirmed a win or the session was closed.
    ko: bool
        Whether Akinator returned a KO / gave up style completion.
    """

    session: str
    step: int
    progression: float
    question: Optional[Question] = None
    guess: Optional[Guess] = None
    finished: bool = False
    ko: bool = False

    @property
    def won(self) -> bool:
        """``True`` when a guess is currently on the table."""

        return self.guess is not None and not self.finished
