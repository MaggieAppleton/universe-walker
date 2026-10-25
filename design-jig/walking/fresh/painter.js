"use strict";
(() => {
// Drawing helpers limited to what badgeware offers on the badge:
// antialiased shapes (circle, rounded_rectangle, custom, line, arc, star),
// linear gradient brushes, alpha pens and the Mona Sans vector font.
const W = 320, H = 240;
const FONT = '"Mona Sans", system-ui, sans-serif';

function rgba(hex, a = 1) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
}

function vgradient(c, y0, y1, stops) {
  const g = c.createLinearGradient(0, y0, 0, y1);
  stops.forEach((s, i) => g.addColorStop(i / (stops.length - 1), s));
  return g;
}

function circle(c, x, y, r, pen) { c.fillStyle = pen; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill(); }
function rrect(c, x, y, w, h, r, pen) { c.fillStyle = pen; c.beginPath(); c.roundRect(x, y, w, h, r); c.fill(); }
function line(c, x0, y0, x1, y1, width, pen) {
  c.strokeStyle = pen; c.lineWidth = width; c.lineCap = "round";
  c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
}
function poly(c, points, pen) {
  c.fillStyle = pen; c.beginPath();
  points.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y));
  c.closePath(); c.fill();
}
function star(c, x, y, r, pen) {
  const pts = [];
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4 - Math.PI / 2, rr = i % 2 ? r * 0.38 : r;
    pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]);
  }
  poly(c, pts, pen);
}

// Silhouette ridge across the screen from a list of [x, y] control points.
function ridge(c, points, bottom, pen) {
  c.fillStyle = pen; c.beginPath(); c.moveTo(-2, bottom);
  points.forEach(([x, y]) => c.lineTo(x, y));
  c.lineTo(W + 2, bottom); c.closePath(); c.fill();
}

function text(c, str, x, y, size, pen, align = "center") {
  c.font = `500 ${size}px ${FONT}`; c.fillStyle = pen; c.textAlign = align; c.textBaseline = "alphabetic";
  c.fillText(str, x, y);
}
function measure(c, str, size) { c.font = `500 ${size}px ${FONT}`; return c.measureText(str).width; }
function inkBounds(c, str, size) {
  c.font = `500 ${size}px ${FONT}`; c.textBaseline = "alphabetic";
  return c.measureText(str);
}
// Several coloured runs on one line, centred (or left aligned) as a whole.
function runs(c, parts, x, y, size, align = "center") {
  const gap = size * 0.5;
  const total = parts.reduce((w, [s]) => w + measure(c, s, size), 0) + gap * (parts.length - 1);
  let cx = align === "center" ? x - total / 2 : x;
  parts.forEach(([s, pen]) => { text(c, s, cx, y, size, pen, "left"); cx += measure(c, s, size) + gap; });
}
// The big count shrinks to fit long values instead of clipping.
function bigNumber(c, str, x, y, size, maxWidth, pen, align = "center", band = null) {
  c.font = `500 ${size}px ${FONT}`;
  let fit = Math.min(size, size * maxWidth / c.measureText(str).width);
  c.save(); c.letterSpacing = `${-fit * 0.03}px`;
  if (band) {
    c.textAlign = align;
    let bounds = inkBounds(c, str, fit);
    // Leave at least 8px beside each label, fitting the ink as well as advance.
    fit *= Math.min(1, maxWidth / Math.max(1, 2 * bounds.actualBoundingBoxLeft, 2 * bounds.actualBoundingBoxRight),
      (band.bottom - band.top - 16) / Math.max(1, bounds.actualBoundingBoxAscent + bounds.actualBoundingBoxDescent));
    c.letterSpacing = `${-fit * 0.03}px`;
    bounds = inkBounds(c, str, fit);
    y = (band.top + band.bottom + bounds.actualBoundingBoxAscent - bounds.actualBoundingBoxDescent) / 2;
  }
  text(c, str, x, y, fit, pen, align);
  c.restore();
  return fit;
}

// Fit coloured counts together, with one font size and one baseline.
function bigRuns(c, parts, x, y, size, maxWidth, align = "center", band = null) {
  c.save(); c.textAlign = "left";
  function layout(fit) {
    c.letterSpacing = `${-fit * 0.03}px`;
    const metrics = parts.map(([str]) => inkBounds(c, str, fit));
    const gap = fit * 0.12;
    let cursor = 0, left = 0, right = 0;
    for (const m of metrics) {
      left = Math.min(left, cursor - m.actualBoundingBoxLeft);
      right = Math.max(right, cursor + m.actualBoundingBoxRight);
      cursor += m.width + gap;
    }
    const advance = cursor - gap;
    right = Math.max(right, advance);
    return { metrics, gap, left, width: right - left,
      ascent: Math.max(...metrics.map(m => m.actualBoundingBoxAscent)),
      descent: Math.max(...metrics.map(m => m.actualBoundingBoxDescent)) };
  }
  let fit = size, row = layout(fit);
  for (let i = 0; i < 3; i++) {
    const scale = Math.min(1, maxWidth / Math.max(1, row.width),
      band ? (band.bottom - band.top - 16) / Math.max(1, row.ascent + row.descent) : 1);
    if (scale >= 1) break;
    fit *= scale; row = layout(fit);
  }
  if (band) y = (band.top + band.bottom + row.ascent - row.descent) / 2;
  let cursor = (align === "center" ? x - row.width / 2 : x) - row.left;
  parts.forEach(([str, pen], i) => {
    text(c, str, cursor, y, fit, pen, "left");
    cursor += row.metrics[i].width + row.gap;
  });
  c.restore();
  return fit;
}
const fmt = n => n.toLocaleString("en-US");

