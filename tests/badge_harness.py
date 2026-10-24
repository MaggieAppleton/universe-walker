"""Run the real app against virtual hardware, never the USB badge."""

import builtins
import copy
import os
import sys
import types
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from test_sync_link import NativeLink, NativeProximity, OWN, PEER, FrameTick, ticks_diff

APP = Path(__file__).parents[1] / "badge/apps/walking"


class Transform:
    def translate(self, value):
        return self

    def scale(self, x, y):
        return self


class Screen:
    clip = (0, 0, 320, 240)
    width, height = 320, 240

    def __init__(self):
        self.texts = []

    def measure_text(self, value):
        return len(value) * 7, 14

    def text(self, value, *args, **kwargs):
        self.texts.append(value)

    def rectangle(self, *args):
        pass

    def line(self, *args):
        pass

    def shape(self, *args):
        pass


class BadgeHarness:
    def __init__(self):
        self.stack = ExitStack()
        self.screen = Screen()
        self.now = 0
        self.raw = 0
        self.back = False
        self.fail_save = False
        self.saved = {"counts": {OWN.hex(): 23, PEER.hex(): 17}, "game": 0x2026,
                      "last_sync": {OWN.hex(): 23, PEER.hex(): 17}}

    def __enter__(self):
        def load(key, values):
            values.update(copy.deepcopy(self.saved))

        def save(key, values):
            if self.fail_save:
                raise OSError("Disk full")
            self.saved = copy.deepcopy(values)

        def read(address, register, size):
            if register == 0x0F:
                return b"\x6a"
            if register == 0x19:
                return b"\xbd"
            if register == 0x4B:
                return bytes((self.raw & 255, self.raw >> 8))
            raise ValueError("Unexpected sensor register")

        firmware = types.ModuleType("badgeware")
        firmware.State = types.SimpleNamespace(load=load, save=save)
        firmware.link = types.SimpleNamespace(Link=NativeLink, Proximity=NativeProximity,
                                             badge_id_hex=lambda value: value.hex())
        machine = types.ModuleType("machine")
        machine.unique_id = lambda: OWN
        machine.Pin = lambda value: value
        machine.I2C = lambda *args, **kwargs: types.SimpleNamespace(readfrom_mem=read)
        clock = types.ModuleType("time")
        clock.ticks_ms = lambda: self.now
        clock.ticks_diff = ticks_diff
        self.badge = types.SimpleNamespace(mode=lambda mode: None, ticks=0,
                                          caselights=lambda *values: None,
                                          pressed=lambda key: self.back and key == "back")
        self.stack.enter_context(patch.dict(sys.modules, {
            "badgeware": firmware, "machine": machine, "time": clock,
        }))
        for name in ("sync_link", "walking_ui", "diagnostics"):
            sys.modules.pop(name, None)
        self.stack.enter_context(patch.multiple(
            builtins, create=True, badge=self.badge, screen=self.screen,
            color=types.SimpleNamespace(rgb=lambda *channels: channels),
            font=types.SimpleNamespace(sins="sins"),
            shape=types.SimpleNamespace(circle=lambda *args: args),
            vec2=lambda x, y: (x, y), mat3=Transform,
            HIRES=1, VSYNC=2, BUTTON_BACK="back",
        ))
        self.stack.enter_context(patch("os.chdir", lambda path: None))
        self.path_before = list(sys.path)
        sys.path.insert(0, str(APP))
        source = Path(os.environ.get("WALKING_TEST_SOURCE", APP / "__init__.py"))
        self.app = {"__name__": "walking_test", "run": self.start}
        exec(compile(source.read_text(), str(source), "exec"), self.app)
        self.app["sync"].link.linked = False
        return self

    def start(self, callback):
        self.callback = callback

    def frame(self, now, raw=0):
        self.now, self.raw = now, raw
        self.badge.ticks = FrameTick(now)
        self.screen.texts.clear()
        return self.callback()

    def __exit__(self, *args):
        sys.path[:] = self.path_before
        self.stack.close()
