"""Drawing helpers ported from design-jig/walking/fresh/painter.js."""

import math

W, H = 320, 240
TURN = math.pi * 2
TOP = -math.pi / 2

# Native text uses a top-aligned line box; the jig uses alphabetic baselines.
ASCENT = 0.8
# Mona Sans "0" advance in em (from MonaSans-Medium.af). Font sizes are scaled
# so the badge's measured advance matches the jig's Chrome rendering.
ZERO_ADVANCE = 0.621

try:
    FONT = font.load("/system/assets/fonts/MonaSans-Medium.af")
except Exception as error:
    print("walking: Mona Sans unavailable:", error)
    FONT = font.sins

_scale = None
_widths = {}


def rgb(hex_value, alpha=1.0):
    n = int(hex_value[1:], 16)
    return color.rgb(n >> 16, (n >> 8) & 255, n & 255, int(alpha * 255 + 0.5))


def fmt(n):
    digits = str(n)
    groups = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return ",".join(groups)


def _size(size):
    global _scale
    if _scale is None:
        screen.font = FONT
        measured = screen.measure_text("0000000000", font_size=100)[0]
        _scale = min(1.4, max(0.7, 1000 * ZERO_ADVANCE / max(1, measured)))
    return size * _scale


def measure(text, size):
    key = (text, size)
    width = _widths.get(key)
    if width is None:
        if len(_widths) > 64:
            _widths.clear()
        width = _widths[key] = screen.measure_text(text, font_size=_size(size))[0]
    return width


def text(value, x, y, size, pen, align="center"):
    if align == "center":
        x -= measure(value, size) / 2
    screen.pen = pen
    screen.text(value, x, y - ASCENT * _size(size), _size(size))


def runs(parts, x, y, size):
    """Several coloured runs on one centred line."""
    gap = size * 0.5
    total = gap * (len(parts) - 1)
    for value, _pen in parts:
        total += measure(value, size)
    x -= total / 2
    for value, pen in parts:
        text(value, x, y, size, pen, "left")
        x += measure(value, size) + gap


def big_number(value, x, y, size, max_width, pen):
    """Fit the width and leave extra raster space below native glyphs."""
    fit = min(size, size * max_width / max(1, measure(value, size)))
    width, height = screen.measure_text(value, font_size=_size(fit))
    screen.pen = pen
    # Allow 4px beyond the reported height for the bottom raster rows and
    # comma descender, instead of relying on the implicit point-based box.
    bounds = rect(x - width / 2, y - ASCENT * _size(fit), math.ceil(width) + 4, math.ceil(height) + 4)
    screen.text(value, bounds, _size(fit))


def big_runs(parts, x, y, size, max_width):
    """One large count row: shared font size, coloured runs, fitted as a whole."""
    gap = size * 0.12
    width = sum(measure(value, size) for value, _pen in parts) + gap * (len(parts) - 1)
    fit = size * min(1, max_width / max(1, width))
    gap = fit * 0.12
    sizes = [screen.measure_text(value, font_size=_size(fit)) for value, _pen in parts]
    width = sum(w for w, _h in sizes) + gap * (len(parts) - 1)
    x -= width / 2
    # Keep the row centred on the calibrated full-size count as it shrinks.
    full_height = screen.measure_text("0", font_size=_size(size))[1]
    height = screen.measure_text("0", font_size=_size(fit))[1]
    top = y - ASCENT * _size(size) + (full_height - height) / 2
    for (value, pen), (w, h) in zip(parts, sizes):
        screen.pen = pen
        screen.text(value, rect(x, top, math.ceil(w) + 4, math.ceil(h) + 4), _size(fit))
        x += w + gap


# Shapes. `c` is the screen or an offscreen image.

def circle(c, x, y, r, pen):
    c.pen = pen
    c.shape(shape.circle(x, y, r))


def rrect(c, x, y, w, h, r, pen):
    c.pen = pen
    c.shape(shape.rounded_rectangle(x, y, w, h, r) if r else shape.rectangle(x, y, w, h))


def polygon(points):
    return shape.custom([vec2(x, y) for x, y in points])


def poly(c, points, pen):
    c.pen = pen
    c.shape(polygon(points))


