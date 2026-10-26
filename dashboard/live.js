"use strict";
(() => {
const P = window.Painter, { paint } = window.Directions;
const { WEARERS, PAIRING, tracker, forPaint, coordinator } = window.LiveModel;
// The approved badge look: design-jig/walking/final/settings.json.
const SETTINGS = { goal: 10000, direction: "horizon", world: "coast", landmark: "big", events: "fullscreen",
  sky: "gradient", big: 70, small: 14, title: 29, trail: 12, scale: 1, gap: 24, partnerAlpha: 0.55,
  stride: 0.4, holdProgress: 0.65, mapStyle: "paper" };
const STALE_S = 10;

const root = document.getElementById("badges"), link = document.getElementById("link");
const errorLine = document.getElementById("error");
const cards = new Map(), pair = coordinator();
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
  order.forEach((x, i) => { root.append(x.el); if (i === 0) root.append(link); });
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
  const now = Date.now() / 1000 - clockSkew, wall = Date.now();
  const phases = [];
  for (const c of cards.values()) {
    const s = c.status;
    if (!s) { waiting(c); continue; }
    const age = Math.max(0, now - s.seen), stale = age > STALE_S;
    const i = pair.inputs(s, age * 1000, wall);
    const m = c.model(i.own, i.team, i.partner, i.status, i.progress, i.successTotal, t);
    phases.push(m.phase);
    paint(c.canvas, "horizon", forPaint(m), { ...SETTINGS, badge: c.name, t, pixelRatio: c.canvas.width / P.W });
    c.el.classList.toggle("stale", stale && !PAIRING.includes(m.phase));
    c.el.classList.toggle("live", !stale);
    const signal = s.rssi === null || s.rssi === undefined ? "" : ` · ${s.rssi} dBm`;
    c.text.textContent = PAIRING.includes(m.phase) && age > 1 ? "Syncing with partner"
      : stale ? `Not heard for ${Math.round(age)} s`
      : `Live${signal}`;
  }
  const synced = pair.celebrating(wall), pairing = phases.some(p => PAIRING.includes(p));
  document.body.classList.toggle("together", synced || pairing);
  document.body.classList.toggle("synced", synced);
  confetti.draw(wall);
  requestAnimationFrame(render);
}

// Full-window confetti, bursting from both screens and falling across the page.
const confetti = (() => {
  const canvas = document.getElementById("confetti"), g = canvas.getContext("2d");
  const COLOURS = ["#ffd56a", "#7ee2a0", "#ff8a7a", "#8ab8ff", "#c79bff", "#ffb547"];
  let bits = [], last = 0;
  function fit() {
    const k = devicePixelRatio || 1;
    canvas.width = innerWidth * k; canvas.height = innerHeight * k;
    g.setTransform(k, 0, 0, k, 0, 0);
  }
  addEventListener("resize", fit); fit();
  function burst() {
    pop();
    setTimeout(pop, 900);
    // A slow shower from above the top edge covers the whole window for a few seconds.
    for (let i = 0; i < 260; i++) bits.push({ x: Math.random() * innerWidth, y: -20 - Math.random() * innerHeight * 1.4,
      vx: (Math.random() - 0.5) * 2, vy: 1 + Math.random() * 2, w: 6 + Math.random() * 7, h: 4 + Math.random() * 6,
      spin: (Math.random() - 0.5) * 0.3, r: Math.random() * 6, wobble: Math.random() * 6, colour: COLOURS[i % COLOURS.length] });
  }
  function pop() {
    const sources = [...cards.values()].map(c => c.canvas.getBoundingClientRect());
    if (!sources.length) sources.push({ left: innerWidth / 2, width: 0, top: innerHeight / 2, height: 0 });
    for (const r of sources) for (let i = 0; i < 120; i++) {
      const a = -Math.PI / 2 + (Math.random() - 0.5) * 2.2, v = 9 + Math.random() * 13;
      bits.push({ x: r.left + r.width / 2, y: r.top + r.height / 2, vx: Math.cos(a) * v, vy: Math.sin(a) * v,
        w: 6 + Math.random() * 7, h: 4 + Math.random() * 6, spin: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 6, wobble: Math.random() * 6, colour: COLOURS[i % COLOURS.length] });
    }
  }
  function draw(now) {
    const dt = Math.min(3, (now - (last || now)) / 16.7); last = now;
    g.clearRect(0, 0, innerWidth, innerHeight);
    if (!bits.length) return;
    bits = bits.filter(b => b.y < innerHeight + 40);
    for (const b of bits) {
      b.vy = Math.min(b.vy + 0.25 * dt, 3.2); b.vx *= Math.pow(0.97, dt);
      b.x += (b.vx + Math.sin(b.wobble += 0.08 * dt)) * dt; b.y += b.vy * dt; b.r += b.spin * dt;
      g.save(); g.translate(b.x, b.y); g.rotate(b.r); g.scale(1, Math.cos(b.wobble * 1.3));
      g.fillStyle = b.colour; g.fillRect(-b.w / 2, -b.h / 2, b.w, b.h); g.restore();
    }
  }
  return { burst, draw };
})();

function scanner(state) {
  const error = state.error ? `Bluetooth unavailable: ${state.error}` : "";
  errorLine.textContent = error; errorLine.hidden = !error;
}

Object.keys(WEARERS).forEach(card);
const events = new EventSource("/events");
events.onmessage = e => {
  const snap = JSON.parse(e.data);
  clockSkew = Date.now() / 1000 - snap.now;
  scanner(snap.scanner);
  if (pair.observe(snap.badges, Date.now())) confetti.burst();
  for (const b of snap.badges) card(b.id).status = b;
};
events.onerror = () => { errorLine.textContent = "Lost the dashboard server, retrying…"; errorLine.hidden = false; };
events.onopen = () => { errorLine.hidden = true; };
window.LiveDashboard = { confetti };
document.fonts.ready.then(() => requestAnimationFrame(render));
})();
