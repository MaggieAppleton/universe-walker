"""Present confirmed shared progress, keeping personal unshared steps honest."""

STATUS = {
    "Hold badges back to back": ("HOLD TO SYNC", "#f2f4f8"),
    "Hold steady": ("HOLD STEADY", "#6aa8ff"),
    "Syncing...": ("SYNCING", "#6aa8ff"),
    "Synced": ("SYNCED", "#5fed83"),
    "Move badges apart": ("MOVE APART", "#5fed83"),
    "Pull badges apart": ("MOVE APART", "#f2a33a"),
    "Hold together to retry": ("TRY AGAIN", "#f2a33a"),
    "Could not sync - try again": ("TRY AGAIN", "#f2a33a"),
    "Sync paused - reopen Walking": ("SYNC PAUSED", "#e88276"),
    "Step sensor unavailable": ("NO SENSOR", "#e88276"),
    "Progress not saved": ("NOT SAVED", "#e88276"),
}


def compose(own, team, partner, status, progress=None, success_age=None, goal=500, person=0):
    confirmed = team is not None and partner is not None
    shared = team if confirmed else 0
    personal_new = max(0, own - (team - partner)) if confirmed else own
    label, pen = STATUS.get(status, ("SYNC PAUSED", "#e88276"))
    if status == "Hold steady" and progress is not None and progress >= 1:
        label = "CONNECTING"
    success = success_age is not None
    if success:
        label, pen = "SYNCED", "#5fed83"
    caption = "SHARED STEPS" if not personal_new else "LAST SHARED"
    detail = "YOU +%s NEW" % format_count(personal_new) if personal_new else ""
    if not confirmed:
        caption, detail = "YOU %s - NOT SHARED" % format_count(own), ""
    elif success:
        caption, detail = "MOVE BADGES APART", ""
    elif status in ("Move badges apart", "Pull badges apart", "Synced"):
        caption, detail = "MOVE APART TO SYNC AGAIN", ""
    elif status == "Sync paused - reopen Walking":
        caption, detail = "REOPEN WALKING TO SYNC", ""
    elif status == "Step sensor unavailable":
        caption, detail = "STEP COUNTER UNAVAILABLE", ""
    elif status == "Progress not saved":
        caption, detail = "PROGRESS NOT SAVED", ""
    elif shared >= goal and not personal_new:
        caption = "WE MADE IT!"
    return dict(own=own, shared=shared, partner=partner, confirmed=confirmed,
                number=format_count(team) if confirmed else "--", caption=caption,
                detail=detail, label=label, pen=pen, progress=progress,
                success=success, success_age=success_age, person=person, goal=goal,
                personal_new=personal_new, shared_progress=min(1, shared / goal),
                own_progress=min(1, (shared + personal_new) / goal))


def format_count(value):
    # Keep this compatible with MicroPython: no locale or grouping format API.
    digits = str(value)
    groups = []
    while digits:
        groups.append(digits[-3:])
        digits = digits[:-3]
    return ",".join(reversed(groups))
