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
    def translate(self, *args):
        return self

    def scale(self, *args):
        return self

    def rotate(self, angle):
        return self


class Shape:
    transform = None

    def __init__(self, *args):
        self.args = args


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


class Surface:
    pen = antialias = font = fill_rule = None
    alpha = 255

    def __init__(self, width=320, height=240, buffer=None, mode=None):
        self.width, self.height = width, height
        self.raw = buffer if buffer is not None else bytearray(width * height * 2)

    def shape(self, value):
        pass

    def rectangle(self, *args):
        pass


class Screen(Surface):
    clip = (0, 0, 320, 240)

    def __init__(self):
        super().__init__()
        self.texts = []

    def measure_text(self, value, font_size=14):
        return len(value) * font_size * 0.55, font_size

    def text(self, value, *args, **kwargs):
        self.texts.append(value)

    def line(self, *args):
        pass


def make_image(width, height, buffer=None, mode=None):
    return Surface(width, height, buffer, mode)


make_image.X4, make_image.RGB565 = 4, 1
make_image.EVEN_ODD, make_image.NON_ZERO = 0, 1


class NativeRadio:
    """The firmware radio that the link advertises through."""

    def __init__(self):
        self.adverts = []
        self.in_session = False
        self.connections = []

    def advertise(self, owner, interval, adv_data=None, connectable=True, resp_data=None):
        self.adverts.append((owner, adv_data, resp_data))

    def stop_advertise(self, owner=None):
        self.adverts.append((owner, None, None))


class BadgeHarness:
    def __init__(self):
        self.stack = ExitStack()
        self.screen = Screen()
        self.now = 0
        self.raw = 0
        self.back = False
        self.up = False
        self.fail_save = False
        self.radio = NativeRadio()
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
        radio = self.radio

        class AdvertisingLink(NativeLink):
            # Like the firmware, a new Link starts advertising straight away.
            def __init__(self, game):
                super().__init__(game)
                radio.advertise("app", 100000, adv_data=b"BL" + OWN, connectable=True)

        firmware.link = types.SimpleNamespace(Link=AdvertisingLink, Proximity=NativeProximity,
                                             badge_id_hex=lambda value: value.hex(), radio=self.radio)
        machine = types.ModuleType("machine")
        machine.unique_id = lambda: OWN
        machine.Pin = lambda value: value
        machine.I2C = lambda *args, **kwargs: types.SimpleNamespace(readfrom_mem=read)
        clock = types.ModuleType("time")
        clock.ticks_ms = lambda: self.now
        clock.ticks_diff = ticks_diff
        self.badge = types.SimpleNamespace(mode=lambda mode: None, ticks=0,
                                          caselights=lambda *values: None,
                                          pressed=lambda key: self.back and key == "back",
                                          held=lambda key: self.up and key == "up")
        self.stack.enter_context(patch.dict(sys.modules, {
            "badgeware": firmware, "machine": machine, "time": clock,
        }))
        for name in ("sync_link", "status_beacon", "walking_ui", "diagnostics", "painter", "coast_scene", "hikers", "moments"):
            sys.modules.pop(name, None)
        self.stack.enter_context(patch.multiple(
            builtins, create=True, badge=self.badge, screen=self.screen,
            color=types.SimpleNamespace(rgb=lambda *channels: channels),
            font=types.SimpleNamespace(sins="sins", load=lambda path: "mona"),
            shape=types.SimpleNamespace(circle=Shape, custom=Shape, rectangle=Shape, rounded_rectangle=Shape),
            brush=types.SimpleNamespace(LINEAR=0, gradient=lambda *args: args),
            image=make_image, vec2=lambda x, y: (x, y), mat3=Transform, rect=Rect,
            HIRES=1, VSYNC=2, BUTTON_BACK="back", BUTTON_UP="up",
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
