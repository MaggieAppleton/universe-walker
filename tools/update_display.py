"""Update the installed goal and native count rendering; preserve saved progress."""

import ast
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("walking_ui.py", "painter.py")


def constants(source):
    return {node.targets[0].id: node.value.value
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant)}


def apply_update(source, target, backup):
    wanted = {name: (source / name).read_bytes() for name in FILES}
    config = constants(wanted["walking_ui.py"])
    if config.get("GOAL") != 10000 or config.get("COUNT_BASELINE") != 75:
        raise ValueError("Source must contain GOAL = 10000 and COUNT_BASELINE = 75")
    for name, data in wanted.items():
        compile(data, name, "exec")
    previous = {name: (target / name).read_bytes() for name in FILES}
    backup.mkdir(parents=True)
    for name, data in previous.items():
        (backup / name).write_bytes(data)
    for name, data in wanted.items():
        with (target / name).open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if (target / name).read_bytes() != data:
            raise RuntimeError("Badge readback differs for " + name)
    installed = constants((target / "walking_ui.py").read_bytes())
    if installed.get("GOAL") != 10000:
        raise RuntimeError("Installed goal verification failed")


def main():
    volume = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/Volumes/BADGER")
    target = volume / "apps/walking"
    if not target.is_dir():
        raise RuntimeError("Double-tap RESET so the BADGER disk appears, then run again")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / "diagnostics" / ("before-display-update-" + stamp)
    apply_update(ROOT / "badge/apps/walking", target, backup)
    print("Verified on badge disk: goal 10,000; large yellow +steps; fitted count row with 4px bottom drawing room.")
    print("Replaced walking_ui.py and painter.py. Previous files backed up to", backup)
    print("Saved steps and sync progress unchanged. Eject BADGER, then press RESET once.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print("Display update failed:", error, file=sys.stderr)
        raise SystemExit(1)
