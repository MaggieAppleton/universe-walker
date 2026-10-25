"""Demo reset profiles and the state written on a connected badge."""

import contextlib
import copy
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
import badge_usb
import reset_demo


class ResetDemoTests(unittest.TestCase):
    def test_profiles_clear_confirmed_progress_on_both_identities(self):
        for own in (reset_demo.MAGGIE, reset_demo.MARTIN):
            for profile, martin in (("near-goal", 9900), ("zero", 0)):
                with self.subTest(own=own, profile=profile):
                    self.assertEqual(reset_demo.seed_state(own, profile), {
                        "counts": {reset_demo.MAGGIE: 0, reset_demo.MARTIN: martin},
                        "game": 0x2026, "last_sync": {},
                    })
        with self.assertRaises(ValueError):
            reset_demo.seed_state("unknown", "zero")
        with self.assertRaises(ValueError):
            reset_demo.seed_state(reset_demo.MAGGIE, "unknown")

    def test_disk_is_ejected_before_switching_to_serial(self):
        with tempfile.TemporaryDirectory() as folder:
            volume = Path(folder) / "BADGER"
            (volume / "apps/walking").mkdir(parents=True)
            events = []
            with patch.object(badge_usb.sys, "platform", "darwin"), \
                 patch.object(badge_usb.subprocess, "run", side_effect=lambda *a, **kw: events.append("eject")), \
                 patch.object(badge_usb, "wait_for_badge", return_value="/dev/badge"), \
                 patch.object(badge_usb, "restart", side_effect=lambda p: events.append("restart") or p):
                self.assertEqual(badge_usb.prepare_badge(volume), "/dev/badge")
            self.assertEqual(events, ["eject", "restart"])

    def test_real_reset_script_backs_up_and_verifies_after_restart(self):
        previous = {"counts": {reset_demo.MAGGIE: 1000, reset_demo.MARTIN: 9900},
                    "last_sync": {reset_demo.MAGGIE: 1000, reset_demo.MARTIN: 9900}, "game": 0x2026}
        saved = copy.deepcopy(previous)
        events = []
        class State:
            @staticmethod
            def load(key, destination):
                destination.update(copy.deepcopy(saved))
            @staticmethod
            def save(key, state):
                events.append("save")
                saved.clear()
                saved.update(copy.deepcopy(state))
        firmware = types.SimpleNamespace(State=State)
        machine = types.SimpleNamespace(unique_id=lambda: bytes.fromhex(reset_demo.MAGGIE))
        def execute(*args):
            source = args[-1]
            with contextlib.redirect_stdout(io.StringIO()) as output:
                exec(source, {})
            return output.getvalue()
        with tempfile.TemporaryDirectory() as folder, \
             patch.dict(sys.modules, {"badgeware": firmware, "machine": machine}), \
             patch.object(reset_demo, "prepare_badge", return_value="/dev/badge"), \
             patch.object(reset_demo, "remote", side_effect=execute), \
             patch.object(reset_demo, "restart", side_effect=lambda p: events.append("restart") or p):
            # Each new interpreter reads a newly opened source stream.
            with patch("builtins.open", side_effect=lambda *a, **kw: io.StringIO("GOAL = 10000\n")):
                receipt = reset_demo.reset_connected("zero", Path(folder), Path("/missing/BADGER"))
            self.assertEqual(saved, {"counts": {reset_demo.MAGGIE: 0, reset_demo.MARTIN: 0},
                                     "last_sync": {}, "game": 0x2026})
            self.assertEqual(json.loads(Path(receipt["backup"]).read_text()), previous)
            self.assertTrue(receipt["verified_after_restart"])
            self.assertEqual(receipt["goal"], 10000)
            self.assertEqual(events, ["save", "restart", "restart"])

    def test_wrong_goal_is_rejected_without_writing_state(self):
        before = {"device_id": reset_demo.MAGGIE, "goal": 500, "state": {}}
        output = reset_demo.MARKER + json.dumps(before)
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(reset_demo, "prepare_badge", return_value="/dev/badge"), \
             patch.object(reset_demo, "remote", return_value=output) as remote, \
             patch.object(reset_demo, "restart", return_value="/dev/badge"):
            with self.assertRaisesRegex(ValueError, "10,000"):
                reset_demo.reset_connected("zero", Path(folder), Path("/missing/BADGER"))
            self.assertEqual(remote.call_count, 1)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_cleanup_error_does_not_hide_the_original_failure(self):
        before = {"device_id": reset_demo.MAGGIE, "goal": 500, "state": {}}
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(reset_demo, "prepare_badge", return_value="/dev/badge"), \
             patch.object(reset_demo, "remote", return_value=reset_demo.MARKER + json.dumps(before)), \
             patch.object(reset_demo, "restart", side_effect=RuntimeError("USB disconnected")), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "10,000"):
                reset_demo.reset_connected("zero", Path(folder), Path("/missing/BADGER"))

    def test_reset_that_does_not_survive_restart_is_not_reported_as_success(self):
        old = {"counts": {reset_demo.MAGGIE: 1000, reset_demo.MARTIN: 9900}, "game": 0x2026,
               "last_sync": {reset_demo.MAGGIE: 1000, reset_demo.MARTIN: 9900}}
        before = {"device_id": reset_demo.MAGGIE, "goal": 10000, "state": old}
        wanted = reset_demo.seed_state(reset_demo.MAGGIE, "zero")
        outputs = [reset_demo.MARKER + json.dumps(value) for value in (before, wanted, before)]
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(reset_demo, "prepare_badge", return_value="/dev/badge"), \
             patch.object(reset_demo, "remote", side_effect=outputs), \
             patch.object(reset_demo, "restart", return_value="/dev/badge"):
            with self.assertRaisesRegex(RuntimeError, "did not survive"):
                reset_demo.reset_connected("zero", Path(folder), Path("/missing/BADGER"))
            saved = list((Path(folder) / reset_demo.MAGGIE).glob("*.json"))
            self.assertEqual(len(saved), 1)
            self.assertTrue(saved[0].name.startswith("before-demo-reset-"))


if __name__ == "__main__":
    unittest.main()
