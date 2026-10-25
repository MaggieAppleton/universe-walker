"""Reset one connected badge for a new demo, starting in disk or normal USB mode."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from badge_usb import prepare_badge, remote, restart

ROOT = Path(__file__).resolve().parents[1]
MAGGIE, MARTIN = "f95119f417c67d7e", "79469e7227b64f70"
WEARERS = {MAGGIE: "Maggie", MARTIN: "Martin"}
MARKER = "WALKING_RESET_REPORT "
READ = '''
import binascii, machine, json
from badgeware import State
state = {}
State.load("walking_demo", state)
goal = None
with open("/system/apps/walking/walking_ui.py") as source:
    for line in source:
        if line.startswith("GOAL ="):
            goal = int(line.split("=", 1)[1].strip())
print("WALKING_RESET_REPORT " + json.dumps({
    "device_id": binascii.hexlify(machine.unique_id()).decode(), "goal": goal, "state": state
}))
'''


def seed_state(device_id, profile="near-goal"):
    if device_id not in WEARERS:
        raise ValueError("This is not one of Maggie and Martin's two known badges")
    if profile not in ("near-goal", "zero"):
        raise ValueError("Choose near-goal or zero")
    return {"counts": {MAGGIE: 0, MARTIN: 9900 if profile == "near-goal" else 0},
            "game": 0x2026, "last_sync": {}}


def report(output):
    lines = [line[len(MARKER):] for line in output.splitlines() if line.startswith(MARKER)]
    if len(lines) != 1:
        raise RuntimeError("Badge did not return a reset report: " + output[-500:])
    return json.loads(lines[0])


def reset_connected(profile, backup_root=ROOT / "diagnostics", volume=Path("/Volumes/BADGER")):
    port = prepare_badge(volume)
    failure = None
    try:
        before = report(remote("connect", port, "exec", READ))
        own = before["device_id"]
        wanted = seed_state(own, profile)
        if before["goal"] != 10000:
            raise ValueError("Install the current 10,000-step-goal app before resetting the demo")
        folder = backup_root / own
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = folder / ("before-demo-reset-" + stamp + ".json")
        backup.write_text(json.dumps(before["state"], indent=2) + "\n")
        write = '''
import binascii, machine, json
from badgeware import State
assert binascii.hexlify(machine.unique_id()).decode() == %r, "Badge changed; refusing reset"
wanted = json.loads(%r)
State.save("walking_demo", wanted)
actual = {}
State.load("walking_demo", actual)
assert actual == wanted, "Reset readback did not match"
print("WALKING_RESET_REPORT " + json.dumps(actual))
''' % (own, json.dumps(wanted))
        actual = report(remote("connect", port, "resume", "exec", write))
        if actual != wanted:
            raise RuntimeError("Saved reset state did not match")
        port = restart(port)
        after = report(remote("connect", port, "exec", READ))
        if after != {"device_id": own, "goal": 10000, "state": wanted}:
            raise RuntimeError("Reset did not survive a restart; saved progress is not verified")
        receipt = {"device_id": own, "wearer": WEARERS[own], "profile": profile,
                   "goal": 10000, "state": wanted, "backup": str(backup), "verified_after_restart": True}
    except BaseException as error:
        failure = error
        raise
    finally:
        # Reading the REPL interrupts the launcher: restart to finish at Home,
        # with no in-memory pairing session or suspended app to overwrite state.
        try:
            restart(port)
        except Exception as error:
            if failure is None:
                raise
            print("Could not also restart the badge after the error: " + str(error), file=sys.stderr)
    (folder / ("demo-reset-" + stamp + ".json")).write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=("near-goal", "zero"), help="Martin 9,900/Maggie 0, or both 0")
    parser.add_argument("--volume", type=Path, default=Path("/Volumes/BADGER"), help="Mounted BADGER disk")
    args = parser.parse_args(argv)
    print("Keep Walking closed on both badges until both have been reset.", flush=True)
    result = reset_connected(args.profile, volume=args.volume)
    own = result["device_id"]
    print("Reset %s (%s): %s personal steps; goal 10,000; no confirmed sync." % (
        result["wearer"], own, format(result["state"]["counts"][own], ",")))
    print("Verified after restart. Previous progress:", result["backup"])
    print("Run the same profile on the other badge BEFORE opening Walking on either badge.")


def cli(argv=None):
    try:
        main(argv)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print("Demo reset failed:", error, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
