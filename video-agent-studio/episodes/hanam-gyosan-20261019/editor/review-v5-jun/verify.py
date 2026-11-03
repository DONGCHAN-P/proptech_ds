from pathlib import Path
import json,hashlib,re,subprocess
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v5-jun';V=O/'gyosan_v5_jun.mp4';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
read=lambda f:json.loads(f.read_text(encoding='utf8'))
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def sha(f):return hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
p=read(O/'rendered_project.json');base=read(EP/'outputs/production-v5/rendered_project.json');t=read(O/'technical.json');c=read(O/'caption_cues.json');scenes=read(E/'scene_timing.json');assert sha(V)==t['sha256']
for record in [p,t]:record.update(paid_api_calls_scope='editor_only',editor_paid_api_calls=0,episode_voice_POST_calls=10,episode_voice_credits=3351,episode_cost_authority='root ledger; no generation by editor')
save(O/'rendered_project.json',p);save(O/'timing_locked.json',p);save(O/'technical.json',t);save(O/'technical_v5_jun.json',t)
assert len(p['audio_units'])==len(c)==261
assert ''.join(x['text'] for x in p['audio_units'])==''.join(x['text'] for x in base['audio_units'])
assert [x['text'] for x in c]==[x['text'] for x in read(EP/'outputs/production-v5/caption_cues.json')]
assert all(x['timing_basis'].startswith('Jun original') for x in p['audio_units'])
assert all(x['start_frame']<x['end_frame'] for x in c)
assert len(p['narration_tracks'])==11 and len(scenes)==10
for s in scenes:
 tracks=[x for x in p['narration_tracks'] if x['scene_id']==s['scene_id']];assert tracks[0]['input_sample_start']==0;assert tracks[-1]['input_sample_end']==s['pcm_samples_48000_stereo']
 assert all(a['input_sample_end']==b['input_sample_start'] for a,b in zip(tracks,tracks[1:]));assert sum(x['input_sample_end']-x['input_sample_start'] for x in tracks)==s['pcm_samples_48000_stereo']
source_set={x['source_file'] for x in base['visual_intervals'] if x.get('source_file')};assert all(x['source_file'] in source_set for x in p['visual_intervals'] if x.get('source_file'))
assert p['outro_start']-p['narration_end_frame']==90
save(E/'ending_timing.json',dict(full_PCM_end_frame=p['narration_end_frame'],last_aligned_character_end_frame=p['audio_units'][-1]['end_frame'],outro_start_frame=p['outro_start'],hold_after_full_clip_s=(p['outro_start']-p['narration_end_frame'])/30,hold_after_last_aligned_character_s=(p['outro_start']-p['audio_units'][-1]['end_frame'])/30,no_original_PCM_tail_truncated=True))
recall=[x for x in p['visual_intervals'] if '실거래 중위값이었습니다' in x.get('props',{}).get('phrase_text','')];assert recall and all(x['props']['reviewKind']=='compare' for x in recall)
save(E/'content_verification.json',dict(passed=True,caption_count=261,approved_v5_text_unchanged=True,all_caption_text_identical_to_free_v5=True,Jun_alignment_used_for_all_units=True,full_scene_pcm_samples_preserved=True,source_pngs_reused_without_rerender=True,M009_resale_recall_preserved=True,brand_intro_frames=150,brand_outro_frames=300,hold_after_full_audio_frames=90,editor_api_calls=0,heami_calls=0,actual_listening=False,continuous_playback=False))
D=O/'encoded_proofs';D.mkdir(exist_ok=True);rows=[]
def grab(frame,label,kind):
 f=D/(label+'.png');z=subprocess.run([str(F),'-v','error','-y','-ss',str(frame/30),'-i',str(V),'-frames:v','1',str(f)],capture_output=True);assert not z.returncode,z.stderr
 rows.append(dict(frame_requested=frame,time_s=frame/30,file=str(f),label=label,kind=kind))
