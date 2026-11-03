"""v3 변경분만 독립 검수: 큐 그룹/박스 합집합, 기존 음성·팩트 재사용."""
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

Q = Path(__file__).resolve().parent
EP = Q.parents[2]
H = EP / 'editor/top20-split-v4/jun-and-shorts-v1'
D = EP / 'director/top20-split-v4/part1-jun-and-shorts-v1'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


VISIBLE = r'''() => {
 function shown(e){for(let p=e;p;p=p.parentElement){let s=getComputedStyle(p);
 if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)<.01)return false;}return true;}
 return {groups:Array.from(document.querySelectorAll('.caption-group')).filter(shown).map(e=>{
  let r=e.querySelector('.caption-rail'),t=e.querySelector('.caption');return {id:e.id,text:t.textContent,
  rail_visible:shown(r),text_visible:shown(t),rail_count:e.querySelectorAll('.caption-rail').length,
  text_count:e.querySelectorAll('.caption').length};}),
  orphan_visible_rails:Array.from(document.querySelectorAll('.caption-rail')).filter(e=>shown(e)&&!e.closest('.caption-group')).length};
}'''


def main():
    spec = importlib.util.spec_from_file_location('own_layout_helper', Q/'review_short_layout.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    out = Q/'source_layout_v3'
    out.mkdir(exist_ok=True)
    reports = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True, args=['--allow-file-access-from-files'])
        for sid in helper.IDS:
            project = H/'shorts/native-v3'/sid
            lock = read(D/'shorts'/sid/'locked_timing.json')
            cues = lock['captions']
            target = out/(sid+'.html')
            helper.flatten(project, target)
            page = browser.new_page(viewport={'width':1080,'height':1920})
            page.route(re.compile(r'^https?://'), lambda rt: rt.abort())
            page.goto(target.as_uri())
            page.evaluate('document.fonts.ready')
            times = {0, .08, lock['total_s']-1/30}
            for c in cues:
                times.update([c['start_s']-.001,c['start_s']+.001,(c['start_s']+c['end_s'])/2,c['end_s']-.001,c['end_s']+.001])
            ends = sorted({0,lock['total_s'],*[c[k] for c in cues for k in ['start_s','end_s']]})
            times.update((a+b)/2 for a,b in zip(ends,ends[1:]) if b>a)
            states, errors, glyphs = [], [], []
            for t in sorted(x for x in times if 0<=x<lock['total_s']):
                page.evaluate('(t)=>independentSeek(t)',t)
                v = page.evaluate(VISIBLE)
                expected = [i for i,c in enumerate(cues) if c['start_s']<=t<c['end_s']]
                actual = [int(g['id'].split('-')[1]) for g in v['groups']]
                passed = expected==actual and not v['orphan_visible_rails'] and all(g['rail_visible'] and g['text_visible'] and g['rail_count']==g['text_count']==1 for g in v['groups'])
                row={'time_s':t,'expected_active_cues':expected,'actual_active_cues':actual,'passed':passed}
                states.append(row)
                if not passed: errors.append({**row,'visible':v})
            for i,c in enumerate(cues):
                t=(c['start_s']+c['end_s'])/2
                page.evaluate('(t)=>independentSeek(t)',t)
                m=page.evaluate(helper.MEASURE)
                actual=next(x for x in m['rows'] if x['id']==f'cap-{i:03}-text')
                b=actual['glyph_bbox']
                passed=re.sub(r'\s+','',actual['text'])==re.sub(r'\s+','',c['text']) and actual['font_loaded'] and actual['font_px']>=54 and b[0]>=140 and b[1]>=260 and b[2]<=840 and b[3]<=1360
                glyphs.append({'cue':i,'text':actual['text'],'glyph_bbox':b,'font_px':actual['font_px'],'passed':passed})
                if not passed:errors.append({'cue':i,'kind':'changed_caption_text_or_glyph_bounds','actual':actual})
            current=read(project/'input_manifest.json')
            reports.append({'short_id':sid,'version':'native-v3','passed':not errors,'caption_count':len(cues),'tested_instants':len(states),'source_hashes':{f:sha(project/f) for f in ['style.css','compositions/captions.html']},'lock_sha256':sha(D/'shorts'/sid/'locked_timing.json'),'master_audio_sha256':current.get('master_audio_sha256'),'states':states,'changed_caption_glyphs':glyphs,'errors':errors})
            page.close()
        browser.close()
    project=H/'main/jun-v3/project'
    lock=read(D/'locked_timing.json')
    cues=lock['captions']
    windows=read(project/'caption_box_windows.json')
    union=[]
    for c in sorted(cues,key=lambda x:x['start_s']):
        a,b=c['start_s'],c['end_s']
        if union and a<=union[-1][1]+1e-7:union[-1][1]=max(union[-1][1],b)
        else:union.append([a,b])
    windows_match=len(union)==len(windows) and all(abs(x-y)<1e-7 for a,b in zip(union,windows) for x,y in zip(a,b))
    command=read(H/'main/jun-v3/render_command.json')['command']
    filt=command[command.index('-filter_complex')+1]
    gate=filt.split('[clear][3:v]overlay=',1)[1].split('[box]',1)[0]
    actual_intervals=[(int(a),int(b)) for a,b in re.findall(r'between\(n,(\d+),(\d+)\)',gate)]
    expected_intervals=[(math.ceil(a*30-1e-7),math.ceil(b*30-1e-7)-1) for a,b in union]
    frame_mismatch=[]
    for n in range(lock['total_frames']):
        active=any(math.ceil(c['start_s']*30-1e-7)<=n<math.ceil(c['end_s']*30-1e-7) for c in cues)
        box=any(a<=n<=b for a,b in actual_intervals)
        if active!=box:frame_mismatch.append(n)
    native=read(project/'native_captions.json')
    v2native=read(H/'main/jun-v2/project/native_captions.json') if (H/'main/jun-v2/project/native_captions.json').exists() else read(H/'main/jun-v1/project/native_captions.json')
    main_report={'asset_id':'MAIN','revision':'jun-v3','caption_count':len(cues),'merged_box_windows':len(windows),'windows_equal_native_cue_union':windows_match,'encode_frame_gate_matches_union':actual_intervals==expected_intervals,'tested_frame_indices':lock['total_frames'],'source_frame_gate_mismatches':frame_mismatch,'native_caption_payload_unchanged':native==v2native,'native_captions_sha256':sha(project/'native_captions.json'),'source_only_not_encoded':True}
    main_report['passed']=windows_match and actual_intervals==expected_intervals and not frame_mismatch and native==v2native
    result={'status':'passed_source_caption_visibility_pending_encoded' if all(x['passed'] for x in reports) and main_report['passed'] else 'required_source_fix','shorts':reports,'main':main_report,'scope':'v3 자막 그룹·글자/박스 visibility·실제 cue 합집합만 검사. 불변 음성/가격/자료 검수 재사용. 소스 검사이며 실제 MP4 관찰과 구분.','actual_listening':False,'actual_hearing':False,'continuous_playback':False}
    write(Q/'caption_visibility_v3_source_review.json',result)
    print(json.dumps({'status':result['status'],'shorts':[{'id':x['short_id'],'passed':x['passed'],'tested':x['tested_instants'],'cues':x['caption_count']} for x in reports],'main':main_report},ensure_ascii=False))


if __name__=='__main__':
    main()
