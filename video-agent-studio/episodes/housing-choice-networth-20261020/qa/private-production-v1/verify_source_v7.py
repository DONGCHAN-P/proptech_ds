"""Independent read-only verification of frozen caption-v7 source inputs."""
import hashlib, html, json, re
from pathlib import Path
from datetime import datetime, timezone

EP = Path(__file__).resolve().parents[2]
QA = EP / 'qa/private-production-v1'
OUT = EP / 'outputs/private-production-v3'
OLD = EP / 'outputs/private-production-v2'
ED = EP / 'editor/private-production-v3'
EXPECTED = 'a97d59fbe5d9dccb4b4b936dc8a839c4a02d754479a34bab4220760925bd40f7'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()
def pin(p): return {'path': p.relative_to(EP).as_posix(), 'sha256': sha(p)}
def compact(s): return re.sub(r'\s+', '', s)
def attr(s, key): return re.search(r'\b'+re.escape(key)+r'="([^"]*)"', s).group(1)
nodes = re.compile(r'<p\b(?=[^>]*\bclass="clip cue")[^>]*>.*?</p>', re.S)
def without_captions(s):
    found=list(nodes.finditer(s)); assert found
    return s[:found[0].start()]+'__FROZEN_CAPTION_BLOCK__'+s[found[-1].end():]

timing_path=EP/'narration/free-tts-v1/caption-v7/final_timing.json'
assert sha(timing_path)==EXPECTED
timing=read(timing_path)
assert sha(EP/'outputs/script-final-v6/script_v6.md')==timing['script_sha256']
packet=read(OUT/'preview_captions/handoff.json')
cli=read(ED/'checks/summary.json'); bbox=read(OUT/'preview/bbox_report.json')
mix=read(ED/'mix_receipt.json'); reuse=read(ED/'visual_audio_reuse_manifest.json')
assert packet['cue_count']==206 and packet['caption_timing_sha256']==EXPECTED
bindings={
 'CLI_summary_sha256':ED/'checks/summary.json',
 'BBox_report_sha256':OUT/'preview/bbox_report.json',
 'mix_receipt_sha256':ED/'mix_receipt.json',
 'narration_handoff_sha256':EP/'narration/free-tts-v1/caption-v7/handoff.json',
 'caption_timing_sha256':timing_path,
 'authorization_sha256':EP/'director/two-episode-production-v1/render_authorization_caption_v7.json',
 'visual_audio_reuse_manifest_sha256':ED/'visual_audio_reuse_manifest.json'}
for k,p in bindings.items(): assert sha(p)==packet['input_revisions'][k], (k,'stale packet')
assert bbox['errors']==bbox['findings']==bbox['external_requests']==[]
assert len(bbox['checked_chapters'])==10 and len(cli['chapters'])==10
rows=[]; all_cues=[]; verified_assets=0; bbox_cues=0
for ch in timing['chapters']:
    n=int(ch['chapter']); base=OUT/f'ch{n:02d}'; oldbase=OLD/f'ch{n:02d}'
    hp=base/'index.html'; tp=base/'timing.json'; h=sha(hp); t=read(tp)
    cr=next(x for x in cli['chapters'] if x['chapter']==n)
    br=next(x for x in bbox['checked_chapters'] if x['chapter']==n)
    mr=next(x for x in mix['chapters'] if x['chapter']==n)
    rr=next(x for x in reuse['chapters'] if x['chapter']==n)
    assert h==cr['html_sha256']==br['html_sha256']==mr['html_sha256']==rr['html_sha256']
    assert sha(tp)==br['timing_sha256']
    assert cr['returncode']==0 and cr['ok'] is True
    assert all(x['errorCount']==0 for x in cr['passes'].values())
    assert all(f['status']=='loaded' for f in br['fonts']) and br['paused'] is True
    source=hp.read_text(encoding='utf-8'); prior=(oldbase/'index.html').read_text(encoding='utf-8')
    assert sha(oldbase/'index.html')==rr['prior_HTML_sha256']
    assert without_captions(source)==without_captions(prior)
    normalized_sha=hashlib.sha256(without_captions(source).encode()).hexdigest()
    assert normalized_sha==rr['non_caption_HTML_normalized_sha256']
    ot=read(oldbase/'timing.json')
    assert {k:v for k,v in t.items() if k not in ('cues','caption_revision','visual_timing_basis')}=={k:v for k,v in ot.items() if k!='cues'}
    assert sha(oldbase/'anchor_audit.json')==rr['anchor_audit_sha256']==sha(base/'anchor_audit.json')
    for name, expected in rr['all_asset_sha256'].items():
        assert sha(base/'assets'/name)==sha(oldbase/'assets'/name)==expected, (n,name)
        verified_assets+=1
    assert sha(base/'assets/narration.wav')==mr['voice_sha256']==ch['audio_sha256']
    assert sha(base/'assets/music-bed.wav')==mr['bed_sha256']
    ns=nodes.findall(source); assert len(ns)==len(t['cues'])==len(ch['cues'])
    for i,(node,c,orig) in enumerate(zip(ns,t['cues'],ch['cues'])):
        assert {k:v for k,v in c.items() if k not in ('paragraph','paragraph_source')}=={k:v for k,v in orig.items() if k!='paragraph'}
        assert c['paragraph_source']==orig['paragraph']
        displayed=html.unescape(re.sub(r'<[^>]*>','',node))
        assert displayed=='\n'.join(c['display_lines'])
        assert compact(displayed)==compact(c['text'])
        assert abs(float(attr(node,'data-start'))-c['start_s'])<1e-8
        body_end=ch['last_speech_end_s'] if n==10 else ch['total_seconds']
        expected_end=min(c['end_s']+.08,t['cues'][i+1]['start_s'] if i+1<len(ns) else ch['total_seconds'],body_end)
        assert abs(float(attr(node,'data-duration'))-(expected_end-c['start_s']))<0.000001
        midpoint=(c['start_s']+c['end_s'])/2
        assert any(abs(s['time_s']-midpoint)<0.000002 for s in br['samples']), (n,c['id'],'missing BBox cue midpoint')
        bbox_cues+=1; all_cues.append((n,c))
    rows.append({'chapter':n,'html_sha256':h,'timing_sha256':sha(tp),'cue_count':len(ns),
      'noncaption_HTML_scenes_T_audio_assets_exact':True,'CLI_pass':True,
      'BBox_all_cue_midpoints_current':True,'asset_file_count':len(rr['all_asset_sha256'])})

