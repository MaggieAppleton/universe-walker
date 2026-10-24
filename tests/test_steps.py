"""Count real sensor changes without treating a reset as a long walk."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))

from steps import StepCounter


class StepCounterTests(unittest.TestCase):
    def test_first_read_does_not_credit_steps_from_before_launch(self):
        counter = StepCounter()
        self.assertEqual(counter.update(400), 0)
        self.assertEqual(counter.total, 0)

    def test_counts_changes_once(self):
        counter = StepCounter()
        counter.update(400)
        self.assertEqual(counter.update(403), 3)
        self.assertEqual(counter.update(403), 0)
        self.assertEqual(counter.update(405), 2)
        self.assertEqual(counter.total, 5)

    def test_signed_counter_transition_is_one_step(self):
        counter = StepCounter()
        counter.update(32767)
        self.assertEqual(counter.update(-32768), 1)
        self.assertEqual(counter.total, 1)

    def test_unsigned_counter_wrap_is_one_step(self):
        counter = StepCounter()
        counter.update(65535)
        self.assertEqual(counter.update(0), 1)
        self.assertEqual(counter.total, 1)

    def test_hardware_reset_preserves_game_progress(self):
        counter = StepCounter(15)
        counter.update(100)
        counter.update(102)
        self.assertEqual(counter.update(0), 0)
        self.assertEqual(counter.total, 17)
        self.assertEqual(counter.update(3), 3)
        self.assertEqual(counter.total, 20)

    def test_implausible_jump_rebaselines_without_credit(self):
        counter = StepCounter()
        counter.update(100)
        self.assertEqual(counter.update(900), 0)
        self.assertEqual(counter.update(902), 2)
        self.assertEqual(counter.total, 2)

    def test_resumes_a_saved_total(self):
        counter = StepCounter(24)
        counter.update(0)
        self.assertEqual(counter.update(4), 4)
        self.assertEqual(counter.total, 28)


if __name__ == "__main__":
    unittest.main()
