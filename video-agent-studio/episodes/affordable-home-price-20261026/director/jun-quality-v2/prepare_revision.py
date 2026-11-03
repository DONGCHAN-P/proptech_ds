from pathlib import Path
import json, shutil, os, hashlib
from datetime import datetime,timezone
EP=Path(__file__).resolve().parents[2]
OLD=EP/'editor/jun-user-script-v1/full-film-v1'
NEW=EP/'editor/jun-quality-v2/main'
NEW.mkdir(parents=True,exist_ok=True)
for name in ['assemble.py','build_visuals.py','check_project.py']:
    dst=NEW/name
    if not dst.exists():shutil.copy2(OLD/name,dst)
p=NEW/'assemble.py';s=p.read_text(encoding='utf-8')
s=s.replace("OUT=EP/'outputs/jun-user-script-v1/full-film-v1'","OUT=EP/'outputs/jun-quality-v2/main'")
s=s.replace("'affordable-price-Jun-user-script-v1'","'affordable-price-Jun-quality-v2'")
p.write_text(s,encoding='utf-8')
target=NEW/'project/assets/mix.m4a';target.parent.mkdir(parents=True,exist_ok=True)
if not target.exists():os.link(OLD/'project/assets/mix.m4a',target)
record={'updated_at':datetime.now(timezone.utc).isoformat(),'revision':'jun-quality-v2',
 'authority':'현재 사용자 요청: Claude와 실제 화면 보완 논의, 좋은 Jun 음성 유지, 썸네일, 본편 및 홍보용·요약용 쇼츠 두 편 비공개 업로드. 최신 지시: 판단은 전부 니가 해봐.',
 'private_upload_authorized':True,'authorized_deliverables':['main','short_promo','short_summary'],
 'public_release_authorized':False,'new_paid_generation_authorized':False,'additional_cash_cap_krw':0,
 'audio_preserved_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'baseline_video_sha256':'0d73a746eee4e2eb1d2e46096a8012d756fd4a19f9f8bdce6c06af3f89a5abfa',
 'ordinary_editorial_decisions_delegated':True,'existing_uploads_delete_authorized':False}
(Path(__file__).parent/'authorization.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state=json.loads((EP/'state.json').read_text(encoding='utf-8-sig'))
state.update(stage='visual_quality_revision_in_progress',active_revision='jun-quality-v2',private_upload_authorized=True,public_release_authorized=False,updated_at=record['updated_at'])
state['current_authorization']='director/jun-quality-v2/authorization.json'
state['active_tasks']=['quality-main','claude-screen-review','portrait-shorts','private-delivery']
(EP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':str(NEW),'audio_preserved':record['audio_preserved_sha256']}))
