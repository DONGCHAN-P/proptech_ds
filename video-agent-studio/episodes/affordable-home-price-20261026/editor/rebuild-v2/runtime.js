/* All information changes are scheduled on one paused clock. No outline focus. */
document.fonts.ready.then(() => {
  const tl = gsap.timeline({paused:true});
  const byId = id => {const el=document.getElementById(id);if(!el)throw Error('Missing graphic target '+id);return el;};
  for (const el of document.querySelectorAll('.semantic')) tl.set(el,{opacity:0},0);
  for (const el of document.querySelectorAll('.bar')) tl.set(el,el.classList.contains('vertical')?{scaleY:0}:{scaleX:0},0);
  // Opening inputs have one CSS initial state and one nonzero-duration tween.
  // Repeated zero-duration sets on the same target are unsafe under render
  // warm-seek / backward-seek reconciliation (including exactly t=0).
  if(MODEL.opening_context){tl.fromTo(byId(MODEL.opening_context.id),{opacity:1},{opacity:0,duration:1/30,ease:'none',immediateRender:false},MODEL.opening_context.end_s);}
  for (const beat of MODEL.beats) {
    const t=beat.start_s, duration=Math.min(.45,Math.max(.06,beat.end_s-t));
    for (const id of beat.reveal) tl.fromTo(byId(id),{opacity:0,y:8},{opacity:1,y:0,duration:Math.min(.24,duration),ease:'power2.out',immediateRender:false},t);
    for (const id of beat.dim) tl.to(byId(id),{opacity:.55,duration:Math.min(.18,duration)},t);
    for (const id of beat.hide) tl.set(byId(id),{opacity:0},t);
    for (const id of beat.fills) {const el=byId(id),axis=el.classList.contains('vertical')?'scaleY':'scaleX';tl.fromTo(el,{[axis]:0},{[axis]:1,duration,ease:'power2.out',immediateRender:false},t);}
    for (const move of beat.transforms) tl.to(byId(move.id),{scaleX:move.scaleX,duration,ease:'power2.out'},t);
  }
  for (const cue of MODEL.cues) {
    const el=byId('cue-'+cue.id);
    tl.set(el,{opacity:0},0);tl.set(el,{opacity:1},cue.start_s);tl.set(el,{opacity:0},cue.end_s);
  }
  window.__timelines=window.__timelines||{};
  window.__timelines.main=tl;
  // Local QA only: production clip lifecycle belongs to HyperFrames.
  window.__sourceSeek=t=>{tl.pause().time(t,false);};
  window.__sourceSeek(0);
});
