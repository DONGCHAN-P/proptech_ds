/* One paused clock. Caption opacity hard-resets at every exact native boundary. */
document.fonts.ready.then(()=>{
  const root=document.getElementById('root');
  const tl=gsap.timeline({paused:true});
  for(const cue of document.querySelectorAll('.cue')){
    const start=Number(cue.dataset.start),end=start+Number(cue.dataset.duration);
    tl.set(cue,{opacity:0},0);
    tl.set(cue,{opacity:1},start);
    tl.set(cue,{opacity:0},end);
  }
  window.__timelines=window.__timelines||{};
  window.__timelines[root.dataset.compositionId]=tl;
  window.__sourcePreviewSeek=t=>{
    tl.pause().time(t,false);
    for(const el of document.querySelectorAll('.clip'))el.style.visibility=t>=Number(el.dataset.start)&&t<Number(el.dataset.start)+Number(el.dataset.duration)?'visible':'hidden';
  };
});
