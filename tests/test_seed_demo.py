"""Keep demo seeding explicit and limited to the two known badges."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from seed_demo import seed_state


class DemoSeedTests(unittest.TestCase):
    def test_each_badge_gets_the_same_seed_without_claiming_a_sync(self):
        for own in ("f95119f417c67d7e", "79469e7227b64f70"):
            state = seed_state(own)
            self.assertEqual(state["counts"], {"f95119f417c67d7e": 0, "79469e7227b64f70": 9900})
            self.assertEqual(state["last_sync"], {})
            self.assertEqual(state["game"], 0x2026)

    def test_unknown_badge_is_rejected(self):
        with self.assertRaises(ValueError):
            seed_state("another-badge")


if __name__ == "__main__":
    unittest.main()
