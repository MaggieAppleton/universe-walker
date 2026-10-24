"""Collect badge firmware pairing code and Walking diagnostics over USB.

Run from a local Terminal. Reads device files; installs nothing on the badge.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVICE_CODE = r'''
import os, sys, json, machine, binascii, time
report = {
    "device_id": binascii.hexlify(machine.unique_id()).decode(),
    "firmware": repr(sys.implementation),
    "sys_path": list(sys.path),
}
report["clock_probe"] = {
    "time_file": getattr(time, "__file__", "built-in"),
    "ticks_diff": repr(time.ticks_diff),
    "period": time.ticks_add(0, -1) + 1,
    "samples": [[a, b, time.ticks_diff(a, b), a - b] for a, b in (
        (22460, 22427), (22527, 22493), (22572, 22527),
        (69995, 69928), (58257, 22527), (68035, 22527),
    )],
}
paths = []
try:
    from badgeware import link as pairing_library
    report["link_file"] = getattr(pairing_library, "__file__", "frozen")
    report["link_exports"] = dir(pairing_library)
    report["Link_members"] = dir(pairing_library.Link)
    report["Proximity_members"] = dir(pairing_library.Proximity)
    for name in (report["link_file"], "badgeware/link.py", "badgeware/link.mpy"):
        for prefix in ("", "/rom/", "/system/lib/", ".frozen/"):
            paths.append(prefix + name.lstrip("/"))
except Exception as error:
    report["import_error"] = repr(error)
for directory in ("/rom", "/rom/badgeware", ".frozen/badgeware"):
    try:
        entries = os.listdir(directory)
        report[directory] = entries
        if directory.endswith("badgeware"):
            for name in entries:
                if name.endswith((".py", ".mpy")):
                    paths.append(directory + "/" + name)
    except OSError:
        pass
paths.extend(("/state/walking_error.txt", "/state/walking_demo.json",
              "/state/walking_pairing.log", "/system/apps/walking/pairing-trace.log"))
files = []
for path in paths:
    if path in files:
        continue
    try:
        info = os.stat(path)
        if not (info[0] & 0x4000) and info[6] <= 262144:
            files.append(path)
    except OSError:
        pass
report["files"] = files
print("WALKING_PAIRING_REPORT " + json.dumps(report))
'''


def remote(*arguments):
    result = subprocess.run(
        [sys.executable, "-m", "mpremote", *arguments],
        capture_output=True, text=True, timeout=45,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def main():
    ports = [line.split()[0] for line in remote("devs").splitlines() if "2e8a:1101" in line]
    if len(ports) != 1:
        raise RuntimeError("Connect exactly one badge over USB, then run this again.")
    port = ports[0]
    output = remote("connect", port, "resume", "exec", DEVICE_CODE)
    marker = "WALKING_PAIRING_REPORT "
    lines = [line for line in output.splitlines() if line.startswith(marker)]
    if len(lines) != 1:
        raise RuntimeError("Firmware inspection did not return a report: " + output[-1000:])
    report = json.loads(lines[0][len(marker):])
    folder = ROOT / "diagnostics" / report["device_id"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pairing-report.json").write_text(json.dumps(report, indent=2) + "\n")
    for index, path in enumerate(report["files"]):
        name = str(index) + "-" + path.strip("/").replace("/", "_")
        destination = folder / name
        remote("connect", port, "resume", "fs", "cp", ":" + path, str(destination))
        print("Read", path)
    print("Report saved to", folder)
    print("No app, saved progress, or firmware files were changed on the badge.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print("Inspection failed:", error, file=sys.stderr)
        raise SystemExit(1)
