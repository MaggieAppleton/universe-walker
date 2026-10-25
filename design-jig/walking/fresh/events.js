"use strict";
(() => {
const P = window.Painter;
// Full-screen moments for pairing, confirmation and retry. The world stays
// faintly visible behind a veil; a ring or icon carries the state, with the
// title underneath. `o.t` (ms) drives the motion; static frames use t = 0.
const WHITE = "#ffffff", SOFT = "rgba(225,232,255,.72)", DIM = "rgba(255,255,255,.14)";
const AMBER = "#ffb547", GOOD = "#7ee2a0", WARN = "#ff9b85", GOLD = "#ffd56a";
const EVENTS = ["holding", "connecting", "syncing", "ack", "success", "cooldown", "retry"];
const CX = 160, CY = 82, R = 38;

function veil(c, a) { c.fillStyle = `rgba(9,12,28,${a})`; c.fillRect(0, 0, P.W, P.H); }
function ring(c, from, to, pen, width = 6, r = R) {
  c.strokeStyle = pen; c.lineWidth = width; c.lineCap = "round";
  c.beginPath(); c.arc(CX, CY, r, from, to); c.stroke();
}
const TOP = -Math.PI / 2, TURN = Math.PI * 2;

// Two badges back to back: the gesture the player is making.
function badges(c, apart = 0, pen = WHITE) {
  P.rrect(c, CX - 15 - apart, CY - 13, 13, 26, 3, pen);
  P.rrect(c, CX + 2 + apart, CY - 13, 13, 26, 3, pen);
  P.rrect(c, CX - 12.5 - apart, CY - 10, 8, 10, 1.5, "rgba(9,12,28,.5)");
  P.rrect(c, CX + 4.5 + apart, CY - 10, 8, 10, 1.5, "rgba(9,12,28,.5)");
}
function arrow(c, x0, y, dir, pen, len = 14) {
  const x1 = x0 + dir * len;
  P.line(c, x0, y, x1, y, 3, pen);
  P.line(c, x1, y, x1 - dir * 5, y - 5, 3, pen);
  P.line(c, x1, y, x1 - dir * 5, y + 5, 3, pen);
}
function check(c, x, y, s, pen) {
  c.strokeStyle = pen; c.lineWidth = 3.4 * s / 10; c.lineCap = "round"; c.lineJoin = "round";
  c.beginPath(); c.moveTo(x - 9 * s / 10, y); c.lineTo(x - 3 * s / 10, y + 6 * s / 10); c.lineTo(x + 9 * s / 10, y - 6 * s / 10); c.stroke();
}
function words(c, o, title, pen, sub, extra) {
  P.bigNumber(c, title, 160, 174, o.title, 296, pen);
  if (sub) P.text(c, sub, 160, 198, o.small, SOFT);
  if (extra) P.text(c, extra, 160, 226, o.small, SOFT);
}

function confetti(c, seed, t) {
  const colours = ["#ffd56a", "#7ee2a0", "#ff8a7a", "#8ab8ff", "#ffffff"];
  let r = seed;
  const rand = () => (r = (r * 9301 + 49297) % 233280) / 233280;
  for (let i = 0; i < 40; i++) {
    const x = rand() * 320, y = (rand() * 260 + t * (0.02 + rand() * 0.03)) % 260 - 10;
    if (x > 60 && x < 260 && y > 14 && y < 206) continue; // keep the text clear
    c.save(); c.translate(x, y); c.rotate(rand() * Math.PI + t * 0.003);
    P.rrect(c, -3, -1.4, 6, 2.8, 1, colours[i % colours.length]);
    c.restore();
  }
}

function draw(c, m, o) {
  const t = o.t || 0, partner = o.badge === "Maggie" ? "Martin" : "Maggie";
  veil(c, 0.74);
  if (m.phase === "holding") {
    ring(c, 0, TURN, DIM);
    ring(c, TOP, TOP + TURN * Math.max(0.02, m.hold), WHITE);
    badges(c);
    return words(c, o, "Hold steady", WHITE, "Keep badges back to back");
  }
  if (m.phase === "connecting") {
    for (let i = 0; i < 3; i++) {
      const k = ((t / 1400) + i / 3) % 1;
      c.globalAlpha = (1 - k) * 0.5; ring(c, 0, TURN, WHITE, 2, R + 6 + k * 20); c.globalAlpha = 1;
    }
    ring(c, 0, TURN, WHITE);
    badges(c);
    return words(c, o, "Connecting", WHITE, `Found ${partner}’s badge`);
  }
  if (m.phase === "syncing") {
    const a = t / 500;
    ring(c, 0, TURN, DIM);
    ring(c, TOP + a, TOP + a + 1.1, P.PEOPLE[o.badge].jacket);
    ring(c, TOP + Math.PI - a, TOP + Math.PI - a + 1.1, P.PEOPLE[partner].jacket);
    arrow(c, CX - 10, CY - 6, 1, WHITE, 20);
    arrow(c, CX + 10, CY + 6, -1, WHITE, 20);
    return words(c, o, "Swapping steps", WHITE, m.newSteps > 0 ? `Sending your +${P.fmt(m.newSteps)}` : "Sharing counts");
  }
  if (m.phase === "ack") {
    const lead = Math.floor(t / 90) % 12;
    for (let i = 0; i < 12; i++) {
      const ang = TOP + i * TURN / 12, age = (lead - i + 12) % 12;
      c.globalAlpha = Math.max(0.15, 1 - age / 8);
      P.circle(c, CX + Math.cos(ang) * R, CY + Math.sin(ang) * R, 4, WHITE);
    }
    c.globalAlpha = 1;
    return words(c, o, "Confirming", WHITE, `Waiting for ${partner}’s badge`);
  }
  if (m.phase === "success") {
    const repeat = m.prevTeam === m.team && m.team > 0, gained = m.team - m.prevTeam;
    if (gained > 0) confetti(c, 7, t);
    P.circle(c, CX, 38, 18, repeat ? "rgba(255,255,255,.16)" : GOOD);
    check(c, CX, 38, 10, repeat ? GOOD : "#0f2a1a");
    P.text(c, repeat ? "Up to date" : "Synced!", 160, 86, o.title, GOOD);
    P.bigNumber(c, P.fmt(m.team), 160, 152, o.big, 280, WHITE);
    P.runs(c, gained > 0 ? [["shared steps", SOFT], [`+${P.fmt(gained)} together`, GOOD]]
      : [[m.team === 0 ? "shared steps so far" : "No new steps since last sync", SOFT]], 160, 182, o.small);
    P.text(c, "Move badges apart", 160, 222, o.small, AMBER);
    return;
  }
  if (m.phase === "cooldown") {
    const k = (Math.sin(t / 300) + 1) / 2;
    badges(c, 4 + k * 8);
    arrow(c, CX - 26 - k * 8, CY, -1, AMBER);
    arrow(c, CX + 26 + k * 8, CY, 1, AMBER);
    return words(c, o, "Move badges apart", AMBER, `${P.fmt(m.team)} shared steps saved`);
  }
  if (m.phase === "retry") {
    const lost = m.id === "timeout";
    ring(c, TOP + 0.5, TOP + TURN - 0.5, WARN);
    badges(c, 6, WARN);
    return words(c, o, lost ? "Lost connection" : "Couldn’t sync", WARN,
      lost ? "Hold together to retry" : "Move apart, then try again", `Still ${P.fmt(m.team)} shared steps`);
  }
}

// Arrival happens over the world itself: walkers cheer at the landmark.
// On a map it takes the map's own ink, left aligned where the count sits.
function arrival(c, m, o, map) {
  if (!map) {
    c.fillStyle = P.vgradient(c, 0, 130, ["rgba(9,12,28,.5)", "rgba(9,12,28,0)"]);
    c.fillRect(0, 0, P.W, 130);
  }
  confetti(c, 3, o.t || 0);
  const x = map ? 16 : 160, align = map ? "left" : "center";
  P.text(c, "You made it!", x, map ? 60 : 52, o.title, map ? map.reached : GOLD, align);
  P.text(c, `${P.fmt(m.team)} steps together`, x, map ? 84 : 76, o.small, map ? map.ink : WHITE, align);
}

window.Events = { EVENTS, draw, arrival };
})();
