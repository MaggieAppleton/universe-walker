"""Fresh layout sketches informed by the stock games, using the same data."""

import bitmap_font as font
import hikers
import scene

INK, WHITE, MUTED = "#101411", "#f2f5f3", "#909692"


class Transform:
    def __init__(self, painter, top=0, scale=1, cx=0, cy=0, sx=None):
        self.p, self.top, self.scale, self.cx, self.cy = painter, top, scale, cx, cy
        self.sx = scale if sx is None else sx
    def layer(self, name):
        self.p.layer(name)
    def rect(self, x, y, width, height, pen):
        self.p.rect(self.cx + x * self.sx, self.top + (y - self.cy) * self.scale,
                    width * self.sx, height * self.scale, pen)


def number(p, view, x, y, size=3, center=False):
    while font.width(view["number"], size) > 146 and size > 1:
        size -= 1
    if center:
        x -= font.width(view["number"], size) / 2
    font.text(p, view["number"], round(x), y, size, WHITE)


def footer(p, view, y=110):
    message = "MOVE BADGES APART" if view["success"] else (
        "YOU +%s NEW" % view["personal_new"] if view["personal_new"] else "HOLD BACK TO BACK")
    p.rect(0, y - 2, 160, 122 - y, INK)
    font.text(p, message, round((160 - font.width(message)) / 2), y, 1,
              view["pen"] if view["success"] else "#f2a33a")


def expedition(p, view):
    p.rect(0, 0, 160, 120, INK)
    tuning = dict(scene.DEFAULTS, landscape="alpine", sky="gradient")
    scene.draw(Transform(p, 37, 83 / 60, cy=60, sx=1), view, tuning)
    p.rect(0, 0, 160, 36, INK)
    number(p, view, 6, 3)
    font.text(p, "SHARED", 6, 27, 1, MUTED)
    font.text(p, view["label"], 155 - font.width(view["label"]), 4, 1, view["pen"])
    font.text(p, "GOAL 500", 155 - font.width("GOAL 500"), 18, 1, MUTED)
    footer(p, view)


def coop_map(p, view):
    p.rect(0, 0, 160, 120, INK)
    tuning = dict(scene.DEFAULTS, landscape="map", sky="solid")
    scene.draw(Transform(p, 50, 70 / 60, cy=60, sx=1), view, tuning)
    p.rect(0, 0, 160, 49, INK)
    number(p, view, 6, 3)
    font.text(p, "SHARED", 6, 25, 1, MUTED)
    font.text(p, view["label"], 79, 5, 1, view["pen"])
    font.text(p, "GOAL 500", 99, 18, 1, MUTED)
    p.rect(6, 34, 148, 2, "#232925")
    p.rect(6, 34, round(148 * view["shared_progress"]), 2, "#5fed83")
    theirs = view["partner"] or 0
    mine = max(0, view["shared"] - theirs)
    font.text(p, "YOU %s" % mine, 6, 40, 1, "#f2aa93")
    font.text(p, "PARTNER %s" % theirs, 79, 40, 1, "#a2c6f6")
    footer(p, view)


def meet(p, view):
    p.rect(0, 0, 160, 120, INK)
    number(p, view, 80, 3, center=True)
    font.text(p, "GOAL 500", 112, 6, 1, MUTED)
    title = "SYNCED" if view["success"] else "SHARED STEPS"
    font.text(p, title, round((160 - font.width(title)) / 2), 29, 1,
              view["pen"] if view["success"] else MUTED)
    for x, person, label in ((36, view["person"], "YOU"), (124, 1 - view["person"], "PARTNER")):
        p.rect(x - 31, 51, 62, 47, "#232925")
        font.text(p, label, round(x - font.width(label) / 2), 41, 1, MUTED)
        portrait = Transform(p, top=88, scale=2, cx=x - 160, cy=100)
        hikers.draw(portrait, person, 80, 100, ghost=label == "PARTNER" and not view["success"])
        count = (view["partner"] or 0) if label == "PARTNER" else view["shared"] - (view["partner"] or 0)
        text = str(count)
        font.text(p, text, round(x - font.width(text) / 2), 90, 1, WHITE)
    color = view["pen"] if view["success"] else "#909692"
    for x in (73, 79, 85):
        p.rect(x, 72, 3, 3, color)
    if view["success"]:
        p.rect(73, 73, 15, 1, color)
    if view["success"]:
        footer(p, view, 109)
    else:
        p.rect(0, 100, 160, 20, INK)
        pending = "YOU +%s NEW" % view["personal_new"]
        font.text(p, pending, round((160 - font.width(pending)) / 2), 101, 1, "#f2a33a")
        action = "HOLD BACK TO BACK"
        font.text(p, action, round((160 - font.width(action)) / 2), 112, 1, WHITE)


CONCEPTS = (("expedition", "Landscape first", "Flappy Mona: a fixed HUD above a larger world, with bigger characters.", expedition),
            ("coop_map", "Co-op map", "Snake: a compact score HUD, contribution colours, and a clear playfield.", coop_map),
            ("meet", "Meet & share", "Merge Conflict / Pong: people, pairing, and a short unmistakable confirmation.", meet))
