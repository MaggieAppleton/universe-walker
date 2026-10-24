"""Candidate badge screen. The jig and future native adapter share this code."""

import bitmap_font as font
import scene

INK = "#10141c"
WHITE = "#f2f4f8"
MUTED = "#9aa4b4"
PENDING = "#f2a33a"


def centered(p, value, y, scale, pen):
    font.text(p, value, round((160 - font.width(value, scale)) / 2), y, scale, pen)


def draw(p, view, tuning, frame=1):
    p.layer("background")
    p.rect(0, 0, 160, 120, INK)
    p.layer("header")
    color = view["pen"]
    if view["success"]:
        steps = ((4, 6), (6, 8), (8, 6), (10, 4), (12, 2))
        visible = min(5, int(view["success_age"] / 52) + 1)
        for x, y in steps[:visible]:
            p.rect(x, y, 2, 2, color)
    else:
        p.rect(4, 4, 2, 5, color)
        p.rect(13, 4, 2, 5, color)
        p.rect(7, 6, 1, 1, color)
        p.rect(11, 6, 1, 1, color)
    font.text(p, view["label"], 18, 3, 1, color)
    goal = "GOAL " + str(view["goal"])
    font.text(p, goal, 157 - font.width(goal), 3, 1, MUTED)
    size = tuning["countSize"]
    while font.width(view["number"], size) > 152 and size > 1:
        size -= 1
    centered(p, view["number"], 14 + max(0, (28 - 7 * size) // 2), size, WHITE)
    caption, detail = view["caption"], view["detail"]
    if font.width(caption) + font.width(detail) + 8 > 152:
        caption = "SHARED"
    if font.width(caption) + font.width(detail) + 8 > 152:
        detail = "YOU +%sK" % (view["personal_new"] // 1000)
    caption_y = 52 if size > 4 else 47
    if detail:
        x = round((160 - font.width(caption) - 8 - font.width(detail)) / 2)
        font.text(p, caption, x, caption_y, 1, MUTED)
        font.text(p, detail, x + font.width(caption) + 8, caption_y, 1, PENDING)
    else:
        centered(p, caption, caption_y, 1, color if view["success"] else MUTED)
    scene.draw(p, view, tuning, frame)
    p.layer("header")
    p.rect(0, 59, 160, 1, "#262c3a")
    if view["success"]:
        progress = min(1, view["success_age"] / 400)
        p.rect(0, 59, round(160 * (1 - (1 - progress) ** 3)), 1, color)
    if view["progress"] is not None and not view["success"]:
        p.rect(4, 11, 152, 2, "#262c3a")
        p.rect(4, 11, round(152 * max(0, min(1, view["progress"]))), 2, color)


def fatal(p, message):
    p.rect(0, 0, 160, 120, INK)
    centered(p, "WALKING", 17, 2, WHITE)
    centered(p, "PAUSED", 35, 2, "#e88276")
    for index, line in enumerate((message[:24], message[24:48])):
        centered(p, line, 65 + index * 10, 1, MUTED)
    centered(p, "PRESS HOME TO RETURN", 105, 1, WHITE)
