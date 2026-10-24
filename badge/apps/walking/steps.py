"""Turn a frequently polled 16-bit pedometer into a game step total."""


class StepCounter:
    def __init__(self, saved_total=0):
        self.total = saved_total
        self.previous = None

    def update(self, raw_count):
        current = raw_count & 0xFFFF
        previous = self.previous
        self.previous = current
        if previous is None:
            return 0
        delta = (current - previous) & 0xFFFF
        # At a 250 ms poll interval, a larger jump indicates a sensor reset
        # or invalid reading. Rebaseline instead of inventing thousands of steps.
        if delta > 32:
            return 0
        self.total += delta
        return delta
