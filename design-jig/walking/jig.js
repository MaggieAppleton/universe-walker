"use strict";
const kit = DialKit.createDialKit("Walking badge", {
  badge: {type:"select", options:["Maggie","Martin"], default:"Maggie"},
  landscape: {type:"select",options:[{value:"sunset",label:"Sunset trail"},{value:"alpine",label:"Alpine pass"},{value:"valley",label:"River valley"},{value:"meadow",label:"Open fields"},{value:"coast",label:"Coastal path"},{value:"map",label:"Overland map"}],default:"sunset"},
  atmosphere:{type:"select",options:[{value:"gradient",label:"Gradient"},{value:"solid",label:"Solid"}],default:"gradient"},
  countSize: [4,3,5,1],
  pathWidth: [4,3,5,1],
  walkerGap: [16,12,20,4],
  markerHeight: [22,18,26,4],
  filledPartner:true,
  stride:[1,0,1,1],
  holdProgress:[55,0,100,5],
  successAge:[400,0,600,100],
}, {id:"walking-landscapes-v2", persist:true});
const root = DialKit.createDialRoot({theme:"light",position:"top-right"});
const rows = [];
let current, timer;
let revision=0;
const imageCache=new Map();
const asset = path => window.walkingEmbeddedFiles?.[path] || path;
const states = document.getElementById("states");
const navigation = document.getElementById("navigation");

function loadImage(url) {
  url=asset(url);
  if (!imageCache.has(url)) imageCache.set(url,new Promise((resolve,reject)=>{
    const image=new Image(); image.onload=()=>resolve(image); image.onerror=reject; image.src=url;
  }));
  return imageCache.get(url);
}

function nativeImage(bundle,key) {
  const id=bundle.lookup[key];
  if (!id) throw new Error(`Missing native render: ${key}`);
  return loadImage(bundle.images[id]);
}

async function refresh() {
  const generation=++revision;
  const p={...current};
  const encoded = JSON.stringify({goal:500,...p});
  document.getElementById("values").textContent = encoded;
  document.getElementById("summary").textContent = `500-step goal · ${p.badge}’s badge · ${rows.length} states`;
  const person=p.badge==="Maggie" ? 0:1;
  await Promise.all(rows.map(async row=>{
    row.before.src=asset(`./renders/reference-${row.id}-${person}.png`);
    row.after.dataset.ready="false";
    const context=row.after.getContext("2d");
    const age=row.id==="holding" ? p.holdProgress:(row.success ? p.successAge:400);
    const images=row.id==="fatal" ? [await loadImage("./renders/fatal.png")] : await Promise.all([
      nativeImage(nativeLayers.scenery,`${p.landscape}|${p.atmosphere}|${p.markerHeight}|${+row.reached}`),
      nativeImage(nativeLayers.trail,`${row.id}|${person}|${p.walkerGap}|${p.pathWidth}|${+p.filledPartner}|${p.stride}|${p.landscape}`),
      nativeImage(nativeLayers.header,`${row.id}|${p.countSize}|${age}`),
    ]);
    if (generation!==revision) return;
    context.imageSmoothingEnabled=false;
    context.fillStyle="#101419";
    context.fillRect(0,0,320,240);
    images.forEach(image=>context.drawImage(image,0,0));
    row.after.dataset.ready="true";
  }));
}

async function start() {
  const cases = window.walkingCases;
  let previous = "";
  for (const item of cases) {
    if (item.group !== previous) {
      const heading = document.createElement("h2");
      heading.className = "group";
      heading.id = item.group.toLowerCase();
      heading.textContent = item.group;
      states.append(heading);
      const link = document.createElement("a");
      link.href = `#${heading.id}`;
      link.textContent = item.group;
      navigation.append(link);
      previous = item.group;
    }
    const section = document.createElement("section");
    section.className = "state";
    section.dataset.state = item.id;
    const title = document.createElement("h3");
    title.textContent = item.title;
    const note = document.createElement("p");
    note.textContent = item.note;
    const screens = document.createElement("div");
    screens.className = "screens";
    const before = new Image(320,240);
    before.alt = `${item.title} · Reference treatment`;
    const after = document.createElement("canvas");
    after.width=320; after.height=240;
    after.setAttribute("role","img");
    after.setAttribute("aria-label",`${item.title} · Refinement`);
    screens.append(before,after);
    section.append(title,note,screens);
    states.append(section);
    rows.push({id:item.id,reached:item.reached,success:item.success,before,after});
  }
  kit.subscribe(values=>{
    current=values;
    clearTimeout(timer);
    timer=setTimeout(()=>refresh().catch(error=>{
      document.getElementById("message").textContent=error.message;
      console.error(error);
    }),100);
  });
}

document.getElementById("copy").onclick=async()=>{
  try {
    await navigator.clipboard.writeText(JSON.stringify({goal:500,...current},null,2));
    document.getElementById("message").textContent="Settings copied.";
  } catch {
    const selection = getSelection();
    const range = document.createRange();
    range.selectNodeContents(document.getElementById("values"));
    selection.removeAllRanges(); selection.addRange(range);
    document.getElementById("message").textContent="Settings selected. Press ⌘C to copy.";
  }
};
document.getElementById("reset").onclick=()=>kit.resetValues();
document.getElementById("controls").onclick=()=>kit.setOpen(!kit.getOpen());
window.walkingJig = {kit,root,rows};
start().catch(error=>document.getElementById("message").textContent=error.message);
