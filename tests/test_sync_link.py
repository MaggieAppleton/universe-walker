"""Exercise the real sync adapter across delayed radio disconnections."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))
from sync_protocol import Exchange

OWN = b"\x01" * 8
PEER = b"\x02" * 8


class FrameTick(int):
    """A badge frame timestamp, not a time.ticks_ms() token."""


def ticks_diff(end, start):
    # MicroPython's API only supports its own tick tokens. The real trace
    # returned 9776 for frame timestamps 18766 and 18687 (a 79 ms interval).
    # Enforce that boundary instead of pretending frame values are supported.
    if isinstance(end, FrameTick) or isinstance(start, FrameTick):
        raise AssertionError("Frame timestamps must not be passed to time.ticks_diff")
    return end - start


class NativeLink:
    def __init__(self, game):
        self.id = OWN
        self.partner = types.SimpleNamespace(id=PEER)
        self.linked = True
        self.incoming = []
        self.outgoing = []
        self.leaving = False
        self.updates = []

    def capacity(self):
        return 243

    def pump(self):
        pass

    def update(self):
        self.updates.append(self.linked)

    def receive(self):
        received, self.incoming = self.incoming, []
        return received

    def send(self, packet):
        self.outgoing.append(packet)
        return True

    def leave(self):
        # A future radio callback reports the actual disconnection.
        self.leaving = True

    def close(self):
        self.linked = False


class NativeProximity:
    def __init__(self, link):
        self.link = link
        self.cooldown_ms = 3000
        self.rest_at = None
        self.apart = False
        self.auto_connect = False

    def rest(self, peer_id, now):
        self.rest_at = now

    def update(self, now):
        if self.apart:
            self.rest_at = None
        elif self.auto_connect and self.cooling(now) is None:
            self.link.linked = True

    def clear(self):
        pass

    def syncing(self):
        return None

    def cooling(self, now):
        if self.rest_at is None:
            return None
        remaining = self.cooldown_ms - (now - self.rest_at)
        return remaining if remaining > 0 else None

    def progress(self, now):
        return 0

    def lights(self, now):
        return None


class SyncLinkTests(unittest.TestCase):
    def setUp(self):
        firmware = types.ModuleType("badgeware")
        firmware.link = types.SimpleNamespace(
            Link=NativeLink, Proximity=NativeProximity,
            badge_id_hex=lambda value: value.hex(),
        )
        with patch.dict(sys.modules, {"badgeware": firmware}):
            sys.modules.pop("sync_link", None)
            module = importlib.import_module("sync_link")
        module.time = types.SimpleNamespace(ticks_diff=ticks_diff)
        self.saved = []
        self.counts = {OWN.hex(): 23}
        self.sync = module.BadgeSync(OWN.hex(), lambda values: self.saved.append(dict(values)))

    def finish_exchange(self):
        self.sync.update(0, self.counts)
        peer = Exchange(PEER.hex(), OWN.hex(), {PEER.hex(): 17}, lambda counts: None)
        peer.receive(self.sync.link.outgoing[0])
        self.sync.link.incoming.extend(peer.packets())
        self.sync.update(100, self.counts)
        self.assertEqual(self.sync.status(100), "Synced")
        self.sync.update(1100, self.counts)

    def test_idle_discovery_does_not_advance_the_connected_link_protocol(self):
        # Stock Merge Conflict, verified working on both real badges, gives
        # idle discovery to Proximity.update and calls Link.update only in
        # the already-linked branch. Guard that boundary sequence here.
        self.sync.link.linked = False
        self.sync.update(0, self.counts)
        self.sync.update(100, self.counts)
        self.assertEqual(self.sync.link.updates, [])
        self.assertIsNone(self.sync.exchange)

    def test_new_connection_is_pumped_before_advancing_its_protocol(self):
        self.sync.link.linked = False
        self.sync.proximity.auto_connect = True
        self.sync.update(0, self.counts)
        self.assertEqual(self.sync.link.updates, [])
        self.assertIsNone(self.sync.exchange)
        self.sync.update(100, self.counts)
        self.assertIsNotNone(self.sync.exchange)
        self.assertEqual(self.sync.link.updates, [True])

    def test_initial_connection_does_not_publish_counts_before_mtu_setup(self):
        # The captured real connection has capacity 19 initially. Walking
        # sends immediately, then tears down within 80-171 ms without a reply.
        # Merge Conflict's first 94-byte message cannot be sent at that point.
        self.sync.link.capacity = lambda: 19
        self.sync.update(23417, self.counts)
        self.assertEqual(self.sync.link.outgoing, [])
        self.assertEqual(self.saved, [])
        self.assertIsNone(self.sync.exchange)
        self.assertEqual(self.sync.link.updates, [True])

    def test_frame_timestamps_keep_retries_and_timeout_in_milliseconds(self):
        self.sync.update(FrameTick(18687), self.counts)
        for now in (18721, 18743, 18766):
            self.sync.update(FrameTick(now), self.counts)
        self.assertEqual(len(self.sync.link.outgoing), 1)
        self.assertFalse(self.sync.link.leaving)
        self.sync.update(FrameTick(18787), self.counts)
        self.assertEqual(len(self.sync.link.outgoing), 2)
        self.sync.update(FrameTick(26686), self.counts)
        self.assertFalse(self.sync.link.leaving)
        self.sync.update(FrameTick(26687), self.counts)
        self.assertTrue(self.sync.link.leaving)

    def test_frame_timestamps_preserve_ack_grace_and_expire_success_feedback(self):
        self.sync.update(FrameTick(22427), self.counts)
        peer = Exchange(PEER.hex(), OWN.hex(), {PEER.hex(): 17}, lambda counts: None)
        peer.receive(self.sync.link.outgoing[0])
        self.sync.link.incoming.extend(peer.packets())
        self.sync.update(FrameTick(22493), self.counts)
        self.sync.update(FrameTick(22527), self.counts)
        self.assertFalse(self.sync.link.leaving)
        self.assertEqual(self.sync.success_age(FrameTick(22527)), 34)
        self.sync.update(FrameTick(23492), self.counts)
        self.assertFalse(self.sync.link.leaving)
        self.sync.update(FrameTick(23493), self.counts)
        self.assertTrue(self.sync.link.leaving)
        self.assertEqual(self.sync.success_age(FrameTick(25292)), 2799)
        self.assertIsNone(self.sync.success_age(FrameTick(25293)))
        self.assertEqual(self.sync.status(FrameTick(26492)), "Synced")
        self.assertNotEqual(self.sync.status(FrameTick(26493)), "Synced")
        self.assertNotEqual(self.sync.status(FrameTick(58257)), "Synced")

    def test_setup_state_change_does_not_cancel_the_connection(self):
        self.sync.link.capacity = lambda: 19
        self.sync.update(23417, self.counts)
        self.sync.link.linked = False
        self.sync.proximity.auto_connect = True
        self.sync.update(23588, self.counts)
        self.assertFalse(self.sync.link.leaving)
        self.assertFalse(self.sync.waiting_for_apart)
        self.sync.link.capacity = lambda: 243
        self.sync.update(23611, self.counts)
        self.assertEqual(len(self.sync.link.outgoing), 1)
        peer = Exchange(PEER.hex(), OWN.hex(), {PEER.hex(): 17}, lambda counts: None)
        peer.receive(self.sync.link.outgoing[0])
        self.sync.link.incoming.extend(peer.packets())
        self.sync.update(23711, self.counts)
        self.assertEqual(self.sync.status(23711), "Synced")
        self.assertEqual(self.sync.synced_total, 40)

    def test_does_not_start_a_new_exchange_during_delayed_disconnect(self):
        self.finish_exchange()
        sent = list(self.sync.link.outgoing)
        self.counts[OWN.hex()] = 24
        self.sync.update(1200, self.counts)
        self.assertIsNone(self.sync.exchange)
        self.assertEqual(self.sync.link.outgoing, sent)
        self.assertEqual(self.sync.status(1200), "Synced")

    def test_expired_cooldown_does_not_resync_without_separation(self):
        self.finish_exchange()
        sent = list(self.sync.link.outgoing)
        self.sync.link.linked = False
        self.sync.proximity.auto_connect = True
        self.counts[OWN.hex()] = 30
        for now in range(1200, 12000, 100):
            self.sync.update(now, self.counts)
        self.assertEqual(self.sync.link.outgoing, sent)
        self.assertIsNone(self.sync.exchange)

    def test_separating_then_holding_again_allows_a_new_sync(self):
        self.finish_exchange()
        self.sync.link.linked = False
        self.sync.proximity.apart = True
        self.sync.update(1200, self.counts)
        self.sync.proximity.apart = False
        self.sync.proximity.auto_connect = True
        self.sync.update(1400, self.counts)
        self.sync.update(1500, self.counts)
        self.assertIsNotNone(self.sync.exchange)
        self.assertIsNone(self.sync.success_age(1500))

    def test_long_pause_does_not_rearm_from_cooldown_expiry(self):
        self.finish_exchange()
        sent = list(self.sync.link.outgoing)
        self.sync.link.linked = False
        self.sync.proximity.auto_connect = True
        self.sync.update(20000, self.counts)
        self.sync.update(20100, self.counts)
        self.assertEqual(self.sync.link.outgoing, sent)
        self.assertIsNone(self.sync.exchange)


if __name__ == "__main__":
    unittest.main()
