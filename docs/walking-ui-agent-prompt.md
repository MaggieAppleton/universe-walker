# Walking badge UI exploration

Design screens for our two-player collaborative walking game. Work in this
existing workspace and edit the existing jig at `design-jig/walking/`.
Maggie wants your independent design judgement, including fresh directions
informed by the other games on the badge. Show working visual comparisons.

Use the current checkout and branch; keep the work in place. The previous
agent is pausing UI edits after this handoff. Preserve existing
references and accommodate any newer edits you find rather than reverting them.

## Start here

Read these before designing:

- `design-jig/walking/README.md`: current proposal, renderer, stock-game
  source links, and review status.
- `design-jig/walking/index.html`, `jig.js`, `gallery.js`, and `preview/`:
  the editable jig and candidate Python pixel painter.
- `design-jig/walking/reference/user-layout-reference.png`.
- `design-jig/walking/reference/selected-hybrid-outlined-apart.png`.
- `design-jig/walking/reference/selected-hybrid-outlined-together.png`.
- `design-jig/walking/reference/chopin-walker-study.html`: the complete
  original design study, including pixel font, sprites and other layouts.
- `badge/apps/walking/__init__.py`, `walking_ui.py`, `progress.py` and
  `sync_link.py`: the working app and its real data/state contract.

The current jig is an unfinished exploration, not an approved design.
You may change its composition, artwork, renderer and controls. Keep the
verified application in `badge/apps/walking/` unchanged during this design pass.
Hardware installation comes after Maggie approves a design.

## The game that already works

Two GitHub Badger 2350 badges count steps independently while Walking is open.
Holding them back to back starts a brief Bluetooth exchange. They save and
acknowledge the combined counts, show an obvious success message, then separate.
After more walking, another hold updates the shared total without double-counting.
This workflow has passed real two-badge testing. There are 51 passing host tests.

The demo goal is **500 shared steps**. Maggie wears the original badge,
`f95119f417c67d7e`; Martin wears `79469e7227b64f70`.
The approved starting sprites are a red-haired/red-jacket hiker for Maggie and
a blue-capped/blue-jacket hiker for Martin. Make them distinct by silhouette
as well as colour. They need readable heads, bodies and separate legs at badge size.

The large shared number is the **last acknowledged team total**. Personal
new steps remain separate until a completed sync. For example:

- Last shared: Maggie 150 + Martin 150 = **300**.
- Maggie walks 75 more: her live personal count is 225, but the shared display
  stays **300**, with **75 new personal steps** shown separately.
- A completed exchange confirms Maggie 225 + Martin 200: both badges show
  **425**. Repeating the sync without walking keeps 425.

Receiving a packet alone is insufficient to update the confirmed display.
The partner’s count/position is last known while apart. “Out of range” and
“With Martin” in the original browser study are simulation labels, not evidence
of a continuous connection. Use wording that fits the brief hold-to-sync flow.
A personal unshared walk past 500 must not falsely claim the team reached its goal.

## What Maggie wants to explore now

She likes the **split numbers / landscape layout**: readable count above,
small meaningful caption, landscape below. Keep that as one serious direction.

Try genuinely different environments: mountains, valleys, open fields,
coastlines and maps. Compare a gradient sky with a solid sky. The request to
restore gradients supersedes the earlier request for only broad colour bands.
Let the path enter and leave both screen edges naturally. Keep people visible
at the beginning/end and when they occupy the same progress point. Last-known
partner styling should still look like a person; sparse dithering was too weak.
Keep landmarks recognisable and avoid duplicate goal labels.

Also ask: **how would you design this game fresh, learning from the stock games?**
Develop a few distinct compositions, not just palette swaps. You can challenge
the current draft. The goal is a small, characterful game that belongs on this
device, with clear state changes and a legible score.

Review **Merge Conflict, Pong, Snake and Flappy Mona**. Source links are in
the jig README; Flappy Mona’s original background is copied into `reference/`.
Look at typography hierarchy, HUD placement, sprite scale, contextual prompts,
pairing progress, motion and celebrations. Inspect installed artwork if the
badge is available in disk mode. Be precise about what you inspected: source,
assets and simulator views are not photographs of the installed screens.

Existing sketches already include six landscapes and three fresh layout ideas.
Use them as context and comparisons, not as the answer you must reproduce.

## State coverage

Use `preview/fixtures.py` as the existing data source. Show the whole flow for
the directions you recommend, including these 24 cases:

| Group | Screens |
| --- | --- |
| Walking | New personal steps while apart; apart and up to date; enough unshared personal steps to pass the goal |
| First use | No shared result yet; walking before the first sync |
| Pairing | Holding steady with scrubbable progress; hold complete but Bluetooth still connecting; exchanging counts; waiting for acknowledgement |
| Confirmation | Successful sync; already up to date; confirmed zero steps |
| Separation | Waiting for badges to move apart; rearmed for the next walk |
| Retry | Connection loss/timeout; failed exchange |
| Destination | Near 500; exactly 500; beyond 500; large counts needing a smaller type size |
| Recovery | Sync unavailable; step sensor unavailable; save failure; app paused with HOME recovery |

Distinguish an unknown total from a confirmed zero. Failed or incomplete syncs
retain the previous confirmed total. Keep the success visible long enough to
read “Synced” and “Move badges apart”. Test both wearer identities, overlapping
positions, and people at the route endpoints.

## Jig and deliverables

Iterate the existing **plain HTML jig with vanilla Dial Kit controls**. Keep
the warm grey page, white preview area, side-by-side comparisons and floating
dials. Show current values and provide Copy settings. Show states on the page
so Maggie can compare them without repeatedly driving a simulation.

Render screens at **320 × 240 physical pixels**, ideally from a 160 × 120
logical pixel painter scaled crisply by two. Show screen pixels edge to edge,
without a device enclosure. Keep browser controls outside the badge screen.
Use honest fixture counts and label them as preview data.

The current jig opens directly as `design-jig/walking/index.html`; its native
PNG layers are generated by `python3 design-jig/walking/export.py`. You may
simplify this implementation. This sandbox blocked starting a localhost server;
the offline HTML avoids that dependency. Browser automation also blocks file
URLs; the previous review used a self-contained browser fixture.

Check every recommended screen at actual size, verify controls, inspect the
last row, and check for clipped text/people. Regenerate stale assets after edits.
The last pixel audit matched a tweaked map preset but found mismatches in the
default preset, so treat the current generated/browser composition as needing
verification rather than assuming it is already exact.

Finish by showing Maggie the jig with a direct opening link and a short note
about the directions. Keep chat concise and make small, reviewable changes.
Run the existing host checks if you touch anything that could affect the app.

Once Maggie approves the final design, provide faithful screen-only PNGs for
apart/pending, holding/syncing, and confirmed/success states, with source paths,
settings, sample counts and status meanings. The originating Chopin design
session (`01a164c7-f5e3-7aa1-8d71-86e66b409dba`) must update its recorded choice
to those exact approved visuals. Intermediate explorations are not final choices.
