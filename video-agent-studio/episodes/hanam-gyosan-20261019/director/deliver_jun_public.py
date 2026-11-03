from pathlib import Path
import json,hashlib,datetime
E=Path(__file__).resolve().parents[1];R=E.parents[2];O=E/'outputs/release-prep-v5-jun';P=E/'outputs/production-v5-jun'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
j=read(O/'upload_job.json');u=read(O/'upload_receipt.json');v=u['verification'];assert u['sha256']==j['sha256'];assert v['status']['privacyStatus']=='public';assert v['snippet']['channelId']==j['channel_id'];assert v['snippet']['title']==j['title'];assert v['snippet']['description'].replace('\r\n','\n').strip()==j['description'].replace('\r\n','\n').strip();assert v['processingDetails']['processingStatus'] in ['processing','succeeded'];assert not v['status'].get('publishAt');assert sha(R/j['video'])==j['sha256']
q=read(E/'qa/review-v5-jun-independent/report.json');assert q['sha256']==j['sha256'] and q['required_unresolved']==0
account=read(E/'narration/jun-v5-final/account_reconciliation.json');assert account['account_total_delta']==account['provider_header_total']==3351
url='https://youtu.be/'+u['video_id'];now=datetime.datetime.now(datetime.timezone.utc).isoformat();processing_done=v['processingDetails']['processingStatus']=='succeeded';processing_label='처리 완료' if processing_done else 'YouTube 영상 처리 중'
summary={'video_id':u['video_id'],'youtube_url':url,'privacy':'public','processing':v['processingDetails']['processingStatus'],'definition':v['contentDetails'].get('definition'),'title':j['title'],'video_sha256':j['sha256'],'duration_s':32272/30,'thumbnail':u.get('thumbnail'),'credits_used':3351,'credits_remaining':account['remaining'],'additional_cash':0,'required_unresolved':0,'actual_listening':False,'continuous_playback':False,'verified_at':now,'old_private_video_preserved':'aeuQbsbRnEY','metadata_verified':True}
write(O/'release_summary.json',summary)
(O/'공개_완료.md').write_text(f'''# 교산 Jun v5 공개 완료

영상: {url}

제목: {j['title']}

- 공개 상태를 YouTube API로 확인했습니다. 처리 상태: {processing_label}. 채널·제목·설명도 확정 업로드 작업과 일치합니다.
- 17분 55.73초, 1920×1080, 30fps. Jun 음성 10장·261개 구절에 맞춰 화면과 자막을 재정렬했습니다.
- 검색 주제와 일치하는 제목·설명 첫 문장·챕터 10개, 왕숙·창릉 연결 링크를 반영했습니다. 추천 노출 성과를 보장하지는 않습니다.
- 실제 음성 사용량 3,351크레딧, 구독 차감과 일치합니다. 승인 상한 10,055 이내, 추가 결제 0원입니다.
- 독립 검수는 실제 MP4 47개 표본과 261개 자막 원문·정렬 범위·겹침 검사입니다. 필수 미해결 0건입니다. 실제 청취·전체 연속 재생·발음 자연스러움 검수는 미실시입니다.
- 기존 무료 검토본 및 이전 비공개 영상(aeuQbsbRnEY)은 보존했습니다.

검수: 작업폴더/qa/review-v5-jun-independent/report.md
업로드 증거: 작업폴더/outputs/release-prep-v5-jun/upload_receipt.json
''',encoding='utf8')
s=read(E/'state.json');s.update(stage='published_jun_v5',current_render=str((R/j['video']).resolve()),current_render_sha256=j['sha256'],current_render_revision='v5-jun',video_path=(R/j['video']).relative_to(E).as_posix(),rendered_video_sha256=j['sha256'],actual_video_duration_seconds=32272/30,qa_review='qa/review-v5-jun-independent/report.json',qa_sha256=sha(E/'qa/review-v5-jun-independent/report.json'),required_unresolved=0,youtube_video_id=u['video_id'],youtube_url=url,youtube_privacy='public',youtube_processing=v['processingDetails']['processingStatus'],upload_receipt='outputs/release-prep-v5-jun/upload_receipt.json',voice='ElevenLabs Jun')
s['jun_v5'].update(status='published',video_sha256=j['sha256'],video=j['video'],youtube_url=url,credits_actual=3351,credits_remaining=account['remaining'],additional_cash=0,upload_performed=True,actual_listening=False,continuous_playback=False,completed_at=now);write(E/'state.json',s)
shelf=read(R/'config/video_shelf.json')
for e in shelf['entries']:
 if e['name']=='교산':
  e.update(status='Jun 최종본 v5 · YouTube 공개 · '+processing_label,youtube_url=url,youtube_revision='v5-jun')
  for k,x in {'영상.mp4':j['video'],'자막.srt':j['srt'],'대본.md':str((E/'outputs/script-review-v5/script_v5.md').relative_to(R)).replace('\\','/'),'개선검토.md':str((O/'공개_완료.md').relative_to(R)).replace('\\','/'),'검토안내.md':str((O/'공개_완료.md').relative_to(R)).replace('\\','/')}.items():e['files'][k]=x
write(R/'config/video_shelf.json',shelf)
c=R/'config/current_video.json';history=R/'config/history';history.mkdir(exist_ok=True);backup=history/'current_video_before_gyosan_jun_v5.json'
if c.exists() and not backup.exists():backup.write_bytes(c.read_bytes())
write(c,{'version':'gyosan-v5-jun','episode':E.name,'video':j['video'],'subtitles':j['srt'],'script':str((E/'outputs/script-review-v5/script_v5.md').relative_to(R)).replace('\\','/'),'voice':'ElevenLabs Jun','duration_seconds':32272/30,'youtube_url':url,'publication_status':'public','previous_video_url':'https://youtu.be/eLF3-1ZaraQ','report':str((O/'release_summary.json').relative_to(R)).replace('\\','/'),'sha256':j['sha256']})
print(json.dumps(summary,ensure_ascii=False))