for s in scenes:
 grab(s['start_frame']+15,s['scene_id']+'_start','scene_start');grab((s['start_frame']+s['end_frame'])//2,s['scene_id']+'_mid','scene_mid');grab(s['end_frame']-3,s['scene_id']+'_end','scene_end_nearby')
for x in p['visual_intervals']:
 if x['kind']=='chapter':grab(x['start_frame']+45,x['scene_id']+'_chapter','chapter')
for label,n in [('intro_before',p['intro_at']-3),('brand_intro',p['intro_at']+30),('intro_after',p['intro_at']+153),('M009_resale_recall',recall[0]['start_frame']+min(20,recall[0]['duration_frames']-1)),('ending_hold',p['outro_start']-45),('brand_outro',p['outro_start']+30)]:grab(n,label,'targeted')
save(O/'representative_timestamps.json',dict(video=str(V),sha256=sha(V),scope='Targeted scene timings,chapter/title/brand/intro connection and preserved M009 recall; seek correspondence not guaranteed absolute-frame exact',samples=rows))
sheet=Image.new('RGB',(1600,250*((len(rows)+3)//4)),'#ddd');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(rows):
 im=Image.open(r['file']);im.thumbnail((400,225));x=i%4*400;y=i//4*250;sheet.paste(im,(x,y));draw.text((x+4,y+229),r['label'],fill='black')
sheet.save(D/'contactsheet.jpg',quality=91)
inputs=[*E.glob('*.py'),EP/'narration/jun-v5-final/segments.json',EP/'narration/jun-v5-final/timing_proposals.json',EP/'outputs/script-review-v5/script_v5.md',EP/'outputs/production-v5/rendered_project.json',*[Path(s['audio_path']) for s in scenes],*[Path(x) for x in source_set]]
save(O/'input_manifest.json',{str(f.relative_to(R)):sha(f) for f in inputs if f.is_file()})
(E/'placement_guide.md').write_text('# 교산 v5 Jun 편집 검토본\n\n'+f'실제 파일: `{V}`\n\n총 길이 {p["duration_frames"]/30:.3f}초, 1920×1080, 30fps. '+
 '승인 v5 원문과 261개 의미 단위 자막을 유지하고 Jun 원문 문자 정렬로 모든 장면을 재배치했다. 기존 v5 PNG·자료·필지·모션 상태를 재사용하며 신규 이미지 렌더는 0회다.\n\n'+
 '장면 WAV10개 전체 PCM을 보존한다. M000은 실제 문자 정렬 gap 안에서 한 번만 샘플 단위로 분리하고 5초 브랜드 인트로를 삽입했다. 브랜드 아웃트로10초·기존 BGM·마지막 전체 음성 파일 끝에서3초 hold를 유지한다. 자막과 출처는 고정 별도 레이어다. AI 개념 챕터 배경과 원문/지도 구분 표시는 기존 그대로다.\n\n'+
 '|장면|시작(초)|끝(초)|자료·전환|\n|---|---:|---:|---|\n'+''.join(f'|{s["scene_id"]}|{s["start_frame"]/30:.3f}|{s["end_frame"]/30:.3f}|v5 기존 자료·모션, 구절 경계 전환|\n' for s in scenes)+
 '\n실제 청취·발음·자연스러움 및 전편 연속 재생은 별도 미검수다. 정지 프레임 seek의 정확 절대프레임 대응은 보장하지 않는다. 편집 담당은 업로드하지 않으며 사용자 지시에 따른 공개 업로드는 총괄 담당이다. 재현 명령은 `production_job.json`의 로컬 runner 단계(build_timeline.py → assemble.py → verify.py)다.\n',encoding='utf8')
save(E/'handoff.json',dict(status='render_complete_independent_qa_pending',video=str(V),sha256=sha(V),duration_s=p['duration_frames']/30,technical=str(O/'technical.json'),timing=str(E/'timing_verification.json'),content_verification=str(E/'content_verification.json'),source_manifest=str(O/'input_manifest.json'),representatives=str(O/'representative_timestamps.json'),alignment=str(EP/'narration/jun-v5-final/segments.json'),placement_guide=str(E/'placement_guide.md'),new_voice='Jun:10 complete scene WAVs with original character alignment',caption_count=261,new_png_renders=0,editor_paid_api_calls=0,episode_voice_POST_calls=10,episode_voice_credits=3351,episode_cost_authority='root ledger',heami_calls=0,actual_listening=False,continuous_playback=False,limitations=['청취·발음·자연스러움 및 전편 연속 재생 미검수','정지 프레임 seek 절대프레임 대응 미보장','v5 불변 자료·위치·수치 검수 범위 계승'],next_owner='independent QA / director'))
h=read(E/'handoff.json');h.update(subtitles=str(O/'gyosan_v5_jun.srt'),caption_cues=str(O/'caption_cues.json'),source_credits='Same verified v5 cached PNG source layers,below persistent captions; no source/map/chart content changed',ending_timing=str(E/'ending_timing.json'));save(E/'handoff.json',h)
print(json.dumps(dict(sha256=sha(V),duration_s=p['duration_frames']/30,samples=len(rows))))
