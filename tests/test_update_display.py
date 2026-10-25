"""Exercise the two-file USB update on a temporary badge disk."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from update_display import apply_update


class DisplayUpdateTests(unittest.TestCase):
    def test_replaces_stale_goal_and_painter_without_changing_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, target, backup = root / "source", root / "badge", root / "backup"
            source.mkdir()
            target.mkdir()
            (source / "walking_ui.py").write_text("GOAL = 10000\nCOUNT_BASELINE = 75\n")
            (source / "painter.py").write_text("# padded text renderer\n")
            (target / "walking_ui.py").write_text("GOAL = 500\n")
            (target / "painter.py").write_text("# old renderer\n")
            (target / "progress.json").write_text('{"counts": [0, 9900]}')
            apply_update(source, target, backup)
            self.assertEqual((backup / "walking_ui.py").read_text(), "GOAL = 500\n")
            self.assertEqual((target / "walking_ui.py").read_text(), "GOAL = 10000\nCOUNT_BASELINE = 75\n")
            self.assertEqual((target / "painter.py").read_text(), "# padded text renderer\n")
            self.assertEqual((target / "progress.json").read_text(), '{"counts": [0, 9900]}')

    def test_refuses_stale_source_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, target = root / "source", root / "badge"
            source.mkdir()
            target.mkdir()
            (source / "walking_ui.py").write_text("GOAL = 500\nCOUNT_BASELINE = 75\n")
            (source / "painter.py").write_text("# new renderer\n")
            (target / "walking_ui.py").write_text("# keep me\n")
            with self.assertRaises(ValueError):
                apply_update(source, target, root / "backup")
            self.assertEqual((target / "walking_ui.py").read_text(), "# keep me\n")


if __name__ == "__main__":
    unittest.main()
