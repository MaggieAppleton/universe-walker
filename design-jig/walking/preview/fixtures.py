"""Every distinct app screen plus useful goal, count and positioning boundaries."""

CASES = (
    ("pending", "Walking", "New personal steps", "Amber path and personal steps are separate from the shared total."),
    ("apart", "Walking", "Apart, up to date", "The partner is shown at the last confirmed point."),
    ("pending_goal", "Walking", "Enough personal steps to finish", "The destination is reached only after those steps are acknowledged."),
    ("first", "First use", "First launch", "No confirmed total or invented partner contribution."),
    ("first_walk", "First use", "Before the first sync", "Personal steps accumulate; the shared count stays unset."),
    ("holding", "Sync", "Holding steady", "The native proximity hold is in progress; its timing can be scrubbed in the dials."),
    ("connecting", "Sync", "Connecting", "Hold complete; Bluetooth setup is still in progress."),
    ("syncing", "Sync", "Exchanging counts", "A brief connection; the old shared total remains visible."),
    ("ack", "Sync", "Waiting for acknowledgement", "Received counts do not become a confirmed team total yet."),
    ("success", "Sync", "Sync confirmed", "Both counts are saved and acknowledged. Move the badges apart."),
    ("no_change", "Sync", "Already up to date", "A repeat sync confirms the same total without double-counting."),
    ("zero_sync", "Sync", "A confirmed zero", "Zero shared steps is different from never having synced."),
    ("cooldown", "Sync", "Waiting for separation", "Sync is finished; another exchange needs separation."),
    ("rearmed", "Sync", "Ready for the next walk", "The new total is retained and the next hold can sync again."),
    ("timeout", "Retry", "Connection lost or timed out", "A failed exchange retains the last confirmed score."),
    ("failed", "Retry", "Could not sync", "The attempt failed without claiming new shared progress."),
    ("near", "Destination", "Near the destination", "A confirmed total just below the 500-step demo goal."),
    ("goal", "Destination", "At the destination", "The confirmed team count reaches the configured goal."),
    ("beyond", "Destination", "Past the goal", "Counts continue honestly; the route stops at the destination."),
    ("large", "Destination", "Large counts", "The counter fits long values and both people stay on screen."),
    ("sync_paused", "Recovery", "Sync unavailable", "Counting can continue; the screen asks to reopen Walking."),
    ("sensor", "Recovery", "Step sensor unavailable", "The saved team total is retained and the sensor failure is visible."),
    ("save", "Recovery", "Progress could not be saved", "No claim that the latest progress was safely stored."),
    ("fatal", "Recovery", "App paused", "A readable error and the existing HOME recovery action."),
)


def fixture(name, goal, person):
    shared = round(goal * 0.6)
    partner = shared // 2
    own = shared - partner
    base = dict(own=own, team=shared, partner=partner, status="Hold badges back to back",
                goal=goal, person=person)
    if name == "first":
        base.update(own=0, team=None, partner=None)
    elif name == "first_walk":
        base.update(own=47, team=None, partner=None)
    elif name in ("pending", "pending_goal", "holding", "connecting", "syncing", "ack", "timeout", "failed"):
        base["own"] += round(goal * (0.45 if name == "pending_goal" else 0.15))
    if name == "holding":
        base.update(status="Hold steady", progress=0.55)
    elif name == "connecting":
        base.update(status="Hold steady", progress=1.0)
    elif name in ("syncing", "ack"):
        base["status"] = "Syncing..."
    elif name in ("success", "cooldown", "rearmed", "no_change", "zero_sync"):
        base.update(team=round(goal * 0.85), own=round(goal * 0.45), partner=round(goal * 0.4))
        if name in ("success", "no_change", "zero_sync"):
            base.update(status="Synced", success_age=400)
            if name == "zero_sync":
                base.update(team=0, own=0, partner=0)
            elif name == "no_change":
                base.update(team=shared, own=own, partner=partner)
        elif name == "cooldown":
            base["status"] = "Move badges apart"
    elif name == "timeout":
        base["status"] = "Hold together to retry"
    elif name == "failed":
        base["status"] = "Could not sync - try again"
    elif name in ("near", "goal", "beyond", "large"):
        total = {"near": goal - 15, "goal": goal, "beyond": goal + 60, "large": 1000025}[name]
        base.update(team=total, partner=total // 2, own=total - total // 2)
    elif name in ("sync_paused", "sensor", "save"):
        base["status"] = {"sync_paused": "Sync paused - reopen Walking",
                          "sensor": "Step sensor unavailable", "save": "Progress not saved"}[name]
    return base
