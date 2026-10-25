# Current walking design captures

**Horizon layout, Coast world, big lighthouse, full-screen sync moments.**
The current capture settings are in [`settings.json`](settings.json); the
review page is [`../fresh.html`](../fresh.html).

The white total shows confirmed shared steps. New local steps sit beside it as
an equally large yellow **+N**. The row shares one baseline and shrinks together
to fit, with `+0` hidden. Sync adds both contributions to the white total and
clears the yellow addition. The lighthouse lights only after confirmed progress
reaches the goal.

These are fixtures with a 10,000-step goal. Martin starts at 9,900 personal
steps and Maggie at 0. Before the first sync, there is no confirmed shared total.
After it, the shared total is 9,900. Maggie then walks 60 and Martin walks 40;
the next sync confirms 10,000: Maggie 60 + Martin 9,940.

| Capture | State |
| --- | --- |
| `pending-maggie.png`, `pending-martin.png` | Shared 9,900; Maggie +60 or Martin +40 waiting to sync |
| `apart-maggie.png` | Shared 9,900, up to date after the initial sync |
| `holding-maggie.png` | Proximity hold at 65% |
| `syncing-maggie.png` | Exchange in progress; the old total remains confirmed |
| `success-maggie.png` | Both counts saved and acknowledged; shared total 10,000 |
| `goal-maggie.png` | Arrival at the confirmed 10,000-step goal |
| `large-maggie.png` | Shared 1,000,025; fitted digits stay between the labels |

`alternatives/` contains the twelve optional comparisons in the current review
page. `../counter-comparison.png` records the count comparison.

## Regenerate

From the repository root:

```sh
python3 design-jig/walking/final/export.py
```

Add `--alternatives` to refresh the comparison captures too. The exporter serves
`fresh/export.html` automatically, using a temporary Chrome/Chromium/Edge profile.
It needs internet access to load Mona Sans 500. Each PNG is exactly 320 × 240.
The badge's `.af` font has different metrics, so browser captures do not replace
checking the design on hardware. Full setup is in [`../README.md`](../README.md).

The stable fixture API is `Walking.model(state, holdProgress, badge)` or
`Walking.fixture(state, badge)`, where badge is `"Maggie"` or `"Martin"`.
`Walking.GOAL` is 10000. Pass the same badge to the painter options to choose the
hiker identity. Preview fixtures never write to a badge.
