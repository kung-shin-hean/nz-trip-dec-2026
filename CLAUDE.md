# NZ Dec 2026 Trip Planner

Static HTML, no build step, no dependencies. Published via GitHub Pages from `main` at
https://kung-shin-hean.github.io/nz-trip-dec-2026/ — **pushing to main deploys immediately**,
and the trip group reads these pages to decide real bookings. Verify before pushing.

Files:
- `index.html` — entry point + progress overview (done vs outstanding)
- `nz_accommodation_v3.html` — accommodation options and booking status
- `nz_itinerary_planner_zh.html` — day-by-day itinerary

## Two sources of truth — edit BOTH

`nz_itinerary_planner_zh.html` holds each day twice:

1. `.day-card` blocks (~line 300–800) — what the page renders
2. the `const days` array inside `buildPrintItinerary()` (~line 1035+) — what the
   print/share modal emits

Changing a day means changing both. The array has silently drifted before: commit
`4e42f76` moved Day 4 to Wanaka in the day cards but left the array saying Queenstown,
and it went unnoticed for two commits. Nothing detects this — the page renders fine and
only the printed copy is wrong.

## Booking a location touches 4 places

In `nz_accommodation_v3.html`, confirming a booking requires all of:

1. A card with `class="card booked"` plus `<span class="booked-badge">🔒 已预订</span>`
2. A `bookedSel` entry — currently `{chc:4, tko:2, mtc:3, wka:3, qtn:4}` — this is what
   locks `pick()` and auto-selects the booking on page load
3. `labels[loc][opt]` **and** `nums[loc][opt]` — keys must match the card's `data-opt`.
   A card whose `data-opt` has no `nums` entry silently drops out of the budget total.
4. The location `.badge` in the header, and the alert text above that location's cards

Unknown price = `nums` value of `null`. The total then appends a note naming what is
missing rather than showing a wrong figure.

## Conventions

- Content is Simplified Chinese. Prices in MYR; NZD converted at ~2.55 and shown as
  `NZD 670.45（≈MYR 1,710）` so the original receipt stays auditable.
- Source of trip facts is the WhatsApp group "NZ Dec Trip". Quote who confirmed and when
  in the alert text (e.g. 「8月2日 WhatsApp 群内确认」) so members can trace any number
  back to a message. See the `sync-from-whatsapp` skill.
- **Never commit a price the group has not actually confirmed.** Use `null` in `nums` and
  「金额待补」 on the card, and say so explicitly when reporting.
- `.gitignore` ignores everything by default and allowlists published files. A new file
  will not be committed until it is added to the allowlist.

## Before pushing

```
python check.py
```

Validates tag balance, embedded JS syntax, and that every card's `data-opt` has matching
`labels`/`nums` entries. There is no CI — this script is the only gate before the group
sees the change.
