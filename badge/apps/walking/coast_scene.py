"""The coast world: rendered once offscreen, then copied in each frame."""

import painter as P

GOAL_X = 262
LIGHT_SCALE = 1.5
SKY = ("#151d3b", "#2f3468", "#7a5690", "#e9967a")
SKY_END = 164
EDGE, BED, WALKED, AMBER = P.rgb("#b28f5c"), P.rgb("#e7cf98"), P.rgb("#fff6dc"), P.rgb("#ffb547")
TRAIL_WIDTH = 12


def ease(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def coast_edge(x):
    return 214 - 40 * ease((x + 20) / 340)


def _sample(f):
    return [(x, f(x)) for x in range(-16, 337, 8)]


# The cliff edge and the path share one curve, so they run together.
TRAIL = P.Path(_sample(lambda x: coast_edge(x) + 17))
START_D = TRAIL.d_at_x(24)
GOAL_D = TRAIL.d_at_x(GOAL_X)
LIGHT_X, LIGHT_Y = 288, coast_edge(288) + 8


def _gradient(y0, y1, hexes):
    last = len(hexes) - 1
    stops = [(i / last, P.rgb(h)) for i, h in enumerate(hexes)]
    return brush.gradient(brush.LINEAR, 0, 0, 0, 1, stops, mat3().translate(0, y0).scale(P.W, y1 - y0))


def _hill(c, points, pen):
    path = P.Path(points)
    P.poly(c, [(path.pts[0][0], 240)] + path.pts + [(path.pts[-1][0], 240)], pen)


_beam = None


def _beam_brush():
    # Fully opaque at the lamp, fading to clear at the far end. Built once:
    # a gradient's lookup table is the costly part.
    global _beam
    if _beam is None:
        length = 80 * LIGHT_SCALE
        stops = [(0.0, P.rgb("#ffe28c", 0)), (1.0, P.rgb("#ffe28c"))]
        _beam = brush.gradient(brush.LINEAR, 0, 0.5, 1, 0.5, stops,
                               mat3().translate(LIGHT_X - length, 0).scale(length, 1))
    return _beam


def lighthouse(c, lit):
    def at(points):
        return [(LIGHT_X + x * LIGHT_SCALE, LIGHT_Y + y * LIGHT_SCALE) for x, y in points]

    s = LIGHT_SCALE
    if lit:
        P.poly(c, at([(0, -30), (-80, -44), (-80, -20)]), _beam_brush())
        P.circle(c, LIGHT_X, LIGHT_Y - 30 * s, 9 * s, P.rgb("#ffe28c", 0.35))
    P.poly(c, at([(-6, 0), (6, 0), (4, -25), (-4, -25)]), P.rgb("#f4f1ea"))
    P.poly(c, at([(-5.4, -8), (5.4, -8), (5, -14), (-5, -14)]), P.rgb("#d6453d"))
    P.poly(c, at([(-4.6, -18), (4.6, -18), (4.3, -23), (-4.3, -23)]), P.rgb("#d6453d"))
    P.rrect(c, LIGHT_X - 4 * s, LIGHT_Y - 33 * s, 8 * s, 7 * s, s, P.rgb("#ffe28a" if lit else "#5b6278"))
    P.poly(c, at([(-6, -33), (6, -33), (0, -39)]), P.rgb("#2d2f45"))


def paint(c):
    """Everything that never changes: sky, sea, land, unlit lighthouse, trail bed."""
    c.antialias = image.X4
    c.pen = _gradient(0, SKY_END, SKY)
    c.shape(shape.rectangle(0, 0, P.W, SKY_END + 2))
    for x, y in ((30, 40), (292, 30), (262, 120), (40, 128), (304, 98), (16, 74)):
        P.circle(c, x, y, 0.9, P.rgb("#ffffff", 0.55))
    P.circle(c, 64, 164, 22, P.rgb("#ffc896", 0.16))
    P.circle(c, 64, 164, 12, P.rgb("#ffd29a"))
    _hill(c, [(-10, 156), (20, 154), (52, 162), (70, 166)], P.rgb("#4b3f78"))
    c.pen = _gradient(164, 240, ("#3d5f9e", "#26407a"))
    c.shape(shape.rectangle(0, 164, P.W, 76))
    for w, y in ((22, 170), (14, 176), (8, 182)):
        P.rrect(c, 64 - w / 2, y, w, 1.6, 1, P.rgb("#ffd2a0", 0.28))
    c.pen = _gradient(170, 240, ("#79b961", "#4b8a48"))
    c.shape(P.polygon([(-16, 240)] + _sample(coast_edge) + [(336, 240)]))
    lighthouse(c, False)
    P.stroke(c, TRAIL.ribbon(0, TRAIL.total, TRAIL_WIDTH + 3), EDGE)
    P.stroke(c, TRAIL.ribbon(0, TRAIL.total, TRAIL_WIDTH), BED)


_scene = None
_offscreen = True


def _build():
    # Match the screen's pixel format so the frame copy is a plain memory move
    # (the same approach as the stock Brattal app's ground layer).
    pixel_bytes = len(screen.raw) // (P.W * P.H)
    if pixel_bytes == 2:
        scene = image(P.W, P.H, bytearray(P.W * P.H * 2), image.RGB565)
    else:
        scene = image(P.W, P.H)
    paint(scene)
    return scene


def background():
    global _scene, _offscreen
    if _offscreen and _scene is None:
        try:
            _scene = _build()
        except MemoryError:
            print("walking: no room for the offscreen scene; drawing it each frame")
            _offscreen = False
    if _scene is not None:
        memoryview(screen.raw)[:] = memoryview(_scene.raw)
    else:
        paint(screen)


_progress_key = None
_progress = ()


def progress(shared, mine):
    """Amber unshared steps, then the confirmed shared stretch, along the trail."""
    global _progress_key, _progress
    key = (shared, mine)
    if key != _progress_key:
        span = GOAL_D - START_D
        shared_d, mine_d = START_D + shared * span, START_D + mine * span
        width = TRAIL_WIDTH * 0.45
        parts = []
        if mine_d > shared_d:
            parts.append((TRAIL.ribbon(shared_d, mine_d, width), AMBER))
        if shared > 0:
            parts.append((TRAIL.ribbon(START_D, shared_d, width), WALKED))
        _progress_key, _progress = key, parts
    for shapes, pen in _progress:
        P.stroke(screen, shapes, pen)
