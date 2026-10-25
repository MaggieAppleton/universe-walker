"""Host USB operations shared by the badge reset and diagnostic commands."""

import subprocess
import sys
import time
from pathlib import Path


def remote(*arguments):
    result = subprocess.run([sys.executable, "-m", "mpremote", *arguments],
                            capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def wait_for_badge(timeout=20):
    deadline = time.monotonic() + timeout
    while True:
        ports = [line.split()[0] for line in remote("devs").splitlines() if "2e8a:1101" in line.lower()]
        if len(ports) > 1:
            raise RuntimeError("Connect one badge at a time")
        if ports:
            return ports[0]
        if time.monotonic() >= deadline:
            raise RuntimeError("No badge serial port found. Press RESET once and run again")
        time.sleep(0.25)


def restart(port):
    remote("connect", port, "resume", "reset")
    # The no-follow reset command returns before the board's USB restarts.
    time.sleep(0.8)
    return wait_for_badge()


def prepare_badge(volume=Path("/Volumes/BADGER")):
    if volume.exists():
        if not (volume / "apps/walking").is_dir():
            raise RuntimeError("The selected disk does not contain the Walking app")
        if sys.platform != "darwin":
            raise RuntimeError("Eject the badge disk, press RESET once, then run again in normal USB mode")
        print("Ejecting BADGER before changing saved progress...", flush=True)
        subprocess.run(["diskutil", "eject", str(volume)], check=True,
                       capture_output=True, text=True, timeout=20)
    # Leave disk mode and discard live app/link state before writing /state.
    return restart(wait_for_badge())