def capsule(x0, y0, x1, y1, width, steps=5):
    """A round-capped line as one convex outline."""
    a = math.atan2(y1 - y0, x1 - x0)
    r = width / 2
    points = []
    for cx, cy, start in ((x1, y1, a - math.pi / 2), (x0, y0, a + math.pi / 2)):
        for i in range(steps + 1):
            t = start + math.pi * i / steps
            points.append((cx + math.cos(t) * r, cy + math.sin(t) * r))
    return points


def line(c, x0, y0, x1, y1, width, pen):
    poly(c, capsule(x0, y0, x1, y1, width), pen)


def star(c, x, y, r, pen):
    points = []
    for i in range(8):
        a = i * math.pi / 4 - math.pi / 2
        rr = r * 0.38 if i % 2 else r
        points.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(c, points, pen)


def _arc_points(cx, cy, r, a0, a1):
    steps = max(2, int(abs(a1 - a0) * r / 6) + 1)
    return [(cx + math.cos(a0 + (a1 - a0) * i / steps) * r,
             cy + math.sin(a0 + (a1 - a0) * i / steps) * r) for i in range(steps + 1)]


def arc(c, cx, cy, r, a0, a1, width, pen):
    """A round-capped stroked arc; angles in canvas radians (0 = right, clockwise)."""
    c.pen = pen
    half = width / 2
    if a1 - a0 >= TURN - 0.001:
        outer = _arc_points(cx, cy, r + half, 0, TURN)
        inner = _arc_points(cx, cy, r - half, TURN, 0)
        c.shape(shape.custom([vec2(x, y) for x, y in outer], [vec2(x, y) for x, y in inner]))
        return
    c.shape(polygon(_arc_points(cx, cy, r + half, a0, a1) + _arc_points(cx, cy, r - half, a1, a0)))
    for a in (a0, a1):
        c.shape(shape.circle(cx + math.cos(a) * r, cy + math.sin(a) * r, half))


class Path:
    """Catmull-Rom curve sampled into an arc-length table."""

    def __init__(self, points, steps=4):
        pts = []
        last = len(points) - 1
        for i in range(last):
            p0, p1 = points[max(0, i - 1)], points[i]
            p2, p3 = points[i + 1], points[min(last, i + 2)]
            for s in range(steps):
                t = s / steps
                t2, t3 = t * t, t * t * t
                pts.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t
                                        + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
        pts.append(tuple(points[last]))
        lengths = [0]
        for i in range(1, len(pts)):
            dx, dy = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            lengths.append(lengths[-1] + math.sqrt(dx * dx + dy * dy))
        self.pts, self.lengths, self.total = pts, lengths, lengths[-1]

    def _index(self, d):
        lo, hi = 1, len(self.lengths) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.lengths[mid] < d:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def point_at(self, d):
        d = max(0, min(self.total, d))
        i = self._index(d)
        span = (self.lengths[i] - self.lengths[i - 1]) or 1
        t = (d - self.lengths[i - 1]) / span
        (x0, y0), (x1, y1) = self.pts[i - 1], self.pts[i]
        return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t

    def d_at_x(self, x):
        best = 0
        for i, p in enumerate(self.pts):
            if abs(p[0] - x) < abs(self.pts[best][0] - x):
                best = i
        return self.lengths[best]

    def ribbon(self, d0, d1, width):
        """Shapes for a round-capped stroke along the path between two distances."""
        d0, d1 = max(0, d0), min(self.total, d1)
        centre = [self.point_at(d0)]
        for i, d in enumerate(self.lengths):
            if d0 < d < d1:
                centre.append(self.pts[i])
        centre.append(self.point_at(d1))
        half = width / 2
        left, right = [], []
        last = len(centre) - 1
        for i, (x, y) in enumerate(centre):
            ax, ay = centre[max(0, i - 1)]
            bx, by = centre[min(last, i + 1)]
            dx, dy = bx - ax, by - ay
            length = math.sqrt(dx * dx + dy * dy) or 1
            nx, ny = -dy / length * half, dx / length * half
            left.append(vec2(x + nx, y + ny))
            right.append(vec2(x - nx, y - ny))
        right.reverse()
        return (shape.custom(left + right),
                shape.circle(centre[0][0], centre[0][1], half),
                shape.circle(centre[last][0], centre[last][1], half))


def stroke(c, shapes, pen):
    c.pen = pen
    for item in shapes:
        c.shape(item)
