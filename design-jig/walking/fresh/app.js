"use strict";
(() => {
const { DIRECTIONS, paint } = window.Directions;
const { GOAL, CASES, model } = window.Walking;
const MAP_COLUMNS = [["pending", "Walking"], ["apart", "Up to date"], ["goal", "Arrival"]];

const kit = DialKit.createDialKit("Walking fresh", {
  badge: { type: "select", options: ["Maggie", "Martin"], default: "Maggie" },
  direction: { type: "select", options: Object.entries(DIRECTIONS).map(([value, d]) => ({ value, label: d.label })), default: "horizon" },
  world: { type: "select", options: Object.entries(window.Worlds.WORLDS).map(([value, w]) => ({ value, label: w.label })), default: "coast" },
  mapStyle: { type: "select", options: Object.entries(window.Directions.MAPS).map(([value, s]) => ({ value, label: s.label })), default: "paper" },
  landmark: { type: "select", options: [{ value: "lighthouse", label: "Lighthouse" }, { value: "big", label: "Big lighthouse" }, { value: "flag", label: "Flag" }], default: "big" },
  events: { type: "select", options: [{ value: "fullscreen", label: "Full screen" }, { value: "status", label: "Status line" }], default: "fullscreen" },
  sky: { type: "select", options: [{ value: "gradient", label: "Gradient" }, { value: "solid", label: "Solid" }], default: "gradient" },
  big: [70, 48, 96, 2],
  small: [14, 10, 18, 1],
  title: [29, 20, 36, 1],
  trail: [12, 4, 14, 1],
  scale: [1, 0.7, 1.6, 0.05],
  gap: [24, 12, 32, 1],
  partnerAlpha: [0.55, 0.2, 1, 0.05],
  stride: [0.4, 0, 1, 0.1],
  holdProgress: [0.65, 0, 1, 0.05],
  zoom: { type: "select", options: [{ value: "1", label: "Actual size" }, { value: "2", label: "2× pixels" }], default: "1" },
}, { id: "walking-fresh-v5", persist: true });
DialKit.createDialRoot({ theme: "light", position: "top-right" });

const compare = document.getElementById("compare-grid");
const statesRoot = document.getElementById("states");
const compareCells = [], stateCells = [];
let current;

function canvas(label) {
  const el = document.createElement("canvas");
  el.width = 320; el.height = 240; el.className = "badge";
  el.setAttribute("role", "img"); el.setAttribute("aria-label", label);
  return el;
}

function buildCompare() {
  for (const [id, style] of Object.entries(window.Directions.MAPS)) {
    const head = document.createElement("div"); head.className = "row-label";
    const pick = document.createElement("button"); pick.type = "button"; pick.textContent = style.label; pick.dataset.map = id;
    pick.onclick = () => kit.setValues({ mapStyle: id, direction: "map" });
    head.append(pick); compare.append(head);
    for (const [state, label] of MAP_COLUMNS) {
      const el = canvas(`${style.label} map, ${label}`);
      const tile = document.createElement("div"); tile.append(el, caption(label)); compare.append(tile);
      compareCells.push({ el, state, mapStyle: id });
    }
  }
}

const WORLD_COLUMNS = [["pending", "gradient", "Walking"], ["goal", "gradient", "Arrival"], ["pending", "solid", "Solid sky"]];
const MOMENTS = [["holding", "Holding steady"], ["connecting", "Connecting"], ["syncing", "Swapping steps"], ["ack", "Confirming"],
  ["success", "Synced"], ["no_change", "Already up to date"], ["cooldown", "Move apart"], ["timeout", "Lost connection"], ["goal", "Goal reached"]];
const worldCells = [], momentCells = [], landmarkCells = [];
const LANDMARKS = [["lighthouse", "Lighthouse"], ["big", "Big lighthouse"], ["flag", "Flag"]];

function buildLandmarks() {
  const grid = document.getElementById("landmark-grid");
  for (const [state, row] of [["pending", "Walking"], ["goal", "Arrival"]]) {
    const head = document.createElement("div"); head.className = "row-label"; head.textContent = row; grid.append(head);
    for (const [landmark, label] of LANDMARKS) {
      const el = canvas(`Coast, ${label}, ${row}`);
      const tile = document.createElement("div"); tile.append(el, caption(label)); grid.append(tile);
      landmarkCells.push({ el, state, landmark });
    }
  }
}

function caption(text) { const el = document.createElement("div"); el.className = "tile-label"; el.textContent = text; return el; }

function buildWorlds() {
  const grid = document.getElementById("worlds-grid");
  for (const [id, w] of Object.entries(window.Worlds.WORLDS)) {
    const head = document.createElement("div"); head.className = "row-label";
    const pick = document.createElement("button"); pick.type = "button"; pick.textContent = w.label; pick.dataset.world = id;
    pick.onclick = () => kit.setValues({ world: id, direction: "horizon" });
    head.append(pick); grid.append(head);
    for (const [state, sky, label] of WORLD_COLUMNS) {
      const el = canvas(`${w.label}, ${label}`);
      const tile = document.createElement("div"); tile.append(el, caption(label)); grid.append(tile);
      worldCells.push({ el, state, sky, world: id });
    }
  }
}

function buildMoments() {
  const grid = document.getElementById("moments-grid");
  for (const [state, label] of MOMENTS) {
    const el = canvas(label);
    const tile = document.createElement("div"); tile.append(el, caption(label)); grid.append(tile);
    momentCells.push({ el, state });
  }
}

function buildStates() {
  let group = "";
  for (const item of CASES) {
    if (item.group !== group) {
      const h = document.createElement("h2"); h.className = "group"; h.textContent = group = item.group; statesRoot.append(h);
    }
    const s = document.createElement("section"); s.className = "state";
    const h = document.createElement("h3"); h.textContent = item.title;
    const p = document.createElement("p"); p.textContent = item.note;
    const screens = document.createElement("div"); screens.className = "screens";
    for (const badge of ["Maggie", "Martin"]) {
      const el = canvas(`${item.title}, ${badge}’s badge`);
      screens.append(el); stateCells.push({ el, state: item.id, badge });
    }
    s.append(h, p, screens); statesRoot.append(s);
  }
}

function render() {
  const o = { ...current };
  document.documentElement.style.setProperty("--screen-w", `${320 * +o.zoom}px`);
  document.documentElement.style.setProperty("--screen-h", `${240 * +o.zoom}px`);
  for (const cell of landmarkCells) paint(cell.el, "horizon", model(cell.state, o.holdProgress, o.badge), { ...o, world: "coast", landmark: cell.landmark });
  for (const cell of worldCells) paint(cell.el, "horizon", model(cell.state, o.holdProgress, o.badge), { ...o, world: cell.world, sky: cell.sky });
  document.querySelectorAll("[data-world]").forEach(b => b.setAttribute("aria-pressed", b.dataset.world === o.world));
  for (const cell of compareCells) paint(cell.el, "map", model(cell.state, o.holdProgress, o.badge), { ...o, mapStyle: cell.mapStyle });
  for (const cell of stateCells) paint(cell.el, o.direction, model(cell.state, o.holdProgress, cell.badge), { ...o, badge: cell.badge });
  document.querySelectorAll("[data-map]").forEach(b => b.setAttribute("aria-pressed", o.direction === "map" && b.dataset.map === o.mapStyle));
  document.getElementById("all-title").textContent = `Every state, ${DIRECTIONS[o.direction].label}`;
  document.getElementById("summary").textContent = `${GOAL.toLocaleString("en-US")}-step goal, ${o.badge}’s badge`;
  document.getElementById("values").textContent = JSON.stringify({ goal: GOAL, ...o });
}

document.getElementById("copy").onclick = async () => {
  const msg = document.getElementById("message");
  try { await navigator.clipboard.writeText(JSON.stringify({ goal: GOAL, ...current }, null, 2)); msg.textContent = "Settings copied."; }
  catch { msg.textContent = "Copy blocked; settings are shown above."; }
};
document.getElementById("reset").onclick = () => kit.resetValues();

// Moments loop so the loading states can be judged in motion.
let last = 0;
function animate(now) {
  if (current && now - last > 33) {
    last = now;
    for (const cell of momentCells) paint(cell.el, current.direction, model(cell.state, current.holdProgress, current.badge), { ...current, t: now });
  }
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

buildLandmarks();
buildWorlds();
buildMoments();
buildCompare();
buildStates();
document.fonts.load('500 16px "Mona Sans"').finally(() => {
  kit.subscribe(values => { current = values; render(); });
});
window.walkingFresh = { kit, render };
})();
