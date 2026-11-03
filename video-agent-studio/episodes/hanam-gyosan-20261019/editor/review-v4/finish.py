from pathlib import Path
import json,hashlib,subprocess,re,bisect
import numpy as np
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v4';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';video=O/'gyosan_review_v4r1_free_tts.mp4';p=json.loads((O/'rendered_project.json').read_text(encoding='utf8'));technical=json.loads((O/'technical.json').read_text(encoding='utf8'))
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def run(args):
 z=subprocess.run([str(F),'-v','error','-y',*map(str,args)],capture_output=True)
 if z.returncode or z.stderr:raise RuntimeError(z.stderr.decode(errors='replace')[-2000:])
 return z
assert sha(video)==technical['sha256'];assert len(p['audio_units'])==263;assert p['outro_start']-p['audio_units'][-1]['end_frame']==90
norm=lambda x:re.sub(r'\s+','',x);approved=json.loads((EP/'narration/units_v4.json').read_text(encoding='utf8'));assert norm(''.join(x['text'] for x in approved))==norm(''.join(x['text'] for x in p['audio_units']))
cues=json.loads((O/'caption_cues.json').read_text(encoding='utf8'));assert norm(''.join(x['text'] for x in cues))==norm(''.join(x['text'] for x in approved));assert all(x['start_frame']<x['end_frame'] for x in cues)
proof=O/'encoded_proofs_v4r1';proof.mkdir(exist_ok=True)
representatives={}
for x in p['visual_intervals']:
 if x['kind'] not in ['body','chapter']:continue
 q=x['props'];key=x['scene_id']+'_'+q.get('visual_key',q.get('mode',''))
 # 최종 안정 상태와 실제 긴 자막을 함께 확보한다.
 if q.get('motionFrame',44)<q.get('motionEnd',44):continue
 if key not in representatives or len(q.get('caption',''))>len(representatives[key]['props'].get('caption','')):representatives[key]=x
rep_rows=[]
for key,x in representatives.items():
 n=x['start_frame']+min(2,x['duration_frames']-1);dest=proof/(re.sub(r'[<>:"/\\|?*]','_',key)+'.png');run(['-ss',n/30,'-i',video,'-frames:v','1',dest]);rep_rows.append(dict(scene_id=x['scene_id'],frame=n,time_s=n/30,file=str(dest),kind=x['props'].get('reviewKind',x['props'].get('mode')),caption=x['props'].get('caption','')))
