#!/usr/bin/env python3
"""Drive the lecture deck from a terminal.

    ./deck.py next              advance one slide
    ./deck.py back              go back one
    ./deck.py goto 7            jump to slide 7 (1-based)
    ./deck.py status            where are we?
    ./deck.py list              numbered list of every slide title
    ./deck.py reload            force a re-read of slides.md
    ./deck.py timer             restart the elapsed clock

Reads DECK_URL and CONTROL_TOKEN from the environment, or from a .env
file sitting next to this script.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

URL = os.environ.get("DECK_URL", "http://localhost:8000").rstrip("/")
TOKEN = os.environ.get("CONTROL_TOKEN", "dev-token")


def call(path: str, payload: dict | None = None) -> dict:
    request = urllib.request.Request(
        URL + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json", "X-Control-Token": TOKEN},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        sys.exit(f"{error.code}: {error.read().decode()[:200]}")
    except urllib.error.URLError as error:
        sys.exit(f"Cannot reach {URL} — {error.reason}")


def main() -> None:
    args = sys.argv[1:]
    command = args[0] if args else "status"

    if command in ("next", "n"):
        print("slide", call("/api/state", {"delta": 1})["index"] + 1)
    elif command in ("back", "prev", "b"):
        print("slide", call("/api/state", {"delta": -1})["index"] + 1)
    elif command in ("goto", "g"):
        if len(args) < 2:
            sys.exit("Which slide? e.g. ./deck.py goto 7")
        print("slide", call("/api/state", {"slide": int(args[1])})["index"] + 1)
    elif command == "reload":
        print("reloaded,", call("/api/reload", {})["count"], "slides")
    elif command == "timer":
        call("/api/state", {"action": "reset_timer"})
        print("timer restarted")
    elif command == "list":
        state = call("/api/state")
        for i, slide in enumerate(state["slides"], 1):
            mark = ">" if i - 1 == state["index"] else " "
            print(f"{mark} {i:>2}  {slide['title']}")
    elif command == "status":
        state = call("/api/state")
        print(f"slide {state['index'] + 1}/{state['count']}  ·  {state['elapsed'] // 60}m elapsed")
        print(f"now:  {state['slides'][state['index']]['title']}")
        if state["index"] + 1 < state["count"]:
            print(f"next: {state['slides'][state['index'] + 1]['title']}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
