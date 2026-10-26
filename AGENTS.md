# Working on Universe Walker

This is a two-badge MicroPython demo with a separate browser design preview.
Make small changes and report the result of each meaningful step. Preserve
work already in the checkout. Plan non-trivial UI changes with Maggie before
implementation: ask for references and intended behaviour, then compare
2–3 approaches.

## Read by task

- **Any behaviour change:** read [docs/architecture.md](docs/architecture.md)
  for the count, sync, clock, and display invariants.
- **USB, installation, state reset, or hardware debugging:** read
  [docs/hardware.md](docs/hardware.md) before connecting to a badge.
- **Visual work:** read [design-jig/walking/README.md](design-jig/walking/README.md)
  and [the approved design](design-jig/walking/final/README.md). Current
  entry points are `fresh.html`, `counter.html`, and `fresh/states.js`.

## Change map

| Responsibility | Files |
| --- | --- |
| Runtime, sensor polling, persistence | `badge/apps/walking/__init__.py`, `steps.py` |
| Count model and confirmed totals | `progress.py` |
| Plain-Python packet exchange | `sync_protocol.py` |
| Native BLE lifecycle and frame clocks | `sync_link.py` |
| Live dashboard status and mirror | `status_beacon.py`, `dashboard/` |
| Screen model and drawing | `walking_ui.py`, `painter.py`, `coast_scene.py`, `hikers.py`, `moments.py` |
| Browser model and renderer | `design-jig/walking/fresh/states.js`, `fresh/painter.js` |
| USB utilities | `tools/` |

Unqualified filenames are relative to `badge/apps/walking/`. Keep pure
model/protocol code host-testable; hardware globals
belong in the runtime and rendering adapters.

## Verification and handoff

Run `python3 -m unittest discover -s tests -v` after app, tool, or fixture
changes. Python 3 and Node.js are required. Inspect real 320×240 renders for
visual changes; confirm native font placement on hardware separately.

Keep diagnostics, backups, serial captures, caches, and temporary screenshots
out of version control. Keep third-party license files with their assets.
Do not change firmware or boot files to install this app. Open PRs with a
real UI image for visual work or a concrete diagram for other work. Merge
only after Maggie explicitly approves that ready PR or identified set.
