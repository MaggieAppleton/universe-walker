"use strict";
(() => {
const P = window.Painter;
// Each world: gradient + solid sky, scenery in the bottom ~90px (y > 150),
// a trail that enters and leaves the side edges, and a landmark at goalX.

const ease = t => { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); };
const sample = (f, x0 = -16, x1 = 336, step = 8) => { const pts = []; for (let x = x0; x <= x1; x += step) pts.push([x, f(x)]); return pts; };

// Filled land whose top edge is a smooth curve through the given points.
function hill(c, points, pen, bottom = 240) {
  const path = P.makePath(points);
  c.fillStyle = pen; c.beginPath(); c.moveTo(path.pts[0][0], bottom);
  path.pts.forEach(([x, y]) => c.lineTo(x, y));
  c.lineTo(path.pts[path.pts.length - 1][0], bottom); c.closePath(); c.fill();
}

function lighthouse(c, x, y, lit) {
  if (lit) {
    const beam = c.createLinearGradient(x, 0, x - 80, 0);
    beam.addColorStop(0, "rgba(255,226,140,1)");
    beam.addColorStop(1, "rgba(255,226,140,0)");
    c.fillStyle = beam;
    c.beginPath(); c.moveTo(x, y - 30); c.lineTo(x - 80, y - 44); c.lineTo(x - 80, y - 20); c.fill();
    P.circle(c, x, y - 30, 9, "rgba(255,226,140,.35)");
  }
  P.poly(c, [[x - 6, y], [x + 6, y], [x + 4, y - 25], [x - 4, y - 25]], "#f4f1ea");
  P.poly(c, [[x - 5.4, y - 8], [x + 5.4, y - 8], [x + 5, y - 14], [x - 5, y - 14]], "#d6453d");
  P.poly(c, [[x - 4.6, y - 18], [x + 4.6, y - 18], [x + 4.3, y - 23], [x - 4.3, y - 23]], "#d6453d");
  P.rrect(c, x - 4, y - 33, 8, 7, 1, lit ? "#ffe28a" : "#5b6278");
  P.poly(c, [[x - 6, y - 33], [x + 6, y - 33], [x, y - 39]], "#2d2f45");
}
// A summit-style flag: a tall pole, the pennant hoisted to the top on arrival.
function flag(c, x, y, raised) {
  if (raised) P.circle(c, x + 8, y - 30, 16, "rgba(255,220,120,.3)");
  P.rrect(c, x - 5, y - 3, 10, 4, 2, "#8a7d70");
  P.line(c, x, y - 2, x, y - 38, 2, "#f1ece4");
  const top = raised ? y - 38 : y - 20;
  P.poly(c, [[x + 1, top], [x + 19, top + 6], [x + 1, top + 12]], raised ? "#ffcf4a" : "#e5484d");
  P.circle(c, x, y - 39, 1.8, "#ffd56a");
}
function windmill(c, x, y, lit) {
  if (lit) P.circle(c, x, y - 24, 20, "rgba(255,236,170,.35)");
  P.poly(c, [[x - 7, y], [x + 7, y], [x + 4.5, y - 22], [x - 4.5, y - 22]], "#f3ead8");
  P.poly(c, [[x - 6, y - 21], [x + 6, y - 21], [x, y - 28]], "#b2463a");
  P.rrect(c, x - 2.5, y - 8, 5, 8, 2, lit ? "#ffd56a" : "#7a5a44");
  c.save(); c.translate(x, y - 23); c.rotate(lit ? 0.5 : 0.2);
  for (let i = 0; i < 4; i++) { c.rotate(Math.PI / 2); P.rrect(c, 1.5, -2.3, 17, 4.6, 1, "#fbf7ee"); }
  c.restore();
  P.circle(c, x, y - 23, 2, "#5a4636");
}
function tree(c, x, y, r, pen) {
  P.rrect(c, x - 1, y - r, 2, r, 0, "#4b3a2a");
  P.circle(c, x, y - r - r * 0.5, r, pen);
}

/* Coast: the cliff edge and the path share one curve, so they run together. */
const coastEdge = x => 214 - 40 * ease((x + 20) / 340);
const coastPath = x => coastEdge(x) + 17;

/* Valley: a river winds out of the gap between two slopes. */
const riverX = y => 204 + 16 * Math.sin((y - 170) / 18);
const riverW = y => 1 + (y - 170) * 0.45;

const WORLDS = {
  coast: {
    label: "Coast",
    sky: ["#151d3b", "#2f3468", "#7a5690", "#e9967a"], solid: "#2a2f5c", skyEnd: 164, stars: true,
    trail: sample(coastPath),
    goalX: 262,
    draw(c, reached, landmark) {
      P.circle(c, 64, 164, 22, "rgba(255,200,150,.16)");
      P.circle(c, 64, 164, 12, "#ffd29a");
      hill(c, [[-10, 156], [20, 154], [52, 162], [70, 166]], "#4b3f78");
      c.fillStyle = P.vgradient(c, 164, 240, ["#3d5f9e", "#26407a"]);
      c.fillRect(0, 164, P.W, 76);
      [[22, 170], [14, 176], [8, 182]].forEach(([w, y]) => P.rrect(c, 64 - w / 2, y, w, 1.6, 1, "rgba(255,210,160,.28)"));
      c.fillStyle = P.vgradient(c, 170, 240, ["#79b961", "#4b8a48"]);
      c.beginPath(); c.moveTo(-16, 240);
      sample(coastEdge).forEach(([x, y]) => c.lineTo(x, y));
      c.lineTo(336, 240); c.fill();
      const x = 288, y = coastEdge(288) + 8;
      if (landmark === "flag") return flag(c, x - 4, y, reached);
      c.save(); c.translate(x, y);
      if (landmark === "big") c.scale(1.5, 1.5);
      lighthouse(c, 0, 0, reached);
      c.restore();
    },
    look: { edge: "#b28f5c", bed: "#e7cf98", walked: "#fff6dc" },
  },

  fields: {
    label: "Fields",
    sky: ["#2c64a8", "#3b77bb", "#5690cc"], solid: "#3570b4", skyEnd: 166,
    trail: [[-14, 200], [30, 212], [80, 222], [130, 218], [160, 204], [184, 192], [216, 190], [244, 178], [264, 168], [300, 162], [336, 160]],
    goalX: 262,
    draw(c, reached) {
      [[44, 158, 7], [56, 154, 9], [70, 158, 6]].forEach(([x, y, r]) => P.circle(c, x, y, r, "rgba(255,255,255,.85)"));
      hill(c, [[-16, 166], [60, 158], [140, 160], [220, 164], [280, 156], [336, 154]], "#8fc66b");
      hill(c, [[-16, 186], [80, 178], [190, 186], [336, 172]], "#e6c15a");
      hill(c, [[-16, 206], [100, 198], [220, 210], [336, 198]], "#79b55a");
      windmill(c, 284, 160, reached);
    },
    look: { edge: "#a88a52", bed: "#f0dca8", walked: "#fffaf0" },
  },

  valley: {
    label: "Valley",
    sky: ["#2b3f6c", "#384f80", "#4f6694"], solid: "#354b7a", skyEnd: 170,
    trail: [[-14, 200], [40, 198], [100, 194], [150, 189], [186, 186], [215, 184], [244, 180], [282, 172], [336, 164]],
    goalX: 215,
    draw(c) {
      hill(c, [[-16, 150], [80, 156], [160, 162], [240, 156], [336, 148]], "#8d9cc4");
      // two slopes meeting at the valley floor; diagonal inner edges, no seams
      hill(c, [[-16, 156], [90, 162], [170, 172], [214, 180], [236, 240]], "#5f8a86");
      hill(c, [[176, 240], [196, 182], [250, 168], [300, 160], [336, 156]], "#4f7b78");
      // river ribbon widening toward the viewer
      c.fillStyle = P.vgradient(c, 170, 240, ["#cfe9f4", "#6fb2d8"]);
      c.beginPath();
      for (let y = 170; y <= 240; y += 3) c.lineTo(riverX(y) - riverW(y), y);
      for (let y = 240; y >= 170; y -= 3) c.lineTo(riverX(y) + riverW(y), y);
      c.fill();
      hill(c, [[-16, 204], [60, 206], [130, 218], [176, 240]], "#4c8250");
      hill(c, [[244, 240], [270, 214], [300, 206], [336, 204]], "#3f7448");
      [[30, 172, 5], [46, 176, 4], [292, 168, 5], [306, 166, 4]].forEach(([x, y, r]) => tree(c, x, y, r, "#355f45"));
    },
    after(c, reached) {
      // stone bridge where the trail crosses the river
      const x = 215, y = 184;
      P.rrect(c, x - 13, y - 4, 26, 8, 3, "#cdbb9c");
      c.fillStyle = P.vgradient(c, 170, 240, ["#cfe9f4", "#6fb2d8"]);
      c.beginPath(); c.ellipse(x, y + 4, 7, 5, 0, Math.PI, 0); c.fill();
      [x - 12, x + 12].forEach(px => {
        P.rrect(c, px - 1, y - 12, 2, 9, 1, "#6b4b3a");
        if (reached) P.circle(c, px, y - 13, 6, "rgba(255,214,110,.35)");
        P.circle(c, px, y - 13, 2.2, reached ? "#ffd56a" : "#8a7a6a");
      });
    },
    look: { edge: "#9a7a4e", bed: "#e8d2a0", walked: "#fff6dc" },
  },
};

window.Worlds = { WORLDS };
})();
