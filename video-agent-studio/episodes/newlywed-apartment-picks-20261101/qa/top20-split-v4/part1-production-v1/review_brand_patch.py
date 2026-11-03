"""음성 불변을 증명한 뒤 브랜드 영상 참조 변경분만 독립 재검수한다."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

Q=Path(__file__).resolve().parent
E=Q.parents[2];R=E.parents[2]
D=E/'director/top20-split-v4/part1-production-v1'
P=E/'editor/top20-split-v4/part1-production-v1/final-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def preserve(name):
    src=Q/(name+'.json');dst=Q/(name+'_before_brand_patch.json')
    if not dst.exists():dst.write_bytes(src.read_bytes())
    return read(dst)

initial=D/'locked_timing_initial_audio_as_visual.json'
current=D/'locked_timing.json'
old=read(initial);new=read(current)
checks=[]
def check(name,value,evidence=None):
    checks.append(dict(check=name,passed=bool(value),evidence=evidence))
check('initial_lock_hash',sha(initial)=='a4a9efe64e87a329917b5b1dc3d6d7c4285f5c16ff6b05555b4a357dc2ceecf5')
check('current_lock_hash',sha(current)=='eb9f879717a1ddbcef4e3d108f0629b93c39e7eca53a4f67df35d146482f2a72')
check('all_non_binding_fields_exact', {k:v for k,v in old.items() if k not in ['locked_at','brand_inserts']}=={k:v for k,v in new.items() if k not in ['locked_at','brand_inserts']})
for a,b in zip(old['brand_inserts'],new['brand_inserts']):
    check('brand_timing_identical_'+a['kind'],{k:v for k,v in a.items() if k not in ['source_file','sha256']}=={k:v for k,v in b.items() if k not in ['source_file','sha256','audio_source_file','audio_source_sha256']})
    check('audio_source_preserved_'+a['kind'],b['audio_source_file']==a['source_file'] and b['audio_source_sha256']==a['sha256'] and sha(Path(b['audio_source_file']))==a['sha256'])
check('actual_narration_WAV_hash_unchanged',sha(R/new['audio_path'])==old['audio_sha256']==new['audio_sha256'])
check('PART1_scope_unchanged',len(new['scenes'])==12 and sum(len(s['sentences']) for s in new['scenes'])==85 and len(new['captions'])==176 and all(s['part']==1 for s in new['scenes']))

old_report=preserve('provisional_source_review')
old_evidence=preserve('source_review_evidence')
old_audio=preserve('audio_script_review')
old_asr=preserve('ASR_support_review')
check('other_HTML_CSS_source_files_unchanged',all(sha(Path(p))==h for p,h in old_report['source_hashes'].items() if Path(p).name!='input_manifest.json'))
manifest=read(P/'input_manifest.json')
check('current_manifest_timing_hash',manifest['timing_sha256']==sha(current))
old_assets={a['dest']:a for a in old_evidence['asset_hash_checks'] if a['dest']}
updated=[]
for a in manifest['assets']:
    src=Path(a['source']);dest=P/a['dest'] if 'dest' in a else None
    matched=src.is_file() and sha(src)==a['sha256'] and (dest is None or dest.is_file() and sha(dest)==a['sha256'])
    check('manifest_asset_'+a.get('dest',src.name),matched)
    if dest and dest.name not in ['brand_intro.mp4','brand_outro.mp4']:
        previous=old_assets[str(dest)]
        check('unchanged_non_brand_asset_'+dest.name,previous['sha256']==a['sha256'] and previous['source']==str(src))
    updated.append(dict(source=str(src),dest=str(dest) if dest else None,sha256=a['sha256'],matched=matched))

probe=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ffmpeg=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
brand=[]
for b in new['brand_inserts']:
    p=P/('assets/brand_'+b['kind']+'.mp4')
    pr=subprocess.run([str(probe),'-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    pj=json.loads(pr.stdout) if pr.returncode==0 else {}
    save(Q/('brand_'+b['kind']+'_actual_video_probe.json'),pj)
    vs=[s for s in pj.get('streams',[]) if s.get('codec_type')=='video']
    dur=float(pj.get('format',{}).get('duration',0))
    check('actual_video_stream_'+b['kind'],pr.returncode==0 and len(vs)==1 and vs[0]['width']==1920 and vs[0]['height']==1080 and abs(dur-b['duration_s'])<=1/30 and sha(p)==sha(Path(b['source_file']))==b['sha256'],dict(duration_s=dur,video_streams=len(vs),codec=vs[0].get('codec_name') if vs else None))
    dc=subprocess.run([str(ffmpeg),'-v','error','-xerror','-i',str(p),'-f','null','-'],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (Q/('brand_'+b['kind']+'_actual_video_decode.txt')).write_text(dc.stderr,encoding='utf-8')
    check('strict_actual_video_decode_'+b['kind'],dc.returncode==0,dict(exit_code=dc.returncode))
    brand.append(dict(kind=b['kind'],path=str(p),sha256=sha(p),container=pj.get('format',{}).get('format_name'),codec=vs[0].get('codec_name') if vs else None,dimensions=[vs[0]['width'],vs[0]['height']] if vs else None,duration_s=dur,strict_decode_exit_code=dc.returncode,pixels='pending_actual_final_MP4_encoded_frames'))
html=(P/'index.html').read_text(encoding='utf-8')
check('brand_video_muted_preserved',all('muted' in html[html.index('id="brand-'+k+'"'):html.index('>',html.index('id="brand-'+k+'"'))] for k in ['intro','outro']))
check('original_ASR_evidence_hashes_unchanged',all(sha(Path(a['file']))==a['sha256'] for a in old_asr['evidence']))
check('prior_ASR_targets_initial_audio_lock',all(a['timing_hash_matches'] and a['actual_clip_hash_matches'] for a in old_asr['evidence']))
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]

cross=dict(previous_lock_sha256=sha(initial),current_lock_sha256=sha(current),identical_fields='all fields other than locked_at and brand visual binding paths/hash plus explicit audio-source fields',scenes=12,sentences=85,words=1277,captions=176,audio_sha256=new['audio_sha256'],ASR_reused_without_rerun=True,reason='ASR 대상인 장면/문장/시간/실제 WAV 바이트가 모두 동일. lock 해시는 영상 바인딩 수정으로만 변경됨.',actual_listening=False)
addendum=dict(task_id='PART1-brand-binding-delta-independent-QA',generated_at=datetime.now(timezone.utc).isoformat(),status='source_patch_verified_pending_encoded_frames',critical_open_count=0,required_open_count=0,cross_revision=cross,checks=checks,brand_videos=brand,ASR_new_execution=False,voice_generated=False,actual_listening=False,continuous_playback=False,source_frames_viewed=0,final_MP4='pending part1_free_v4.mp4',patch_receipt_sha256=sha(D/'brand_binding_patch.json'))
save(Q/'brand_binding_patch_review.json',addendum)

asr=dict(old_asr);asr['cross_revision_reuse']=cross
save(Q/'ASR_support_review.json',asr)
audio=dict(old_audio)
audio['original_checked_revision']=old_audio['checked_revision']
audio['checked_revision']=dict(old_audio['checked_revision'],locked_timing_sha256=sha(current))
audio['cross_revision_reuse']=cross
for a in audio['inputs']:
    if Path(a['path']).name=='locked_timing.json':a['path']=str(initial)
audio['inputs'].append(dict(path=str(current),sha256=sha(current),bytes=current.stat().st_size))
audio['ASR_support']['sha256']=sha(Q/'ASR_support_review.json')
audio['brand_binding_patch_review']=dict(path=str(Q/'brand_binding_patch_review.json'),sha256=sha(Q/'brand_binding_patch_review.json'))
save(Q/'audio_script_review.json',audio)

evidence=dict(old_evidence);evidence['asset_hash_checks']=updated;evidence['brand_evidence']=brand
for c in evidence['checks']:
    if c['check'].startswith('brand_video_container_'):
        c['passed']=True;c['evidence']='actual MP4 video stream and strict decode confirmed in brand_binding_patch_review.json'
evidence['delta_checks']=checks
save(Q/'source_review_evidence.json',evidence)
report=dict(old_report)
report.update(generated_at=datetime.now(timezone.utc).isoformat(),status='source_checks_passed_pending_encoded_review',required_open_count=0,required_issues=[],resolved_source_issues=['QA-PART1-SOURCE-001','QA-PART1-SOURCE-002'],failed_checks=[],evidence_sha256=sha(Q/'source_review_evidence.json'),cross_revision_reuse=cross,delta_review=str(Q/'brand_binding_patch_review.json'),next_owner='director: render part1_free_v4.mp4 and send actual encoded frames; QA: independent final_review.json')
report['source_hashes'][str(P/'input_manifest.json')]=sha(P/'input_manifest.json')
save(Q/'provisional_source_review.json',report)
findings=read(Q/'findings.json')
for i in findings:
    if i['issue_id']=='QA-PART1-SOURCE-001':
        i['status']='resolved_source_verified_pending_encoded'
        i['checked_revision']=dict(revision='final-v3 brand patched; output target v4',locked_timing_sha256=sha(current),input_manifest_sha256=sha(P/'input_manifest.json'))
        i['current_evidence']=brand
        i['rechecked_latest_version']='실제 영상 스트림1920x1080 및5s/10s 길이·전체 strict decode·승인 원본 해시·muted 연결 확인. 최종 MP4 브랜드 픽셀은 대기.'
        save(Q/('issue_'+i['issue_id']+'.json'),i)
save(Q/'findings.json',findings)
h=read(Q/'handoff.json');h.update(status=report['status'],required_open_count=0,critical_open_count=0,open_issue_ids=[],input_versions=audio['checked_revision'],cross_revision_reuse=cross,next_owner=report['next_owner'])
h['outputs']=list(dict.fromkeys(h['outputs']+[str(Q/'brand_binding_patch_review.json')]))
h['output_hashes']={Path(p).name:sha(Path(p)) for p in h['outputs']}
save(Q/'handoff.json',h)
print(json.dumps(dict(status=addendum['status'],required=0,critical=0,delta_checks=len(checks),brand=brand,ASR_reexecuted=False),ensure_ascii=False))
