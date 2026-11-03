"""Verify cue-owned caption backgrounds, preserving every v2 fact/timing/audio input."""
import json
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_native_v3 as b
import measure
from playwright.sync_api import sync_playwright

VISIBLE = r"""() => {
 const visible=(e)=>{for(let a=e;a;a=a.parentElement){const s=getComputedStyle(a);if(s.display==='none'||s.visibility==='hidden'||+s.opacity<.01)return false}return true};
 return [...document.querySelectorAll('.caption-group')].filter(visible).map(g=>({id:g.id,text:g.querySelector('.caption').textContent,
   text_visible:visible(g.querySelector('.caption')),background_visible:visible(g.querySelector('.caption-rail'))}));
}"""


def check(sid,browser):
    old=b.HERE/'native-v2'/sid;project=b.HERE/'native-v3'/sid
    before=b.read(old/'input_manifest.json');now=b.read(project/'input_manifest.json')
    changed=[]
    for r in now['project_files']:
        earlier=next(x for x in before['project_files']if x['path']==r['path'])
        if r['sha256']!=earlier['sha256']:changed.append(r['path'].replace('\\','/'))
    for path in changed:
        if path in ['compositions/captions.html','style.css']:continue
        if re.fullmatch(r'compositions/scene-\d+\.html',path):
            original=(old/path).read_text(encoding='utf-8')
            expected=original.replace(' · 현재 매물 가격 아님','').replace(' · 현재 매물 아님','')
            if (project/path).read_text(encoding='utf-8')==expected:continue
        raise ValueError(f'Unapproved render change: {path}')
    if now['lock_sha256']!=before['lock_sha256']or now['master_audio_sha256']!=before['master_audio_sha256']:
        raise ValueError('Audio/lock changed')
    css=(project/'style.css').read_bytes().replace(b'.caption-group{position:absolute;inset:0}\r\n',b'').replace(b'.caption-group{position:absolute;inset:0}\n',b'')
    import hashlib
    if hashlib.sha256(css).hexdigest()!=next(x['sha256']for x in before['project_files']if x['path']=='style.css'):
        raise ValueError('CSS geometry changed beyond new cue-group wrapper')
    lock=b.read(b.D/'shorts'/sid/'locked_timing.json');cues=lock['captions']
    page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
    page.goto(measure.flatten(project).as_uri(),wait_until='load');page.evaluate('document.fonts.ready')
    representative=[.08,(cues[0]['start_s']+cues[0]['end_s'])/2,(lock['total_frames']-1)/30]
    representative += [s['start_s']-.1 for s in lock['scenes'][1:]]
    if sid=='SHORT01-PROMO':representative += [4.18,18.68,31.02]
    if sid=='SHORT02-R20-R16':representative += [14.68]
    times=set(representative)
    for cue in cues:times.update([cue['start_s']+.001,cue['end_s']-.001,cue['end_s']+.001,(cue['start_s']+cue['end_s'])/2])
    for left,right in zip(cues,cues[1:]):
        if right['start_s']>left['end_s']+.002:times.add((right['start_s']+left['end_s'])/2)
    results=[]
    norm=lambda s:re.sub(r'\s','',s)
    for t in sorted(times):
        if not 0<=t<lock['total_s']:continue
        page.evaluate('(t)=>qaSeek(t)',t)
        actual=page.evaluate(VISIBLE)
        expected=[(i,c)for i,c in enumerate(cues)if c['start_s']<=t<c['end_s']]
        passed=len(actual)==len(expected)and all(a['id']==f'cap-{i:03d}'and norm(a['text'])==norm(c['text'])and a['background_visible']and a['text_visible']for a,(i,c)in zip(actual,expected))
        results.append({'time_s':t,'expected_active_cues':[i for i,c in expected],'visible_groups':actual,'passed':passed})
    elements=[]
    for cue in cues:
        t=(cue['start_s']+cue['end_s'])/2;page.evaluate('(t)=>qaSeek(t)',t)
        elements.extend([{**r,'time_s':t}for r in page.evaluate(measure.MEASURE)if r['kind']=='caption'])
    bounds={'profile':'youtube_portrait_full_frame_v2','safe_rect':[140,260,840,1360],'scope':'Changed caption groups only; all other render source SHA identical to v2','elements':elements}
    b.save(project/'caption_glyph_bounds.json',bounds)
    proc=subprocess.run([str(b.ROOT/'tools/python311/python.exe'),'-X','utf8',str(b.ROOT/'analysis/validate_vertical_layout.py'),str(project/'caption_glyph_bounds.json'),'--profile','youtube_portrait_full_frame_v2','--report',str(project/'caption_safe_area_report.json')],capture_output=True,creationflags=b.NO_WINDOW)
    proofs=[]
    for i,t in enumerate(sorted(set(representative))):
        page.evaluate('(t)=>qaSeek(t)',t)
        dest=project/'caption_visibility_proofs'/f'case-{i:02d}-{t:.3f}s.png';dest.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(dest))
        proofs.append({'time_s':t,'frame':str(dest),'sha256':b.sha(dest)})
    page.close()
    passed=all(r['passed']for r in results)and proc.returncode==0 and len(elements)==len(cues)
    record={'short_id':sid,'version':'native-v3','passed':passed,'caption_cues':len(cues),'tested_instants':len(results),
            'changed_render_files':changed,'all_other_render_sources_identical_to_v2':True,
            'screen_note_cleanup':'Removed current-listing negation suffix only; transaction cutoff wording retained; approved before first v3 render',
            'audio_lock_cue_text_and_timing_unchanged':True,'master_audio_sha256':now['master_audio_sha256'],'lock_sha256':now['lock_sha256'],
            'policy':'Background and text share one timed cue group; no standalone persistent caption rail. No group outside active cue window.',
            'representative_times_s':sorted(set(representative)),'caption_glyphs_measured':len(elements),'caption_safe_area_passed':proc.returncode==0,
            'results':results,'proofs':proofs,'actual_listening':False,'continuous_playback':False}
    b.save(project/'caption_visibility_checks.json',record)
    b.save(project/'source_measurement_receipt.json',{'short_id':sid,'passed':passed,'safe_area_passed':proc.returncode==0,
           'caption_visibility_check':str(project/'caption_visibility_checks.json'),'changed_caption_groups_measured':len(elements),
           'unchanged_geometry_and_price_review_reused':True,'previous_receipt':str(old/'source_measurement_receipt.json'),
           'previous_receipt_sha256':b.sha(old/'source_measurement_receipt.json')})
    return {k:record[k]for k in ['short_id','passed','caption_cues','tested_instants','caption_glyphs_measured','changed_render_files']}


if __name__=='__main__':
    with sync_playwright()as pw:
        browser=pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',args=['--allow-file-access-from-files'])
        result=[check(sid,browser)for sid in b.IDS];browser.close()
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if not all(r['passed']for r in result):raise SystemExit(1)