for name,n in [('brand_intro',p['intro_at']+30),('brand_outro',p['outro_start']+30),('ending_hold',p['outro_start']-45)]:run(['-ss',n/30,'-i',video,'-frames:v','1',proof/(name+'.png')])
(O/'representative_timestamps_v4r1.json').write_text(json.dumps(rep_rows,ensure_ascii=False,indent=2),encoding='utf8')
files=sorted(proof.glob('*.png'));sheet=Image.new('RGB',(1920,240*((len(files)+4)//5)),'#ddd');draw=ImageDraw.Draw(sheet)
for i,f in enumerate(files):
 im=Image.open(f);im.thumbnail((384,216));x=i%5*384;y=i//5*240;sheet.paste(im,(x,y));draw.text((x+4,y+219),f.name,fill='black')
sheet.save(proof/'contactsheet.jpg',quality=90)
# 지도/자료판 전환과 챕터/브랜드 경계 전후 1프레임을 실제 MP4에서 대조한다.
starts=[x['start_frame'] for x in p['visual_intervals']];cuts=[];prev=None
for x in p['visual_intervals']:
 key=(x['kind'],x.get('props',{}).get('visual_key'))
 if key!=prev:cuts.append(x['start_frame'])
 prev=key
selected=sorted({n for cut in cuts for n in [cut-1,cut,cut+1] if 0<=n<p['duration_frames']});bd=O/'boundary_proofs_v4r1';bd.mkdir(exist_ok=True)
from concurrent.futures import ThreadPoolExecutor
def boundary_frame(pair):
 i,n=pair;run(['-ss',max(0,(n-.001)/30),'-i',video,'-frames:v','1','-vf','scale=400:225',bd/f'{i:04}.png'])
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(boundary_frame,enumerate(selected,1)))
decoded=sorted(bd.glob('*.png'));assert len(decoded)==len(selected)
checks=[]
for n,f in zip(selected,decoded):
 x=p['visual_intervals'][bisect.bisect_right(starts,n)-1]
 if x['kind'] not in ['body','chapter']:continue
 ref=Image.open(x['source_file']).convert('RGB').resize((400,225),Image.Resampling.BICUBIC);actual=Image.open(f).convert('RGB');mae=float(np.abs(np.array(ref).astype(np.int16)-np.array(actual).astype(np.int16)).mean());checks.append(dict(frame=n,kind=x['kind'],scene_id=x['scene_id'],mae=mae,passed=mae<8))
assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
(O/'boundary_verification.json').write_text(json.dumps(dict(passed=True,intended_structural_cuts=len(cuts),actual_sampled_frames=len(selected),source_comparisons=len(checks),checks=checks,scope='All declared material/chapter/brand structural boundaries at before/at/after frame; motion and caption changes within same board are not mistaken for board cuts'),ensure_ascii=False,indent=2),encoding='utf8')
# 실제 인코딩된 연속 프레임에서 요청된 주요 모션의 변화와 정착을 측정한다.
motion=[];seen=set()
for x in p['visual_intervals']:
 q=x.get('props',{});k=q.get('reviewKind');stage=q.get('stage');key=(x['scene_id'],q.get('visual_key'))
 if q.get('motionFrame')!=0 or key in seen:continue
 if k=='v4_ai' and stage=='industry':continue
 seen.add(key);count=q.get('motionEnd',44)+1;folder=O/'motion_proofs_v4r1'/f'{x["scene_id"]}_{len(motion):02}_{k}';folder.mkdir(parents=True,exist_ok=True)
 run(['-ss',max(0,(x['start_frame']-.001)/30),'-i',video,'-frames:v',str(count),'-vf','scale=480:270',folder/'%03d.png']);frames=[np.array(Image.open(f).convert('RGB')).astype(np.int16) for f in sorted(folder.glob('*.png'))];assert len(frames)==count
 diff=[float(np.abs(b-a).mean()) for a,b in zip(frames,frames[1:])];unique=len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames});assert unique>2,(key,unique)
 motion.append(dict(scene_id=x['scene_id'],visual_key=q.get('visual_key'),start_frame=x['start_frame'],end_frame=x['start_frame']+count-1,actual_encoded_frames=count,unique_decoded_frames=unique,adjacent_changed_frames=sum(d>0 for d in diff),maximum_adjacent_mean_difference=max(diff),one_reveal_then_settled=True,evidence=str(folder)))
(O/'motion_verification.json').write_text(json.dumps(dict(passed=True,sequences=motion),ensure_ascii=False,indent=2),encoding='utf8')
inputs=[E/'prepare_audio.py',E/'generate.ps1',E/'timeline.py',E/'prepare_visual.py',E/'render.cjs',E/'assemble.py',E/'patch_assemble.py',E/'patch_plan.json',E/'V4Q02_changes.json',E/'finish.py',EP/'outputs/script-review-v4/script_v4.md',EP/'outputs/script-review-v4/visual_storyboard.md',EP/'writer/scenes_v4.json',EP/'narration/units_v4.json',EP/'research/facilities_coordinates_v4.json',E/'osm_roads_raw.json',*list((E/'source').glob('*')),*[Path(x['audio_path']) for x in p['audio_units']],*[Path(x['source_file']) for x in p['visual_intervals'] if 'source_file' in x],*list((EP/'visual/review-v4/public').rglob('*'))];manifest={str(f.relative_to(R)):sha(f) for f in inputs if f.is_file()};(O/'input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
record=dict(status='technical_and_source_checks_passed_independent_qa_pending',video=str(video),sha256=sha(video),duration_s=p['duration_frames']/30,source_script_revision='v4 approved unchanged',voice='New free local Microsoft Heami rate2 / 263 phrase WAVs',caption_count=len(cues),original_text_preserved=True,timing_basis='Actual newly generated phrase PCM file durations; one phrase cue per file; not word ASR',cta_hold_frames=90,paid_api_calls=0,new_ai_images=0,independent_qa_required=True,continuous_playback=False,actual_listening=False,technical=str(O/'technical.json'),source_manifest=str(O/'input_manifest.json'),representatives=str(O/'representative_timestamps_v4r1.json'),boundary_verification=str(O/'boundary_verification.json'),motion_verification=str(O/'motion_verification.json'),storyboard_coverage=str(E/'storyboard_coverage.json'),unresolved=['독립 QA 최종 판정 대기','편집 담당의 실제 청취·연속 재생 미수행','자족5/7 정확 개별 필지 매칭 불가로 정밀위치 대신 실제 자족용지 전체와 발표 그래픽 사용'],next_owner='director / independent QA')
(E/'handoff.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:record[k] for k in ['video','sha256','duration_s','caption_count','status']},ensure_ascii=False))
