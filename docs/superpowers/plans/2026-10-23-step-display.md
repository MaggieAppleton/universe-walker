# Live step display

**Goal:** Open Walking from the badge menu, take a short walk, and see the
hardware step count increase. Preserve recorded progress on normal exit.

**Scope:** Count while this app is open. Use the documented internal I2C bus
and the enabled LSM6DS3TR-C pedometer verified by the user's Terminal probe.
Use the 2026 runtime's supplied graphics, controls, and app loop. Do not change
firmware, the boot script, or other apps.

- [x] Add `tests/test_steps.py`, then run the tests before implementation.
  Verify first-read baselining, ordinary increments, signed and unsigned
  16-bit wraps, hardware reset handling, and saved totals.
- [x] Implement `badge/apps/walking/steps.py`. At a 250 ms poll interval,
  discard and rebaseline jumps above 32 steps instead of crediting a reset
  as thousands of steps. Run `python3 -m unittest discover -s tests -v`.
- [x] Add `badge/apps/walking/__init__.py`, `README.md`, and a 24x24 PNG icon.
  Render a large count; show a readable error if the sensor cannot be read.
  Save changed progress every two seconds and on HOME/normal exit. A power
  cut can lose the most recent two seconds. Bluetooth is not in this slice.
- [x] Check Python syntax, icon dimensions, app packaging, and the full tests.
- [x] Copy only the Walking app to the existing BADGER app directory. If
  session permissions prevent copying, provide the exact local command.
- [x] User ejects the disk, presses RESET, opens Walking, and walks about
  20 steps. Reopen after a normal exit to check saved progress. Record the
  observed result; host tests do not establish hardware or display success.

Verification: 14 tests pass. The seven new counter tests initially could not
import the missing `steps` module and pass after implementation. All Python
sources parse; the icon is a 24x24 PNG; the app description meets the upstream
README format. Each of the five installed files matches its local SHA-256.

Hardware result: Maggie reported 23 steps, returned HOME, reopened Walking,
and confirmed the count was saved. Step detection, the real display, normal
exit, and saved-state restoration are verified on the first badge.
