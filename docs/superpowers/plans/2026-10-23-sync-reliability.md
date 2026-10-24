# Sync reliability and feedback

## Hardware feedback

Pairing appeared to work, but badge `79469e7227b64f70` repeatedly returned to
Home. Moving one badge after separation appeared to change the other's score.
The changing meaning of the large number made ownership and team totals unclear.
No error message was reported, so a genuine exception is not established.

Maggie requires holding the badges together as the only sync action. She
rejected SELECT-to-arm. She asked for an obvious animated success screen,
using Merge Conflict as the pairing reference.

## Reproduced failures and fixes

- Delayed native disconnect: clearing the exchange immediately after `leave`
  let the still-linked next frame create another exchange. A departing state
  now waits for the actual disconnected observation without sending new counts.
- Native cooldown can permit a timed retry. Keep renewing its rest window
  before expiry so timing alone cannot rearm syncing; native separation clears
  the gate. Real separation detection remains a hardware dependency to retest.
- A quick new sync could still show the prior success animation. Starting a
  new exchange now clears the old success timestamp.
- A Back touch in the installed entrypoint immediately returned the menu
  path in the integration harness. Remove that touch exit and retain HOME.
  Accidental Back input during real pairing is plausible, not yet proven.
- Personal counts stay live and dominant. The team/partner display comes
  from a separately persisted `last_sync`, committed only after matching ACK.
  Pending data and subsequent walking do not change the shared score.
- Full-screen animated checkmark, Synced, Team total, and Move badges apart
  remain visible for 2.8 seconds. A frame exception produces a visible pause
  and a diagnostic at `/state/walking_error.txt` instead of a silent exit.

## Verification and handoff

39 host tests pass, including actual app entrypoint tests with virtual hardware.
The Back-touch test failed against the installed prior entrypoint and passes
against the new one. Disconnect, cooldown, and stale-success regressions failed
before their fixes. Tests also cover a pause longer than cooldown, failed
confirmation saves, and preservation of steps taken during the exchange.
Code review found no confirmed important issues; native cooling/separation
semantics still need a physical two-badge test. No firmware or boot changes.

- [x] Syntax, icon, and full host tests.
- [x] Back up and update the connected second badge; verify copied files.
- [x] Update the original badge to the same build; verify copied files.
- [ ] Repeat the two-badge hardware test, including movement after separation.

Second-badge deployment: `79469e7227b64f70`, nine app files copied and read
back with matching SHA-256. Previous app backed up at
`/private/tmp/universe-walking-79469e7227b64f70-before-reliability-20261023`.
Saved State and boot files were not overwritten. Original badge is still on
the prior build and needs the same update before a meaningful retest.

2026-10-24: original badge `f95119f417c67d7e` identified by USB ID and updated
to the same reliability build. All nine files read back with matching SHA-256;
full host suite still passes 39 tests. Prior app backed up at
`/private/tmp/universe-walking-f95119f417c67d7e-before-reliability-20261024`.
Saved State and boot files were not overwritten. Both badges are now updated;
the revised two-badge hardware test is pending.

Retest result: both badges enter Hold steady but never show Synced despite
repeated long holds. It was not established whether Exchange was created. The existing
host pairing stand-in does not model the real firmware's hold/connect logic.
Do not infer a firmware fix from those tests or ship another guessed patch.

`tools/inspect_pairing.py` is prepared for one local Terminal run. It reads
pairing-module metadata and any available source/bytecode from the firmware
package, plus Walking's own error/state diagnostics, into `diagnostics/<id>`.
It does not install anything on the badge. Next step is to inspect that real
implementation and compare its required update sequence with Merge Conflict.

Inspection result (original badge): the pairing library is frozen; no source
or bytecode file was readable. The report captured its actual exported classes
and methods. Saved progress contains only own ID `f95119f417c67d7e`: 124 steps,
empty last_sync. There is no saved partner contribution, so prior apparent
syncs did not establish a durable count exchange on this badge.

Specific sequence difference to isolate: stock Merge Conflict calls pump,
then Proximity.update while idle; Link.update is called only in its linked
branch. Walking currently calls Link.update after the idle proximity update
as well. No patch deployed for this hypothesis. Maggie was asked to test
stock Merge Conflict on both devices as a hardware control first.

Control result: Maggie confirmed Merge Conflict pairs successfully on these
same two badges. Walking's adapter was changed to capture the linked state
after pump, then call Link.update only in that linked branch; idle frames call
Proximity.update alone, exactly matching the working reference. Two boundary
sequence tests failed before this change and pass after it. Full suite: 41
tests pass. This is a targeted hardware experiment, not a confirmed radio fix;
only sync_link.py needs updating on each device before the next real test.

