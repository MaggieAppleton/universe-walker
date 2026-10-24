"""Simple pixel scenery primitives; all use the badge's rectangle painter."""


def mix(first, second, amount):
    a = [int(first[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(second[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % round(x + (y - x) * amount) for x, y in zip(a, b))


def sky(p, style, colors, solid):
    if style == "solid":
        p.rect(0, 60, 160, 32, solid)
        return
    for y in range(60, 92):
        fraction = (y - 60) / 31
        segment = min(len(colors) - 2, int(fraction * (len(colors) - 1)))
        local = fraction * (len(colors) - 1) - segment
        p.rect(0, y, 160, 1, mix(colors[segment], colors[segment + 1], local))


def ridge(p, points, bottom, pen):
    for index in range(len(points) - 1):
        left, right = points[index], points[index + 1]
        for x in range(left[0], right[0]):
            y = round(left[1] + (right[1] - left[1]) * (x - left[0]) / max(1, right[0] - left[0]))
            if y < bottom:
                p.rect(x, y, 1, bottom - y, pen)


def sun(p, cx, cy, radius, pen):
    for y in range(-radius, radius + 1):
        half = int(max(0, radius * radius - y * y) ** 0.5)
        p.rect(cx - half, cy + y, half * 2 + 1, 1, pen)


def tree(p, x, base, size=8, pen="#315e50"):
    p.rect(x, base - size, 1, size, "#6c4f39")
    for y in range(size - 2):
        half = min(4, y // 2)
        p.rect(x - half, base - size + y, half * 2 + 1, 1, pen)


def flag(p, height, reached):
    base, x = 92, 146
    top = base - height
    p.rect(x, top, 1, height, "#26372e")
    p.rect(x + 1, top + 1, 8, 5, "#5fed83" if reached else "#ed7254")
    p.rect(x + 1, top + 6, 5, 1, "#31513b")
    p.rect(x - 2, base - 1, 5, 2, "#b9c58c")


def beacon(p, height, reached):
    base, x = 91, 146
    top = base - height
    p.rect(x - 3, top + 6, 7, height - 6, "#f6f2ea")
    for y in range(top + 8, base, 7):
        p.rect(x - 3, y, 7, min(3, base - y), "#d8423a")
    p.rect(x - 4, top + 5, 9, 1, "#3a2a2a")
    p.rect(x - 2, top + 2, 5, 3, "#ffe38a")
    p.rect(x - 3, top + 1, 7, 1, "#3a2a2a")
    p.rect(x - 1, top, 3, 1, "#d8423a")
    if reached:
        p.rect(x - 13, top + 3, 9, 2, "#fff2b8")
