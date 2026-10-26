# Architecture and invariants

## Progress model

`counts` maps stable badge IDs to cumulative nonnegative integer step counts.
Merge snapshots by taking the maximum for each ID, then sum the resulting
counts. This makes retries, stale snapshots, and repeated syncs safe. Adding
two team totals would count the same walk twice. A team has at most two IDs;
once a partner's STATE is persisted, that saved team rejects another partner.

`last_sync` is the separately saved, acknowledged two-player snapshot. It
drives the shared display and goal. Receiving and saving a partner's STATE
packet alone does not advance it. A matching ACK confirms that exact merged
snapshot. Steps taken during the exchange stay in `counts` for the next sync.

For example, with `last_sync = {Maggie: 150, Martin: 150}`, the white total
stays **300** when Maggie walks 75 more; her yellow addition becomes **+75**.
If Martin then reaches 200 and the exchange completes, both badges confirm
**425**. Repeating the exchange without walking preserves 425.

The fixed demo game ID is `0x2026`; the goal is **10,000**. The same game ID
must be used on both badges. Reusing an old snapshot can restore a higher
count, so resetting a demo requires resetting both badges.

## Modules

All app paths below are relative to `badge/apps/walking/`.

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Launcher entry point, hardware polling, State persistence, frame loop, cleanup. |
| `steps.py` | Normalize a raw 16-bit pedometer into a cumulative game count. |
| `progress.py` | Validate/merge counts and derive confirmed display totals. |
| `sync_protocol.py` | Hardware-independent STATE/ACK exchange. |
| `sync_link.py` | Firmware Link/Proximity adapter, retry timing, separation gate. |
| `status_beacon.py` | Broadcast the screen's inputs for the live dashboard (optional). |
| `walking_ui.py` | Translate app state into screen moments and progress. |
| `painter.py` | Native text metrics, fitted counts, and drawing helpers. |
| `coast_scene.py`, `hikers.py`, `moments.py` | Landscape, wearers, and full-screen sync/goal moments. |
| `pairing_trace.py`, `diagnostics.py` | Bounded pairing trace and latest exception. |

The browser model in `design-jig/walking/fresh/states.js` uses fixtures, not
device data. Keep its count/goal semantics aligned with the app. Its renderer
is a visual reference; the badge font has different metrics.

## Durable exchange

The native link supplies the peer identity. Each 12-byte `<BBHII` packet
contains kind, protocol version, game ID, the sender's count, and its latest
known partner count. STATE and ACK use the same shape.

1. Freeze the outgoing snapshot and persist local counts before publishing
   STATE. Merely discovering a peer does not bind the saved team.
2. Validate game, packet, and partner identity; merge a received STATE by
   per-ID maximum and persist it before making its ACK available.
3. Retry STATE and ACK fairly. Commit `last_sync` only when the incoming ACK
   matches the exact merged snapshot; failed saves cannot report success.
4. Keep sending acknowledgments during the success grace period, then leave.
   Wait for the native disconnect and require physical separation before a
   new session.

`Exchange` remains independent of native hardware so tests can cover loss,
reordering, malformed packets, persistence failures, and count convergence.

## Native pairing constraints

Pairing is a brief **back-to-back hold**, using firmware `Link` and
`Proximity` as in the stock Merge Conflict app. There is no SELECT arming or
continuous background sharing.

- Pump the link first. In idle frames call `Proximity.update`; in linked
  frames call `Link.update`. Advancing both during idle broke the handshake.
- Keep `START_CAPACITY = 94`. Merge Conflict's initial message naturally
  waits for this capacity. Sending Walking's smaller packet at the initial
  capacity of 19 caused premature exchange failures on the demo hardware.
- Preserve the departing state until an actual disconnected observation.
  Otherwise a still-linked frame can create a duplicate exchange.
- Renew the native cooldown while waiting for separation. A timer expiring
  alone must not rearm another sync while the badges remain together.
- Clear the previous success timestamp when a new exchange begins.

These constraints came from physical failures and two-badge retests. Host
stand-ins cannot establish the firmware's actual radio/separation behaviour.

## Live dashboard status

`status_beacon.py` adds a 29-byte scan response to Link's own pairing
advert: 16-bit service data `0x5557` holding own/team/partner counts, a status
index, hold progress and a success flag. That is exactly what
`walking_ui.model()` needs, so `dashboard/` can redraw the screen. The laptop
only scans; nothing connects to the badge.

- It never starts advertising on its own. It only re-sends Link's last
  advert, with the same arguments, when Link is already advertising.
- It never re-advertises while linking, linked or in a radio session, and at
  most every 500 ms when the status changes.
- Any beacon error disables it; pairing carries on unchanged. `on_exit`
  restores the shared firmware radio.
- Link stops advertising during an exchange, so the dashboard holds the last
  status until the badges separate.

`STATUSES` order is the wire format: append new statuses, never reorder.
`dashboard/model.js` mirrors `walking_ui.model()`; `tests/test_dashboard.py`
checks they agree.

## Two clocks

`badge.ticks` is a native frame timestamp (`FrameTick`). Use ordinary
subtraction for elapsed frame time, as stock apps do. Passing those objects
to `time.ticks_diff` produced false timeouts within tens of milliseconds on
real hardware. Preserve direct subtraction for sync retries, timeout, ACK
grace, cooldown, notices, animation, and trace checkpointing.

`time.ticks_ms()` returns MicroPython tick tokens. Sensor polling and save
timers use `time.ticks_diff` for those values. Keep each clock paired with
its appropriate arithmetic; the test harness distinguishes them.

## Display contract

- A large white number shows the last confirmed shared total; an equally
  large yellow `+N` shows local steps since that snapshot. Measure the whole
  row and shrink both parts together. Hide `+0`.
- Before any confirmed sync, show personal steps with **Your steps, not
  synced yet**. Local unshared progress cannot trigger the shared goal.
- The amber trail shows local progress; the faded partner stays at the last
  synced position. Sync moments show holding, connecting, swapping, success,
  and separation; a retry cannot claim success.
- Native count baseline is **75**, with **4px extra draw-box height** to
  avoid clipping. Keep this hardware calibration when changing font fitting.
  Browser placement uses its own measured font metrics.
