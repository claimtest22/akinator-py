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

from enum import Enum


class Theme(Enum):
    """Game theme identifiers used by Akinator's ``sid`` field.

    Attributes
    ----------
    characters: Theme
        Guess a character (``sid=1``).
    objects: Theme
        Guess an object (``sid=2``).
    animals: Theme
        Guess an animal (``sid=14``).
    """

    characters = 1
    objects = 2
    animals = 14

    def __str__(self) -> str:
        return self.name


class Answer(Enum):
    """Canonical answers for a question.

    Values match the integers accepted by ``POST /answer``.

    Attributes
    ----------
    yes: Answer
        Affirmative (``0``).
    no: Answer
        Negative (``1``).
    idk: Answer
        Don't know (``2``).
    probably: Answer
        Probably yes (``3``).
    probably_not: Answer
        Probably no (``4``).
    """

    yes = 0
    no = 1
    idk = 2
    probably = 3
    probably_not = 4

    def __int__(self) -> int:
        return int(self.value)

    def __str__(self) -> str:
        return self.name


class Language(Enum):
    """Language subdomain codes for ``https://{code}.akinator.com``.

    Not every language supports every :class:`Theme`. Characters are
    available on all listed locales.
    """

    english = "en"
    arabic = "ar"
    chinese = "cn"
    german = "de"
    spanish = "es"
    french = "fr"
    hebrew = "il"
    italian = "it"
    japanese = "jp"
    korean = "kr"
    dutch = "nl"
    polish = "pl"
    portuguese = "pt"
    russian = "ru"
    turkish = "tr"
    indonesian = "id"

    def __str__(self) -> str:
        return self.value


ANSWER_LABELS: dict[Answer, str] = {
    Answer.yes: "Yes",
    Answer.no: "No",
    Answer.idk: "Don't know",
    Answer.probably: "Probably",
    Answer.probably_not: "Probably not",
}
