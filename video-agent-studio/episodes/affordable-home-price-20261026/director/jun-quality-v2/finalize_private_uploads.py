from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];DIR=Path(__file__).parent
REL=EP/'outputs/jun-quality-v2/release';BATCH=REL/'private-upload-20261028'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
records=[]
for name in ['main','promo','summary']:
    folder=BATCH/name;job=read(folder/'upload_job.json');r=read(folder/'upload_receipt.json')
    assert r['sha256']==job['sha256']==sha(ROOT/job['video']) and r['private_verified']
    v=r['verification'];assert v['status']['privacyStatus']=='private' and not v['status'].get('publishAt')
    assert v['snippet']['channelId']==job['channel_id'] and v['snippet']['title']==job['title']
    assert v['processingDetails']['processingStatus']=='succeeded' and r['caption_serving_verified']
    if name=='main':assert r['thumbnail_uploaded']
    records.append({'id':name,'video_id':r['video_id'],'url':r['url'],'sha256':r['sha256'],'privacy':'private','processing':'succeeded','caption':'serving','title':job['title']})
assert len({r['video_id'] for r in records})==3
stamp=datetime.now(timezone.utc).isoformat();report={'status':'private_uploaded_verified','updated_at':stamp,'items':records,'public_release':False,'existing_videos_deleted':False,'claude_final_review_pass':False,'source_authorization':'director/jun-quality-v2/current_upload_authorization.json'}
save(BATCH/'completion.json',report)
status='# 비공개 업로드 완료\n\n'+ '\n'.join('- '+r['title']+' — '+r['url'] for r in records)+'\n\n세 영상의 비공개 상태·처리 완료·한국어 자막 제공을 API로 확인했습니다. 본편 썸네일을 적용했습니다. 공개 전환과 기존 영상 삭제는 수행하지 않았습니다. Claude 수정본 최종 검수는 미확인 상태로 유지합니다.\n'
(REL/'upload_status.md').write_text(status,encoding='utf-8')
manifest=read(REL/'upload_manifest.json');manifest.update(status='private_uploaded_verified',uploads_performed=3,uploaded_items=records,updated_at=stamp);save(REL/'upload_manifest.json',manifest)
external=read(DIR/'external_status.json');external['youtube'].update(existing_API_probe='reauthenticated_existing_scopes_same_channel',uploads_performed=3,new_video_ids=[r['video_id'] for r in records],verified_items=records,verified_at=stamp,error_code=None,error_description=None,next_step='사용자 지시가 있을 때만 공개 범위 변경');save(DIR/'external_status.json',external)
state=read(EP/'state.json');state.update(stage='private_uploaded_verified',new_upload_performed=True,private_upload_url=records[0]['url'],private_upload_authorized=True,public_release_authorized=False,updated_at=stamp)
state['blocked_tasks']=[{'task':'Claude final review','reason':'final review remains unconfirmed; private upload performed on latest direct user instruction'}]
state['private_uploads']=records;state['active_work'].update(new_upload_performed=True,private_upload_url=records[0]['url'],private_uploads=records,stage='private_uploaded_verified');save(EP/'state.json',state)
local_report=EP/'outputs/jun-quality-v2/main/completion.json';d=read(local_report);d.update(status='private_uploaded_verified',new_upload_performed=True,private_uploads=records,upload_verified_at=stamp);save(local_report,d)
review=EP/'outputs/jun-quality-v2/main/검토안내.md'
review.write_text(review.read_text(encoding='utf-8')+'\n\n## 비공개 업로드 확인\n\n2026-10-28 현재 직접 업로드 지시에 따라 기존 계정을 같은 권한으로 재연결하고 세 편을 비공개로 업로드했습니다. 위의 인증 만료·업로드 미실행 설명은 이전 작업 시점의 기록입니다. 현재 비공개 상태·처리·자막과 본편 썸네일 확인은 비공개_업로드.md에 있습니다. Claude 최종 검수 미확인과 실제 청취·연속 재생 범위는 그대로 유지합니다.\n',encoding='utf-8')
shelf=ROOT/'config/video_shelf.json';cfg=read(shelf);entry=next(e for e in cfg['entries'] if e['workspace'].endswith('affordable-home-price-20261026'))
entry.update(status='Jun 화면 개선 본편·쇼츠 2편 비공개 업로드 및 자막 확인 완료 / Claude 최종 검수 미확인',youtube_url=records[0]['url'],youtube_visibility='private',shorts_youtube_urls=[r['url'] for r in records[1:]])
save(shelf,cfg)
print(json.dumps(report,ensure_ascii=False))
