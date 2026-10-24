# Walking badge design jig

Open [index.html](index.html) directly in a browser. It works offline, with
vanilla Dial Kit controls, comparison screens and a Copy settings button.
All screens are exactly 320 × 240 physical pixels, painted at 160 × 120 and
scaled by two without smoothing. The flat PNGs and composited layers come
from the same candidate Python rectangle painter in `preview/`.

This is a review proposal. Nothing in `badge/apps/walking` or on the actual
badges was changed. The confirmed step protocol, counter and saved progress
remain the verified implementation. Native adaptation follows design review.

Settled choices: count + trail, outlined hikers, 500-step demo goal;
Maggie wears `f95119f417c67d7e`, Martin wears `79469e7227b64f70`.
The screen’s dominant number is confirmed shared progress. Personal steps
since confirmation appear separately and cannot light the lighthouse early.

The landscape gallery compares sunset, alpine, valley, meadow, coast and map
views with gradient and solid treatments. Click a gallery screen or choose
Landscape/Atmosphere in Dial Kit to apply it throughout the state matrix.
The map compares shaded and flat paper rather than a literal sky.

Three additional fresh layout sketches use the same pending and acknowledged
fixture data: a landscape-first HUD from Flappy Mona, a co-op map HUD from
Snake, and a people-first pairing composition from Merge Conflict/Pong.
These are starting concepts, not approved replacements. Their two key states
are shown; the complete 24-state review applies to the count-and-trail track.

The 24 cases cover first use, walking apart, personal pending steps, all sync
phases, confirmed zero, unchanged repeat sync, separation, retry, destination
boundaries, long counts, and all current recovery/error messages. These are
review fixtures, not readings from either badge. Change the Badge selector
to see both hiker identities. The comparison uses the selected reference’s
art treatment with the same fixture data and honest native status wording.

## Game references reviewed

- [Merge Conflict UI](https://github.com/badger/home/blob/main/badge/apps/merge_conflict/ui.py):
  a disciplined body/title/huge type hierarchy, dark surfaces, bright green
  for positive emphasis, and short character reactions rather than constant
  full-screen effects. The proposal retains the chosen reference font and
  composition, using Merge Conflict’s positive green and a short check cue.
- [Pong](https://github.com/badger/home/blob/main/badge/apps/pong/__init__.py):
  separate holding, connecting and pull-apart messages; a clearly visible
  progress bar. The jig exposes hold progress and keeps confirmation separate
  from connection setup.
- [Snake](https://github.com/badger/home/blob/main/badge/apps/snake/__init__.py):
  a stable HUD and quiet playfield; prompts are contextual. The count stays
  anchored and the scenery carries no extra duplicate goal label.
- [Flappy Mona](https://github.com/badger/home/blob/main/badge/apps/flappy_mona/__init__.py):
  broad landscape silhouettes and character motion, with the HUD kept legible.
  The proposed landscape uses broad bands and a clean horizon. The dials
  expose both walking frames without changing progress.

Upstream source and Flappy Mona’s landscape asset were inspected; current
badge storage was not mounted during this source review. These observations
are not claimed as screenshots of the installed games.

## Regenerate

Run `PYTHONDONTWRITEBYTECODE=1 python3 design-jig/walking/export.py` from the
project root after changing the painter. Generated layer packs are image
assets, not browser reimplementations of the badge drawing logic. Dial Kit’s
offline vanilla distribution and its license live in `vendor/`.

Maggie explicitly requested iteration before hardware changes and asked for
new environments plus fresh designs informed by stock games. The app and
badges remain unchanged throughout these studies.

The Chopin design session must receive the approved source/settings and
faithful screen-only renders after Maggie approves the final design. Current
renders are intermediate proposals and must not be recorded as final choices.
