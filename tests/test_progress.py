"""Exercise sync retries and out-of-order snapshots without badge hardware."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))

from progress import merge_counts


class ProgressTests(unittest.TestCase):
    def test_combines_independent_walks(self):
        counts = merge_counts({"a": 12}, {"b": 18})
        self.assertEqual(counts, {"a": 12, "b": 18})
        self.assertEqual(sum(counts.values()), 30)

    def test_repeated_sync_does_not_credit_steps_twice(self):
        counts = {"a": 12, "b": 18}
        for _ in range(5):
            counts = merge_counts(counts, {"a": 12, "b": 18})
        self.assertEqual(sum(counts.values()), 30)

    def test_delayed_snapshot_cannot_reduce_progress(self):
        self.assertEqual(
            merge_counts({"a": 12, "b": 18}, {"a": 5, "b": 10}),
            {"a": 12, "b": 18},
        )

    def test_walks_after_sync_converge_in_either_order(self):
        first = {"a": 20, "b": 18}
        second = {"a": 12, "b": 25}
        self.assertEqual(merge_counts(first, second), {"a": 20, "b": 25})
        self.assertEqual(merge_counts(second, first), {"a": 20, "b": 25})
        self.assertEqual(first, {"a": 20, "b": 18})
        self.assertEqual(second, {"a": 12, "b": 25})

    def test_rejects_a_third_player(self):
        with self.assertRaises(ValueError):
            merge_counts({"a": 12, "b": 18}, {"c": 5})

    def test_rejects_invalid_counts_in_either_snapshot(self):
        for count in (-1, 1.5, True, "12", None):
            for known, incoming in (({"a": count}, {}), ({}, {"a": count})):
                with self.subTest(known=known, incoming=incoming):
                    with self.assertRaises(ValueError):
                        merge_counts(known, incoming)

    def test_rejects_invalid_device_ids(self):
        for badge_id in ("", None, 123):
            with self.subTest(badge_id=badge_id):
                with self.assertRaises(ValueError):
                    merge_counts({}, {badge_id: 0})


if __name__ == "__main__":
    unittest.main()