The original badge `f95119f417c67d7e` has received that single-file loop update.
All nine app files now match local SHA-256. Its previous adapter was backed up
at `/private/tmp/walking-f95119f417c67d7e-before-linked-loop-20261024.py`.
The second badge `79469e7227b64f70` still needs this same one-file update.

The second badge `79469e7227b64f70` has now also received the loop update.
All nine app files match local SHA-256 on that badge too. Its previous adapter
is backed up at `/private/tmp/walking-79469e7227b64f70-before-linked-loop-20261024.py`.
Both badges are ready for the focused native-pairing retest. No saved State
or boot files were overwritten.

That retest also failed: Maggie saw Hold steady followed by rapidly changing
states, with no Synced screen or team total. The initial mpremote live capture
lost its USB handle with errno 6. A reconnecting, receive-only host listener
then completed a 60-second capture on the original badge, but received no app
output. This does not establish where native connection or exchange fails.

Next diagnostic: add a bounded RAM trace on the original badge only. Record
native connection/GATT events through the stock journal hook (returning its
values unchanged), UI state transitions, capacity, transmitted/received step
packets, and errors. Exclude nearby advertisements. Write only on normal HOME
exit to `/system/apps/walking/pairing-trace.log`, readable afterward on BADGER
as `apps/walking/pairing-trace.log`. No serial capture is needed. The second
badge needs no update because the protocol and handshake are unchanged.

44 host tests pass, including transparent journal callbacks, bounded trace
storage and failure handling. Hardware still needs the trace-producing trial.

Maggie completed two holds, pressed HOME, and remounted the original badge.
The installed diagnostic files are present but no trace file was created in
the app directory. Whether HOME ran cleanup or the app directory was writable
is unproven. Therefore no radio conclusion can be drawn from this attempt.
Capture v2 checkpoints automatically every two seconds, including the first
frame, with `/state/walking_pairing.log` as a fallback if the app directory is
unwritable. The existing serial collector now includes both trace locations.
46 host tests pass, including saving without exit and the read-only fallback.
Only pairing_trace.py needs updating on the original badge for the next trial.

The next trial produced `/state/walking_pairing.log`, collected successfully
by the serial inspector. The app-directory trace is still absent. Actual
evidence: at ticks 23417 the original badge connected to the correct peer,
reported capacity 19, and accepted one 12-byte outgoing STATE. At ticks 23588
Walking called leave with "Hold together to retry". This is only 171 ms later,
so it is the link-loss branch, not the eight-second exchange timeout. A native
disconnect IRQ followed at 23657. Repeats at 32878/32958, 42194/42365 and
51508/51599 show the same early abort. No incoming step packet was recorded.

Working-reference difference: Merge Conflict's first queued message is `H`
plus its packed 53-by-7 chart: 1 + ceil(371/4) = 94 bytes. Its flush function
skips that message until capacity reaches 94. Walking instead begins at 19,
then explicitly calls leave on the next unlinked observation. Hypothesis:
the small packet starts the application exchange during transport setup;
that transient state change then makes Walking cancel the native connection.
This is not established as a firmware bug, and the native source remains
unavailable. A capacity threshold is a reference-derived experiment, not an
independent guarantee of GATT readiness.

Small change: before creating Exchange, wait for the same 94-byte capacity
used by the working reference, continuing native Link.update while linked.
No exchange exists yet to trigger the loss/leave path during setup. The step
packet format stays unchanged. Two new boundary tests fail before the guard
and pass after it: no publication at initial capacity, and no cancellation
through a setup state change followed by successful exchange. Full suite:
48 tests pass. Trace snapshots now include capacity to verify this on hardware.
Both badges need the adapter and trace files before a meaningful retest.

Original badge `f95119f417c67d7e` now has both updated files, read back with
matching SHA-256. Previous versions are backed up in
`/private/tmp/walking-f95119f417c67d7e-before-capacity-wait-20261024/`.
The observed failing trace is preserved in
`diagnostics/f95119f417c67d7e/pairing-before-capacity-wait.log`.
Second badge update and the two-badge physical retest remain outstanding.

Second badge `79469e7227b64f70` has now received sync_link.py and
pairing_trace.py. All ten app files read back with matching SHA-256; 48 host
tests still pass. Its previous adapter is backed up at
`/private/tmp/walking-79469e7227b64f70-before-capacity-wait-20261024/sync_link.py`.
Both badges now have the capacity-wait experiment and automatic internal
tracing. Saved progress and firmware were not overwritten. Physical retest
is pending; no claim of successful BLE exchange yet.

Hardware result: Maggie replied "yay it worked!" after being asked to verify
both badges show Synced and the same team total. This confirms the first
reported successful two-badge exchange with the capacity-wait build.
Remaining regression checks: no live sharing after separation; resync without
walking leaves the total unchanged; walking on one badge changes only its own
live count until another sync; confirmed totals survive reopening the apps.

