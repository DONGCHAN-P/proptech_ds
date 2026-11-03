from pathlib import Path
import json,subprocess,sys,hashlib,shutil,datetime
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/readable-video-v2'
cfgfile=ROOT/'config/video_shelf.json';cfg=json.loads(cfgfile.read_text('utf-8'));entry=next(e for e in cfg['entries'] if e['name']=='지역별가격회복');f=entry['files']
new=(O/'대본.md').relative_to(ROOT).as_posix()
for name in ['대본.md','논문영상_대본.md']:
    if f[name]!=new:f.setdefault('이전_논문_v1_'+name,f[name])
    f[name]=new
f['논문영상_인용자료.md']=(O/'인용자료.md').relative_to(ROOT).as_posix()
entry['status']='가독성 대본 v2·상세 인용자료 정리 완료 · 전체 화면 검토본 렌더 중 · 음성 보류'
cfgfile.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),'utf-8')
director=EP/'director/readable-video-v2';director.mkdir(parents=True,exist_ok=True)
if not (director/'state_before.json').exists():shutil.copy2(EP/'state.json',director/'state_before.json')
state=json.loads((EP/'state.json').read_text('utf-8'))
state.update(stage='literature_readable_v2_rendering_narration_on_hold',script_revision='readable-video-v2',script_status='rewritten_under_current_user_instruction',script_file=new,script_sha256=hashlib.sha256((O/'대본.md').read_bytes()).hexdigest(),updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
state['pending_production']={'revision':'readable-video-v2','mode':'full_local_visual_review','render_log':str((O/'checks/render-corrected.log').relative_to(ROOT).as_posix()),'voice_on_hold':True,'paid_media_calls':0,'external_send':False,'upload':False}
(EP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),'utf-8')
p=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
print(p.stdout);print(p.stderr);sys.exit(p.returncode)
