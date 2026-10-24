"""Six environments for the same confirmed/shared walking journey."""

import math
from scenery_tools import sky, ridge, sun, tree, flag, beacon, mix

STYLES = (("sunset", "Sunset trail"), ("alpine", "Alpine pass"),
          ("valley", "River valley"), ("meadow", "Open fields"),
          ("coast", "Coastal path"), ("map", "Overland map"))


def draw(p, view, tuning):
    style, sky_style = tuning["landscape"], tuning["sky"]
    reached, height = view["shared_progress"] >= 1, tuning["lighthouseHeight"]
    if style == "sunset":
        sky(p, sky_style, ("#2d2f62", "#925182", "#f2ad74"), "#e5a4a3")
        sun(p, 26, 84, 5, "#ffe3a2")
        ridge(p, ((0, 86), (16, 80), (40, 87), (85, 82), (124, 87), (160, 87)), 90, "#63507d")
        p.rect(124, 85, 36, 6, "#4d83af")
        p.rect(0, 90, 160, 30, "#609e57")
        p.rect(0, 111, 160, 9, "#7ab568")
        beacon(p, height, reached)
    elif style == "alpine":
        sky(p, sky_style, ("#325477", "#97b6c1", "#d3dfd0"), "#94bfd0")
        ridge(p, ((0, 85), (26, 63), (52, 87), (88, 64), (118, 88), (145, 73), (160, 86)), 94, "#6a7b8b")
        ridge(p, ((16, 72), (26, 63), (37, 73)), 74, "#e7e9dc")
        ridge(p, ((78, 73), (88, 64), (99, 74)), 75, "#e7e9dc")
        p.rect(0, 92, 160, 28, "#718d66")
        ridge(p, ((0, 93), (50, 99), (95, 94), (160, 98)), 120, "#8da27a")
        tree(p, 18, 95, 10)
        tree(p, 57, 95, 8)
        flag(p, height, reached)
    elif style == "valley":
        sky(p, sky_style, ("#6688a6", "#c8c9b2", "#f2d49e"), "#aec9cf")
        ridge(p, ((0, 73), (30, 85), (65, 89), (105, 79), (160, 72)), 96, "#5c8066")
        ridge(p, ((0, 82), (39, 90), (80, 94), (124, 87), (160, 81)), 120, "#83a96a")
        p.rect(0, 110, 160, 10, "#a1bd7b")
        for y in range(87, 120):
            center, width = 72 + round((y - 87) * 0.9), 3 + (y - 87) // 4
            p.rect(center - width // 2, y, width, 1, "#65acb7")
        tree(p, 24, 98, 9, "#466e53")
        flag(p, height, reached)
    elif style == "meadow":
        sky(p, sky_style, ("#81b7ca", "#d6d5ad", "#f4dfaa"), "#f1d8a8")
        ridge(p, ((0, 84), (43, 79), (88, 87), (125, 82), (160, 84)), 120, "#8aa76b")
        ridge(p, ((0, 96), (50, 92), (102, 97), (160, 91)), 120, "#a9c47b")
        p.rect(0, 113, 160, 7, "#bed78d")
        for x, y in ((18, 96), (53, 111), (118, 92)):
            p.rect(x, y, 2, 2, "#d57268")
            p.rect(x + 1, y + 2, 1, 2, "#4e8054")
        flag(p, height, reached)
    elif style == "coast":
        sky(p, sky_style, ("#7089ab", "#c6b6b7", "#e7cba6"), "#accbd5")
        p.rect(0, 84, 160, 36, "#598da6")
        p.rect(0, 91, 160, 2, "#79b5bd")
        for x, y in ((12, 88), (52, 90), (109, 87)):
            p.rect(x, y, 15, 1, "#b2d4cb")
        ridge(p, ((0, 98), (35, 91), (73, 99), (110, 96), (145, 88), (160, 91)), 120, "#d8cb9b")
        ridge(p, ((0, 100), (35, 93), (73, 101), (110, 98), (145, 90), (160, 93)), 120, "#8ba776")
        beacon(p, height, reached)
    else:
        for y in range(60, 120):
            pen = mix("#f2e5c5", "#d3bf91", (y - 60) / 59) if sky_style == "gradient" else "#e7d8ae"
            p.rect(0, y, 160, 1, pen)
        for y in range(60, 120):
            center = 75 + round(10 * math.sin(y * 0.07))
            p.rect(center - 5, y, 10, 1, "#86afb5")
            p.rect(center - 5, y, 1, 1, "#b6c8b4")
        for x, base in ((15, 83), (24, 89), (43, 79), (111, 82), (122, 88)):
            tree(p, x, base, 9, "#6a8b5d")
        p.rect(76, 91, 16, 7, "#97724a")
        for x in range(78, 91, 3):
            p.rect(x, 92, 1, 5, "#c7aa7b")
        flag(p, height, reached)
