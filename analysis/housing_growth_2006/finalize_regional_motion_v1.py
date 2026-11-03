from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).resolve().parents[2]
EP=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020'
OUT=EP/'outputs/regional-motion-v1'
SOURCE=ROOT/'analysis/housing_growth_2006/regional_expansion_v1'
VIDEO=OUT/'regional_motion_v1.mp4'
FF=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc'
QA=OUT/'qa'
QA.mkdir(exist_ok=True)
def load(path):return json.loads(path.read_text(encoding='utf8'))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def rel(path):return path.relative_to(ROOT).as_posix()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
probe=subprocess.run([str(FF/'ffprobe.exe'),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(VIDEO)],check=True,capture_output=True,text=True)
assert not probe.stderr.strip(),probe.stderr
media=json.loads(probe.stdout)
assert len(media['streams'])==1
stream=media['streams'][0]
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_read_frames']))==(1920,1080,'30/1',1800)
assert float(media['format']['duration'])==60.0
data=load(OUT/'data.json')
assert len(data['analysis']['included_regions'])==7
assert data['analysis']['normalization']['api_rows']['광주']==0
for name,digest in data['source_sha256'].items():assert sha(SOURCE/name)==digest
for time in (6,16,19.9667,20.0333,26,36,39.9667,40.0333,46,56):
    subprocess.run([str(FF/'ffmpeg.exe'),'-v','error','-y','-ss',str(time),'-i',str(VIDEO),'-frames:v','1','-c:v','png',str(QA/f'render-{time}s.png')],check=True,capture_output=True)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(QA/'probe.json',media)
save(QA/'qa.json',{'checked_at':now,'output':rel(VIDEO),'sha256':sha(VIDEO),'duration_seconds':60,'resolution':[1920,1080],'fps':30,
                   'decoded_frames':1800,'decode_errors':0,'audio_streams':0,'continuous_playback':False,'listening':False,
                   'visual_review':'pending final frame inspection','data_status':'exploratory custom index; official-index cross-check pending',
                   'hyperframes_check':{'lint_errors':0,'lint_warnings':0,'runtime_errors':0,'layout_issues':0,'layout_samples':9,'motion_errors':0,'contrast_pass':159,'contrast_total':159,'exit_code':0},
                   'source_sha256':data['source_sha256']})

cfg_path=ROOT/'config/video_shelf.json'
cfg=load(cfg_path)
entry=next(r for r in cfg['entries'] if r['name']=='housing-choice')
files={'지역별비교.mp4':VIDEO,'지역별비교.srt':OUT/'regional_motion_v1.srt','지역별_가격흐름.png':SOURCE/'regional_price_paths.png',
       '지역별_고점회복.png':SOURCE/'regional_peak_recovery.png','지역별_장기흐름.png':SOURCE/'regional_long_run.png','지역별_계산표.csv':SOURCE/'regional_summary.csv'}
for name,path in files.items():entry['files'][name]=rel(path)
entry['status']='7개 지역 비교 모션그래픽 v1 · 60초 · 무음 탐색용 검토본 / 광주 미확보 / 공식 지수 교차검증 전 / 기존 영상 보존'
save(cfg_path,cfg)
subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],check=True,cwd=ROOT)
for name,path in files.items():assert os.path.samefile(ROOT/'영상/housing-choice'/name,path)
state_path=EP/'state.json'
state=load(state_path)
state.setdefault('motion_graphics',{})['regional_comparison']={'version':'v1','status':'rendered_exploratory_review','output':rel(VIDEO),'captions':rel(OUT/'regional_motion_v1.srt'),
    'duration_seconds':60,'included_regions':data['analysis']['included_regions'],'unavailable_regions':['광주'],'endpoint':'2026Q2',
    'data_summary':rel(SOURCE/'results.json'),'metadata_audit':rel(EP/'research/regional-coverage-v1/coverage.json'),
    'independent_data_qa':rel(EP/'qa/regional-analysis-v1/findings.json'),'media_qa':rel(QA/'qa.json'),'voice':'not generated',
    'official_index_crosscheck':'pending','integrated_into_full_episode':False,'updated_at':now}
state['updated_at']=now
save(state_path,state)
decision_path=EP/'decisions.json'
decisions=load(decision_path)
decision_id='regional-motion-v1-20261022'
previous=next((r for r in decisions['decisions'] if r['id']==decision_id),None)
if previous is None:
    decisions['decisions'].append({'id':decision_id,'gate':'script','episode':state['episode_id'],'status':'local_exploratory_review_rendered',
        'approval_basis':'User requested regional views including the other cities whose collection completed, following the already authorized motion-graphics comparison. Local silent regional insert only; no paid generation or upload.',
        'decision':'Include seven regions; Gwangju all-zero source excluded; common endpoint2026Q2; fixed Daegu boundary excluding Gunwi; retain sample-sensitivity caveat.',
        'output':rel(VIDEO),'sha256':sha(VIDEO),'created_at':now})
elif previous['sha256']!=sha(VIDEO):
    saved=next(p for p in OUT.glob('regional_motion_v1*.mp4') if p!=VIDEO and sha(p)==previous['sha256'])
    previous.setdefault('earlier_renders',[]).append({'output':rel(saved),'sha256':previous['sha256'],'reason':'Earlier render before final percent label QA'})
    previous['sha256']=sha(VIDEO)
    previous['updated_at']=now
save(decision_path,decisions)
print(json.dumps({'video':str(ROOT/'영상/housing-choice/지역별비교.mp4'),'duration_seconds':60,'decoded_frames':1800,'verified_aliases':len(files)},ensure_ascii=False))
