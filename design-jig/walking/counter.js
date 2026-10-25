"use strict";
(() => {
const SCENE = {
  direction: "horizon", world: "coast", landmark: "big", events: "fullscreen", sky: "gradient",
  big: 70, small: 14, title: 29, trail: 12, scale: 1, gap: 24, partnerAlpha: .55, stride: .4,
  holdProgress: .65, mapStyle: "paper", zoom: "1", goal: window.Walking.GOAL,
};
const kit = DialKit.createDialKit("Walking count", {
  shared: [9900, 0, 1000025, 1],
  maggie: [5, 0, 12345, 1],
  martin: [20, 0, 12345, 1],
  big: [70, 48, 96, 2],
}, { id: "walking-large-contribution", persist: false });
DialKit.createDialRoot({ theme: "light", position: "bottom-right" });
let current;
const live = [], checks = [];

function pair(root, title, state) {
  const heading = document.createElement("div"); heading.className = "wearer"; heading.textContent = title;
  const grid = document.createElement("div"); grid.className = "pair";
  const row = { ...state, canvases: [] };
  for (const [style, label] of [["caption", "Current"], ["inline", "Adjusted"]]) {
    const cell = document.createElement("div");
    const caption = document.createElement("div"); caption.className = "label"; caption.textContent = label;
    const canvas = document.createElement("canvas"); canvas.width = 320; canvas.height = 240;
    canvas.setAttribute("role", "img"); canvas.setAttribute("aria-label", `${title}, ${label}`);
    cell.append(caption, canvas); grid.append(cell); row.canvases.push({ canvas, style });
  }
  root.append(heading, grid);
  return row;
}

function walking(shared, added, badge) {
  const model = Walking.model(shared === null ? "first_walk" : "apart", .65, badge);
  return { ...model, team: shared, newSteps: added,
    reached: shared !== null && shared >= Walking.GOAL,
    shared: Math.min(1, (shared || 0) / Walking.GOAL),
    mine: Math.min(1, ((shared || 0) + added) / Walking.GOAL) };
}

function paint(row, shared, added, badge, big) {
  for (const { canvas, style } of row.canvases) {
    Directions.paint(canvas, "horizon", walking(shared, added, badge),
      { ...SCENE, badge, big, pendingStyle: style });
  }
}

for (const badge of ["Maggie", "Martin"]) live.push(pair(document.getElementById("live"), badge, { badge }));
const cases = [
  ["Just synced · no +0", 9900, 0],
  ["A longer contribution", 9900, 94],
  ["Enough to finish · still needs a sync", 9900, 100],
  ["Long counts · shrink the whole line", 1000025, 12345],
  ["Before the first sync · your personal count", null, 47],
];
for (const [title, shared, added] of cases) checks.push(pair(document.getElementById("checks"), title, { shared, added }));

function render(values) {
  current = values;
  for (const row of live) paint(row, values.shared, values[row.badge.toLowerCase()], row.badge, values.big);
  for (const row of checks) paint(row, row.shared, row.added, "Maggie", values.big);
  document.getElementById("values").textContent = JSON.stringify({ goal: Walking.GOAL, ...values });
}

document.getElementById("maggie-step").onclick = () => kit.setValues({ maggie: current.maggie + 1 });
document.getElementById("martin-step").onclick = () => kit.setValues({ martin: current.martin + 1 });
document.getElementById("sync").onclick = () => kit.setValues({
  shared: current.shared + current.maggie + current.martin, maggie: 0, martin: 0,
});
document.getElementById("reset").onclick = () => kit.resetValues();
document.getElementById("copy").onclick = async () => {
  const message = document.getElementById("message");
  try {
    await navigator.clipboard.writeText(JSON.stringify({ goal: Walking.GOAL, ...current }, null, 2));
    message.textContent = "Values copied.";
  } catch { message.textContent = "Select the values above to copy them."; }
};
document.fonts.load('500 16px "Mona Sans"').finally(() => kit.subscribe(render));
window.walkingCounter = { kit, render };
})();
