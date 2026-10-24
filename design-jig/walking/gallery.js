"use strict";
(() => {
  const choices=[];
  const {kit}=window.walkingJig;
  const image=(path,label)=>{
    const img=new Image(320,240);
    img.src=window.walkingEmbeddedFiles?.[path]||path;
    img.alt=label;
    return img;
  };
  for(const item of walkingExamples.scenes){
    const section=document.createElement("section");
    section.className="state";
    const title=document.createElement("h3");title.textContent=item.title;
    const pair=document.createElement("div");pair.className="screens";
    for(const sky of ["gradient","solid"]){
      const label=item.id==="map" ? (sky==="gradient" ? "Shaded paper":"Flat paper") : (sky==="gradient" ? "Gradient sky":"Solid sky");
      const button=document.createElement("button");
      button.className="scene-choice";button.type="button";
      button.setAttribute("aria-label",`Use ${item.title}, ${label.toLowerCase()}`);
      const caption=document.createElement("span");caption.textContent=label;
      button.append(image(item[sky],`${item.title} · ${label}`),caption);
      button.onclick=()=>kit.setValues({landscape:item.id,atmosphere:sky});
      choices.push({button,id:item.id,sky});
      pair.append(button);
    }
    section.append(title,pair);
    document.getElementById("landscape-gallery").append(section);
  }
  for(const item of walkingExamples.concepts){
    const section=document.createElement("section");section.className="state";
    const title=document.createElement("h3");title.textContent=item.title;
    const note=document.createElement("p");note.textContent=item.note;
    const labels=document.createElement("div");labels.className="column-labels";
    labels.innerHTML="<span>Walking apart</span><span>Sync confirmed</span>";
    const pair=document.createElement("div");pair.className="screens";
    pair.append(image(item.pending,`${item.title} · Walking apart`),image(item.success,`${item.title} · Sync confirmed`));
    section.append(title,note,labels,pair);
    document.getElementById("concept-gallery").append(section);
  }
  kit.subscribe(values=>{
    for(const choice of choices)choice.button.setAttribute("aria-pressed",String(choice.id===values.landscape&&choice.sky===values.atmosphere));
    const scene=walkingExamples.scenes.find(item=>item.id===values.landscape);
    document.getElementById("active-design").textContent=`${scene?.title||values.landscape} · ${values.atmosphere==="gradient" ? "Gradient":"Solid"}`;
  });
})();
