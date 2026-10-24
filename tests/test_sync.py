"""Exercise two real exchanges, including loss and durable-save failures."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))

from sync_protocol import Exchange


class Storage:
    def __init__(self):
        self.counts = None
        self.fail = False

    def save(self, counts):
        if self.fail:
            raise OSError("Disk full")
        self.counts = dict(counts)


class SyncTests(unittest.TestCase):
    def pair(self, first=None, second=None):
        a_store, b_store = Storage(), Storage()
        a = Exchange("a", "b", first or {"a": 23}, a_store.save)
        b = Exchange("b", "a", second or {"b": 17}, b_store.save)
        return a, b, a_store, b_store

    def exchange_snapshots(self, a, b):
        a.receive(b.packets()[0])
        b.receive(a.packets()[0])

    def finish(self, a, b):
        self.exchange_snapshots(a, b)
        a.receive(b.packets()[1])
        b.receive(a.packets()[1])

    def test_both_save_the_same_combined_total(self):
        a, b, a_store, b_store = self.pair()
        self.finish(a, b)
        self.assertTrue(a.done and b.done)
        self.assertEqual(a.total, 40)
        self.assertEqual(b.total, 40)
        self.assertEqual(a_store.counts, {"a": 23, "b": 17})
        self.assertEqual(b_store.counts, {"a": 23, "b": 17})

    def test_repeated_packets_do_not_duplicate_steps(self):
        a, b, a_store, b_store = self.pair()
        for _ in range(4):
            self.finish(a, b)
        self.assertEqual(a.total, 40)
        self.assertEqual(b.total, 40)
        self.assertEqual(a_store.counts, b_store.counts)

    def test_next_walk_adds_only_new_steps(self):
        a, b, _, _ = self.pair({"a": 28, "b": 17}, {"b": 21, "a": 23})
        self.finish(a, b)
        self.assertEqual(a.total, 49)
        self.assertEqual(b.total, 49)

    def test_partner_can_restore_a_higher_previously_saved_count(self):
        a, b, a_store, _ = self.pair({"a": 20, "b": 17}, {"b": 17, "a": 23})
        self.finish(a, b)
        self.assertEqual(a_store.counts["a"], 23)
        self.assertEqual(a.total, 40)
        self.assertEqual(b.total, 40)

    def test_no_success_before_matching_saved_acknowledgment(self):
        a, b, _, _ = self.pair()
        self.exchange_snapshots(a, b)
        self.assertFalse(a.done or b.done)
        a.receive(b.packets()[1])
        self.assertTrue(a.done)
        self.assertFalse(b.done)
        b.receive(a.packets()[1])
        self.assertTrue(b.done)

    def test_acknowledgment_can_arrive_before_snapshot(self):
        a, b, a_store, _ = self.pair()
        b.receive(a.packets()[0])
        a.receive(b.packets()[1])
        self.assertFalse(a.done)
        self.assertEqual(a_store.counts, {"a": 23})
        a.receive(b.packets()[0])
        self.assertTrue(a.done)
        self.assertEqual(a_store.counts, {"a": 23, "b": 17})

    def test_late_stale_acknowledgment_cannot_undo_success(self):
        old_a, old_b, _, _ = self.pair({"a": 20}, {"b": 17})
        self.finish(old_a, old_b)
        a, b, _, _ = self.pair()
        self.finish(a, b)
        a.receive(old_b.packets()[1])
        self.assertTrue(a.done)
        self.assertEqual(a.total, 40)

    def test_failed_save_never_produces_acknowledgment(self):
        a, b, a_store, _ = self.pair()
        a_store.fail = True
        with self.assertRaises(OSError):
            a.receive(b.packets()[0])
        self.assertFalse(a.done)
        self.assertEqual(len(a.packets()), 1)
        self.assertEqual(a_store.counts, {"a": 23})
        a_store.fail = False
        self.finish(a, b)
        self.assertTrue(a.done and b.done)

    def test_constructor_does_not_bind_an_unseen_partner(self):
        _, _, a_store, _ = self.pair()
        self.assertEqual(a_store.counts, {"a": 23})

    def test_rejects_a_different_partner(self):
        with self.assertRaises(ValueError):
            Exchange("a", "c", {"a": 23, "b": 17}, Storage().save)

    def test_rejects_invalid_packets_without_changing_saved_progress(self):
        a, b, a_store, _ = self.pair()
        valid = b.packets()[0]
        bad_game = bytearray(valid)
        bad_game[2] ^= 1
        bad_version = bytearray(valid)
        bad_version[1] += 1
        bad_kind = bytearray(valid)
        bad_kind[0] = 99
        for packet in (b"", valid[:-1], bytes(bad_game), bytes(bad_version), bytes(bad_kind)):
            with self.subTest(packet=packet):
                with self.assertRaises(ValueError):
                    a.receive(packet)
                self.assertEqual(a_store.counts, {"a": 23})
                self.assertFalse(a.done)

    def test_packet_fits_small_native_link_capacity(self):
        a, b, _, _ = self.pair()
        self.finish(a, b)
        for packet in a.packets() + b.packets():
            self.assertLessEqual(len(packet), 16)


if __name__ == "__main__":
    unittest.main()
