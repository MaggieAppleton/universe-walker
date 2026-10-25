"use strict";
(() => {
// Preview-only counts; never written to a badge's saved progress.
const GOAL = 10000;
const SEED = { Maggie: 0, Martin: 9900 };
const PENDING = { Maggie: 60, Martin: 40 };
const CASES = [
  ["pending", "Walking", "New personal steps", "Your unshared steps stay amber, apart from the shared total."],
  ["apart", "Walking", "Apart, up to date", "Your partner stands where you last synced."],
  ["pending_goal", "Walking", "Enough personal steps to finish", "The destination waits until those steps are confirmed."],
  ["first", "First use", "First launch", "No confirmed total, no invented partner steps."],
  ["first_walk", "First use", "Before the first sync", "Personal steps grow; the shared count is still unset."],
  ["holding", "Pairing", "Holding steady", "Native proximity hold in progress."],
  ["connecting", "Pairing", "Connecting", "Hold complete; Bluetooth still setting up."],
  ["syncing", "Pairing", "Exchanging counts", "The old shared total stays visible."],
  ["ack", "Pairing", "Waiting for acknowledgement", "Received counts are not confirmed yet."],
  ["success", "Confirmation", "Sync confirmed", "Both counts saved and acknowledged."],
  ["no_change", "Confirmation", "Already up to date", "Repeat sync, no double counting."],
  ["zero_sync", "Confirmation", "A confirmed zero", "Zero shared steps, distinct from never synced."],
  ["cooldown", "Separation", "Waiting for separation", "Another exchange needs the badges apart first."],
  ["rearmed", "Separation", "Ready for the next walk", "New total kept; the next hold can sync."],
  ["timeout", "Retry", "Connection lost or timed out", "Keeps the last confirmed total."],
  ["failed", "Retry", "Could not sync", "No new shared progress claimed."],
  ["near", "Destination", "Near the destination", "Just below the 10,000-step goal."],
  ["goal", "Destination", "At the destination", "Confirmed team count reaches the goal."],
  ["beyond", "Destination", "Past the goal", "Counts continue; the route stops at the destination."],
  ["large", "Destination", "Large counts", "Long values shrink to fit."],
  ["sync_paused", "Recovery", "Sync unavailable", "Counting continues; reopen Walking."],
  ["sensor", "Recovery", "Step sensor unavailable", "Saved team total is kept."],
  ["save", "Recovery", "Progress could not be saved", "No claim that progress is stored."],
  ["fatal", "Recovery", "App paused", "Readable error and the HOME recovery action."],
].map(([id, group, title, note]) => ({ id, group, title, note }));

function fixture(name, badge = "Maggie") {
  const goal = GOAL;
  const them = badge === "Martin" ? "Maggie" : "Martin", shared = SEED.Maggie + SEED.Martin;
  const f = { own: SEED[badge], team: shared, partner: SEED[them], goal, phase: "apart" };
  if (name === "first") Object.assign(f, { team: null, partner: null });
  if (name === "first_walk") Object.assign(f, { own: SEED[badge] + PENDING[badge], team: null, partner: null });
  if (["pending", "pending_goal", "holding", "connecting", "syncing", "ack", "timeout", "failed"].includes(name))
    f.own += name === "pending_goal" ? 100 : PENDING[badge];
  if (["success", "cooldown", "rearmed", "no_change", "zero_sync"].includes(name)) {
    const maggie = SEED.Maggie + PENDING.Maggie, martin = SEED.Martin + PENDING.Martin;
    Object.assign(f, { team: maggie + martin, own: badge === "Martin" ? martin : maggie, partner: badge === "Martin" ? maggie : martin });
    if (name === "zero_sync") Object.assign(f, { team: 0, own: 0, partner: 0 });
  }
  if (["near", "goal", "beyond", "large"].includes(name)) {
    const total = { near: shared, goal, beyond: goal + 1200, large: 1000025 }[name];
    const maggie = name === "near" ? SEED.Maggie : PENDING.Maggie + Math.floor((total - goal) / 2), martin = total - maggie;
    Object.assign(f, { team: total, own: badge === "Martin" ? martin : maggie, partner: badge === "Martin" ? maggie : martin });
  }
  return f;
}

// Status copy fits the brief hold-to-sync flow; it never implies a live link.
const STATUS = {
  apart: ["Hold badges back to back to sync", "muted"],
  holding: ["Hold steady", "live"],
  connecting: ["Connecting", "live"],
  syncing: ["Swapping steps", "live"],
  ack: ["Confirming with partner", "live"],
  success: ["Synced", "good"],
  no_change: ["Synced, no new steps", "good"],
  cooldown: ["Move badges apart", "live"],
  timeout: ["Lost connection, hold together to retry", "warn"],
  failed: ["Couldn’t sync, try again", "warn"],
  sync_paused: ["Sync paused, reopen Walking", "warn"],
  sensor: ["Step sensor unavailable", "warn"],
  save: ["Progress not saved", "warn"],
};

function model(name, holdProgress = 0.55, badge = "Maggie") {
  const f = fixture(name, badge);
  const phase = { holding: "holding", connecting: "connecting", syncing: "syncing", ack: "ack",
    success: "success", no_change: "success", zero_sync: "success", cooldown: "cooldown",
    timeout: "retry", failed: "retry", fatal: "fatal" }[name] || "apart";
  const fresh = f.team === null ? f.own : f.own - (f.team - f.partner);
  const [status, tone] = STATUS[name] || STATUS[phase] || STATUS.apart;
  return {
    ...f, id: name, phase, status, tone,
    newSteps: phase === "success" || phase === "cooldown" ? 0 : fresh,
    hold: name === "holding" ? holdProgress : name === "connecting" ? 1 : null,
    shared: f.team === null ? 0 : Math.min(1, f.team / f.goal),
    mine: Math.min(1, ((f.team ?? 0) + fresh) / f.goal),
    reached: f.team !== null && f.team >= f.goal,
    prevTeam: name === "success" ? SEED.Maggie + SEED.Martin : f.team,
    together: ["holding", "connecting", "syncing", "ack", "success"].includes(phase),
    unknownPartner: f.team === null,
  };
}

window.Walking = { GOAL, SEED, PENDING, CASES, fixture, model };
})();
