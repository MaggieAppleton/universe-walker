# Walking

Combine your walking steps with a partner by holding two Universe 2026 badges together.

Walk independently with Walking open on both badges. Hold the badges back to
back and keep them still while the pairing indicator fills. Both screens show
a full-screen animated **Synced**, the combined score, and **Move badges apart**.
Separate the badges before another sync. Pairing uses the same firmware Link
and Proximity APIs as Merge Conflict; no button is needed to start syncing.

The normal screen always shows **Your steps** as the large live number.
**Team total** is the combined score from the last completed sync, and
**Partner at last sync** is the partner's contribution at that point. Until
the first completed sync with this version, these two fields show `--`.

After another walk, sync again to update each other's count. Repeating a sync
without walking does not add the same steps again. While apart, only your
personal count changes; the team total updates when you sync again.

Bluetooth sync is under hardware test. Shared goal celebrations are not
included yet.

Open Walking from the badge menu and walk with the badge in its normal
lanyard position. Keep the app open. Press HOME to save and return
to the menu; reopen Walking to check saved progress. The hardware pedometer
can take several steps to start reporting, and a counter alone does not
prove step accuracy.

Progress is saved every two seconds while steps change and on a normal exit.
A sudden loss of power can lose the most recent two seconds. Sync snapshots
are saved before being acknowledged. Existing sensor
steps are used as a baseline when the app opens, so steps taken while it is
closed are not credited by this version.

## Install and test

In USB disk mode, copy this entire `walking` directory into `apps` at the
root of the BADGER volume. That volume maps to the badge's `/system` tree.
Eject the volume, press RESET once, then open Walking from the menu.

The first badge has already counted 23 steps and preserved them across a
normal exit. For the two-badge test:

1. Open Walking on both badges and note each count.
2. Hold them back to back until both show Synced and the sum of those counts.
3. Separate and sync again without walking. The total should stay the same.
4. Move one badge while the other stays still: only that badge's personal
   count should increase. Neither team total should change until the next sync.
5. Exit and reopen both apps. Personal counts and the confirmed team score
   should remain saved.

The first successful exchange fixes the two-player team. A different partner
is rejected. Both builds use the same demo game ID; there is no new-game or
team-reset control in this version.

No Wi-Fi, credentials, external sensors, or firmware changes are required.
The app reads the enabled onboard LSM6DS3TR-C pedometer over the documented
internal I2C1 bus on GPIO18/19. It does not reset or configure that sensor.

Onboard progress uses the `walking_demo` State key. Host verification:

```sh
python3 -m unittest discover -s tests -v
```

If a frame fails, Walking pauses visibly and writes the latest exception to
`/state/walking_error.txt`. A local `mpremote fs cat` can read that diagnostic.
