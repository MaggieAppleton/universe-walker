"""Coast walk: the last confirmed shared total in the sky, both hikers on the trail."""

import coast_scene as coast
import hikers
import moments
import painter as P

GOAL = 10000
GOAL_LABEL = "of %s shared steps" % P.fmt(GOAL)
BACKGROUND = P.rgb("#151d3b")
WHITE = P.rgb("#ffffff")
SOFT = P.rgb("#ebeeff", 0.74)
AMBER, GOLD = P.rgb("#ffb547"), P.rgb("#ffd27a")
TONES = {"warn": P.rgb("#ff9b85")}
BIG, SMALL, GAP = 70, 14, 24
# Native font calibration: 3px above the installed baseline of 78.
# The browser measures its own font ink and keeps its existing placement.
COUNT_BASELINE = 75
PARTNER_ALPHA, STRIDE = 0.55, 0.4
ARRIVAL_MS = 6000

WEARERS = {"f95119f417c67d7e": "Maggie", "79469e7227b64f70": "Martin"}
WARNINGS = {
    "Step sensor unavailable": "Step sensor unavailable",
    "Progress not saved": "Progress not saved",
    "Sync paused - reopen Walking": "Sync paused, reopen Walking",
}
COOLDOWN = ("Move badges apart", "Pull badges apart", "Synced")
RETRY = {"Hold together to retry": True, "Could not sync - try again": False}

me, partner = "Maggie", "Martin"


def set_badge(device_id):
    global me, partner
    me = WEARERS.get(device_id, "Maggie")
    partner = "Martin" if me == "Maggie" else "Maggie"


class Moment:
    """What the screen shows, mapped from the app's sync state."""

    def __init__(self, own, team, partner_steps, status, progress, success_age, success_total, prev_team):
        if success_age is not None and success_total is not None:
            team = success_total
        self.me = me
        self.team = team
        fresh = own if team is None else max(0, own - (team - partner_steps))
        self.status, self.tone = "Hold badges back to back to sync", None
        self.hold, self.lost = None, False
        if success_age is not None and success_total is not None:
            self.phase = "success"
        elif progress is not None:
            self.phase = "holding" if progress < 1 else "connecting"
            self.hold = min(1, progress)
        elif status == "Syncing...":
            self.phase = "syncing"
        elif status in COOLDOWN:
            self.phase = "cooldown"
        elif status in RETRY:
            self.phase, self.lost = "retry", RETRY[status]
        else:
            self.phase = "apart"
            if status in WARNINGS:
                self.status, self.tone = WARNINGS[status], "warn"
        self.new_steps = 0 if self.phase in ("success", "cooldown") else fresh
        confirmed = team or 0
        self.shared = min(1, confirmed / GOAL)
        self.mine = min(1, (confirmed + fresh) / GOAL)
        self.reached = team is not None and team >= GOAL
        self.prev_team = prev_team
        self.arrival = False


# The confirmed total before the current success, and the arrival timer.
_settled = 0
_success_prev = None
_arrival_pending = False
_arrival_until = None


def model(own, team, partner_steps, status, progress=None, success_age=None, success_total=None, now=0):
    global _settled, _success_prev, _arrival_pending, _arrival_until
    succeeding = success_age is not None and success_total is not None
    if succeeding and _success_prev is None:
        _success_prev = _settled
        _arrival_pending = _settled < GOAL <= success_total
    m = Moment(own, team, partner_steps, status, progress, success_age, success_total,
               _success_prev if succeeding else team)
    if not succeeding:
        _success_prev = None
        _settled = team or 0
        if _arrival_pending:
            _arrival_pending = False
            _arrival_until = now + ARRIVAL_MS
        m.arrival = (_arrival_until is not None and now < _arrival_until
                     and m.reached and m.phase in ("apart", "cooldown"))
    return m


def people(m):
    span = coast.GOAL_D - coast.START_D
    # Stop just short of the destination so walkers never hide the landmark.
    end = coast.GOAL_D - GAP * 0.6
    shared_d = min(end, coast.START_D + m.shared * span)
    mine_d = min(end, coast.START_D + m.mine * span)
    at = coast.TRAIL.point_at
    if m.arrival:
        figures = [(at(shared_d - GAP), m.me, 1, 0, True, 1), (at(shared_d), partner, -1, 0, True, 1)]
    else:
        # Overlapping walkers step apart; at the trailhead the partner steps forward instead.
        partner_d = min(shared_d, mine_d) - GAP * 0.75 if abs(mine_d - shared_d) < GAP else shared_d
        if at(partner_d)[0] < 14:
            partner_d = max(shared_d, mine_d) + GAP * 0.75
        figures = [(at(partner_d), partner, 1, 0.15, False, PARTNER_ALPHA), (at(mine_d), m.me, 1, STRIDE, False, 1)]
    figures.sort(key=lambda f: f[0][1])
    for (x, y), who, facing, phase, cheer, alpha in figures:
        hikers.draw(x, y, who, facing, phase, cheer, alpha)


def hud(m):
    """The synced count and live local addition share the large number row."""
    P.text(m.status, 160, 22, SMALL, TONES.get(m.tone, SOFT))
    # Before the first sync, the large number is explicitly personal.
    if m.team is None:
        P.big_number(P.fmt(m.new_steps), 160, COUNT_BASELINE, BIG, 280, WHITE)
        P.text("Your steps, not synced yet", 160, 112, SMALL, SOFT)
        return
    if m.new_steps > 0:
        P.big_runs([(P.fmt(m.team), WHITE), ("+%s" % P.fmt(m.new_steps), AMBER)],
                   160, COUNT_BASELINE, BIG, 280)
    else:
        P.big_number(P.fmt(m.team), 160, COUNT_BASELINE, BIG, 280, WHITE)
    if m.reached:
        P.runs([("shared steps", SOFT), ("Goal reached", GOLD)], 160, 112, SMALL)
    else:
        P.text(GOAL_LABEL, 160, 112, SMALL, SOFT)


def draw(own, team, partner_steps, status, progress=None, success_age=None, success_total=None):
    now = badge.ticks
    m = model(own, team, partner_steps, status, progress, success_age, success_total, now)
    screen.antialias = image.X4
    screen.font = P.FONT
    coast.background()
    coast.progress(m.shared, m.mine)
    if m.reached:
        coast.lighthouse(screen, True)
    if m.phase in moments.EVENTS and not m.arrival:
        moments.draw(m, now, partner)
        return
    people(m)
    if m.arrival:
        moments.arrival(m, now)
    else:
        hud(m)


def _lines(message, width=296):
    lines, line = [], ""
    for word in message.split():
        candidate = (line + " " + word).strip()
        if line and P.measure(candidate, SMALL) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return (lines + [line])[:2]


def error(message):
    screen.font = P.FONT
    screen.pen = P.rgb("#151a2c")
    screen.rectangle(0, 0, P.W, P.H)
    P.text("Walking paused", 160, 92, SMALL * 1.5, WHITE)
    for i, line in enumerate(_lines(message)):
        P.text(line, 160, 124 + i * 20, SMALL, SOFT)
    P.text("Press HOME to return", 160, 210, SMALL, GOLD)
