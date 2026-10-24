"""Outlined hikers from the approved pixel study; no radio or counter state."""

HEADS = (
    ("...hhhh..", "..hhhhhh.", ".hhhhsss.", "hh.hsses.", "h...sss.."),
    ("....w....", "...cccc..", "..cccccc.", "..hhsses.", "...hsss.."),
)
BODIES = (
    ("...jjjj..", "..jjjjjj.", "..djjjjs.", "...jjjj..", "...pppp..", "..pp..pp.", ".pp....pp", ".bb....bb"),
    ("...jjjj..", "..jjjjjj.", "..djjjjs.", "...jjjj..", "...pppp..", "...pp.p..", "...pp.p..", "...bb.bb."),
)
COMMON = {"s": "#fde4c8", "e": "#20141a", "p": "#2c3450", "b": "#5a3820", "w": "#f6f2ea"}
PALETTES = (
    dict(COMMON, h="#8a3c1c", j="#f05a46", d="#b8362a", c="#8a3c1c", o="#2a1418"),
    dict(COMMON, h="#3a2c28", j="#4c8cf0", d="#2a5ab8", c="#1f3c80", o="#121a34"),
)


def draw(painter, person, cx, feet, frame=1, ghost=False, solid_ghost=True):
    rows = HEADS[person] + BODIES[frame % 2]
    palette = PALETTES[person]
    x0, y0 = round(cx - 5.5), round(feet) - len(rows)

    def at(x, y):
        return 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] != "."

    for y in range(-1, len(rows) + 1):
        for x in range(-1, 10):
            if at(x, y):
                ch = rows[y][x]
                if ghost and not solid_ghost and (x + y) % 2:
                    continue
                pen = palette[ch]
                if ghost and solid_ghost and ch in ("j", "d"):
                    pen = "#f2aa93" if person == 0 else "#a2c6f6"
            elif any(at(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                pen = palette["o"] if not ghost or solid_ghost else palette["j"]
            else:
                continue
            painter.rect(x0 + x + 1, y0 + y, 1, 1, pen)
