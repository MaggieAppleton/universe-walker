"use strict";
// Mirrors badge/apps/walking/walking_ui.py: Moment() and model().
(() => {
const GOAL = 10000, ARRIVAL_MS = 6000;
const WEARERS = { f95119f417c67d7e: "Maggie", "79469e7227b64f70": "Martin" };
const WARNINGS = {
  "Step sensor unavailable": "Step sensor unavailable",
  "Progress not saved": "Progress not saved",
  "Sync paused - reopen Walking": "Sync paused, reopen Walking",
};
const COOLDOWN = ["Move badges apart", "Pull badges apart", "Synced"];
const RETRY = { "Hold together to retry": true, "Could not sync - try again": false };

function moment(own, team, partner, status, progress, successTotal, prevTeam) {
  const success = successTotal !== null && successTotal !== undefined;
  if (success) team = successTotal;
  const fresh = team === null ? own : Math.max(0, own - (team - partner));
  const m = { own, team, partner, goal: GOAL, status: "Hold badges back to back to sync", tone: null,
    hold: null, lost: false, together: false, unknownPartner: team === null };
  if (success) m.phase = "success";
  else if (progress !== null && progress !== undefined) {
    m.phase = progress < 1 ? "holding" : "connecting";
    m.hold = Math.min(1, progress);
  } else if (status === "Syncing...") m.phase = "syncing";
  else if (COOLDOWN.includes(status)) m.phase = "cooldown";
  else if (status in RETRY) { m.phase = "retry"; m.lost = RETRY[status]; }
  else {
    m.phase = "apart";
    if (status in WARNINGS) { m.status = WARNINGS[status]; m.tone = "warn"; }
  }
  m.newSteps = m.phase === "success" || m.phase === "cooldown" ? 0 : fresh;
  const confirmed = team || 0;
  m.shared = Math.min(1, confirmed / GOAL);
  m.mine = Math.min(1, (confirmed + fresh) / GOAL);
  m.reached = team !== null && team >= GOAL;
  m.prevTeam = prevTeam;
  m.arrival = false;
  return m;
}

// One tracker per badge holds what walking_ui keeps in module globals.
function tracker() {
  const s = { settled: 0, successPrev: null, arrivalPending: false, arrivalUntil: null };
  return function model(own, team, partner, status, progress, successTotal, now) {
    const succeeding = successTotal !== null && successTotal !== undefined;
    if (succeeding && s.successPrev === null) {
      s.successPrev = s.settled;
      s.arrivalPending = s.settled < GOAL && GOAL <= successTotal;
    }
    const m = moment(own, team, partner, status, progress, successTotal, succeeding ? s.successPrev : team);
    if (!succeeding) {
      s.successPrev = null;
      s.settled = team || 0;
      if (s.arrivalPending) { s.arrivalPending = false; s.arrivalUntil = now + ARRIVAL_MS; }
      m.arrival = s.arrivalUntil !== null && now < s.arrivalUntil && m.reached && ["apart", "cooldown"].includes(m.phase);
    }
    return m;
  };
}

// The design-jig renderer keys a few drawings off fixture ids.
function forPaint(m) {
  const id = m.arrival ? "goal" : m.phase === "retry" && m.lost ? "timeout" : m.phase;
  return { ...m, id, phase: m.arrival ? "apart" : m.phase };
}

// Badges stop advertising while linked, so the page fills the gap: a badge
// that goes quiet mid-hold is syncing, and one confirmed total shows as a
// shared success on both screens at once.
const QUIET_MS = 900, CELEBRATE_MS = 4500, PAIRING = ["holding", "connecting", "syncing"];

function coordinator() {
  const teams = new Map();
  let party = null, parties = 0;
  return {
    // Feed each snapshot; returns true when a new shared sync begins.
    observe(badges, now) {
      let started = false;
      for (const b of badges) {
        const known = teams.has(b.id), prev = teams.get(b.id);
        const rose = known && b.team !== null && (prev === null || b.team > prev);
        if ((b.success || rose) && b.team !== null && (!party || party.total !== b.team)) {
          party = { total: b.team, until: now + CELEBRATE_MS, n: ++parties };
          started = true;
        }
        if (b.success && party && party.total === b.team) party.until = Math.max(party.until, now + 1500);
        teams.set(b.id, b.team);
      }
      return started;
    },
    celebrating(now) { return party !== null && now < party.until; },
    // Screen inputs for one badge, given how long since it was last heard.
    inputs(b, quietMs, now) {
      const raw = { own: b.own, team: b.team, partner: b.partner, status: b.status,
        progress: b.progress, successTotal: b.success ? b.team : null };
      if (this.celebrating(now)) return { ...raw, status: "Synced", progress: null, successTotal: party.total };
      if (b.progress !== null && b.progress !== undefined && quietMs > QUIET_MS)
        return { ...raw, status: "Syncing...", progress: null };
      return raw;
    },
  };
}

const api = { GOAL, WEARERS, PAIRING, QUIET_MS, CELEBRATE_MS, moment, tracker, forPaint, coordinator };
if (typeof module !== "undefined") module.exports = api;
if (typeof window !== "undefined") window.LiveModel = api;
})();
