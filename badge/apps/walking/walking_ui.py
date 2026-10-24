"""Keep personal steps distinct from the last confirmed shared score."""

BACKGROUND = color.rgb(247, 245, 239)
INK = color.rgb(32, 48, 39)
MUTED = color.rgb(100, 113, 102)
ACCENT = color.rgb(31, 128, 75)
SOFT_GREEN = color.rgb(218, 239, 222)


def centred(text, y, pen, scale=1, max_height=80):
    screen.font = font.sins
    width, height = screen.measure_text(text)
    scale = min(scale, (screen.width - 32) / max(width, 1), max_height / max(height, 1))
    x = (screen.width - width * scale) / 2
    at = vec2(x, y)
    screen.pen = pen
    transform = mat3().translate(at).scale(scale, scale).translate(vec2(-x, -y))
    screen.text(text, at, transform=transform)


def clear():
    screen.pen = BACKGROUND
    screen.rectangle(screen.clip)


def confirmation(total, age):
    clear()
    t = max(0, min(1, age / 260))
    eased = 1 - (1 - t) ** 3
    cx = screen.width / 2
    screen.pen = SOFT_GREEN
    screen.shape(shape.circle(cx, 34, 13 + 3 * eased))
    screen.pen = ACCENT
    stroke = eased * 2
    for offset in (0, 1):
        first = min(1, stroke)
        screen.line(cx - 8, 34 + offset, cx - 8 + 6 * first, 34 + 7 * first + offset)
        if stroke > 1:
            second = stroke - 1
            screen.line(cx - 2, 41 + offset, cx - 2 + 13 * second, 41 - 15 * second + offset)
    centred("Synced", 65, ACCENT, scale=2, max_height=32)
    centred(str(total), 106, INK, scale=4, max_height=60)
    centred("Team total", 177, INK)
    centred("Move badges apart", screen.height - 28, MUTED)


def draw(own, team, partner, status, progress=None, success_age=None, success_total=None):
    if success_age is not None and success_total is not None:
        confirmation(success_total, success_age)
        return
    clear()
    centred("Your steps", 18, MUTED)
    centred(str(own), 48, INK, scale=5)
    centred("Team total: %s" % (team if team is not None else "--"), 148, ACCENT, scale=1.3, max_height=25)
    centred("Partner at last sync: %s" % (partner if partner is not None else "--"), 181, MUTED)
    centred(status, screen.height - 28, MUTED)
    if progress is not None:
        screen.pen = MUTED
        screen.rectangle(24, 201, screen.width - 48, 3)
        screen.pen = ACCENT
        screen.rectangle(24, 201, int((screen.width - 48) * max(0, min(1, progress))), 3)


def error(message):
    clear()
    centred("Walking paused", 40, INK)
    centred(message[:34], 90, INK)
    centred(message[34:68], 112, MUTED)
    centred("Press HOME to return", screen.height - 28, MUTED)
