"""Render the proposed native pixel painter at 320 by 240, using only stdlib."""

import struct
import zlib
import display
import presentation
import scene


class Raster:
    def __init__(self, alpha=False):
        self.channels = 4 if alpha else 3
        self.pixels = bytearray(320 * 240 * self.channels)
        self.colors = {}

    def layer(self, name):
        pass

    def rect(self, x, y, width, height, pen):
        x, y, right, bottom = round(x * 2), round(y * 2), round((x + width) * 2), round((y + height) * 2)
        x, y, right, bottom = max(0, x), max(0, y), min(320, right), min(240, bottom)
        if right <= x or bottom <= y:
            return
        if pen not in self.colors:
            rgb = [int(pen[i:i + 2], 16) for i in (1, 3, 5)]
            self.colors[pen] = bytes(round(round(c / 255 * limit) / limit * 255)
                                     for c, limit in zip(rgb, (31, 63, 31)))
            if self.channels == 4:
                self.colors[pen] += b"\xff"
        row = self.colors[pen] * (right - x)
        for line in range(y, bottom):
            offset = (line * 320 + x) * self.channels
            self.pixels[offset:offset + len(row)] = row

    def png(self):
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        stride = 320 * self.channels
        rows = b"".join(b"\x00" + self.pixels[y * stride:(y + 1) * stride] for y in range(240))
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 320, 240, 8, 6 if self.channels == 4 else 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


class Layers:
    def __init__(self):
        self.layers = {}
        self.layer("background")

    def layer(self, name):
        if name not in self.layers:
            self.layers[name] = Raster(alpha=True)
        self.active = self.layers[name]

    def rect(self, *args):
        self.active.rect(*args)


def render_layers(values, tuning=None, frame=1):
    params = dict(scene.DEFAULTS)
    params.update(tuning or {})
    painter = Layers()
    display.draw(painter, presentation.compose(**values), params, frame)
    return {name: image.png() for name, image in painter.layers.items()}


def render_layer(values, tuning, name, frame=1):
    class Only:
        active = False
        def layer(self, current):
            self.active = current == name
        def rect(self, *args):
            if self.active:
                painter.rect(*args)
    painter = Raster(alpha=True)
    params = dict(scene.DEFAULTS)
    params.update(tuning)
    display.draw(Only(), presentation.compose(**values), params, frame)
    return painter.png()


def render(values, tuning=None, baseline=False, frame=1, fatal=False):
    params = dict(scene.DEFAULTS)
    params.update(tuning or {})
    if baseline:
        params.update(skyBands=4, trailY=102, pathWidth=4, walkerGap=12,
                      lighthouseHeight=18, edgePath=False, solidPartner=False,
                      cleanSky=False, cleanLighthouse=False, countSize=4,
                      landscape="reference")
    painter = Raster()
    if fatal:
        display.fatal(painter, "COULD NOT UPDATE DISPLAY")
    else:
        display.draw(painter, presentation.compose(**values), params, frame)
    return painter.png()
