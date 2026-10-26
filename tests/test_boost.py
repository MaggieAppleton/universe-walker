import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "badge" / "apps" / "walking"))
from boost import HoldBoost  # noqa: E402

from badge_harness import BadgeHarness, OWN  # noqa: E402


def hold(seconds, frame_ms=50, boost=None):
    boost = boost or HoldBoost()
    total = sum(boost.update(True, t) for t in range(0, int(seconds * 1000) + 1, frame_ms))
    boost.update(False, int(seconds * 1000) + frame_ms)
    return total


class HoldBoostTests(unittest.TestCase):
    def test_tap_adds_one_step(self):
        self.assertEqual(hold(0.1), 1)

    def test_accidental_second_long_press_stays_small(self):
        self.assertLess(hold(1), 5)
        self.assertLess(hold(2), 40)

    def test_ten_and_a_half_seconds_reaches_the_goal_range(self):
        self.assertTrue(9000 <= hold(10.5) <= 10001)

    def test_total_does_not_depend_on_frame_rate(self):
        self.assertEqual(hold(6, frame_ms=16), hold(6, frame_ms=100))

    def test_release_restarts_the_slow_ramp(self):
        boost = HoldBoost()
        hold(8, boost=boost)
        self.assertEqual(hold(0.4, boost=boost), 1)


class HoldUpInAppTests(unittest.TestCase):
    def test_holding_up_adds_saved_personal_steps(self):
        with BadgeHarness() as badge:
            badge.frame(0)
            badge.up = True
            for now in range(0, 3001, 50):
                badge.frame(now)
            badge.up = False
            badge.frame(6000)
            own = badge.saved["counts"][OWN.hex()]
            self.assertGreater(own, 23 + 30)
            self.assertEqual(badge.saved["last_sync"][OWN.hex()], 23)


if __name__ == "__main__":
    unittest.main()
