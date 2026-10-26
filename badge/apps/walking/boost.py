"""Demo buttons: hold UP/DOWN to ramp steps, hold SELECT to reset."""

DELAY_MS = 500
# Steps after t seconds of ramp are RATE * t**3: 10 at 1 s, 80 at 2 s,
# 1,250 at 5 s and 10,000 at 10 s, so a brief accidental press adds very few.
RATE = 10
# The button may raise your unsynced steps (the yellow +N) to at most this.
LIMIT = 9957
# Hold SELECT this long to clear every count, as on first start.
RESET_MS = 3000
# Show the reset countdown only once SELECT is clearly being held.
RESET_HINT_MS = 300


def room(own, synced_own):
    """How many more steps UP may add before the next sync."""
    return max(0, LIMIT - (own - synced_own))


def spare(own, synced_own):
    """How many steps DOWN may remove: only those not yet synced."""
    return max(0, own - synced_own)


class HoldBoost:
    def __init__(self):
        self.start = None
        self.given = 0

    def update(self, down, now):
        """Return the steps to add this frame; `now` is a frame timestamp in ms."""
        if not down:
            self.start = None
            return 0
        if self.start is None:
            self.start, self.given = now, 1
            return 1
        t = (now - self.start - DELAY_MS) / 1000
        if t <= 0:
            return 0
        target = 1 + int(RATE * t * t * t)
        added, self.given = target - self.given, target
        return added


class LongPress:
    """Fire once when a button has been held for `ms`; release re-arms it."""

    def __init__(self, ms=RESET_MS):
        self.ms = ms
        self.start = None
        self.fired = False

    def update(self, down, now):
        if not down:
            self.start, self.fired = None, False
            return False
        if self.start is None:
            self.start = now
        if self.fired or now - self.start < self.ms:
            return False
        self.fired = True
        return True

    def remaining(self, now):
        """Milliseconds left in an armed hold past the hint delay, else None."""
        if self.start is None or self.fired:
            return None
        held = now - self.start
        return self.ms - held if held >= RESET_HINT_MS else None
