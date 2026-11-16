"""
Akinator web API client.

Typical usage::

    from akinator import Akinator, Answer

    with Akinator() as aki:
        print(aki.start())
        while not aki.won:
            print(aki.answer(Answer.yes))
        print(aki.guess)
"""

from __future__ import annotations

__title__ = "akinator"
__author__ = "frat"
__license__ = "MIT"
__version__ = "1.0.0"

from .client import Akinator
from .enums import ANSWER_LABELS, Answer, Language, Theme
from .errors import (
    AkinatorException,
    AntiBotBlocked,
    CannotGoBack,
    CloudflareException,
    GameNotStarted,
    HTTPException,
    InvalidAnswer,
    InvalidResponse,
    ServerKO,
    SessionClosed,
)
from .models import GameState, Guess, Question
from .utils import setup_logging

__all__ = (
    "ANSWER_LABELS",
    "Akinator",
    "AkinatorException",
    "Answer",
    "AntiBotBlocked",
    "CannotGoBack",
    "CloudflareException",
    "GameNotStarted",
    "GameState",
    "Guess",
    "HTTPException",
    "InvalidAnswer",
    "InvalidResponse",
    "Language",
    "Question",
    "ServerKO",
    "SessionClosed",
    "Theme",
    "setup_logging",
    "__version__",
)