assert len(all_cues)==206
assert sha(OUT/'assembly_edl.json')==sha(OLD/'assembly_edl.json')==packet['EDL_sha256']
assert sha(OUT/'captions_measured.srt')==packet['SRT_sha256']
edl=read(OUT/'assembly_edl.json')
blocks=(OUT/'captions_measured.srt').read_text(encoding='utf-8-sig').strip().split('\n\n')
assert len(blocks)==206
def seconds(x):
    h,m,s,ms=map(int,re.split('[:,]',x));return h*3600+m*60+s+ms/1000
max_srt_error=0
for (n,c),block in zip(all_cues,blocks):
    lines=block.splitlines(); start,end=lines[1].split(' --> ')
    assert lines[2:]==c['display_lines']
    offset=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==n and o['local_start_s']<=c['start_s']<o['local_end_s'])
    err=max(abs(seconds(start)-(c['start_s']+offset)),abs(seconds(end)-(c['end_s']+offset)))
    assert err<=.000501; max_srt_error=max(max_srt_error,err)
assert len(packet['frames'])==120 and len(set(x['group_id'] for x in packet['frames']))==50
for f in packet['frames']:
    assert sha(OUT/f['file'])==f['sha256']
    assert f['html_sha256']==rows[f['chapter']-1]['html_sha256']
    c=next(c for n,c in all_cues if c['id']==f['cue_id'])
    assert f['display_lines']==c['display_lines'] and f['text']==c['text']
    assert c['start_s']<=f['time_s']<=c['end_s']
for contact in packet['caption_crop_contacts']: assert sha(OUT/contact['file'])==contact['sha256']
for p in [EP/'director/two-episode-production-v1/producer_caption_v7_review.json',EP/'director/two-episode-production-v1/edl_review_v7.json']:
    assert read(p)['timing_sha256']==EXPECTED
evidence=[pin(p) for p in list(bindings.values())+[OUT/'preview_captions/handoff.json',ED/'handoff.json',ED/'caption_renderer_contract.json',OUT/'assembly_edl.json',OUT/'captions_measured.srt',QA/'caption-v7/cue_review.json',QA/'caption-v7/audit-a97d59fbe5d9/timing_text_audit.json',EP/'director/two-episode-production-v1/producer_caption_v7_review.json',EP/'director/two-episode-production-v1/edl_review_v7.json']]
report={'status':'pass_independent_source_pins_conservation_and_invariance','checked_at':datetime.now(timezone.utc).isoformat(),
 'script_sha256':timing['script_sha256'],'caption_timing_sha256':EXPECTED,'chapters':rows,
 'checked_cues':206,'BBox_cue_midpoints_verified':bbox_cues,'asset_files_rehashed_old_and_current':verified_assets,
 'PNG_files_SHA_verified':120,'changed_groups':50,'contact_files_SHA_verified':len(packet['caption_crop_contacts']),
 'SRT_cues':len(blocks),'max_SRT_rounding_error_s':max_srt_error,'EDL_byte_identical_v2':True,
 'producer_BBox_basis':'Current 206-cue midpoint and boundary samples, actual loaded font/Range glyph checks; receipt reused, not independently rerun',
 'source_HTML_native_end_hold':'Existing <=80ms readability hold, capped at next cue and last speech; SRT retains native end',
 'CLI_note':'Current HTML pins match editor CLI receipt; nonfatal lint/history warnings preserved. Actual all-cue glyph evidence comes from current BBox.',
 'evidence':evidence,'required_issues':[],'critical_issues':[],
 'actual_images_visual_review':'Recorded separately after opening images; hashing is not visual inspection',
 'actual_listening':False,'continuous_playback':False,'ASR_rerun':False,'final_media_approved':False}
dest=QA/'caption-v7/source_precheck.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('chapters','evidence')},ensure_ascii=False))
