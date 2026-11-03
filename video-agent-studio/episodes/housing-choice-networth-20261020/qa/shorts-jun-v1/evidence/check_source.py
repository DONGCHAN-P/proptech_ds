"""SOURCE 독립 검수. 제작 입력은 읽기만 하며 QA 근거만 저장한다."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import re

import numpy as np
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
EP = HERE.parents[2]
PROJECT = EP.parents[2]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def norm(s):
    return re.sub(r'\s+', '', s)

paths = []
for kind in ('funnel', 'analysis'):
    p = EP / 'outputs/shorts-jun-v1' / kind
    paths.extend(p / n for n in ('index.html', 'timing.json', 'scenes.json', 'anchor_audit.json', 'preview/bbox_report.json'))
    paths.extend(sorted((p / 'preview').glob('*.png')))
    paths.append(EP / 'narration/shorts-jun-v1' / kind / 'script.txt')
paths.extend(EP / n for n in ('outputs/script-final-v6/script_v6.md', 'outputs/growth-explanation-v1/facts.json', 'brief.json', 'state.json', 'director/launch-and-jun-v1/shorts_authorization.json'))
paths.extend(PROJECT / n for n in ('video-agent-studio/WORKFLOW.md', 'video-agent-studio/agents/video_qa.toml', 'video-agent-studio/agents/video_director.toml', 'video-agent-studio/guides/호출_효율_운영.md', 'config/video_call_policy.json', 'config/vertical_video_safe_area.json'))
manifest = {str(p.relative_to(EP)) if p.is_relative_to(EP) else str(p): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in paths}
initial = {p: sha(p) for p in paths}
script = (EP / 'outputs/script-final-v6/script_v6.md').read_text(encoding='utf-8-sig')
facts = read(EP / 'outputs/growth-explanation-v1/facts.json')
profile = read(PROJECT / 'config/vertical_video_safe_area.json')['profiles']['youtube_portrait_full_frame_v2']
summary = {'review_stage': 'SOURCE', 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'safe_rect': profile['critical_rect'], 'tracks': {}, 'network_requests_blocked': [], 'coverage_note': '현재 SOURCE HTML의 수동 타임라인 seek·클립 가시성 적용 후 DOM Range 재측정. HyperFrames CLI check 또는 실제 인코딩 검사와 다르다. 음성은 재생하지 않음.'}
measure_js = """t => {
  document.querySelectorAll('audio,video').forEach(e=>{e.pause();e.muted=true});
  window.__timelines.main.totalTime(t,false).pause();
  document.querySelectorAll('.clip').forEach(e=>{
    const s=Number(e.dataset.start||0), d=Number(e.dataset.duration||0);
    e.style.visibility=(t>=s && t<s+d)?'visible':'hidden';
  });
  const rows=[];
  for(const el of document.querySelectorAll('[data-kind]')) {
    const st=getComputedStyle(el);
    if(st.visibility!=='visible' || Number(st.opacity)===0) continue;
    const walk=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
    while(walk.nextNode()) {
      const node=walk.currentNode;
      if(!node.textContent.trim()) continue;
      const range=document.createRange();range.selectNodeContents(node);
      for(const r of range.getClientRects()) if(r.width>0.01 && r.height>0.01)
        rows.push({kind:el.dataset.kind,text:node.textContent,scene_id:el.closest('.scene')?.id||null,font_px:parseFloat(st.fontSize),bbox:[r.left,r.top,r.right,r.bottom],time_s:t});
    }
  }
  return rows;
}"""
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
    summary['browser_version'] = browser.version
    context = browser.new_context(viewport={'width':1080,'height':1920},device_scale_factor=1,offline=True)
    def route_handler(route):
        if route.request.url.startswith(('file:', 'data:')):
            route.continue_()
        else:
            summary['network_requests_blocked'].append(route.request.url)
            route.abort()
    context.route('**/*',route_handler)
    for kind in ('funnel','analysis'):
        p = EP / 'outputs/shorts-jun-v1' / kind
        html = (p/'index.html').read_text(encoding='utf-8-sig')
        soup = BeautifulSoup(html,'html.parser')
        timing, scenes, bbox = (read(p/n) for n in ('timing.json','scenes.json','preview/bbox_report.json'))
        narration = (EP/'narration/shorts-jun-v1'/kind/'script.txt').read_text(encoding='utf-8-sig')
        page = context.new_page()
        page.goto((p/'index.html').as_uri())
        page.evaluate('document.fonts.ready')
        rows = []
        times = set(bbox['sample_times'])
        for s in scenes['scenes']:
            times.update((s['start_s'],s['start_s']+1/30,s['end_s']-1/30))
        for t in sorted(times):
            rows.extend(page.evaluate(measure_js,t))
        failures = [e for e in rows if e['bbox'][0]<139.99 or e['bbox'][1]<259.99 or e['bbox'][2]>840.01 or e['bbox'][3]>1360.01]
        measured = {norm(e['text']) for e in rows}
        expected = {norm(el.get_text('\n')) for el in soup.select('[data-kind]')}
        # 줄바꿈으로 분리된 텍스트 노드는 각각의 Range로 얻는다.
        combined = {norm(el.get_text('\n')) for el in soup.select('[data-kind]') if all(norm(n) in measured for n in el.strings if n.strip())}
        missing = sorted(expected - measured - combined)
        caption_mismatch = []
        for i,cue in enumerate(timing['cues']):
            if norm(''.join(cue['display_lines'])) != norm(cue['text']):caption_mismatch.append(cue['id'])
            if i and cue['start_s']<timing['cues'][i-1]['end_s']-1e-7:caption_mismatch.append(cue['id']+':overlap')
        pixels=[]
        for s in bbox['snapshots']:
            f = p/'preview'/(s['scene_id']+'.png')
            with Image.open(f) as im:
                a=np.asarray(im.convert('RGB'))
                mask=(a[260:420,:,0]<80)&(a[260:420,:,1]<110)&(a[260:420,:,2]<130)
                ys,xs=np.where(mask)
                pixels.append({'scene_id':s['scene_id'],'time_s':s['time_s'],'file':str(f.relative_to(EP)),'sha256':sha(f),'snapshot_hash_match':sha(f)==s['sha256'],'size':list(im.size),'title_ink_bbox':[int(xs.min()),int(ys.min()+260),int(xs.max()+1),int(ys.max()+261)],'title_ink_pixels_outside_right840':int(mask[:,840:].sum())})
        axis_checks=[]
        for section in soup.select('.scene'):
            bars=section.select('.bar')
            if not bars:continue
            values=[]
            for bar in bars:
                top=float(re.search(r'top:([\d.]+)px',bar['style'])[1]); height=float(re.search(r'height:([\d.]+)px',bar['style'])[1]); value=float(bar['data-value'])
                values.append({'value_eok':value,'top':top,'height':height,'baseline':top+height,'px_per_eok':height/value})
            axis_checks.append({'scene_id':section['id'],'unit':'억원','axis_range':[0,10],'bars':values})
        result={'html_sha256':sha(p/'index.html'),'report_html_hash_match':sha(p/'index.html')==bbox['html_sha256'],'declared_seconds':timing['duration_s'],'sample_times_count':len(times),'independent_Range_rows':len(rows),'independent_Range_failures':failures,'source_text_missing_from_independent_ranges':missing,'producer_Range_rows':len(bbox['elements']),'producer_Range_outside_rect':sum(e['bbox'][0]<140 or e['bbox'][1]<260 or e['bbox'][2]>840 or e['bbox'][3]>1360 for e in bbox['elements']),'font_min_px':{k:min(e['font_px'] for e in rows if e['kind']==k) for k in {e['kind'] for e in rows}},'narration_matches_timing_text':norm(narration)==norm(''.join(c['text'] for c in timing['clips'])),'clip_text_in_main_script':[norm(c['text']) in norm(script) for c in timing['clips']],'source_script_hash_matches':timing['source_script_sha256']==sha(EP/'outputs/script-final-v6/script_v6.md'),'caption_text_or_overlap_errors':caption_mismatch,'snapshots':pixels,'chart_geometry':axis_checks,'actual_listening':'unchecked','continuous_playback':'unchecked','encoded_MP4':'unchecked'}
        (HERE/(kind+'_range_measurements.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        summary['tracks'][kind]=result
        page.close()
    browser.close()
summary['model_checks']={'baseline_eok':{k:round(v/1e8,1) for k,v in next(r for r in facts['sensitivity'] if r['house_growth_pct']==2)['networth_krw'].items()},'buy_sensitivity_eok':{str(r['house_growth_pct']):round(r['networth_krw']['매매']/1e8,1) for r in facts['sensitivity']},'funding_identity_eok':2.4+3.6,'first_year_gain_manwon':60000*0.02,'gain_div_equity_pct':1200/24000*100,'price2_is_planning_scenario':any('planning scenario' in s for s in facts['scope_notes']),'constant_inputs':facts['constant_model_inputs'],'leverage_example':facts['leverage_example']}
summary['input_changes_during_checks']=[str(p) for p,h in initial.items() if sha(p)!=h]
(HERE/'input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'independent_source_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'tracks':{k:{'times':v['sample_times_count'],'range_rows':v['independent_Range_rows'],'range_failures':len(v['independent_Range_failures']),'missing_text':v['source_text_missing_from_independent_ranges'],'caption_errors':v['caption_text_or_overlap_errors'],'narration_matches':v['narration_matches_timing_text'],'main_text_matches':all(v['clip_text_in_main_script']),'snapshot_hashes_match':all(s['snapshot_hash_match'] for s in v['snapshots'])} for k,v in summary['tracks'].items()},'input_changes':summary['input_changes_during_checks'],'blocked_network_requests':summary['network_requests_blocked'],'model_checks':{k:v for k,v in summary['model_checks'].items() if k not in ('constant_inputs','leverage_example')}},ensure_ascii=False))
