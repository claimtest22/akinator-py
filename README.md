# akinator

Typed Python client for [Akinator](https://akinator.com)'s **public web game API**.

Drives the same HTML/XHR flow the site uses (`/game`, `/answer`, `/cancel_answer`, `/exclude`, `/choice`) with browser TLS impersonation via [`curl_cffi`](https://github.com/lexiforest/curl_cffi) so Cloudflare challenges are handled in the common case.

Not tied to Discord or any other platform.

## Install

```bash
pip install -e .
# optional pretty logging
pip install loguru
```

## Quick start

```python
from akinator import Akinator, Answer

with Akinator() as aki:
    print(aki.start())
    while not aki.won and not aki.ko:
        print(aki.question, f"({aki.progression:.1f}%)")
        # replace with real user input
        result = aki.answer(Answer.yes)
        if aki.won:
            print("Guess:", aki.guess)
            aki.confirm()
```

Answers accept enums, ints `0`–`4`, or aliases: `yes` / `y`, `no` / `n`, `idk` / `i`, `probably` / `p`, `pn`.

## Options

```python
from akinator import Akinator, Language, Theme, setup_logging

setup_logging(level="DEBUG")  # optional; loguru if installed else stdlib

aki = Akinator(
    language=Language.english,   # or "en"
    theme=Theme.characters,      # objects=2, animals=14
    child_mode=False,
    impersonate="safari17_0",    # curl_cffi profile
    proxy=None,                  # "http://user:pass@host:port"
)
```

## API surface

| Member | Purpose |
|--------|---------|
| `start()` | Begin game → first question `str` |
| `answer(value)` | Submit answer → next `str` or `Guess` |
| `back()` | Undo last answer |
| `decline()` | Reject guess (`/exclude`) |
| `confirm()` | Accept guess (`/choice`) |
| `question` / `progression` / `step` / `guess` / `won` | State |
| `state()` | `GameState` snapshot |

Exceptions live in `akinator.errors` (`CloudflareException`, `ServerKO`, `AntiBotBlocked`, …).

## Notes

- `/exclude` (wrong guess → continue) is the most aggressively protected endpoint; if it raises `AntiBotBlocked`, call `start()` again.
- Prefer `safari17_0` impersonation from many datacenter IPs; override with `impersonate=` if needed.
- Logging is silent by default. Use `setup_logging()` or configure `logging.getLogger("akinator")` / loguru yourself.

## License

MIT
