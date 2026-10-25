"""Compatibility shortcut for reset_demo.py near-goal."""

import sys

from reset_demo import MAGGIE, MARTIN, WEARERS, cli, seed_state

if __name__ == "__main__":
    cli(["near-goal", *sys.argv[1:]])
