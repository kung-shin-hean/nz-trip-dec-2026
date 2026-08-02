# NZ Dec 2026 Trip Planner

Three static HTML pages the family uses to plan an 8-person South Island trip
(21–31 Dec 2026). No build step, no dependencies, no framework — open a file in a
browser and it works.

**Live:** https://kung-shin-hean.github.io/nz-trip-dec-2026/

| File | What it is |
| --- | --- |
| `index.html` | Entry point. Link cards + a "done vs outstanding" progress block. |
| `nz_accommodation_v3.html` | Accommodation options per location, booking status, live budget total. |
| `nz_itinerary_planner_zh.html` | Day-by-day itinerary with interactive route/activity decisions and a printable view. |
| `check.py` | Pre-push validation. See [Before you push](#before-you-push). |
| `CLAUDE.md` | Conventions and coupling rules, for AI assistants and humans alike. |

All user-facing content is Simplified Chinese — the readers are family members, not
developers. Code, comments, and commits are English.

## Running locally

Opening the file directly works for everything:

```bash
start index.html          # Windows
open index.html           # macOS
```

If you want a real origin (e.g. to avoid `file://` quirks, or to test on your phone
over the LAN):

```bash
python -m http.server 8000
# then http://localhost:8000/
```

There is nothing to install and nothing to compile. Edit the HTML, refresh the browser.

## How the pages work

### Accommodation page

Each location (`chc` Christchurch, `tko` Tekapo, `mtc` Twizel/Mt Cook, `wka` Wanaka,
`qtn` Queenstown) is a `.loc-block` containing option cards. A card is identified by
its `data-loc` + `data-opt` pair, and that pair is the join key into three JS tables:

```js
const bookedSel = {chc:4, tko:2, mtc:3, wka:3, qtn:4};  // locked-in bookings
const labels    = { chc:{1:'MYR 972 (Airbnb)', ...}, ... };  // budget row text
const nums      = { chc:{1:972, ..., 4:null}, ... };         // budget arithmetic
```

- A location listed in `bookedSel` is **locked** — `pick()` returns early, and the
  booked option is auto-selected on page load so it always counts toward the total.
- `nums` value of `null` means "booked but the amount isn't known yet". The total then
  appends a note naming what's missing rather than silently under-reporting.
- User selections for unlocked locations persist in `localStorage` under
  `nz_accom_v3_sel`.

Because all five locations are currently booked, every non-booked card is a
price-comparison record: its button is greyed out and relabelled at runtime.

### Itinerary page

Day cards are collapsible (`toggleDay`). Four decisions — Hobbiton, the Wanaka route,
Milford Sound day, and the post-group split — are held in a `decisions` object and
drive `.variant-content` blocks that show or hide route-specific advice.

**Known gotcha:** decisions are in-memory only. There is no persistence, so a refresh
resets them to defaults. If you add persistence, mirror the accommodation page's
`localStorage` approach.

The print/share modal rebuilds the whole itinerary from a **separate** `const days`
array inside `buildPrintItinerary()`. That array is a second copy of the schedule and
must be edited alongside the day cards — see below.

## The two things that break silently

Neither of these produces an error. Both have shipped broken before.

**1. The itinerary exists twice.** `.day-card` blocks render the page; the `const days`
array in `buildPrintItinerary()` feeds the print modal. Commit `4e42f76` updated the
cards to move Day 4 to Wanaka and left the array saying Queenstown — the page looked
perfect and the printout was wrong for two commits. Edit both.

**2. A booking touches four places.** Confirming an accommodation means all of:

1. The card — `class="card booked"` + `<span class="booked-badge">🔒 已预订</span>`
2. `bookedSel` — locks the location and auto-selects on load
3. `labels[loc][opt]` **and** `nums[loc][opt]` — keys must match the card's `data-opt`
4. The location's header `.badge` and the alert text above its cards

Miss step 3 and the card renders normally while quietly vanishing from the budget total.
`check.py` catches exactly this case.

## Before you push

```bash
python check.py
```

Validates HTML tag balance, embedded `<script>` syntax (needs `node` on PATH), and that
every card's `data-opt` has matching `labels`/`nums` entries. Exits non-zero on failure.

This runs automatically as a `Stop` hook for Claude Code sessions
(`.claude/settings.json`), but run it yourself before pushing by hand.

**There is no CI, and pushing to `main` publishes to GitHub Pages immediately.** The
family reads these pages to make real booking decisions, so a bad push is visible to
them within a minute.

## Data provenance

The source of truth for what is actually booked is the WhatsApp group "NZ Dec Trip",
not this repo. When recording a booking, quote who confirmed it and when in the alert
text (「8月2日 WhatsApp 群内确认」) so any number can be traced back to a message.

**Never record a price the group hasn't confirmed.** Use `null` in `nums` and
「金额待补」 on the card. An honest gap is useful; an invented number is not.

Claude Code sessions can automate the sync — see
`.claude/skills/sync-from-whatsapp/SKILL.md`.

## Adding a file

`.gitignore` denies everything by default and allowlists specific paths:

```gitignore
*
!.gitignore
!index.html
...
```

A new file will be invisible to git until you add a `!` line for it. If a file you
just created isn't showing up in `git status`, this is why.

## Conventions

- Prices in MYR. NZD converted at ~2.55 and shown as `NZD 670.45（≈MYR 1,710）` so the
  original receipt stays auditable.
- Location keys are the three-letter codes above; reuse them, don't invent new ones.
- Styling is inline `<style>` per page with CSS custom properties at `:root`. Pages are
  mobile-first — most readers open these on a phone.
- Tell readers to open in Safari/Chrome rather than WhatsApp's in-app preview, which
  can reset `localStorage` selections.
