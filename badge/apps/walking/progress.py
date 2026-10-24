"""Merge cumulative steps; callers must check partner and game identity first."""


def merge_counts(known, incoming):
    """Keep each player's highest count without changing either input."""
    merged = {}
    for snapshot in (known, incoming):
        for badge_id, count in snapshot.items():
            if not isinstance(badge_id, str) or not badge_id.strip():
                raise ValueError("A player needs a device ID")
            if type(count) is not int or count < 0:
                raise ValueError("Steps must be a nonnegative integer")
            merged[badge_id] = max(merged.get(badge_id, 0), count)
    if len(merged) > 2:
        raise ValueError("This game has two players")
    return merged


def display_totals(own_id, counts, last_sync):
    """Return live own steps and the last confirmed team/partner counts."""
    own = counts[own_id]
    if len(last_sync) != 2 or own_id not in last_sync:
        return own, None, None
    team = sum(last_sync.values())
    return own, team, team - last_sync[own_id]
