# Two-badge walking demo

## Agreed behaviour

- Two badges count their owners' steps independently.
- For the one-minute demo, keep the walking app open and both badges awake.
- Hold the badges together to start a brief Bluetooth connection.
- Exchange cumulative counts for each badge, save the resulting progress,
  acknowledge receipt, and disconnect. Both screens show the combined total.
- Repeated syncs must not count the same steps again. Interrupted syncs can
  safely retry. Show success only after the partner acknowledges saved data.
- Shared goals unlock when the combined count reaches their thresholds.
  Goal thresholds and visual design are still to be chosen.

## Data

Each badge has a stable device ID and stores the latest cumulative step count
for each of the two players. Merge matching IDs by taking the higher count,
then sum the two counts for team progress. Never add two team totals together.
Counts must be nonnegative integers. Reject a third player rather than silently
changing the team. The Bluetooth session must verify the intended partner and
game before applying a received snapshot.

The game needs one shared game ID and thresholds on both badges. Starting a
new game must establish a new game ID on both; an individual reset must not
erase the other player's contribution. Persist local counts before sending a
snapshot and persist received counts before acknowledging them.

## Hardware checks before the full app

1. Confirm the actual firmware exposes a working hardware step counter.
2. Check counting during a short walk with this app open. Normalize the raw
   16-bit counter and separate its resets from the game's saved totals.
3. Verify direct Bluetooth connection and two-way exchange on both badges.
4. Tune the holding-together gesture on the real hardware; Bluetooth signal
   strength alone does not establish physical contact.

Existing references: `martinwoodward/action-trainer` for Airtime and pedometer
access, and `badger/home` for the 2026 runtime, saved state, and app lifecycle.
No model training, Wi-Fi, background service, or firmware changes are required
for the initial demo unless the hardware checks establish otherwise.

## First slice

Implement and test the count merge independently of hardware. Then check the
connected badge, add the smallest step-count display, and prove the Bluetooth
exchange with the second badge before adding goals and celebrations.

## Current evidence

The workspace started empty, without Git metadata. The badge
(`f95119f417c67d7e`) has been reconnected and enumerates at
`/dev/cu.usbmodem101`, USB `2e8a:1101`, with a `BADGER` volume.
`mpremote` and a direct PySerial open both fail before reaching the badge:
`[Errno 1] Operation not permitted`. No owning process was reported by `lsof`.
The session's serial access is restricted. The initial probes changed no
badge files. Actual radio communication and walking accuracy remain unverified.

`tools/probe_badge.py` is an inspection probe for a local Terminal run. The
required mpremote, PySerial, and platformdirs packages are installed in
`/private/tmp/universe-badge-tools`. It queries firmware, motion APIs, a raw
step count, and Bluetooth API availability. It imports `badgeware` if the app
runtime is absent, which may initialize the display and motion hardware. It
contains no file writes or radio-activation calls. API presence does not prove
a walk or two-badge exchange works.

The user's first Terminal probe succeeded: MicroPython 1.29.0-preview,
GitHub Badger 2350, firmware build 2026-10-13, device ID as above. BLE scan,
advertise, connect, service registration, read, and write methods are present;
the radio was inactive. The raw REPL had no `builtins.badge`, so the pedometer
was not queried. The revised probe explicitly imports the app runtime before
looking for the motion and step APIs. The user's second run again reported
no `badge` export despite importing `badgeware` without an exception. That
does not establish the absence of the sensor or the app runtime.

The next probe records `badgeware` exports and reads the onboard LSM6DS3TR-C
directly over the documented I2C1 bus (GPIO18/19, address 0x6A). It checks the
chip ID, accelerometer configuration, embedded-function enables, and raw
16-bit step count. It writes no sensor registers. It also preserves any
existing global named `badge` instead of masking it with `None`.

The user's third probe confirmed the onboard sensor: power on, chip ID 0x6A,
accelerometer configuration 0x40, function configuration 0xBD, pedometer
enabled, raw step count 0. This proves register access and configuration, not
step detection during a walk. The app runtime object remains unavailable to
the standalone REPL probe; ordinary apps use launcher-provided globals.

The first Walking app now displays local steps using direct sensor reads,
retains totals in State, checkpoints changes every two seconds, and saves on
normal exit. It includes no Bluetooth transport or shared goal UI yet.
Fourteen host tests pass. The five app files were copied to
`/Volumes/BADGER/apps/walking` and read back byte-for-byte. The first on-device
launch and walking test succeeded: Maggie reported 23 steps, returned HOME,
reopened Walking, and confirmed that the count was preserved. She has a second
GitHub Badger 2350 ready for the Bluetooth sync test.

The next build adds native Link/Proximity pairing based on Merge Conflict
(Maggie's requested reference) and Contacts. Its 12-byte state/ack exchange
merges per-device maxima and saves before acknowledgment; 26 host tests pass.
The success screen shows the shared acknowledged snapshot while newer local
steps remain saved for the next update. Independent code review found no
remaining important issues. Native Bluetooth and two-badge pairing are still
pending real hardware verification. Shared goal celebrations are not built yet.

Both physical badges now have that same seven-file sync build. Every copied
file was read back and matched its local SHA-256. The original badge's prior
count-only app was backed up before replacement. Saved State and boot files
were not overwritten. Next action: eject/reset the original badge, open
Walking on both, and perform the first back-to-back sync test.

## Reliability iteration after the first sync trial

The initial trial revealed repeated returns to Home on the second badge and
unclear count attribution. Apparent continued syncing after separation is not
yet distinguished from live local team-total changes. See the concrete
regressions and fixes in `../plans/2026-10-23-sync-reliability.md`.

The chosen interaction remains hold-only: no SELECT arming. The normal screen
now keeps personal steps as the main live count and shows the confirmed team
total and partner contribution separately. Only a completed acknowledged sync
updates the shared score. A dedicated 2.8-second animated Synced screen tells
both users to move the badges apart. Current host verification: 39 tests pass;
both physical badges must be updated and retested before claiming resolution.

Reliability build deployment: the second badge `79469e7227b64f70` now has
the nine-file revised app, with every file read back and SHA-256 matched.
Its prior app is backed up, and saved progress was not overwritten. The
original badge `f95119f417c67d7e` still needs this same build, followed by a
fresh two-badge test.

2026-10-24: the original badge has also been updated to the reliability build,
with all nine copied files SHA-256 verified. Both badges now have the same app.
All 39 host tests pass. Revised separation, feedback, and exit behaviour still
require a physical two-badge retest.
