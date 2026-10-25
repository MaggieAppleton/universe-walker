"""Full-screen pairing, confirmation and arrival moments (design-jig events.js)."""

import math

import painter as P
from hikers import JACKETS

WHITE, SOFT, DIM = P.rgb("#ffffff"), P.rgb("#e1e8ff", 0.72), P.rgb("#ffffff", 0.14)
AMBER, GOOD, WARN, GOLD = P.rgb("#ffb547"), P.rgb("#7ee2a0"), P.rgb("#ff9b85"), P.rgb("#ffd56a")
VEIL, SCREEN_GLASS, CHECK_DARK = P.rgb("#090c1c", 0.74), P.rgb("#090c1c", 0.5), P.rgb("#0f2a1a")
FAINT = P.rgb("#ffffff", 0.16)
CONFETTI = [P.rgb(h) for h in ("#ffd56a", "#7ee2a0", "#ff8a7a", "#8ab8ff", "#ffffff")]
CX, CY, R = 160, 82, 38
TITLE, SMALL, BIG = 29, 14, 70
EVENTS = ("holding", "connecting", "syncing", "success", "cooldown", "retry")

_confetti = None
_arrival_veil = None


def ring(a0, a1, pen, width=6, r=R):
    P.arc(screen, CX, CY, r, a0, a1, width, pen)


def badges(apart=0, pen=WHITE):
    """Two badges back to back: the gesture the player is making."""
    P.rrect(screen, CX - 15 - apart, CY - 13, 13, 26, 3, pen)
    P.rrect(screen, CX + 2 + apart, CY - 13, 13, 26, 3, pen)
    P.rrect(screen, CX - 12.5 - apart, CY - 10, 8, 10, 1.5, SCREEN_GLASS)
    P.rrect(screen, CX + 4.5 + apart, CY - 10, 8, 10, 1.5, SCREEN_GLASS)


def arrow(x0, y, direction, pen, length=14):
    x1 = x0 + direction * length
    P.line(screen, x0, y, x1, y, 3, pen)
    P.line(screen, x1, y, x1 - direction * 5, y - 5, 3, pen)
    P.line(screen, x1, y, x1 - direction * 5, y + 5, 3, pen)


def check(x, y, pen):
    P.line(screen, x - 9, y, x - 3, y + 6, 3.4, pen)
    P.line(screen, x - 3, y + 6, x + 9, y - 6, 3.4, pen)


def words(title, pen, sub=None, extra=None):
    P.big_number(title, 160, 174, TITLE, 296, pen)
    if sub:
        P.text(sub, 160, 198, SMALL, SOFT)
    if extra:
        P.text(extra, 160, 226, SMALL, SOFT)


def confetti(seed, t):
    """Falling paper kept clear of the text."""
    global _confetti
    if _confetti is None:
        _confetti = [shape.rounded_rectangle(-3, -1.4, 6, 2.8, 1) for _ in CONFETTI]
    r = seed

    def rand():
        nonlocal r
        r = (r * 9301 + 49297) % 233280
        return r / 233280

    for i in range(40):
        x = rand() * 320
        y = (rand() * 260 + t * (0.02 + rand() * 0.03)) % 260 - 10
        if 60 < x < 260 and 14 < y < 206:
            continue
        piece = _confetti[i % len(CONFETTI)]
        piece.transform = mat3().translate(x, y).rotate((rand() * math.pi + t * 0.003) * 57.29578)
        screen.pen = CONFETTI[i % len(CONFETTI)]
        screen.shape(piece)


def shared_words(team):
    return "No shared steps yet" if team is None else "%s shared steps" % P.fmt(team)


def draw(m, t, partner):
    screen.pen = VEIL
    screen.rectangle(0, 0, P.W, P.H)
    turn, top = P.TURN, P.TOP
    if m.phase == "holding":
        ring(0, turn, DIM)
        ring(top, top + turn * max(0.02, m.hold), WHITE)
        badges()
        words("Hold steady", WHITE, "Keep badges back to back")
    elif m.phase == "connecting":
        for i in range(3):
            k = (t / 1400 + i / 3) % 1
            screen.alpha = int((1 - k) * 0.5 * 255)
            ring(0, turn, WHITE, 2, R + 6 + k * 20)
        screen.alpha = 255
        ring(0, turn, WHITE)
        badges()
        words("Connecting", WHITE, "Found %s's badge" % partner)
    elif m.phase == "syncing":
        a = t / 500
        ring(0, turn, DIM)
        ring(top + a, top + a + 1.1, JACKETS[m.me])
        ring(top + math.pi - a, top + math.pi - a + 1.1, JACKETS[partner])
        arrow(CX - 10, CY - 6, 1, WHITE, 20)
        arrow(CX + 10, CY + 6, -1, WHITE, 20)
        words("Swapping steps", WHITE,
              "Sending your +%s" % P.fmt(m.new_steps) if m.new_steps > 0 else "Sharing counts")
    elif m.phase == "success":
        success(m, t)
    elif m.phase == "cooldown":
        k = (math.sin(t / 300) + 1) / 2
        badges(4 + k * 8)
        arrow(CX - 26 - k * 8, CY, -1, AMBER)
        arrow(CX + 26 + k * 8, CY, 1, AMBER)
        words("Move badges apart", AMBER, shared_words(m.team) + (" saved" if m.team is not None else ""))
    elif m.phase == "retry":
        ring(top + 0.5, top + turn - 0.5, WARN)
        badges(6, WARN)
        still = "No shared steps yet" if m.team is None else "Still %s shared steps" % P.fmt(m.team)
        if m.lost:
            words("Lost connection", WARN, "Hold together to retry", still)
        else:
            words("Couldn't sync", WARN, "Move apart, then try again", still)


def success(m, t):
    repeat = m.prev_team == m.team and m.team > 0
    gained = m.team - m.prev_team
    if gained > 0:
        confetti(7, t)
    P.circle(screen, CX, 38, 18, FAINT if repeat else GOOD)
    check(CX, 38, GOOD if repeat else CHECK_DARK)
    P.text("Up to date" if repeat else "Synced!", 160, 86, TITLE, GOOD)
    P.big_number(P.fmt(m.team), 160, 152, BIG, 280, WHITE)
    if gained > 0:
        P.runs([("shared steps", SOFT), ("+%s together" % P.fmt(gained), GOOD)], 160, 182, SMALL)
    else:
        P.text("shared steps so far" if m.team == 0 else "No new steps since last sync", 160, 182, SMALL, SOFT)
    P.text("Move badges apart", 160, 222, SMALL, AMBER)


def arrival(m, t):
    """Arrival happens over the world itself: walkers cheer at the landmark."""
    global _arrival_veil
    if _arrival_veil is None:
        stops = [(0, P.rgb("#090c1c", 0.5)), (1, P.rgb("#090c1c", 0))]
        _arrival_veil = brush.gradient(brush.LINEAR, 0, 0, 0, 1, stops, mat3().translate(0, 0).scale(P.W, 130))
    screen.pen = _arrival_veil
    screen.shape(shape.rectangle(0, 0, P.W, 130))
    confetti(3, t)
    P.text("You made it!", 160, 52, TITLE, GOLD)
    P.text("%s steps together" % P.fmt(m.team), 160, 76, SMALL, WHITE)
