# Hardware and demo operation

## Devices

The demo uses two GitHub Badger 2350 badges with the existing RP2350 firmware.

| Wearer | Stable device ID |
| --- | --- |
| Maggie | `f95119f417c67d7e` |
| Martin | `79469e7227b64f70` |

The app chooses its wearer from that ID; unknown IDs use Maggie's artwork.
The USB tools expect one connected badge at a time. Identify the device
before writing, back up the existing files/state, and verify written content.

## Storage and installation

The badge has two relevant filesystem locations:

| Location | Access and contents |
| --- | --- |
| `/system` | Read-only over normal serial. USB **BADGER** disk mode exposes this tree; install app files here through the mounted disk. |
| `/state` | Persistent app state, writable through the runtime/serial. Not exposed by the normal BADGER system disk. |

Double-tap RESET to enter BADGER disk mode. Copy the complete
`badge/apps/walking/` directory from this repository into `apps/walking/` on
the mounted volume, backing up an existing installation first. Eject the
volume, press RESET once, and open Walking from the menu. Install the same
build on both badges. Copy app files only; firmware and boot files stay as-is.

The `walking_demo` State key is stored at `/state/walking_demo.json`:

```json
{"counts": {"<device-id>": 0}, "game": 8230, "last_sync": {}}
```

Installing app files does not reset this saved progress. A file named
`state/walking_demo.json` on the BADGER disk would be under `/system/state`,
not the persistent `/state` location. Use the reset tool over serial for
progress changes; it must leave disk mode first.

## Demo reset

The reset utility provides two deliberate starting points, both with a
10,000-step goal and no confirmed shared total:

| Profile | Maggie | Martin |
| --- | --- | --- |
| `near-goal` | 0 | 9,900 |
| `zero` | 0 | 0 |

Reset both badges to the same profile. The first completed sync confirms the
starting shared total; until then each screen labels its personal count as
unsynced. An unreset peer can restore its older higher contribution on the
next merge.

Connect one badge, run either command, then repeat for the other badge:

```sh
python3 tools/reset_demo.py near-goal
python3 tools/reset_demo.py zero
```

See `python3 tools/reset_demo.py --help` for profiles and the disk path option.
The tool identifies each badge automatically and backs up its saved state.
When starting in disk mode, follow its automatic mode transition or physical
RESET prompt to reach serial; the disk cannot directly write `/state`.
Automatic disk ejection uses macOS `diskutil`. On other systems, eject the
disk and press RESET once before running the same command in normal USB mode.
The tool refuses an installed app whose goal is not 10,000, verifies the new
state after a restart, and returns the badge to Home with no live pairing.

## Steps and persistence

Walk with Walking open and the badge in its normal lanyard position. The
onboard LSM6DS3TR-C pedometer is read over **I2C1, SDA GPIO18, SCL GPIO19,
address 0x6A**, at 400 kHz. The app reads the enabled sensor; it does not
reset or reconfigure it. The step registers are `0x4B/0x4C`.

Poll every 250 ms. The first reading establishes a baseline; steps taken
while Walking was closed are not credited. The counter normalizes 16-bit
wrap and discards jumps above 32 steps per poll as reset/invalid readings.
The sensor may take several steps to begin reporting; a changing counter is
not an accuracy measurement.

Changed progress saves every two seconds and on HOME/normal exit. Abrupt
power loss can lose the newest two seconds. Sync counts save before STATE
publication/ACK, and confirmed progress saves only after matching ACK.

## Two-badge acceptance check

1. Install the same app build on both badges. Open Walking and note each
   personal count and any confirmed shared total.
2. Walk independently. Hold the badges back to back and still until both
   show Synced and the same total. Check the total against both contributions.
3. Separate them. Walk with one badge only: its yellow pending count grows;
   both white shared totals stay unchanged.
4. Hold together again. Both shared totals should include the new steps.
   Separate and repeat without walking: the total must stay unchanged.
5. Press HOME, reopen both apps, and check personal/confirmed counts persist.
6. Check the large white/yellow row on the real screen, including long
   counts: no clipping, a shared baseline, and both parts shrinking together.
7. With `dashboard/server.py` running, repeat a hold and check both mirrors
   follow the badges and that pairing behaves as before.

Earlier step/persistence and repeated-sync builds passed reported physical
checks on these two badges. The latest count-row/font calibration needs its
own visual hardware check after installation. Host tests and preview fixtures
verify logic and rendering assumptions separately from that check.

## Diagnostics

Install USB dependencies from `requirements-dev.txt` in a local virtual
environment; see the root README. In normal USB mode:

```sh
python3 tools/inspect_pairing.py
python3 tools/capture_pairing.py --seconds 60
python3 -m mpremote run tools/probe_badge.py
```

`inspect_pairing.py` reads firmware metadata, saved progress, installed
display code, and available logs into ignored `diagnostics/<device-id>/`.
`capture_pairing.py` listens to USB output and reconnects without sending
badge commands. `probe_badge.py` inspects runtime/sensor/BLE APIs and may
initialize runtime hardware; it does not write sensor registers or activate
the radio.

Frame errors pause visibly and save `/state/walking_error.txt`. The bounded
pairing trace checkpoints every two seconds; on this read-only system tree
it falls back to `/state/walking_pairing.log`. Read state/logs over serial,
not the BADGER system disk. These files contain device identifiers and local
progress; keep captures and backups out of Git.
