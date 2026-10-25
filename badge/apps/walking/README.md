# Walking

Walk independently, then hold two Universe 2026 badges back to back to combine
steps towards a shared **10,000-step** goal. Keep Walking open while walking.
No Wi-Fi, external sensors, or firmware changes are needed.

## On the badge

The coast screen shows the last confirmed shared total in white. Your steps
since that sync appear beside it as a yellow **+N**, in the same font size;
the whole row shrinks to fit and +0 is hidden. Before the first sync, the
large number is your personal count, labelled **Your steps, not synced yet**.
Your amber trail grows as you walk; your partner stands faded where you last
synced. Only a confirmed shared total can light the lighthouse and trigger
"You made it!".

Hold the badges back to back and keep them still while the ring fills. The
screen shows **Connecting**, **Swapping steps**, then **Synced!** with the
shared total and its increase. Move the badges apart before another sync.
Repeating without walking leaves the total unchanged and shows **Up to date**.
The first exchange fixes the two-player team; other partners are rejected.
The known device IDs choose Maggie or Martin; unknown badges use Maggie's art.

Press HOME to save and return to the menu. Progress also saves every two
seconds while steps change, so sudden power loss can lose the latest two
seconds. Opening Walking baselines the sensor's existing count; steps taken
while the app is closed are not credited. The pedometer can take several
steps to start reporting.

## Install and reset the demo

Double-tap RESET to enter USB disk mode. Copy this entire `walking` directory
into `apps` on the BADGER volume, eject it, press RESET once, and open Walking
from the menu. The disk maps to `/system`; saved progress lives separately in
`/state` and survives replacing app files.

For host tools, follow the [repository setup](../../../README.md). Connect
one badge at a time and run from the repository root:

```sh
python3 tools/reset_demo.py near-goal  # Maggie 0, Martin 9,900
python3 tools/reset_demo.py zero       # both players 0
```

Run the chosen command once for each badge. Both modes clear the last
confirmed sync and keep the goal at 10,000. If the badge starts in disk mode,
the tool ejects and resets it into normal USB mode to write saved progress.

Check a two-badge demo by syncing, separating, and syncing again without
walking: the shared total must stay unchanged. Then walk with one badge:
only its yellow addition should change until the next sync. Exit and reopen
both apps to check that progress remains saved.

## Code map

| File | Responsibility |
| --- | --- |
| `__init__.py` | Firmware entry point, sensor polling, saves, frame and exit callbacks |
| `steps.py` | Convert the 16-bit pedometer reading into a cumulative personal count |
| `progress.py` | Merge per-player maxima and derive confirmed display totals |
| `sync_protocol.py` | Durable STATE/ACK exchange, independent of the radio |
| `sync_link.py` | Native Link/Proximity lifecycle, retries and separation gate |
| `walking_ui.py` | Map sync state to the coast screen and full-screen moments |
| `coast_scene.py`, `hikers.py`, `moments.py`, `painter.py` | Drawing and native font fitting |
| `pairing_trace.py`, `diagnostics.py` | Bounded pairing journal and latest frame error |

These modules run as flat imports on MicroPython. The firmware injects
`badge`, `screen`, drawing primitives, fonts, and `run`; they are not missing
Python imports. Host tests supply them through `tests/badge_harness.py`.

Preserve these hardware and data rules when editing:

- Sensor reads use I2C1, GPIO18/19, address `0x6A`. Read the enabled pedometer;
  do not reset or reconfigure it. The first reading establishes a baseline.
- Merge the highest count for each player. Save counts before sending STATE
  or ACK; update `last_sync` only after the matching saved ACK arrives.
  Live steps taken during the exchange must survive those saves.
- `badge.ticks` frame timestamps use ordinary subtraction. Use
  `time.ticks_diff` only with `time.ticks_ms()` sensor/save timestamps.
- Wait for native Link capacity **94** before exchanging packets, and require
  physical separation before a repeat session. The small packet size alone
  does not mean the radio is ready.
- Keep the approved count baseline at **75**, with **4px** of bottom drawing
  padding, and fit the white total and yellow addition together.

Host verification uses the actual app with virtual hardware and does not
write to a connected badge:

```sh
python3 -m unittest discover -s tests -v
```

A frame failure pauses visibly and saves the latest exception to
`/state/walking_error.txt`. Pairing traces checkpoint automatically to
`/system/apps/walking/pairing-trace.log`, falling back to
`/state/walking_pairing.log` when the app directory is read-only. Read `/state`
files over the normal USB serial connection; they are absent from the
BADGER disk.
