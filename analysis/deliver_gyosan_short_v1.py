from pathlib import Path
from datetime import datetime,timezone
import json

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/hanam-gyosan-20261019'
OUT=EP/'outputs/shorts-release-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
receipt=read(OUT/'upload_receipt.json');job=read(OUT/'upload_job.json')
assert receipt['verification']['status']['privacyStatus']=='public'
processing=receipt['verification'].get('processingDetails',{}).get('processingStatus')
now=datetime.now(timezone.utc).isoformat()
state=read(EP/'state.json')
state['shorts_leader_v1'].update(status='published' if processing=='succeeded' else 'uploaded_public_processing',revision='v1r2',video_path=job['video'],sha256=job['sha256'],youtube_url=receipt['url'],youtube_video_id=receipt['video_id'],youtube_processing=processing,gates=job['gates'],qa=job['qa'],completed_at=now)
save(EP/'state.json',state)
event_path=ROOT/'output/telegram_conversation/inbox/718066306.json'
event=read(event_path);event.update(application_status='applied',application_result='public_short_uploaded',applied_at=now,application_note='Gyosan leader Short v1r2 rendered from existing approved Jun narration and official map diagrams, corrected parcel clipping, sampled final QA plus full AV decode passed. Five scoped gate records retained; no new paid generation. Public upload verified; processing status recorded in episode.',deliverable_url=receipt['url'])
save(event_path,event)
notes=OUT/'검토안내.md'
notes.write_text('# 하남 교산 대장 후보 쇼츠\n\n'+f"공개 주소: {receipt['url']}\n\nYouTube 처리 상태: {processing}\n\n"+'50.453초 / 1080×1920 / 30fps. C2·B2 공식 토지이용계획도와 기존 Jun 음성을 재사용했습니다. 분양가·역 출입구 공개 후 비교 조건과 본편 안내를 포함했습니다. 새 유료 생성은 없습니다.\n\n실제 MP4 표본 프레임과 변경된 필지 구도, 글자 경계204개 및 전체 AV 디코딩을 확인했습니다. 실제 청취·연속 재생·실기기 검수는 미실시입니다.\n\n기존 v1은 보존하고, 게시본은 v1r2입니다. 기존 채널 영상의 AI 설정을 변경하지 않았습니다. 새 쇼츠의 공개 지도 도표·일반 합성 내레이션 구성을 개별 검토했고, 설명에 합성 내레이션 사용을 밝혔습니다. YouTube 자동 라벨의 부재를 보장하지 않습니다.\n',encoding='utf-8')
shelf_path=ROOT/'config/video_shelf.json';shelf=read(shelf_path)
entry=next(e for e in shelf['entries'] if e['name']=='교산')
entry['files'].update({'쇼츠_대장후보.mp4':job['video'],'쇼츠_대장후보.srt':str((EP/'outputs/shorts-leader-v1/gyosan_leader_short_v1.srt').relative_to(ROOT)).replace('\\','/'),'쇼츠_대장후보_검토.md':str(notes.relative_to(ROOT)).replace('\\','/')})
entry['shorts_youtube_url']=receipt['url'];save(shelf_path,shelf)
print(json.dumps({'url':receipt['url'],'privacy':'public','processing':processing,'alias':'영상/교산/쇼츠_대장후보.mp4'},ensure_ascii=False))
