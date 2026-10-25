"use strict";
(() => {
const P = window.Painter;
const TONES = { muted: null, live: "#ffd27a", good: "#7ee2a0", warn: "#ff9b85" };
const AMBER = "#ffb547";

// Me, partner, and the pairing link, placed along any trail.
function people(c, path, startD, goalD, m, o) {
  if (o.quietPeople) return;
  const span = goalD - startD, gap = o.gap;
  // Stop just short of the destination so walkers never hide the landmark.
  const end = goalD - gap * 0.6;
  const sharedD = Math.min(end, startD + m.shared * span), mineD = Math.min(end, startD + m.mine * span);
  const me = o.badge, them = me === "Maggie" ? "Martin" : "Maggie";
  const tilt = p => (o.tilt ? p.angle : 0);
  const figures = [];
  if (m.together) {
    const centre = m.phase === "success" ? sharedD : mineD, pair = gap * 0.8;
    const a = P.pointAt(path, centre - pair), b = P.pointAt(path, centre + pair);
    const cheer = m.phase === "success";
    figures.push([a, me, { facing: 1, cheer, phase: 0 }], [b, them, { facing: -1, cheer, phase: 0 }]);
    link(c, a, b, m, o);
  } else if (o.quietHud && m.reached) {
    // arrival: both cheer just short of the landmark
    figures.push([P.pointAt(path, sharedD - gap), me, { cheer: true, phase: 0 }], [P.pointAt(path, sharedD), them, { cheer: true, phase: 0, facing: -1 }]);
  } else {
    const ahead = Math.abs(mineD - sharedD) < gap;
    // Overlapping walkers step apart; at the trailhead the partner steps forward instead.
    let partnerD = ahead ? Math.min(sharedD, mineD) - gap * 0.75 : sharedD;
    if (P.pointAt(path, partnerD).x < 14) partnerD = Math.max(sharedD, mineD) + gap * 0.75;
    figures.push([P.pointAt(path, partnerD), them, { alpha: o.partnerAlpha, phase: 0.15 }]);
    figures.push([P.pointAt(path, mineD), me, { phase: o.stride }]);
  }
  figures.sort((x, y) => x[0].y - y[0].y).forEach(([p, who, opts]) =>
    P.hiker(c, p.x, p.y, who, { ...opts, scale: o.scale, angle: tilt(p) }));
}

// Dots arc between the two heads: fills with the hold, then shuttles counts.
function link(c, a, b, m, o) {
  if (m.phase === "success" || m.phase === "cooldown") {
    const cx = (a.x + b.x) / 2, top = Math.min(a.y, b.y) - 44 * o.scale;
    [[-16, 8, 5], [15, 2, 4], [-4, -10, 3.5], [24, -14, 2.5], [-24, -8, 2.5]].forEach(([dx, dy, r]) =>
      P.star(c, cx + dx * o.scale, top + dy * o.scale, r * o.scale, dx % 2 ? "#ffcf4a" : (o.linkPen || "#ffffff")));
    return;
  }
  const n = 7, cx = (a.x + b.x) / 2, base = Math.min(a.y, b.y) - 36 * o.scale;
  const lit = m.hold === null ? n : Math.round(m.hold * n);
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1), x = a.x + (b.x - a.x) * t + (t - 0.5) * 6 * o.scale;
    const y = base - Math.sin(t * Math.PI) * 12 * o.scale;
    let on = i < lit;
    if (m.phase === "syncing") on = i === 2 || i === 4;
    if (m.phase === "ack") on = i % 2 === 0;
    const pen = o.linkPen || "#ffffff";
    c.globalAlpha = on ? 1 : 0.35; P.circle(c, x, y, (on ? 2.1 : 1.5) * o.scale, pen); c.globalAlpha = 1;
  }
}

// Status, count and caption: two type sizes, distinguished by colour.
function hud(c, m, x, y, o, theme, align = "center") {
  if (o.quietHud) return;
  const small = o.small, ink = theme.ink, soft = theme.soft;
  const inline = o.pendingStyle !== "caption";
  const statusPen = TONES[m.tone] ? (theme.tones?.[m.tone] || TONES[m.tone]) : soft;
  const status = m.phase === "success" ? "✓ " + m.status : m.status;
  P.text(c, status, x, y.status, small, statusPen, align);
  let parts;
  if (m.phase === "success") parts = [["Move badges apart", theme.tones?.good || TONES.good]];
  else if (m.team === null) parts = [[inline ? "Your steps, not synced yet" : "No shared steps yet", soft]];
  else if (m.reached) parts = [["shared steps", soft], ["Goal reached", theme.gold || "#ffd27a"]];
  else parts = [[`of ${P.fmt(m.goal)} shared steps`, soft]];
  if (!inline && m.newSteps > 0 && m.phase !== "success") parts.push([`+${P.fmt(m.newSteps)} yours`, theme.amber || AMBER]);
  // Centre the visible digits in the clear space, rather than their baseline.
  const band = theme.centerCount ? {
    top: y.status + P.inkBounds(c, status, small).actualBoundingBoxDescent,
    bottom: y.caption - Math.max(...parts.map(([s]) => P.inkBounds(c, s, small).actualBoundingBoxAscent)),
  } : null;
  if (m.team === null && !inline) P.text(c, "Not synced yet", x, y.count - 18, o.title, ink, align);
  else if (m.team !== null && inline && m.newSteps > 0) {
    P.bigRuns(c, [[P.fmt(m.team), ink], [`+${P.fmt(m.newSteps)}`, theme.amber || AMBER]],
      x, y.count, o.big, theme.maxWidth || 280, align, band);
  } else P.bigNumber(c, P.fmt(m.team === null ? m.newSteps : m.team), x, y.count, o.big, theme.maxWidth || 280, ink, align, band);
  P.runs(c, parts, x, y.caption, small, align);
}

