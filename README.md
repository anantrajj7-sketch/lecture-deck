# Lecture deck

Slides on the projector, controls on your phone, and a terminal that can edit
the deck while you are still talking.

- `/` — the audience view. Open this on the projector. Read-only.
- `/present?t=TOKEN` — the presenter view. Open this on your phone.
- `deck.py` — the command line, for you or for Claude Code.

Everything is driven by one number held on the server: the current slide index.
Changes reach every connected screen over Server-Sent Events in well under a
second.

## Try it locally

```bash
pip install -r requirements.txt
CONTROL_TOKEN=dev-token uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000` in one window and
`http://localhost:8000/present?t=dev-token` in another. Tapping **Next slide**
on the second moves the first.

## Deploy it

**Render** — push this folder to a GitHub repo, then New → Blueprint and point
it at the repo. `render.yaml` sets everything up and generates a random
`CONTROL_TOKEN` for you. Copy that value out of the dashboard under
Environment; it is the only thing standing between a stranger and your slides.

**Fly.io** — `fly launch` picks up the `Dockerfile`. Then:

```bash
fly secrets set CONTROL_TOKEN=$(openssl rand -hex 16)
```

Either way you end up with a URL. The projector gets the bare URL. Your phone
gets `/present?t=THE_TOKEN` once — after that it is remembered on the device, so
bookmark it or add it to your home screen.

## Writing slides

`slides.md`. Slides split on a line containing exactly three dashes:

```markdown
## A heading

- a point
- another point

Note: What you actually say out loud. Only ever shown on your phone.

---

## The next slide
```

Save the file and every screen updates within half a second, keeping your place.
No restart, no refresh.

## Driving it from a terminal

```bash
cp .env.example .env     # fill in DECK_URL and CONTROL_TOKEN
./deck.py status
./deck.py next
./deck.py goto 12
./deck.py list
```

`CLAUDE.md` tells Claude Code how to use these and — more importantly — the
rules for editing a deck that two hundred people are currently looking at.

## Before you walk in

- **Wake the server.** Free tiers sleep. Load the URL a few minutes early so
  your first slide is instant.
- **Check the tally strip** down the left edge of your phone. Amber means
  connected. Red and pulsing means the stream dropped and your remote is dead.
- **Use cellular on your phone if the venue wifi is strange.** Because the
  server is on the internet rather than your laptop, the two devices never need
  to see each other — which is the entire reason this survives campus networks
  that block device-to-device traffic.
- The projector view ignores its own keyboard and touch input on purpose, so a
  stray keypress on the lectern laptop cannot desync the room.

## Notes

Fonts, reveal.js and the markdown parser are all served from `static/vendor/`
rather than a CDN — about 360 KB — so the deck renders identically whether or
not the venue's network is cooperating.
