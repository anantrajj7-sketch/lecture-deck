# Operating this deck during a live lecture

You are helping run a presentation **that is on a projector right now**. The
audience can see every change you make, immediately. Act accordingly.

## Moving the deck

```bash
./deck.py status          # where we are, what's next
./deck.py list            # numbered titles
./deck.py next            # forward one
./deck.py back            # back one
./deck.py goto 7          # jump to slide 7 (1-based)
```

`DECK_URL` and `CONTROL_TOKEN` live in `.env`.

## Editing slides

Slides are `slides.md`. Slides are separated by a line of exactly `---`.
Anything after `Note:` on its own line is speaker notes — visible only on the
presenter's phone, never projected.

```markdown
## Slide heading

- a point
- another point

Note: Say the thing about the wifi here.
```

Save the file and the server reloads within half a second and pushes the new
deck to every screen. **No restart, no command needed.** The current slide
position is preserved.

## Rules while the lecture is live

- **Never reorder or delete slides before the current index.** The presenter is
  mid-sentence; shifting the ground under them is worse than a typo.
- **Add new slides after the current position**, so they arrive before they are
  reached. Check `./deck.py status` first.
- **Do not advance the deck unless asked.** The presenter drives. Your job is
  content unless they explicitly say "next slide" or "go to the summary".
- **Keep new slides short.** Six lines maximum. This is projected in a room, not
  read on a laptop.
- **Put the elaboration in `Note:`,** not on the slide. That is what the
  presenter will actually say out loud.
- Edit and save once. Repeated saves flash the projector.

## When asked to answer an audience question on a slide

Add one new slide immediately after the current one, with the question as the
heading and at most four lines of answer. Then say — do not do — that it is
ready, so the presenter chooses when to advance.
