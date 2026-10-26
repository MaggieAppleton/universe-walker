"use strict";
(() => {
const P = window.Painter, { paint } = window.Directions, { WEARERS, tracker, forPaint } = window.LiveModel;
// The approved badge look: design-jig/walking/final/settings.json.
const SETTINGS = { goal: 10000, direction: "horizon", world: "coast", landmark: "big", events: "fullscreen",
  sky: "gradient", big: 70, small: 14, title: 29, trail: 12, scale: 1, gap: 24, partnerAlpha: 0.55,
  stride: 0.4, holdProgress: 0.65, mapStyle: "paper" };
const STALE_S = 10;

const root = document.getElementById("badges"), scannerLine = document.getElementById("scanner");
const cards = new Map();
let clockSkew = 0;

function card(id) {
  if (cards.has(id)) return cards.get(id);
  const name = WEARERS[id] || `Badge ${id.slice(0, 6)}`;
  const el = document.createElement("section"); el.className = "badge";
  el.innerHTML = `<h2></h2><div class="bezel"><canvas width="640" height="480"></canvas></div>
    <div class="meta"><span class="dot"></span><span class="text">Waiting for badge…</span></div>`;
  el.querySelector("h2").textContent = name;
  el.querySelector("canvas").setAttribute("aria-label", `${name}'s badge screen`);
  const c = { id, name, el, canvas: el.querySelector("canvas"), text: el.querySelector(".text"), model: tracker(), status: null };
  cards.set(id, c);
  const order = [...cards.values()].sort((a, b) => rank(a.id) - rank(b.id) || a.id.localeCompare(b.id));
  order.forEach(x => root.append(x.el));
  return c;
}

function rank(id) { const i = Object.keys(WEARERS).indexOf(id); return i < 0 ? 99 : i; }

function waiting(c) {
  const g = c.canvas.getContext("2d"), k = c.canvas.width / P.W;
  g.setTransform(k, 0, 0, k, 0, 0);
  g.fillStyle = "#151d3b"; g.fillRect(0, 0, P.W, P.H);
  P.text(g, `Waiting for ${c.name}'s badge`, 160, 112, 16, "rgba(235,238,255,.74)");
  P.text(g, "Open Walking on the badge", 160, 138, 12, "rgba(235,238,255,.45)");
}

function render(t) {
  const now = Date.now() / 1000 - clockSkew;
  for (const c of cards.values()) {
    const s = c.status;
    if (!s) { waiting(c); continue; }
    const m = c.model(s.own, s.team, s.partner, s.status, s.progress, s.success ? s.team : null, t);
    paint(c.canvas, "horizon", forPaint(m), { ...SETTINGS, badge: c.name, t, pixelRatio: c.canvas.width / P.W });
    const age = Math.max(0, now - s.seen), stale = age > STALE_S;
    c.el.classList.toggle("stale", stale); c.el.classList.toggle("live", !stale);
    const signal = s.rssi === null || s.rssi === undefined ? "" : ` · ${s.rssi} dBm`;
    c.text.textContent = stale ? `Not heard for ${Math.round(age)} s — badge may be syncing or out of range`
      : `Live${signal} · ${age < 1 ? "just now" : `${Math.round(age)} s ago`}`;
  }
  requestAnimationFrame(render);
}

function scanner(state) {
  const text = { scanning: "Listening for badge adverts over Bluetooth",
    demo: "Demo mode: simulated badges", starting: "Starting Bluetooth scan…" }[state.state];
  scannerLine.textContent = state.error ? `Bluetooth unavailable: ${state.error}` : text || state.state;
  scannerLine.classList.toggle("error", Boolean(state.error));
}

Object.keys(WEARERS).forEach(card);
const events = new EventSource("/events");
events.onmessage = e => {
  const snap = JSON.parse(e.data);
  clockSkew = Date.now() / 1000 - snap.now;
  scanner(snap.scanner);
  for (const b of snap.badges) card(b.id).status = b;
};
events.onerror = () => { scannerLine.textContent = "Lost the dashboard server, retrying…"; scannerLine.classList.add("error"); };
document.fonts.ready.then(() => requestAnimationFrame(render));
})();
