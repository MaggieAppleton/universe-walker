"""Check the live-dashboard status carried in the pairing scan response."""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))
import status_beacon as sb
from badge_harness import BadgeHarness, NativeRadio

MAGGIE = "f95119f417c67d7e"
LINK_ADVERT = bytes.fromhex("02010614ffffff424c014fa6f95119f417c67d7e00000000")


class Clock:
    def __init__(self):
        self.now = 0

    def ticks_ms(self):
        return self.now

    def ticks_diff(self, end, start):
        return end - start


def decode(resp):
    """What the laptop reads: one 16-bit service-data AD structure."""
    length, kind, low, high = resp[:4]
    assert kind == 0x16 and (high << 8 | low) == sb.SERVICE_UUID and length == len(resp) - 1
    return sb.unpack(resp[4:])


class WireFormatTests(unittest.TestCase):
    def test_fits_a_legacy_scan_response(self):
        self.assertLessEqual(len(sb.scan_response(sb.pack(MAGGIE, 0, 0, 0, 0, sb.STATUSES[0]))), 31)

    def test_round_trips_every_screen_input(self):
        cases = [
            (0, None, None, "Hold badges back to back", None, None),
            (60, 9900, 9900, "Hold steady", 0.65, None),
            (60, 9900, 9900, "Hold steady", 1.0, None),
            (60, 9900, 9940, "Synced", None, 10000),
            (60, 9900, 9940, "Step sensor unavailable", None, None),
        ]
        for own, team, partner, status, progress, success in cases:
            with self.subTest(status=status, progress=progress):
                got = decode(sb.scan_response(sb.pack(MAGGIE, 7, own, team, partner, status, progress, success)))
                self.assertEqual(got["id"], MAGGIE)
                self.assertEqual(got["status"], status)
                self.assertEqual((got["own"], got["partner"]), (own, partner))
                self.assertEqual(got["team"], success if success is not None else team)
                self.assertEqual(got["success"], success is not None)
                if progress is None:
                    self.assertIsNone(got["progress"])
                else:
                    self.assertAlmostEqual(got["progress"], progress, places=2)

    def test_rejects_other_versions_and_unknown_status_is_none(self):
        payload = sb.pack(MAGGIE, 0, 1, 2, 1, "Something new")
        self.assertIsNone(sb.unpack(payload)["status"])
        self.assertIsNone(sb.unpack(b"\x02" + payload[1:]))
        self.assertIsNone(sb.unpack(payload[:-1]))


class BeaconTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        patcher = patch.object(sb, "time", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.radio = NativeRadio()
        self.link = types.SimpleNamespace(linked=False, linking=False)
        self.beacon = sb.Beacon(self.radio, self.link, MAGGIE)

    def link_advertises(self):
        self.radio.advertise("app", 100000, adv_data=LINK_ADVERT, connectable=True)

    def test_adds_status_to_the_links_own_advert_without_changing_it(self):
        self.beacon.publish(5, None, None, "Hold badges back to back")
        self.assertEqual(self.radio.adverts, [], "Never starts advertising on its own")
        self.link_advertises()
        owner, adv, resp = self.radio.adverts[-1]
        self.assertEqual((owner, adv), ("app", LINK_ADVERT))
        self.assertEqual(decode(resp)["own"], 5)

    def test_refreshes_changes_at_most_twice_a_second(self):
        self.link_advertises()
        sent = len(self.radio.adverts)
        self.beacon.publish(5, None, None, "Hold badges back to back")
        self.assertEqual(len(self.radio.adverts), sent + 1)
        self.clock.now = 100
        self.beacon.publish(6, None, None, "Hold badges back to back")
        self.assertEqual(len(self.radio.adverts), sent + 1)
        self.clock.now = 500
        self.beacon.publish(6, None, None, "Hold badges back to back")
        self.assertEqual(decode(self.radio.adverts[-1][2])["own"], 6)
        self.beacon.publish(6, None, None, "Hold badges back to back")
        self.clock.now = 5000
        self.beacon.publish(6, None, None, "Hold badges back to back")
        self.assertEqual(len(self.radio.adverts), sent + 2, "Unchanged status is not re-sent")

    def test_never_readvertises_during_a_badge_session_or_after_stop(self):
        self.link_advertises()
        sent = len(self.radio.adverts)
        for flag in ("linked", "linking"):
            setattr(self.link, flag, True)
            self.clock.now += 1000
            self.beacon.publish(self.clock.now, 1, 1, "Syncing...")
            setattr(self.link, flag, False)
        self.radio.connections = [object()]
        self.clock.now += 1000
        self.beacon.publish(self.clock.now, 1, 1, "Syncing...")
        self.radio.connections = []
        self.assertEqual(len(self.radio.adverts), sent)
        self.radio.stop_advertise("app")
        self.clock.now += 1000
        self.beacon.publish(9, 1, 1, "Synced")
        self.assertEqual(self.radio.adverts[-1], ("app", None, None))

    def test_idle_firmware_session_flag_does_not_block_updates(self):
        # On hardware radio.in_session is True for the whole idle Link.
        self.radio.in_session = True
        self.link_advertises()
        self.beacon.publish(3, None, None, "Hold badges back to back")
        self.assertEqual(decode(self.radio.adverts[-1][2])["own"], 3)

    def test_waits_for_its_link(self):
        beacon = sb.Beacon(NativeRadio(), None, MAGGIE)
        beacon.radio.advertise("app", 100000, adv_data=LINK_ADVERT, connectable=True)
        sent = len(beacon.radio.adverts)
        beacon.publish(3, None, None, "Hold badges back to back")
        self.assertEqual(len(beacon.radio.adverts), sent)

    def test_close_restores_the_radio(self):
        self.beacon.close()
        self.assertEqual(self.radio.advertise.__func__, NativeRadio.advertise)
        self.assertEqual(self.radio.stop_advertise.__func__, NativeRadio.stop_advertise)


class AppBeaconTests(unittest.TestCase):
    def test_app_broadcasts_the_values_it_draws(self):
        with BadgeHarness() as app:
            app.frame(0)
            app.frame(1000, raw=0)
            app.frame(2000, raw=12)
            got = decode(app.radio.adverts[-1][2])
            self.assertEqual(got["own"], 23 + 12)
            self.assertEqual((got["team"], got["partner"]), (40, 17))
            self.assertEqual(got["status"], "Hold badges back to back")

    def test_wraps_the_radio_before_link_advertises_on_creation(self):
        # The firmware Link advertises from its constructor.
        with BadgeHarness() as app:
            self.assertIsNotNone(app.app["beacon"].call)
            app.frame(0)
            app.frame(1000, raw=4)
            self.assertIsNotNone(app.radio.adverts[-1][2])

    def test_exit_restores_the_radio(self):
        with BadgeHarness() as app:
            app.app["on_exit"]()
            self.assertEqual(app.radio.advertise.__func__, NativeRadio.advertise)


if __name__ == "__main__":
    unittest.main()
