# Walking badge design review

The current design is **Horizon, Coast, big lighthouse, full-screen sync moments**,
with a 10,000-step shared goal. A large white number shows the confirmed shared
total; an equally large yellow `+N` shows local steps waiting to sync. The two
numbers shrink together to fit, and `+0` stays hidden.

## Open the previews

From the repository root, run:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory design-jig/walking
```

Open [the design review](http://127.0.0.1:8765/) for every state on both badges,
world comparisons and animated sync moments. The folder's `index.html` opens
`fresh.html`, which remains the main review page.

Open [the count comparison](http://127.0.0.1:8765/counter.html) to add steps to
either badge and sync them. Its left column keeps the previous small contribution
for comparison; the right column shows the current large yellow contribution.
Both pages have vanilla Dial Kit controls and a button to copy the chosen values.
Reset clears the review page's saved dial settings.

These are browser fixtures; they never read or write a badge. Mona Sans loads
from Google Fonts, so matching the saved captures needs an internet connection.

## Files to edit

| File | Purpose |
| --- | --- |
| `fresh.html`, `fresh/app.js` | Review page and Dial Kit controls |
| `counter.html`, `counter.js` | Live step/sync comparison and long-number checks |
| `fresh/painter.js` | Canvas drawing and number fitting |
| `fresh/directions.js` | Horizon/map layouts and the count row |
| `fresh/worlds.js`, `fresh/events.js` | Landscapes and sync/arrival moments |
| `fresh/states.js` | Shared preview fixtures; also checked by the Python tests |
| `final/settings.json` | Settings used for the current saved captures |
| `final/` | Current 320 × 240 PNG captures and their notes |
| `final/alternatives/` | Comparisons available in the current review page |
| `vendor/` | Dial Kit's vanilla distribution and its licence |

The native badge implementation lives in [`../../badge/apps/walking`](../../badge/apps/walking).
Browser font metrics can differ from the badge's `.af` font.

## Export PNGs

With Python 3.9+ and Chrome, Chromium or Edge installed, run from the repository root:

```sh
python3 design-jig/walking/final/export.py
```

The exporter starts its own temporary local server and browser profile, loads
`final/settings.json`, and saves eight PNGs in `final/`. No separate server or
Python packages are needed. It fails if Mona Sans cannot load, so fallback fonts
cannot silently replace the current design.

Useful options:

```sh
python3 design-jig/walking/final/export.py --alternatives
python3 design-jig/walking/final/export.py --output /tmp/walking-captures
python3 design-jig/walking/final/export.py --browser /path/to/chromium
```

`--alternatives` also refreshes the twelve comparison captures. See
[`final/README.md`](final/README.md) for the fixture counts and saved states.
The old rectangle-painter experiments and their generated layers have been removed.
