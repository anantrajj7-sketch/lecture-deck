"""
Lecture deck sync server.

Holds one number — the current slide — and pushes it to every connected
screen over SSE. Also watches slides.md and reloads the deck when it
changes, so slides can be edited mid-lecture.

Run locally:   uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
SLIDES = ROOT / "slides.md"
CONTROL_TOKEN = os.environ.get("CONTROL_TOKEN", "dev-token")
HEARTBEAT_SECONDS = 15
WATCH_INTERVAL = 0.5


# ---------------------------------------------------------------- deck parsing

def parse_deck(text: str) -> list[dict]:
    """Split markdown into slides on `---`, pulling out `Note:` blocks.

    A slide's notes are every line after a line starting with `Note:`.
    """
    slides = []
    chunks = re.split(r"^---\s*$", text, flags=re.MULTILINE)
    for chunk in chunks:
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        body_lines, note_lines, in_note = [], [], False
        for line in chunk.split("\n"):
            if not in_note and line.strip().lower().startswith("note:"):
                in_note = True
                remainder = line.split(":", 1)[1].strip()
                if remainder:
                    note_lines.append(remainder)
                continue
            (note_lines if in_note else body_lines).append(line)
        body = "\n".join(body_lines).strip()
        # First heading doubles as the slide's short title for the phone.
        heading = ""
        for line in body_lines:
            if line.strip().startswith("#"):
                heading = line.lstrip("#").strip()
                break
        slides.append({
            "markdown": body,
            "title": heading or (body.split("\n")[0][:60] if body else "Untitled"),
            "notes": "\n".join(note_lines).strip(),
        })
    return slides or [{"markdown": "# Empty deck", "title": "Empty deck", "notes": ""}]


def load_deck() -> list[dict]:
    try:
        return parse_deck(SLIDES.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return parse_deck("# slides.md is missing\nCreate it next to app.py.")


# ---------------------------------------------------------------------- state

class Deck:
    def __init__(self) -> None:
        self.slides = load_deck()
        self.index = 0
        self.revision = 0
        self.started_at = time.time()
        self.mtime = SLIDES.stat().st_mtime if SLIDES.exists() else 0.0
        self.subscribers: set[asyncio.Queue] = set()

    # -- broadcast ---------------------------------------------------------
    def publish(self, event: str, data: dict) -> None:
        payload = (event, data)
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                self.subscribers.discard(queue)

    def snapshot(self) -> dict:
        return {
            "index": self.index,
            "count": len(self.slides),
            "revision": self.revision,
            "elapsed": int(time.time() - self.started_at),
            "slides": self.slides,
        }

    # -- mutations ---------------------------------------------------------
    def goto(self, index: int) -> dict:
        self.index = max(0, min(index, len(self.slides) - 1))
        self.publish("slide", {"index": self.index})
        return {"index": self.index, "count": len(self.slides)}

    def reload(self) -> None:
        self.slides = load_deck()
        self.revision += 1
        self.index = min(self.index, len(self.slides) - 1)
        self.publish("deck", {
            "slides": self.slides,
            "index": self.index,
            "revision": self.revision,
        })

    def reset_timer(self) -> None:
        self.started_at = time.time()
        self.publish("timer", {"elapsed": 0})


deck = Deck()


async def watch_slides() -> None:
    """Reload the deck whenever slides.md changes on disk."""
    while True:
        await asyncio.sleep(WATCH_INTERVAL)
        try:
            mtime = SLIDES.stat().st_mtime
        except FileNotFoundError:
            continue
        if mtime != deck.mtime:
            deck.mtime = mtime
            deck.reload()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if CONTROL_TOKEN == "dev-token":
        print(
            "\n  !!  CONTROL_TOKEN is unset, so anyone who finds this URL can\n"
            "      drive your slides. Set it before you present publicly.\n"
        )
    task = asyncio.create_task(watch_slides())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


# ------------------------------------------------------------------- helpers

def require_token(token: str | None) -> None:
    if token != CONTROL_TOKEN:
        raise HTTPException(status_code=401, detail="Bad or missing control token.")


# --------------------------------------------------------------------- pages

@app.get("/")
async def audience() -> FileResponse:
    return FileResponse(ROOT / "static" / "audience.html")


@app.get("/present")
async def presenter() -> FileResponse:
    return FileResponse(ROOT / "static" / "presenter.html")


# ----------------------------------------------------------------------- api

@app.get("/api/state")
async def get_state() -> JSONResponse:
    return JSONResponse(deck.snapshot())


@app.post("/api/state")
async def set_state(request: Request, x_control_token: str | None = Header(default=None)):
    require_token(x_control_token)
    body = await request.json()

    if body.get("action") == "reset_timer":
        deck.reset_timer()
        return {"ok": True, "elapsed": 0}

    if "delta" in body:
        target = deck.index + int(body["delta"])
    elif "index" in body:
        target = int(body["index"])
    elif "slide" in body:  # 1-based convenience for humans and CLIs
        target = int(body["slide"]) - 1
    else:
        raise HTTPException(400, "Send one of: index, slide, delta, or action.")

    return {"ok": True, **deck.goto(target)}


@app.post("/api/reload")
async def force_reload(x_control_token: str | None = Header(default=None)):
    require_token(x_control_token)
    deck.reload()
    return {"ok": True, "count": len(deck.slides), "revision": deck.revision}


@app.get("/api/events")
async def events(request: Request) -> StreamingResponse:
    queue: asyncio.Queue = asyncio.Queue(maxsize=32)
    deck.subscribers.add(queue)

    async def stream():
        # Bring every new listener fully up to date before streaming deltas.
        yield sse("init", deck.snapshot())
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event, data = await asyncio.wait_for(
                        queue.get(), timeout=HEARTBEAT_SECONDS
                    )
                    yield sse(event, data)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            deck.subscribers.discard(queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
