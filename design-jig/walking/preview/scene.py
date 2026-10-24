"""A native-friendly 160 by 120 landscape, painted with rectangles."""

import math
import hikers
import landscapes

SKY = ("#2d2f62", "#58428a", "#b45f80", "#ef9a6c")
DEFAULTS = dict(skyBands=3, trailY=104, pathWidth=4, walkerGap=16,
                lighthouseHeight=22, solidPartner=True, edgePath=True,
                cleanSky=True, cleanLighthouse=True, countSize=4,
                landscape="sunset", sky="gradient")


def path_y(x, tuning):
    if tuning["landscape"] == "map":
        return 100 + round(4 * math.sin(x * 0.055 + 0.4))
    if tuning["landscape"] == "alpine":
        return 105 + round(2 * math.sin(x * 0.06))
    return tuning["trailY"] + round(2.5 * math.sin(x * 0.07))


def lighthouse(p, tuning, reached):
    base, height, cx = 91, tuning["lighthouseHeight"], 146
    top = base - height
    if tuning["cleanLighthouse"]:
        p.rect(cx - 3, top + 6, 7, height - 6, "#f6f2ea")
        for y in range(top + 8, base, 7):
            p.rect(cx - 3, y, 7, min(3, base - y), "#d8423a")
        p.rect(cx - 4, top + 5, 9, 1, "#3a2a2a")
        p.rect(cx - 2, top + 2, 5, 3, "#ffe38a")
        p.rect(cx - 3, top + 1, 7, 1, "#3a2a2a")
        p.rect(cx - 1, top, 3, 1, "#d8423a")
        if reached:
            p.rect(cx - 13, top + 3, 9, 2, "#fff2b8")
    else:
        for y in range(height - 5):
            half = 2 + int(y / (height - 5) * 1.6)
            p.rect(cx - half, base - 1 - y, half * 2 + 1, 1,
                   "#d8423a" if y // 3 % 2 == 0 else "#f6f2ea")
        p.rect(cx - 3, top + 4, 7, 1, "#3a2a2a")
        p.rect(cx - 2, top + 2, 5, 2, "#ffe38a")
        p.rect(cx - 2, top + 1, 5, 1, "#3a2a2a")
        p.rect(cx - 1, top, 3, 1, "#d8423a")
        for i in range(4, 18):
            if i % 2 == 0 or i < 9:
                p.rect(cx - i, top + 4 + round(i * 0.08), 1, 1, "#fff2b8")


def reference_background(p, view, tuning):
    p.layer("scenery")
    top, horizon = 60, 88
    count = tuning["skyBands"]
    bands = [SKY[round(i * 3 / (count - 1))] for i in range(count)]
    for i, pen in enumerate(bands):
        y = top + i * (horizon - top) // count
        end = top + (i + 1) * (horizon - top) // count
        p.rect(0, y, 160, end - y, pen)
        if not tuning["cleanSky"] and i:
            for x in range(i % 2, 160, 2):
                p.rect(x, y - 1, 1, 1, pen)
    for y in range(-5, 6):
        half = int(math.sqrt(max(0, 25 - y * y)))
        p.rect(26 - half, 84 + y, half * 2 + 1, 1, "#ffe0a0")
    for x in range(124):
        if tuning["cleanSky"]:
            ridge = max(0, 6 - abs(x - 12) // 4, 4 - abs(x - 91) // 7)
            y = horizon - ridge
        else:
            y = round(horizon - 4 - 3 * math.sin(x * 0.08 + 0.5) - 2 * math.sin(x * 0.21))
        p.rect(x, y, 1, horizon - y, "#55467f")
    p.rect(124, 85, 36, 4, "#3f6fb2")
    p.rect(130, 86, 5, 1, "#8fb8ea")
    p.rect(0, horizon, 160, 32, "#5ea152")
    grass_y = 111 if tuning["cleanSky"] else 106
    p.rect(0, grass_y, 160, 120 - grass_y, "#6db55c")
    if not tuning["cleanSky"]:
        def noise(value):
            value = math.sin(value * 127.1 + 311.7) * 43758.5453
            return value - math.floor(value)
        for x in range(1, 160, 2):
            p.rect(x, grass_y, 1, 1, "#5ea152")
        for k in range(18):
            p.rect(int(noise(k + 1000) * 160), 90 + int(noise(k + 1100) * 28),
                   1, 1, "#f4e27a" if noise(k + 1200) < 0.2 else "#3f7a3c")
    lighthouse(p, tuning, view["shared_progress"] >= 1)


def draw(p, view, tuning, frame=1):
    p.layer("scenery")
    if tuning["landscape"] == "reference":
        reference_background(p, view, tuning)
    else:
        landscapes.draw(p, view, tuning)
    p.layer("trail")
    left, right = (0, 159) if tuning["edgePath"] else (8, 136)
    span = right - left
    for x in range(left, right + 1):
        progress = (x - left) / span
        completed = "#b96346" if tuning["landscape"] == "map" else "#f3d692"
        pen = completed if progress <= view["shared_progress"] else (
            "#f2a33a" if progress <= view["own_progress"] else "#cbb780")
        y = path_y(x, tuning)
        p.rect(x, y - 1, 1, 1, "#b89660")
        p.rect(x, y, 1, tuning["pathWidth"], pen)
        p.rect(x, y + tuning["pathWidth"], 1, 1, "#b89660")

    def clamp(x):
        return max(8, min(151, round(x)))

    own_x = clamp(left + view["own_progress"] * span)
    shared_x = clamp(left + view["shared_progress"] * span)
    person = view["person"]
    if not view["confirmed"]:
        hikers.draw(p, person, own_x, path_y(own_x, tuning) + 2, frame)
        return
    if view["success"]:
        mid = clamp(shared_x)
        shared_x, own_x = mid - tuning["walkerGap"] / 2, mid + tuning["walkerGap"] / 2
    if abs(own_x - shared_x) < tuning["walkerGap"]:
        shared_x = own_x - tuning["walkerGap"]
    if shared_x < 8:
        own_x += 8 - shared_x
        shared_x = 8
    if own_x > 151:
        shared_x -= own_x - 151
        own_x = 151
    hikers.draw(p, 1 - person, shared_x, path_y(shared_x, tuning) + 2,
                1, not view["success"], tuning["solidPartner"])
    hikers.draw(p, person, own_x, path_y(own_x, tuning) + 2, frame)
