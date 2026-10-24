"""Check the actual app flow across its hardware boundaries."""

import unittest
import io
from contextlib import redirect_stdout

from badge_harness import BadgeHarness, OWN, PEER
from sync_protocol import Exchange


class AppTests(unittest.TestCase):
    def test_back_touch_does_not_return_home(self):
        with BadgeHarness() as app:
            app.back = True
            self.assertIsNone(app.frame(100))
            self.assertIn("Your steps", app.screen.texts)

    def test_live_personal_steps_do_not_change_last_synced_team_total(self):
        with BadgeHarness() as app:
            app.frame(250, raw=0)
            app.frame(500, raw=5)
            self.assertIn("28", app.screen.texts)
            self.assertIn("Team total: 40", app.screen.texts)
            self.assertIn("Partner at last sync: 17", app.screen.texts)
            app.frame(2500, raw=5)
            self.assertEqual(app.saved["counts"][OWN.hex()], 28)
            self.assertEqual(app.saved["last_sync"], {OWN.hex(): 23, PEER.hex(): 17})
            self.assertEqual(app.app["counts"][OWN.hex()], 28)

    def test_shared_display_changes_only_after_ack_and_shows_confirmation(self):
        with BadgeHarness() as app:
            sync = app.app["sync"]
            sync.link.linked = True
            app.frame(0)
            peer = Exchange(PEER.hex(), OWN.hex(), {PEER.hex(): 20}, lambda counts: None)
            peer.receive(sync.link.outgoing[0])
            sync.link.incoming.append(peer.packets()[0])
            app.frame(100)
            self.assertIn("Team total: 40", app.screen.texts)
            sync.link.incoming.append(peer.packets()[1])
            app.frame(200)
            self.assertIn("Synced", app.screen.texts)
            self.assertIn("43", app.screen.texts)
            self.assertIn("Move badges apart", app.screen.texts)
            self.assertEqual(app.saved["last_sync"], {OWN.hex(): 23, PEER.hex(): 20})

    def test_sync_snapshot_preserves_steps_taken_during_exchange(self):
        with BadgeHarness() as app:
            app.frame(250, raw=0)
            app.frame(500, raw=5)
            app.app["save_sync"]({OWN.hex(): 23, PEER.hex(): 20})
            self.assertEqual(app.saved["counts"][OWN.hex()], 28)
            self.assertEqual(app.saved["last_sync"], {OWN.hex(): 23, PEER.hex(): 17})
            app.app["confirm_sync"]({OWN.hex(): 23, PEER.hex(): 20})
            self.assertEqual(app.saved["counts"][OWN.hex()], 28)
            self.assertEqual(app.saved["last_sync"], {OWN.hex(): 23, PEER.hex(): 20})

    def test_repeat_sync_updates_partner_then_leaves_total_unchanged_without_walking(self):
        with BadgeHarness() as app:
            sync = app.app["sync"]

            def hold_and_separate(now, partner_steps):
                sync.link.linked = True
                sync.link.leaving = False
                app.frame(now)
                peer = Exchange(PEER.hex(), OWN.hex(), {PEER.hex(): partner_steps}, lambda counts: None)
                peer.receive(sync.link.outgoing[-1])
                sync.link.incoming.extend(peer.packets())
                app.frame(now + 100)
                peer.receive(sync.link.outgoing[-1])
                self.assertTrue(peer.done)
                self.assertIn("Synced", app.screen.texts)
                self.assertEqual(sync.synced_total, peer.total)
                app.frame(now + 1100)
                self.assertTrue(sync.link.leaving)
                sync.link.linked = False
                sync.proximity.apart = True
                app.frame(now + 1200)
                sync.proximity.apart = False

            hold_and_separate(0, 17)
            self.assertEqual(sum(app.saved["last_sync"].values()), 40)
            hold_and_separate(3000, 37)
            self.assertEqual(app.saved["last_sync"], {OWN.hex(): 23, PEER.hex(): 37})
            hold_and_separate(6000, 37)
            self.assertEqual(sum(app.saved["last_sync"].values()), 60)
            app.frame(9000)
            self.assertIn("Team total: 60", app.screen.texts)
            self.assertIn("Partner at last sync: 37", app.screen.texts)

    def test_failed_confirmation_save_does_not_show_success(self):
        with BadgeHarness() as app:
            sync = app.app["sync"]
            sync.link.linked = True
            app.frame(0)
            peer = Exchange(PEER.hex(), OWN.hex(), {PEER.hex(): 20}, lambda counts: None)
            peer.receive(sync.link.outgoing[0])
            sync.link.incoming.append(peer.packets()[0])
            app.frame(100)
            app.fail_save = True
            sync.link.incoming.append(peer.packets()[1])
            with redirect_stdout(io.StringIO()):
                app.frame(200)
            self.assertNotIn("Synced", app.screen.texts)
            self.assertIsNone(sync.success_age(200))
            self.assertEqual(app.saved["last_sync"], {OWN.hex(): 23, PEER.hex(): 17})


if __name__ == "__main__":
    unittest.main()