Follow-up hardware result: repeat sync failed. Maggie reports that the
second badge still shows its previous partner contribution and team total.
USB identifies that connected badge as `79469e7227b64f70`; it is in normal
mode, with no BADGER volume mounted. The existing collector has been requested
to read its automatic internal trace and State. Do not assume this is a
cooldown/rearming failure, stale packets, or a missing ACK until that trace
distinguishes the stage. No further app change has been made for this result.

Second-badge trace received. First session confirmed 89 own + 124 partner =
213. Two later sessions received partner STATE=144 and saved counts=233,
but last_sync remains 213 because no matching partner ACK arrived. Each was
aborted just 67 ms after Exchange creation (69928->69995, 77534->77601).
The first success grace also lasted only 34 ms (22493->22527), and 100 ms
send retry checks fired between frames only 33 ms apart. A later stale
"Synced" notice reappeared while unlinked. These timer observations cannot
be explained by the intended thresholds.

Read-only clock probe on the same firmware returned correct literal results:
ticks_diff(69995,69928)=67 and the other captured samples equal subtraction;
period=1073741824. Thus a broken builtin has not been established. Preserve
the failure trace and State as `pairing-repeat-failure.log` and
`progress-after-repeat-failure.json` in this badge's diagnostics directory.

Added diagnostic-only records for the actual send timer inputs/results,
timeout branch, disconnect branch and leave timestamps. These distinguish
the abort route and stored values without changing thresholds or handshake.
48 host tests pass. Updated only sync_link.py on second badge
`79469e7227b64f70`, read back with matching SHA-256. Prior adapter backed up
at `/private/tmp/walking-79469e7227b64f70-before-timer-trace-20261024.py`.
No second update is needed on the original badge for this diagnostic trial.

Timer trace proves the mismatch: at frame 18721, previous frame 18687,
ticks_diff returned 4464 instead of 34. At frame 18766, started 18687, the
explicit timeout branch logged 9776 instead of 79 and immediately left.
Preserved as `diagnostics/79469e7227b64f70/pairing-frame-clock-failure.log`.
The earlier inference that a short wall-time abort must be the disconnect
branch is therefore invalid; the bad timer could fire the timeout branch.

MicroPython documents ticks_diff inputs as tokens from ticks_ms/us/cpu.
Its C implementation directly applies MP_OBJ_SMALL_INT_VALUE to its arguments,
assuming the representation supplied by those functions. See
https://docs.micropython.org/en/latest/library/time.html#time.ticks_diff and
https://github.com/micropython/micropython/blob/master/extmod/modtime.c .
Badge frame timestamps are outside that API contract. The exact representation
used by the frozen badge getter is uninspected, but the live mismatch is proven.
Stock Merge Conflict subtracts badge.ticks timestamps directly.

Fix only the adapter's frame-time arithmetic: direct subtraction for retries,
timeout, ACK grace, cooldown renewal, notices and success animation. Keep
the entrypoint's time.ticks_ms/ticks_diff pair, native pairing and step packets
unchanged. Keep timer trace records, now logging the correct frame difference.

Two new regression tests fail before the fix by enforcing the documented
clock boundary, and pass after it. They use the captured timestamps and check
100 ms retries, a full 8 s timeout, 1 s ACK grace, 2.8 s success feedback and
notice expiry. The app harness now distinguishes badge frame values from
MicroPython tick tokens. A full entrypoint test covers first sync, partner
adding 20 steps, repeat sync, and another unchanged-total sync. 51 tests pass.
The timer fix has not yet been installed: second badge disk is not mounted.

Second badge `79469e7227b64f70` now has the frame-clock fix in sync_link.py.
All ten app files read back with matching SHA-256; 51 tests still pass.
Prior adapter backed up at
`/private/tmp/walking-79469e7227b64f70-before-frame-clock-fix-20261024.py`.
Original badge `f95119f417c67d7e` still needs the same single-file update.
Both badges must use the corrected timers before the next physical retest.

Original badge `f95119f417c67d7e` has now received the same single-file timer
fix. All ten app files read back with matching SHA-256. Prior adapter backed
up at `/private/tmp/walking-f95119f417c67d7e-before-frame-clock-fix-20261024.py`.
Both badges now run the same corrected frame-time arithmetic; saved State and
firmware were not overwritten. Physical repeat-sync verification is pending.

Physical result after both timer fixes: Maggie confirmed "amazing! it's all
working! yay" after the requested initial sync, separation, adding steps to
one badge, and second sync showing the same updated team total on both.
The reported repeat-sync failure is resolved on the real two-badge setup.
Final code validation remains 51 passing host tests; installation was verified
by SHA-256 on both badges. No further change was made after this hardware pass.
