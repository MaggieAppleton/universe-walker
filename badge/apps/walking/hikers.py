"""Hiker sprites from the design jig, built once as shapes and moved by transform."""

import math

import painter as P

PEOPLE = {
    "Maggie": {"jacket": "#e5484d", "shade": "#a8282f", "hair": "#c4441b", "style": "hair"},
    "Martin": {"jacket": "#3b82f6", "shade": "#1d4fb8", "hair": "#3b2a20", "style": "cap"},
}
JACKETS = {who: P.rgb(p["jacket"]) for who, p in PEOPLE.items()}
SKIN, TROUSERS, OUTLINE = P.rgb("#f3c9a4"), P.rgb("#2a3350"), P.rgb("#141a2a")
TROUSERS_NEAR = P.rgb("#36416a")

_built = {}


def _half_disc(x, y, r):
    # Canvas arc(PI -> 0) filled: the top half of a circle.
    return [(x + math.cos(math.pi + math.pi * i / 8) * r, y + math.sin(math.pi + math.pi * i / 8) * r)
            for i in range(9)]


def _parts(who, phase, cheer):
    """(shape, pen) pairs with the feet at the origin: an outline pass, then the fill."""
    p = PEOPLE[who]
    jacket, shade, hair = P.rgb(p["jacket"]), P.rgb(p["shade"]), P.rgb(p["hair"])
    stride = math.sin(phase * math.pi) * 3.4
    parts = []

    def line(x0, y0, x1, y1, width, pen):
        parts.append((P.polygon(P.capsule(x0, y0, x1, y1, width)), pen))

    def rrect(x, y, w, h, r, pen):
        parts.append((shape.rounded_rectangle(x, y, w, h, r), pen))

    def circle(x, y, r, pen):
        parts.append((shape.circle(x, y, r), pen))

    for fill in (False, True):
        grow = 0 if fill else 1.4

        def pen(colour):
            return colour if fill else OUTLINE

        line(-1.4, -11, -1.4 - stride, -1.2, 3.4 + grow * 2, pen(TROUSERS))
        line(1.4, -11, 1.4 + stride, -1.2, 3.4 + grow * 2, pen(TROUSERS_NEAR))
        rrect(-8.6 - grow, -21.6 - grow, 5.6 + grow * 2, 10 + grow * 2, 2.2, pen(shade))
        rrect(-5.2 - grow, -22.5 - grow, 10.4 + grow * 2, 13.2 + grow * 2, 4.4, pen(jacket))
        if cheer:
            line(3.2, -19.5, 7.5, -29, 3 + grow * 2, pen(jacket))
            line(-3, -19.5, -6.5, -29, 3 + grow * 2, pen(jacket))
        else:
            line(0.5, -19, 0.5 + stride * 0.9 + 1.5, -12.5, 3 + grow * 2, pen(shade))
        if p["style"] == "hair":
            circle(-0.6, -28.6, 5.6 + grow, pen(hair))
            circle(-6.2, -26.6, 3 + grow, pen(hair))
            if fill:
                circle(1.6, -27, 4.2, SKIN)
                circle(-0.8, -31.2, 3.6, hair)
        else:
            circle(0.4, -27.6, 5.2 + grow, pen(SKIN))
            parts.append((P.polygon(_half_disc(0.2, -29.2, 5.6 + grow)), pen(jacket)))
            rrect(1 - grow, -30.4 - grow, 9 + grow * 2, 2.6 + grow * 2, 1.3, pen(jacket))
    circle(4.2, -27.4, 0.9, OUTLINE)
    return parts


def draw(x, y, who, facing=1, phase=0.6, cheer=False, alpha=1.0):
    key = (who, phase, cheer)
    parts = _built.get(key)
    if parts is None:
        parts = _built[key] = _parts(who, phase, cheer)
    transform = mat3().translate(x, y).scale(facing, 1)
    if alpha < 1:
        screen.alpha = int(alpha * 255)
    for item, pen in parts:
        item.transform = transform
        screen.pen = pen
        screen.shape(item)
    screen.alpha = 255
