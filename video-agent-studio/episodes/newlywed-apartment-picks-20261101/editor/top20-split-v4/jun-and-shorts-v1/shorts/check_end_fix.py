"""QA-requested end-only verification; reuse unchanged native-v1 glyph/price review."""
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build as b
import measure
from playwright.sync_api import sync_playwright

qa=b.EP/'qa/top20-split-v4/jun-and-shorts-v1/issue_JUN-CAPTION-RAIL-01.json'
with sync_playwright()as pw:
    browser=pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',args=['--allow-file-access-from-files'])
    summaries=[]
    for sid in b.IDS:
        old=b.HERE/'native-v1'/sid;new=b.HERE/'native-v2'/sid
        previous=b.read(old/'input_manifest.json');current=b.read(new/'input_manifest.json')
        changed=[]
        for r in current['project_files']:
            oldrow=next(x for x in previous['project_files']if x['path']==r['path'])
            oldcanonical=oldrow.get('before_studio_identity_stamp_sha256',oldrow['sha256'])
            if oldcanonical!=r['sha256']:changed.append(r['path'])
        if changed!=['compositions\\captions.html'] and changed!=['compositions/captions.html']:
            raise ValueError(f'Unexpected change beyond caption rail: {changed}')
        oldcaps=re.sub(rb' data-hf-id="[^"]*"',b'',(old/'compositions/captions.html').read_bytes())
        newcaps=(new/'compositions/captions.html').read_bytes()
        normalized=newcaps.replace(b'id="captions-rail" ',b'')
        normalized=re.sub(rb'tl\.set\("#captions-rail",\{opacity:0\},[0-9.]+\);',b'',normalized)
        if normalized!=oldcaps:raise ValueError('Caption change was more than end rail opacity')
        lock=b.read(b.D/'shorts'/sid/'locked_timing.json');last=max(s['end_s']for s in lock['sentences'])
        page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
        page.goto(measure.flatten(new).as_uri(),wait_until='load');page.evaluate('document.fonts.ready')
        gap=next((a['end_s']+c['start_s'])/2 for a,c in zip(lock['captions'],lock['captions'][1:])if c['start_s']-a['end_s']>.05)
        results=[]
        for name,t,expected in [('intersentence_gap',gap,1),('last_native_word',last-.01,1),('after_last_word',last+.01,0),('last_frame',(lock['total_frames']-1)/30,0)]:
            page.evaluate('(t)=>qaSeek(t)',t)
            opacity=float(page.locator('#captions-rail').evaluate('(e)=>getComputedStyle(e).opacity'))
            captions=page.locator('.caption').evaluate_all('(es)=>es.filter(e=>getComputedStyle(e).display!=="none").map(e=>e.textContent)')
            dest=new/'end_fix_proofs'/f'{name}.png';dest.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(dest))
            results.append({'name':name,'time_s':t,'rail_opacity':opacity,'expected_opacity':expected,'passed':opacity==expected,'visible_captions':captions,'frame':str(dest),'sha256':b.sha(dest)})
        page.close()
        receipt={'short_id':sid,'version':'native-v2','passed':all(x['passed']for x in results),
                 'change':'JUN-CAPTION-RAIL-01: hide caption background at last native utterance end only; intersentence gaps preserved',
                 'latest_user_scope':'end interval only; first-frame rail unchanged per latest explicit request',
                 'changed_render_files':changed,'caption_text_and_timing_unchanged':True,'all_other_render_sources_identical':True,
                 'source_lock_sha256':b.sha(b.D/'shorts'/sid/'locked_timing.json'),'master_audio_sha256':current['master_audio_sha256'],
                 'reused_geometry_review':str(old/'source_measurement_receipt.json'),'independent_QA_issue':str(qa),'independent_QA_issue_sha256':b.sha(qa),
                 'unchanged_layout_and_price_checks_reused':True,'results':results,'actual_listening':False,'continuous_playback':False}
        b.save(new/'end_fix_verification.json',receipt)
        b.save(new/'source_measurement_receipt.json',{'short_id':sid,'passed':receipt['passed'],'safe_area_passed':True,'overlaps':0,
              'unchanged_geometry_and_price_review_reused':True,'previous_receipt':str(old/'source_measurement_receipt.json'),
              'previous_receipt_sha256':b.sha(old/'source_measurement_receipt.json'),'new_end_only_check':str(new/'end_fix_verification.json')})
        summaries.append({'short_id':sid,'passed':receipt['passed'],'last_native_word_end_s':last,'changed_files':changed})
    browser.close()
print(json.dumps(summaries,ensure_ascii=False))
if not all(s['passed']for s in summaries):raise SystemExit(1)
