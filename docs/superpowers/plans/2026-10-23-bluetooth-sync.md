# Brief two-badge sync

**Goal:** Hold the two badges together, exchange saved step counts, and show
the same combined total. Repeating the exchange must not duplicate steps.

Use `badgeware.link.Link` and `Proximity`, following the stock Merge Conflict
and Contacts apps. Maggie explicitly requested Merge Conflict as guidance.
These APIs are provided by the badge firmware; their hardware transport still
needs verification on both badges. The simulator's implementation is a stub.

## Protocol

The native link supplies the peer's stable ID. A 12-byte packet holds kind,
version, a shared 16-bit demo game ID, sender's count, and sender's latest known
partner count (`<BBHII`). Each session freezes its outgoing snapshot. Merge
both snapshots by per-device maximum, persist, then acknowledge that exact
merged snapshot. Success requires receiving the partner snapshot and its
matching acknowledgment. Keep retrying snapshot and acknowledgment packets
until successful or timed out. Continue counting during the exchange.

Both badges retain the two device IDs in their saved counts. Reject a third
player or a different game. Preserve the 23 steps already recorded. This slice
adds syncing and a combined-total screen; shared goal celebrations come next.

## Files and checks

- [x] Test the real protocol engine in `tests/test_sync.py` before writing
  `badge/apps/walking/sync_protocol.py`: convergence, repeated sync, stale
  counts, lost/reordered acknowledgments, save failure, wrong game/partner,
  malformed packets, and small packet size.
- [x] Implement that plain-Python engine and run the full host suite.
- [x] Add `badge/apps/walking/sync_link.py` as the native-link adapter. Poll
  proximity while idle, retry packets fairly, release after completion, and
  require the badges to separate before another sync. Show recoverable errors.
- [x] Connect the engine to existing saved state and screen in `__init__.py`.
  Preserve the tested sensor loop and counter. Save before acknowledging.
- [x] Verify syntax, packaging, and tests; install and read back both copies.
- [ ] On hardware: walk independently, hold badges back to back, verify equal
  totals, separate and repeat without walking, then reopen to check persistence.

Do not claim the native Bluetooth exchange works until the real test passes.

## Verification so far

Twenty-six host tests pass. The added stale-ACK regression failed before the
fix and passes afterward: a delayed older acknowledgment cannot undo a valid
success. An independent read-only code review found no remaining important
correctness issues. Radio and native connection lifecycle tests remain pending.

The success display uses the exact acknowledged snapshot on both badges.
New steps counted during the exchange stay saved and appear after the short
success notice; they are not discarded to force the live counters to agree.

Hardware identities: original badge `f95119f417c67d7e` (23 verified saved
steps), second badge `79469e7227b64f70`. The second is currently connected
in USB disk mode for installation. Both badges now have the same seven app
files, each read back and SHA-256 verified. The original badge's count-only app
was backed up to `/private/tmp/universe-walking-f95119f417c67d7e-before-sync-20261023`.
Only application files were copied; saved State files and boot files were not
overwritten. The latest full host suite passes all 26 tests.