function trailProgress(c, path, startD, goalD, m, o, look) {
  const span = goalD - startD;
  P.strokePath(c, path, 0, path.total, o.trail + 3, look.edge);
  P.strokePath(c, path, 0, path.total, o.trail, look.bed);
  const sharedD = startD + m.shared * span, mineD = startD + m.mine * span;
  if (mineD > sharedD) P.strokePath(c, path, sharedD, mineD, o.trail * 0.45, look.amber || AMBER);
  if (m.shared > 0) P.strokePath(c, path, startD, sharedD, o.trail * 0.45, look.walked);
}

// Arc length of the trail point nearest a given x.
function dAtX(path, x) {
  let best = 0;
  path.pts.forEach((p, i) => { if (Math.abs(p[0] - x) < Math.abs(path.pts[best][0] - x)) best = i; });
  return path.lengths[best];
}

const { WORLDS } = window.Worlds;

/* ---------- Horizon: count in the sky, a world below ---------- */
function horizon(c, m, o) {
  const w = WORLDS[o.world] || WORLDS.coast;
  c.fillStyle = o.sky === "gradient" ? P.vgradient(c, 0, w.skyEnd, w.sky) : w.solid;
  c.fillRect(0, 0, P.W, P.H);
  if (w.stars) [[30, 40], [292, 30], [262, 120], [40, 128], [304, 98], [16, 74]].forEach(([x, y]) => P.circle(c, x, y, 0.9, "rgba(255,255,255,.55)"));
  w.draw(c, m.reached, o.landmark);
  const path = P.makePath(w.trail);
  const startD = dAtX(path, 24), goalD = dAtX(path, w.goalX);
  trailProgress(c, path, startD, goalD, m, o, w.look);
  w.after?.(c, m.reached);
  people(c, path, startD, goalD, m, o);
  hud(c, m, 160, { status: 22, count: 78, caption: 112 }, o, { ink: "#ffffff", soft: "rgba(235,238,255,.74)", centerCount: true });
}

/* ---------- Trail map: a walking map you carry ---------- */
const MAPS = {
  paper: {
    label: "Paper", bg: ["#f6f1e5", "#ece3cf"], contour: "#dccfb0", water: "#bfd9e2", shore: "#97bccb", woods: "#b8d4a2",
    route: "#8c7a5a", walked: "#d2452f", amber: "#e0901f", ink: "#24302a", soft: "#7c7462", link: "#24302a",
    pin: "#d2452f", reached: "#2f9e5a", tones: { live: "#b5751d", good: "#2f9e5a", warn: "#c8452f" },
  },
  night: {
    label: "Night", bg: ["#141d3a", "#0b1226"], contour: "rgba(130,170,255,.16)", water: "rgba(80,140,230,.22)", shore: "rgba(120,170,255,.35)", woods: "rgba(120,210,170,.12)",
    route: "rgba(200,215,255,.45)", walked: "#8ae6ff", glow: "rgba(138,230,255,.22)", amber: "#ffb547", ink: "#ffffff", soft: "rgba(210,222,255,.65)", link: "#ffffff",
    pin: "#ff8a7a", reached: "#ffd56a",
  },
  patchwork: {
    label: "Patchwork", bg: ["#ebe5d2", "#e4ddc6"], water: "#a9cfe0", shore: "#86b4c8", woods: "#5f9a6a",
    patches: ["#cfdca8", "#e6d58f", "#b9d39c", "#dfe3b4", "#e9cf86"],
    road: "#fbf8ef", roadEdge: "#c7bb98", route: null, walked: "#d2452f", amber: "#e0901f", ink: "#24302a", soft: "#6f6a58", link: "#24302a",
    pin: "#d2452f", reached: "#2f9e5a", tones: { live: "#b5751d", good: "#2f9e5a", warn: "#c8452f" },
  },
};
const MAP_ROUTE = [[-12, 216], [26, 206], [70, 194], [110, 200], [150, 182], [184, 156], [216, 142], [238, 118], [252, 92], [272, 70], [300, 58], [334, 52]];

