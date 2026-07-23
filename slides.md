# A deck you can drive from your pocket

Slides on the projector. Controls on your phone.

Note: This is the demo deck. Replace it with your lecture — every slide here is just markdown in slides.md.

---

## The problem with presenting

You are standing at the front of the room.

The laptop is over there. The clicker only goes forward and back.
And you cannot see what is coming next.

Note: Open /present on your phone now. Tap the big arrow. This slide should advance on the projector.

---

## Three views, one number

- **Audience** — the projector. Renders whatever slide the server says.
- **Presenter** — your phone. Big buttons, next slide, notes, timer.
- **Claude Code** — a terminal. Same permissions as your thumb.

Note: The server holds exactly one piece of state: the current slide index. Everything else is a view onto it.

---

## How the sync works

A slide change is one `POST`. Every connected screen hears about it
over a Server-Sent Events stream in under 50ms.

No polling. No refresh. No websocket library.

Note: SSE rather than websockets because the traffic is one-directional and it survives flaky mobile networks better — the browser reconnects on its own.

---

## What your phone shows

The next slide, larger than the current one.

You already know what is on screen behind you. What you need
is thirty seconds of warning.

Note: This is the one real design decision in the whole thing. Every other presenter view gets the hierarchy backwards.

---

## Live editing

Ask Claude Code to add a slide and it appears here.

The server watches `slides.md`. On any change it reparses the deck
and pushes it to every screen — without losing your place.

Note: Try it. Say "add a slide after this one with a worked example" and watch this deck grow mid-sentence.

---

## The gotcha nobody warns you about

University wifi often blocks phone-to-laptop traffic.

Your remote dies in front of two hundred people.

Note: Client isolation. It is on by default on most campus and conference networks. This is why the server lives on the internet instead of your laptop.

---

## Cost of running it

One free web service. One markdown file.

Roughly eighty lines of Python.

Note: Free tiers sleep after inactivity — hit the URL a few minutes before you walk in so the first slide is instant.

---

# Your turn

Delete everything in `slides.md` and write your lecture.

Note: Slides split on a line containing three dashes. Anything after "Note:" is for your eyes only.
