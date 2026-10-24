"""Diagnostics must preserve native journal values and survive log failures."""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import mock_open, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "badge/apps/walking"))
from pairing_trace import PairingTrace


class PairingTraceTests(unittest.TestCase):
    def test_saves_automatically_without_an_exit_callback(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "trace.log"
            link = SimpleNamespace(linked=False, id=b"own", capacity=lambda: 19)
            trace = PairingTrace(link, str(destination))
            sync = SimpleNamespace(status=lambda now: "Hold steady", link=link,
                                   proximity=SimpleNamespace(), progress=lambda now: 0.5,
                                   waiting_for_apart=False)
            trace.now = 100
            trace.observe(sync)
            self.assertIn("Hold steady", destination.read_text())
            sync.status = lambda now: "Syncing..."
            trace.now = 2200
            trace.observe(sync)
            self.assertIn("Syncing...", destination.read_text())

    def test_radio_journal_returns_the_same_events_without_logging_advertisements(self):
        link = SimpleNamespace()
        trace = PairingTrace(link)
        events = [(5, ("nearby advertisement",)), (6, ()), (7, (1, 0, b"peer"))]
        self.assertIs(link.journal("ble", events), events)
        output = "\n".join(trace.lines)
        self.assertNotIn("nearby advertisement", output)
        self.assertIn("peer", output)

    def test_preserves_an_existing_journal_callback(self):
        replacement = [(8, (1,))]
        link = SimpleNamespace(journal=lambda kind, value: replacement)
        PairingTrace(link)
        self.assertIs(link.journal("ble", []), replacement)

    def test_falls_back_to_state_if_the_app_directory_is_read_only(self):
        trace = PairingTrace(SimpleNamespace())
        handle = mock_open().return_value
        with patch("builtins.open", side_effect=[OSError("Read-only filesystem"), handle]) as opener:
            self.assertTrue(trace.save())
        self.assertEqual(opener.call_args_list[1].args[0], "/state/walking_pairing.log")
        self.assertEqual(trace.path, "/state/walking_pairing.log")

    def test_saves_bounded_trace_on_request_and_tolerates_unwritable_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = str(Path(directory) / "trace.log")
            trace = PairingTrace(SimpleNamespace(), destination)
            for index in range(1000):
                trace.record("transition", (index, "x" * 1000))
            trace.save()
            output = Path(destination).read_text()
            self.assertLess(len(output), 40000)
            self.assertIn("999", output)
            self.assertIn("omitted", output)
            with patch("builtins.open", side_effect=OSError("Disk unavailable")):
                trace.save()


if __name__ == "__main__":
    unittest.main()