function contours(c, pen, hills) {
  hills.forEach(([hx, hy, rings]) => {
    for (let i = rings; i > 0; i--) {
      c.strokeStyle = pen; c.lineWidth = 1; c.beginPath();
      for (let a = 0; a <= 64; a++) {
        const t = a / 64 * Math.PI * 2, r = i * 13 * (1 + 0.1 * Math.sin(t * 3 + i));
        const x = hx + Math.cos(t) * r * 1.4, y = hy + Math.sin(t) * r * 0.85;
        a ? c.lineTo(x, y) : c.moveTo(x, y);
      }
      c.stroke();
    }
  });
}

function map(c, m, o) {
  const s = MAPS[o.mapStyle] || MAPS.paper;
  c.fillStyle = o.sky === "gradient" ? P.vgradient(c, 0, 240, s.bg) : s.bg[0];
  c.fillRect(0, 0, P.W, P.H);
  if (s.patches) {
    // flat field patchwork, leaving the count's corner clear
    const cells = [[190, 0, 70, 50], [262, 0, 58, 40], [190, 52, 46, 60], [238, 42, 82, 44], [0, 120, 60, 56], [62, 118, 70, 48],
      [134, 112, 54, 60], [238, 88, 82, 60], [190, 114, 46, 58], [62, 168, 80, 72], [0, 178, 60, 62], [144, 174, 80, 66]];
    cells.forEach(([x, y, w, h], i) => P.rrect(c, x + 1.5, y + 1.5, w - 3, h - 3, 4, s.patches[i % s.patches.length]));
  }
  c.fillStyle = s.water; c.beginPath(); c.ellipse(270, 206, 66, 32, -0.15, 0, Math.PI * 2); c.fill();
  c.strokeStyle = s.shore; c.lineWidth = 1.2; c.stroke();
  if (s.contour) contours(c, s.contour, [[226, 74, 5], [90, 190, 3]]);
  [[52, 148, 7], [64, 156, 6], [44, 160, 5], [298, 120, 6], [288, 130, 5], [308, 132, 5]].forEach(([x, y, r]) => P.circle(c, x, y, r, s.woods));
  const path = P.makePath(MAP_ROUTE);
  const startD = dAtX(path, 26), goalD = dAtX(path, 272), span = goalD - startD;
  const sharedD = startD + m.shared * span, mineD = startD + m.mine * span;
  if (s.road) { P.strokePath(c, path, 0, path.total, 7, s.roadEdge); P.strokePath(c, path, 0, path.total, 5, s.road); }
  else P.strokePath(c, path, 0, path.total, 2, s.route, [4, 4]);
  if (mineD > sharedD) P.strokePath(c, path, sharedD, mineD, 4, s.amber);
  if (m.shared > 0) {
    if (s.glow) P.strokePath(c, path, startD, sharedD, 10, s.glow);
    P.strokePath(c, path, startD, sharedD, 4, s.walked);
  }
  P.circle(c, 26, 206, 4, s.ink); P.circle(c, 26, 206, 2, s.bg[0]);
  people(c, path, startD, goalD, m, { ...o, linkPen: s.link });
  // destination pin sits beside the trail end so walkers never hide it
  const g = P.pointAt(path, goalD), px = g.x + 14, py = g.y - 10, pin = m.reached ? s.reached : s.pin;
  if (m.reached) P.circle(c, px, py - 12, 14, s.glow || "rgba(47,158,90,.18)");
  P.circle(c, px, py - 12, 8, pin);
  P.poly(c, [[px - 6, py - 8], [px + 6, py - 8], [px, py + 2]], pin);
  P.circle(c, px, py - 12, 3.2, s.bg[0]);
  hud(c, m, 16, { status: 228, count: 74, caption: 98 }, o,
    { ink: s.ink, soft: s.soft, amber: s.amber, gold: s.reached, maxWidth: 170, tones: s.tones }, "left");
}

function fatal(c, o) {
  c.fillStyle = "#151a2c"; c.fillRect(0, 0, P.W, P.H);
  P.text(c, "Walking paused", 160, 92, o.small * 1.5, "#ffffff");
  P.text(c, "MemoryError in app frame", 160, 124, o.small, "rgba(235,238,255,.72)");
  P.text(c, "Press HOME to return", 160, 210, o.small, "#ffd27a");
}

const DIRECTIONS = {
  horizon: { label: "Horizon", draw: horizon },
  map: { label: "Trail map", draw: map },
};

function paint(canvas, direction, m, o) {
  const c = canvas.getContext("2d");
  c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, P.W, P.H);
  if (m.phase === "fatal") return fatal(c, o);
  const full = o.events === "fullscreen", event = full && window.Events.EVENTS.includes(m.phase), arrived = full && m.id === "goal";
  DIRECTIONS[direction].draw(c, m, { ...o, quietHud: event || arrived, quietPeople: event });
  if (event) window.Events.draw(c, m, o);
  if (arrived) window.Events.arrival(c, m, o, direction === "map" ? MAPS[o.mapStyle] || MAPS.paper : null);
}

window.Directions = { DIRECTIONS, WORLDS, MAPS, paint };
})();
