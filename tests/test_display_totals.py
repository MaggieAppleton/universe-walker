"""Own steps stay live; the shared score changes only after a completed sync."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))
from progress import display_totals


class DisplayTotalsTests(unittest.TestCase):
    def test_walking_changes_only_the_personal_count(self):
        self.assertEqual(
            display_totals("a", {"a": 28, "b": 17}, {"a": 23, "b": 17}),
            (28, 40, 17),
        )

    def test_unacknowledged_peer_data_does_not_change_shared_score(self):
        self.assertEqual(
            display_totals("a", {"a": 28, "b": 20}, {"a": 23, "b": 17}),
            (28, 40, 17),
        )

    def test_successful_sync_updates_the_shared_score(self):
        self.assertEqual(
            display_totals("a", {"a": 28, "b": 20}, {"a": 28, "b": 20}),
            (28, 48, 20),
        )

    def test_no_sync_yet_is_not_presented_as_a_team_total(self):
        self.assertEqual(display_totals("a", {"a": 23, "b": 17}, {}), (23, None, None))


if __name__ == "__main__":
    unittest.main()
