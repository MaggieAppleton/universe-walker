"""Hold UP to add demo steps: one per press, then a slowly accelerating ramp."""

DELAY_MS = 500
# Steps after t seconds of ramp are RATE * t**3: 10 at 1 s, 80 at 2 s,
# 1,250 at 5 s and 10,000 at 10 s, so a brief accidental press adds very few.
RATE = 10
# The button may raise your unsynced steps (the yellow +N) to at most this.
LIMIT = 9957


def room(own, synced_own):
    """How many more steps UP may add before the next sync."""
    return max(0, LIMIT - (own - synced_own))


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