// Path sampled into an arc-length table so progress maps to an even distance.
function makePath(points) {
  const pts = [];
  // Catmull-Rom through the control points, so the trail stays smooth.
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)], p1 = points[i], p2 = points[i + 1], p3 = points[Math.min(points.length - 1, i + 2)];
    for (let t = 0; t < 1; t += 1 / 24) {
      const t2 = t * t, t3 = t2 * t;
      const f = k => 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3);
      pts.push([f(0), f(1)]);
    }
  }
  pts.push(points[points.length - 1]);
  const lengths = [0];
  for (let i = 1; i < pts.length; i++) lengths.push(lengths[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return { pts, lengths, total: lengths[lengths.length - 1] };
}
function pointAt(path, d) {
  const { pts, lengths } = path;
  d = Math.max(0, Math.min(path.total, d));
  let i = 1; while (i < lengths.length - 1 && lengths[i] < d) i++;
  const t = (d - lengths[i - 1]) / ((lengths[i] - lengths[i - 1]) || 1);
  const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
  return { x: x0 + (x1 - x0) * t, y: y0 + (y1 - y0) * t, angle: Math.atan2(y1 - y0, x1 - x0) };
}
function strokePath(c, path, d0, d1, width, pen, dash) {
  c.strokeStyle = pen; c.lineWidth = width; c.lineCap = "round"; c.lineJoin = "round";
  c.setLineDash(dash || []);
  c.beginPath();
  const a = pointAt(path, d0); c.moveTo(a.x, a.y);
  path.pts.forEach((p, i) => { if (path.lengths[i] > d0 && path.lengths[i] < d1) c.lineTo(p[0], p[1]); });
  const b = pointAt(path, d1); c.lineTo(b.x, b.y);
  c.stroke(); c.setLineDash([]);
}

const PEOPLE = {
  Maggie: { jacket: "#e5484d", shade: "#a8282f", hair: "#c4441b", style: "hair" },
  Martin: { jacket: "#3b82f6", shade: "#1d4fb8", hair: "#3b2a20", style: "cap" },
};
const SKIN = "#f3c9a4", TROUSERS = "#2a3350", OUTLINE = "#141a2a";

// A hiker standing with feet at (x, y). Drawn twice: a dark outline pass,
// then the fill pass, so the figure reads on any background.
function hiker(c, x, y, who, o = {}) {
  const s = o.scale || 1, face = o.facing || 1, phase = o.phase ?? 0.6, p = PEOPLE[who];
  c.save(); c.translate(x, y); c.rotate(o.angle || 0); c.scale(s * face, s);
  c.globalAlpha = o.alpha ?? 1;
  const stride = Math.sin(phase * Math.PI) * 3.4;
  const cheer = o.cheer;
  for (const pass of [0, 1]) {
    const grow = pass ? 0 : 1.4;
    const pen = col => pass ? col : OUTLINE;
    // legs
    line(c, -1.4, -11, -1.4 - stride, -1.2, 3.4 + grow * 2, pen(TROUSERS));
    line(c, 1.4, -11, 1.4 + stride, -1.2, 3.4 + grow * 2, pen(pass ? "#36416a" : TROUSERS));
    // backpack, body, arm
    rrect(c, -8.6 - grow, -21.6 - grow, 5.6 + grow * 2, 10 + grow * 2, 2.2, pen(p.shade));
    rrect(c, -5.2 - grow, -22.5 - grow, 10.4 + grow * 2, 13.2 + grow * 2, 4.4, pen(p.jacket));
    if (cheer) {
      line(c, 3.2, -19.5, 7.5, -29, 3 + grow * 2, pen(p.jacket));
      line(c, -3, -19.5, -6.5, -29, 3 + grow * 2, pen(p.jacket));
    } else {
      line(c, 0.5, -19, 0.5 + stride * 0.9 + 1.5, -12.5, 3 + grow * 2, pen(p.shade));
    }
    // head
    if (p.style === "hair") {
      circle(c, -0.6, -28.6, 5.6 + grow, pen(p.hair));
      circle(c, -6.2, -26.6, 3 + grow, pen(p.hair));
      if (pass) { circle(c, 1.6, -27, 4.2, SKIN); circle(c, -0.8, -31.2, 3.6, p.hair); }
    } else {
      circle(c, 0.4, -27.6, 5.2 + grow, pen(SKIN));
      c.fillStyle = pen(p.jacket); c.beginPath(); c.arc(0.2, -29.2, 5.6 + grow, Math.PI, 0); c.fill();
      rrect(c, 1 - grow, -30.4 - grow, 9 + grow * 2, 2.6 + grow * 2, 1.3, pen(p.jacket));
    }
  }
  if (s >= 1) circle(c, 4.2, -27.4, 0.9, OUTLINE);
  c.restore();
}

window.Painter = { W, H, rgba, vgradient, circle, rrect, line, poly, star, ridge, text, runs, measure, inkBounds, bigNumber, bigRuns, fmt, makePath, pointAt, strokePath, hiker, PEOPLE };
})();
