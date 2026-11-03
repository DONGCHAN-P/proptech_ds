"""Check only the two note suffix removals; reuse unchanged v3 cue/audio/fact QA."""
import html
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_native_v4 as b
import measure
from playwright.sync_api import sync_playwright

SUFFIXES=[' · 현재 매물 가격 아님',' · 현재 매물 아님']


def verify(sid,browser):
    before=b.HERE/'native-v3'/sid;project=b.HERE/'native-v4'/sid
    previous=b.read(before/'input_manifest.json');current=b.read(project/'input_manifest.json')
    changed=[]
    for r in current['project_files']:
        old=next(x for x in previous['project_files']if x['path']==r['path'])
        if old['sha256']==r['sha256']:continue
        rel=r['path'].replace('\\','/')
        if not rel.startswith('compositions/scene-'):raise ValueError('Unexpected non-note change: '+rel)
        expected=(before/rel).read_text(encoding='utf-8')
        for suffix in SUFFIXES:expected=expected.replace(suffix,'')
        actual=(project/rel).read_text(encoding='utf-8')
        if actual!=expected:raise ValueError('Unexpected scene edit: '+rel)
        changed.append(rel)
    if previous['lock_sha256']!=current['lock_sha256']or previous['master_audio_sha256']!=current['master_audio_sha256']:
        raise ValueError('Native lock/audio changed')
    for file in (project/'compositions').glob('*.html'):
        if any(s in file.read_text(encoding='utf-8')for s in SUFFIXES):raise ValueError('Forbidden suffix remains: '+str(file))
    reuse=b.read(before/'caption_visibility_checks.json')
    if not reuse['passed']:raise ValueError('v3 cue visibility QA not passed')
    b.save(project/'caption_visibility_checks.json',{**reuse,'version':'native-v4','reused_caption_visibility_from':str(before/'caption_visibility_checks.json'),'reused_sha256':b.sha(before/'caption_visibility_checks.json'),'v4_change':'two screen note suffixes only; caption HTML/CSS and native timing hashes unchanged'})
    page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
    page.goto(measure.flatten(project).as_uri(),wait_until='load');page.evaluate('document.fonts.ready')
    notes=[];proofs=[]
    for sc in b.read(project/'storyboard.json')['scenes']:
        t=(sc['start_s']+sc['end_s'])/2;page.evaluate('(t)=>qaSeek(t)',t)
        rows=[{**x,'time_s':t}for x in page.evaluate(measure.MEASURE)if x['id'].endswith('-note')]
        notes.extend(rows)
        for row in rows:
            if row['text']not in ['10월은 조회일까지 신고분','10월 계약은 조회일까지 신고분']:raise ValueError('Incorrect retained note: '+row['text'])
        if sc['composition_id']in ['scene-00','scene-03']:
            path=project/'note_cleanup_proofs'/f'{sc["composition_id"]}.png';path.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(path));proofs.append({'time_s':t,'frame':str(path),'sha256':b.sha(path)})
    page.close()
    b.save(project/'note_glyph_bounds.json',{'profile':'youtube_portrait_full_frame_v2','safe_rect':[140,260,840,1360],'elements':notes})
    p=subprocess.run([str(b.ROOT/'tools/python311/python.exe'),'-X','utf8',str(b.ROOT/'analysis/validate_vertical_layout.py'),str(project/'note_glyph_bounds.json'),'--profile','youtube_portrait_full_frame_v2','--report',str(project/'note_safe_area_report.json')],capture_output=True,creationflags=b.NO_WINDOW)
    passed=p.returncode==0 and len(notes)==len(changed)
    receipt={'short_id':sid,'version':'native-v4','passed':passed,'changed_render_files':changed,'screen_note_suffixes_remaining':0,
             'only_approved_note_suffixes_removed':True,'all_other_render_file_hashes_identical_to_v3':True,
             'caption_group_html_css_and_cue_timing_unchanged':True,'reused_v3_caption_visibility_check':str(before/'caption_visibility_checks.json'),
             'lock_sha256':current['lock_sha256'],'master_audio_sha256':current['master_audio_sha256'],'notes':notes,'proofs':proofs,
             'actual_listening':False,'continuous_playback':False}
    b.save(project/'note_cleanup_verification.json',receipt)
    b.save(project/'source_measurement_receipt.json',{'short_id':sid,'passed':passed,'safe_area_passed':p.returncode==0,
           'note_cleanup_verification':str(project/'note_cleanup_verification.json'),'caption_and_price_geometry_review_reused':True,
           'previous_receipt':str(before/'source_measurement_receipt.json'),'previous_receipt_sha256':b.sha(before/'source_measurement_receipt.json')})
    return {k:receipt[k]for k in ['short_id','passed','screen_note_suffixes_remaining','changed_render_files']}


if __name__=='__main__':
    with sync_playwright()as pw:
        browser=pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',args=['--allow-file-access-from-files'])
        results=[verify(sid,browser)for sid in b.IDS];browser.close()
    print(json.dumps(results,ensure_ascii=False),flush=True)
    if not all(r['passed']for r in results):raise SystemExit(1)
