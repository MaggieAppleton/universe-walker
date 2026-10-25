"""Check the screen copy each sync state maps to."""

import unittest
from unittest.mock import patch

from badge_harness import BadgeHarness

IDLE = "Hold badges back to back"


class WalkingUITests(unittest.TestCase):
    def test_native_total_is_lifted_and_has_room_for_bottom_ink(self):
        with BadgeHarness() as app:
            ui = app.app["ui"]
            # A 70px native line was drawn at y=22 with the installed baseline 78.
            # Lift it to y=19, retaining 4px below its measured line box.
            def native_measure(value, font_size=14):
                advance = 6.21 if value == "0000000000" else len(value) * 0.6
                return advance * font_size, font_size

            with patch.object(app.screen, "measure_text", side_effect=native_measure):
                for total, y, height in ((0, 19, 74), (9900, 19, 74), (10000, 19, 74),
                                         (1000025, 33.5185185185, 56)):
                    with self.subTest(total=total), patch.object(app.screen, "text", wraps=app.screen.text) as draw:
                        ui.hud(ui.model(0, total, total, IDLE))
                        number = draw.call_args_list[1].args
                        self.assertEqual(len(number), 3, "Use an explicit padded drawing rectangle")
                        value, bounds, size = number
                        self.assertAlmostEqual(bounds.y, y)
                        self.assertAlmostEqual(bounds.h, height)
                        width, measured_height = native_measure(value, size)
                        self.assertGreaterEqual(bounds.h - measured_height, 4 - 1e-6)
                        self.assertGreaterEqual(bounds.x, 20 - 1e-6)
                        self.assertLessEqual(bounds.x + width, 300 + 1e-6)

    def test_seeded_sync_stays_below_goal_until_ten_thousand(self):
        for device_id in ("f95119f417c67d7e", "79469e7227b64f70"):
            with self.subTest(device=device_id), BadgeHarness() as app:
                ui = app.app["ui"]
                ui.set_badge(device_id)
                own, partner = (0, 9900) if device_id.startswith("f951") else (9900, 0)
                self.draw(app, own, None, None, IDLE)
                self.draw(app, own, 9900, partner, "Synced", success_age=0, success_total=9900)
                texts = self.draw(app, own, 9900, partner, IDLE, now=5000)
                self.assertIn("of 10,000 shared steps", texts)
                self.assertNotIn("Goal reached", texts)
                self.assertNotIn("You made it!", texts)
                self.assertFalse(ui.model(own, 9999, 9999 - own, IDLE).reached)
                self.assertTrue(ui.model(own, 10000, 10000 - own, IDLE).reached)

    def draw(self, app, *args, now=1000, **kwargs):
        app.badge.ticks = now
        app.screen.texts.clear()
        app.app["ui"].draw(*args, **kwargs)
        return app.screen.texts

    def test_first_use_has_no_invented_total(self):
        with BadgeHarness() as app:
            texts = self.draw(app, 0, None, None, IDLE)
            self.assertIn("0", texts)
            self.assertIn("Your steps, not synced yet", texts)
            self.assertIn("47", self.draw(app, 47, None, None, IDLE))
            self.assertNotIn("of 10,000 shared steps", texts)

    def test_pending_steps_stay_apart_from_the_shared_total(self):
        with BadgeHarness() as app:
            texts = self.draw(app, 4000, 6000, 3000, IDLE)
            self.assertEqual(texts, ["Hold badges back to back to sync", "6,000", "+1,000", "of 10,000 shared steps"])

    def test_large_local_addition_fits_with_the_shared_total(self):
        for shared, added in ((9900, 5), (9900, 94), (9900, 1000), (1000025, 12345)):
            with self.subTest(shared=shared, added=added), BadgeHarness() as app:
                ui = app.app["ui"]
                rendered = []
                def record(value, *args):
                    rendered.append((value, args, app.screen.pen))
                with patch.object(app.screen, "text", side_effect=record):
                    ui.hud(ui.model(added, shared, shared, IDLE))
                _, white, yellow, *_ = rendered
                self.assertEqual(white[0], format(shared, ","))
                self.assertEqual(yellow[0], "+" + format(added, ","))
                self.assertEqual(white[2], ui.WHITE)
                self.assertEqual(yellow[2], ui.AMBER)
                left, left_size = white[1]
                right, right_size = yellow[1]
                self.assertEqual(left_size, right_size)
                self.assertEqual(left.y, right.y)
                self.assertGreater(right.x, left.x)
                self.assertGreaterEqual(left.x, 20 - 1e-6)
                width, height = app.screen.measure_text(yellow[0], font_size=right_size)
                self.assertLessEqual(right.x + width, 300 + 1e-6)
                self.assertGreaterEqual(right.h - height, 4 - 1e-6)
                if shared == 9900:
                    self.assertFalse(ui.model(added, shared, shared, IDLE).reached)

    def test_confirmed_sync_clears_the_large_local_addition(self):
        with BadgeHarness() as app:
            self.assertIn("+5", self.draw(app, 5, 9900, 9900, IDLE))
            texts = self.draw(app, 5, 9925, 9920, "Synced", success_age=0, success_total=9925)
            self.assertIn("9,925", texts)
            self.assertNotIn("+5", texts)
            texts = self.draw(app, 5, 9925, 9920, IDLE, now=5000)
            self.assertIn("9,925", texts)
            self.assertNotIn("+0", texts)

    def test_success_shows_the_confirmed_gain_once(self):
        with BadgeHarness() as app:
            self.draw(app, 4000, 6000, 3000, IDLE)
            texts = self.draw(app, 4000, 8500, 4500, "Synced", success_age=0, success_total=8500)
            self.assertEqual(texts, ["Synced!", "8,500", "shared steps", "+2,500 together", "Move badges apart"])
            self.draw(app, 4000, 8500, 4500, "Move badges apart", now=5000)
            texts = self.draw(app, 4000, 8500, 4500, "Synced", success_age=0, success_total=8500, now=9000)
            self.assertIn("Up to date", texts)
            self.assertIn("No new steps since last sync", texts)

    def test_goal_needs_a_confirmed_total(self):
        with BadgeHarness() as app:
            self.assertNotIn("Goal reached", self.draw(app, 4750, 9700, 4850, IDLE))
            texts = self.draw(app, 4750, 10000, 5250, "Synced", success_age=0, success_total=10000)
            self.assertIn("+300 together", texts)
            texts = self.draw(app, 4750, 10000, 5250, IDLE, now=4000)
            self.assertEqual(texts, ["You made it!", "10,000 steps together"])
            texts = self.draw(app, 4750, 10000, 5250, IDLE, now=20000)
            self.assertIn("Goal reached", texts)

    def test_pairing_phases_and_partner_name(self):
        with BadgeHarness() as app:
            ui = app.app["ui"]
            self.assertIn("Hold steady", self.draw(app, 150, 300, 150, "Hold steady", progress=0.5))
            self.assertIn("Found Martin's badge", self.draw(app, 150, 300, 150, "Hold steady", progress=1))
            ui.set_badge("79469e7227b64f70")
            self.assertIn("Found Maggie's badge", self.draw(app, 150, 300, 150, "Hold steady", progress=1))
            self.assertIn("Sending your +25", self.draw(app, 175, 300, 150, "Syncing..."))
            texts = self.draw(app, 150, 300, 150, "Hold together to retry")
            self.assertEqual(texts, ["Lost connection", "Hold together to retry", "Still 300 shared steps"])
            self.assertIn("Couldn't sync", self.draw(app, 150, 300, 150, "Could not sync - try again"))
            self.assertIn("Sync paused, reopen Walking", self.draw(app, 150, 300, 150, "Sync paused - reopen Walking"))

    def test_large_totals_use_separators_and_errors_show_recovery(self):
        with BadgeHarness() as app:
            self.assertIn("1,000,025", self.draw(app, 0, 1000025, 500000, IDLE))
            app.screen.texts.clear()
            app.app["ui"].error("MemoryError in app frame")
            self.assertEqual(app.screen.texts, ["Walking paused", "MemoryError in app frame", "Press HOME to return"])


if __name__ == "__main__":
    unittest.main()
