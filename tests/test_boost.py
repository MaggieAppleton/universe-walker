import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "badge" / "apps" / "walking"))
from boost import HoldBoost, LIMIT, LongPress, room, spare  # noqa: E402

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


class LimitTests(unittest.TestCase):
    def test_room_counts_only_unsynced_steps(self):
        self.assertEqual(room(100, 100), 9957)
        self.assertEqual(room(100 + 9957, 100), 0)
        self.assertEqual(room(20000, 100), 0)

    def test_spare_counts_only_unsynced_steps(self):
        self.assertEqual(spare(150, 100), 50)
        self.assertEqual(spare(100, 100), 0)


class LongPressTests(unittest.TestCase):
    def test_fires_once_after_three_seconds(self):
        press = LongPress()
        fired = [t for t in range(0, 6001, 50) if press.update(True, t)]
        self.assertEqual(fired, [3000])

    def test_short_hold_never_fires_and_release_rearms(self):
        press = LongPress()
        self.assertFalse(any(press.update(True, t) for t in range(0, 2951, 50)))
        press.update(False, 3000)
        self.assertFalse(press.update(True, 3050))
        self.assertTrue(press.update(True, 6050))

    def test_countdown_appears_after_the_hint_delay(self):
        press = LongPress()
        press.update(True, 0)
        self.assertIsNone(press.remaining(100))
        press.update(True, 1200)
        self.assertEqual(press.remaining(1200), 1800)


class HoldUpInAppTests(unittest.TestCase):
    def test_holding_up_stops_at_the_unsynced_limit(self):
        with BadgeHarness() as badge:
            badge.frame(0)
            badge.up = True
            for now in range(0, 20001, 50):
                badge.frame(now)
            badge.up = False
            badge.frame(23000)
            self.assertEqual(badge.saved["counts"][OWN.hex()], 23 + LIMIT)

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


class HoldDownInAppTests(unittest.TestCase):
    def test_holding_down_removes_only_unsynced_steps(self):
        with BadgeHarness() as badge:
            badge.frame(0)
            badge.up = True
            for now in range(0, 3001, 50):
                badge.frame(now)
            badge.up = False
            badge.down = True
            for now in range(3050, 20001, 50):
                badge.frame(now)
            badge.down = False
            badge.frame(23000)
            self.assertEqual(badge.saved["counts"][OWN.hex()], 23)

    def test_tap_down_removes_one_step(self):
        with BadgeHarness() as badge:
            badge.frame(0)
            badge.up = True
            for now in range(0, 3001, 50):
                badge.frame(now)
            badge.up = False
            badge.frame(3050)
            before = badge.app["counts"][OWN.hex()]
            badge.down = True
            badge.frame(3100)
            badge.down = False
            badge.frame(3150)
            self.assertEqual(badge.app["counts"][OWN.hex()], before - 1)


class ResetInAppTests(unittest.TestCase):
    def hold_select(self, badge, until):
        badge.frame(0)
        badge.select = True
        for now in range(0, until + 1, 50):
            badge.frame(now)
        badge.select = False
        badge.frame(until + 50)

    def test_three_second_select_clears_own_and_team(self):
        with BadgeHarness() as badge:
            self.hold_select(badge, 3000)
            self.assertEqual(badge.saved, {"counts": {OWN.hex(): 0}, "game": 0x2026, "last_sync": {}})
            self.assertIn("Counts reset to zero", badge.screen.texts)

    def test_shorter_select_hold_keeps_counts(self):
        with BadgeHarness() as badge:
            self.hold_select(badge, 2900)
            self.assertEqual(badge.saved["counts"][OWN.hex()], 23)
            self.assertEqual(badge.saved["last_sync"][OWN.hex()], 23)

    def test_countdown_shows_while_holding(self):
        with BadgeHarness() as badge:
            badge.frame(0)
            badge.select = True
            badge.frame(0)
            badge.frame(1500)
            self.assertIn("Keep holding to reset... 2", badge.screen.texts)


if __name__ == "__main__":
    unittest.main()
