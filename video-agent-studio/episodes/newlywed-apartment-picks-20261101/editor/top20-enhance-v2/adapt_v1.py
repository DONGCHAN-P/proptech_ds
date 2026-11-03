"""One-time source copy and scoped main-only adaptation; never edits v1."""
from pathlib import Path
import shutil

H=Path(__file__).resolve().parent
OLD=H.with_name('top20-production-v1')
for name in ['build.py','caption_tools.py','caption_backgrounds.py','local_jobs.py','apply_bgm.py']:
    shutil.copy2(OLD/name,H/name)
p=H/'build.py';s=p.read_text(encoding='utf-8')
s=s.replace('python build.py [--timing /path/to/timing.json] [--shorts /path/to/shorts.json]', 'python build.py --script /path/to/script.json --timing /path/to/locked_timing.json')
s=s.replace("ap.add_argument('--shorts');", "ap.add_argument('--scene-data',help='Optional visual specs/data JSON');ap.add_argument('--visual-module',action='append',default=[],help='Additional local Python renderer module');")
s=s.replace("T=read(a.timing) if a.timing else", "if not a.timing and (E/'director/top20-enhance-v2/locked_timing.json').exists():a.timing=str(E/'director/top20-enhance-v2/locked_timing.json')\nT=read(a.timing) if a.timing else")
s=s.replace("E/'writer/top20-8min-v2/scene_proposals_v3.json'", "E/'director/top20-enhance-v2/scene_proposals_v5.json'")
s=s.replace("assert len(scenes)==27 and len(regions)==20 and len({p['sha256'] for p in photos.values()})==20", "assert scenes and len({s['scene_id'] for s in scenes})==len(scenes),'Scene IDs must be unique'\nassert len(regions)==20 and len({p['sha256'] for p in photos.values()})==20\nassert all(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',s['scene_id']) for s in scenes),'Unsafe scene ID'")
start=s.index("md=script_path.with_name(");end=s.index("if a.timing:inputs.append",start)
s=s[:start]+"inputs=[script_path,Path(__file__),H/'visuals.py',H/'extra_scenes.py',H/'caption_tools.py',H/'caption_backgrounds.py',H/'design.md',E/'research/top20-8min-v2/combined_facts.json',E/'visual/top20-8min-v2/photo_assets_v2.json',E/'visual/top20-8min-v2/maps/map_assets.json',R/'config/channel_style_tokens.json',R/'config/video_style.json',E/'director/top20-enhance-v2/authorization.json']\nif a.scene_data:inputs.append(Path(a.scene_data))\ninputs.extend(Path(v) for v in a.visual_module)\n"+s[end:]
s=s.replace(" wp=Path(T.get('words_file') or (T.get('scenes',[{}])[0].get('words_path')) or E/'narration/top20-production-v1/production-v2/words_v2.json')\n if not wp.is_absolute():wp=R/wp\n if wp.exists():\n  inputs.append(wp)\n  for w in read(wp)['words']:word_groups.setdefault(w['sentence_id'],[]).append(w)", " word_paths={str(T.get('words_file') or '')}|{str(v.get('words_path') or '') for v in T.get('scenes',[])}\n if not any(word_paths):raise ValueError('Locked input must identify words_file or per-scene words_path; no old-word fallback')\n for word_path in sorted(word_paths-{''}):\n  wp=Path(word_path)\n  if not wp.is_absolute():wp=R/wp\n  if not wp.exists():raise FileNotFoundError(wp)\n  inputs.append(wp)\n  for w in read(wp)['words']:\n   group=word_groups.setdefault(w['sentence_id'],[])\n   if w not in group:group.append(w)")
s=s.replace(" rp=Path(T.get('source_timing') or E/'narration/top20-production-v1/timing_proposals_v2.json')", " rp=Path(T.get('source_timing') or a.timing)")
s=s.replace("  for ns in read(rp)['scenes']:", "  inputs.append(rp)\n  for ns in read(rp)['scenes']:")
s=s.replace("float(ov.get('start_s',s['start_s']))", "float(ov.get('start_s',s.get('start_s',0)))").replace("float(ov.get('end_s',s['end_s']))", "float(ov.get('end_s',s.get('end_s',0)))")
s=s.replace("s['anchors']=ov.get('anchors',{})", "s['anchors']=dict(ov.get('anchors',{}))\n if T.get('timing_locked') and s['scene_id'] not in overrides:raise ValueError('Scene missing from actual lock: '+s['scene_id'])")
s=s.replace("md=", "md=")
s=s.replace("write(assets/f'{rid}_locator.svg',paths_svg([*base_paths,target]))", "write(assets/f'{rid}_locator.svg',paths_svg([*base_paths,target]))\n # Source paths contain only straight M/L/Z commands; fit a static viewBox to actual geometry.\n d=target.get('d','');assert not re.search('[CcQqAaSsTtHhVv]',d),'Unsupported geometry command'\n coords=[float(v) for v in re.findall(r'-?\\d+(?:\\.\\d+)?',d)];xs=coords[::2];ys=coords[1::2]\n x0,y0,x1,y1=min(xs),min(ys),max(xs),max(ys);pad=max(x1-x0,y1-y0)*.09\n view=f'{x0-pad:.3f} {y0-pad:.3f} {x1-x0+2*pad:.3f} {y1-y0+2*pad:.3f}'\n focus=copy.deepcopy(target);focus.set('stroke','#173348');focus.set('stroke-width','0.65');focus.set('vector-effect','non-scaling-stroke')\n write(assets/f'{rid}_focus.svg',paths_svg([focus],view))")
s=s.replace("'top20-hf-production-v1'", "'top20-enhance-editor-v2'")
s=s.replace("def count(s,id,val,at):\n # Immutable numeric endpoint + tabular width. Same position/ease as paired bar.\n return f'{{const el=document.getElementById(\"{id}\");const proxy={{v:0}};tl.fromTo(proxy,{{v:0}},{{v:{val},duration:1.6,ease:\"power2.out\",immediateRender:false,onUpdate:()=>{{el.textContent=Math.round(proxy.v).toLocaleString(\"en-US\")}}}},{at:.4f});}}'", "def count(s,id,val,at):\n # Exact final value; reveal only. No unspoken intermediate count values.\n return f'document.getElementById(\"{id}\").textContent=\"{val:,}\";'+tween('#'+id,{'opacity':0},{'opacity':1},at,.25)")
point=s.index('hosts=[];story=[]')
s=s[:point]+"from visuals import install_visuals\nfrom extra_scenes import load_renderers\nvisual_context=install_visuals(globals())\nextra_renderers=load_renderers(visual_context,a.scene_data,a.visual_module)\n"+s[point:]
s=s.replace(" if s.get('region_id'): body,anim=region_scene(s)", " if s['scene_id'] in extra_renderers:body,anim=extra_renderers[s['scene_id']](s,visual_context)\n elif s.get('visual',{}).get('type'):body,anim=extra_renderers['__generic__'](s,visual_context)\n elif s.get('region_id'): body,anim=region_scene(s)")
s=s.replace(" else:body,anim=opening(s)", " elif sid in ['O001','O002']:body,anim=opening(s)\n else:raise ValueError('No visual renderer/spec for '+sid+'; add to extra_scenes.py or --scene-data')")
s=s.replace("rule='stat-bars-and-fills + counting-dynamic-scale' if s.get('region_id') else 'stat-bars-and-fills'", "rule='spoken-value-reveal + current-region-highlight'")
s=s.replace("s[\"title\"]", "s.get(\"title\",sid)")
s=s.replace("'words_file':str(wp) if word_groups else None", "'words_files':sorted(word_paths-{''}) if word_groups else []")
s=s.replace("'script_v3_estimated_27_scene_480s'", "'script_estimate_not_audio_aligned'")
s=s.replace("27 scene ids remain fixed.", "Any unique scene IDs; each must be present in script, lock and a visual renderer/spec. Extra scenes use extra_scenes.py or --scene-data.")
s=s.replace("'# 신혼부부가 사는 곳 · 27장면\\n\\n잠정 480초. 음성 미연결. 실제 타임록으로 교체.\\n\\n'", "f'# 신혼부부가 사는 곳 · {len(scenes)}장면\\n\\n입력: {script_path.name} / {Path(a.timing).name if a.timing else chr(32)}. 잠금 상태: {T.get(\"timing_locked\",False)}. 실제 청취 미실행.\\n\\n'")
s=s.replace("'shorts':[str(H/'shorts/promo'),str(H/'shorts/analysis')],", "'scope':'main-only', 'script_file':str(script_path), 'source_timing':a.timing, 'layout_families':visual_context['layout_families'],")
s=s.replace("subprocess.run([sys.executable,str(H/'build_shorts.py')]+(['--clips',a.shorts] if a.shorts else []),check=True)", "js(H/'anchor_audit.json',visual_context['anchor_audit'])")
p.write_text(s,encoding='utf-8')
print('Copied generator and four helpers; v1 untouched')
