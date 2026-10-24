# Step merge implementation plan

> Implement inline using executing-plans and test-driven-development. Keep
> this slice independent of the badge UI and Bluetooth transport.

**Goal:** Combine two cumulative step counts without crediting steps twice.

**Architecture:** A plain MicroPython-compatible function takes two maps from
device ID to step count and returns their per-device maxima. It rejects invalid
counts and teams larger than two. Identity and game checks belong to the later
Bluetooth session; this function does not establish either.

**Tech stack:** Python standard library, with `unittest` for host verification.

## Task 1: Count merge

Files: `badge/apps/walking/progress.py`, `tests/test_progress.py`.

- [x] Write tests proving that `{a: 12}` and `{b: 18}` combine to 30 steps;
  repeated or stale snapshots preserve that total; and fresh contributions
  produce the same result in either order without mutating inputs.
- [x] Include rejection cases for a third badge, negative counts, fractional
  counts, booleans, and missing device IDs.
- [x] Run `python3 -m unittest discover -s tests -v` before implementation.
  Expected: failure because the merge function does not exist.
- [x] Implement `merge_counts(known, incoming)` using validation followed by
  `max(known_count, incoming_count)` for each ID. Return a new dictionary.
- [x] Run the full test command again. Expected: all scenarios pass.

Result: seven tests pass. The initial run failed because `progress` did not
exist. No hardware is represented or mocked by these tests. This verifies
count merging only, not Bluetooth, saved state, or the step sensor.

## Next slice

Run a read-only hardware probe after the badge is reconnected. A second badge
is needed to validate Bluetooth sync; host tests cannot establish radio success.
