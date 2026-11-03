"""Finalize only the two exact, privately processed, caption-serving Shorts releases."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
RELEASE=EP/'outputs/shorts-release-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

main=read(EP/'outputs/jun-release-v1/completion.json')
assert main['status']=='Jun_private_uploaded_verified_old_private_replaced'
public_path=ROOT/'config/current_video.json'
assert sha(public_path)==main['current_public_config_sha256_unchanged']
codex=read(EP/'qa/shorts-jun-v1/final_review.json')
claude=read(HERE/'claude/shorts-final-v2/receipt.json')
assert codex['approved'] and not codex['required_issues'] and not codex.get('critical_issues',[])
assert claude['approved'] and claude['exit_code']==0 and not claude['is_error']
results=[]
for ident in ['funnel','analysis']:
    out=RELEASE/ident;job=read(out/'upload_job.json');receipt=read(out/'upload_receipt.json')
    dual=read(out/'dual_media_review.json')
    assert job['short_id']==ident and receipt['sha256']==job['sha256']==dual['video_sha256']
    assert sha(ROOT/job['video'])==job['sha256'] and sha(ROOT/job['subtitles'])==job['subtitles_sha256']
    assert not dual['required_open'] and not dual['critical_open']
    for who in ['codex','claude']:
        reviewer=dual[who];assert reviewer['approved'] and sha(ROOT/reviewer['receipt'])==reviewer['receipt_sha256']
    verification=receipt['verification']
    assert receipt['private_verified'] and receipt['caption_serving_verified'] and receipt['caption_status']=='serving'
    assert verification['status']['privacyStatus']=='private' and not verification['status'].get('publishAt')
    assert verification['snippet']['channelId']==job['channel_id'] and verification['snippet']['title']==job['title']
    assert verification['processingDetails']['processingStatus']=='succeeded'
    assert receipt['video_id'] not in ['exEGpjcqdF0','szSvG_2IehY','XWAWnSrz7FE',main['video_id']]
    video_id=receipt['video_id'];render=read(EP/f'outputs/shorts-jun-v2/{ident}/renders/render_receipt.json')
    results.append({'id':ident,'title':job['title'],'video_id':video_id,'url':'https://www.youtube.com/shorts/'+video_id,
        'video':job['video'],'video_sha256':job['sha256'],'subtitles':job['subtitles'],
        'subtitles_sha256':job['subtitles_sha256'],'duration_s':render['duration_s'],
        'privacy':'private','scheduled':False,'processing':'succeeded','Korean_caption_status':'serving',
        'dual_review':rel(out/'dual_media_review.json'),'new_TTS_calls':0,'new_paid_credits':0})
assert len({r['video_id'] for r in results})==2
related=read(HERE/'shorts_related_video_receipt.json')
completion={'status':'two_Shorts_private_uploaded_processed_and_caption_serving','revision':'shorts-jun-v2',
    'main_url':main['url'],'items':results,'Codex_approved':True,'Claude_Opus_max_approved':True,
    'new_TTS_calls':0,'new_paid_voice_credits':0,'additional_cash_usd':0,'coverage':codex['coverage'],
    'actual_listening':False,'continuous_playback':False,'main_publication_changed':False,
    'related_video_setting':related['status'],'related_video_receipt':rel(HERE/'shorts_related_video_receipt.json'),
    'main_last_observed_privacy':related['main_last_observed_privacy'],
    'verified_at_utc':datetime.now(timezone.utc).isoformat()}
save(RELEASE/'completion.json',completion)
lines=['# 매매·전세·월세 쇼츠 비공개 업로드 완료','',f'본편: {main["url"]}','',
    '| 편 | 비공개 URL | 길이 |','|---|---|---|']
for row in results:
    label='유입용' if row['id']=='funnel' else '분석 요약용'
    lines.append(f'| {label} | {row["url"]} | {row["duration_s"]:.3f}초 |')
lines += ['', '두 편 모두 처리 완료와 한국어 자막 serving을 조회했습니다. 예약은 없고 비공개를 유지합니다. 기존 Jun 음성에서 완전한 문장을 사용해 추가 TTS 호출·음성 크레딧·추가 결제는0입니다.', '',
    'Codex와 Claude Opus/max가 동일 영상·자막의 제공된 검수 범위를 승인했습니다. 독립 Codex 검수는 실제 MP4의95시점·18장면·30자막·전환·마지막 발화 후 안내, 전체 AV 디코드·신호 확인을 포함합니다. Claude에는 승인된12장과 대본·자막·집계·검수 기록을 제공했습니다. 직접 청취·연속 재생은 미확인입니다.', '',
    '원본과 이전 버전·출처·승인·검수 기록은 보존했습니다. 본편과 다른 영상의 게시 설정은 이번 쇼츠 작업에서 변경하지 않았습니다.', '',
    '관련 동영상의 본편 지정은 미설정입니다. Windows 컴퓨터 사용이 현재 브라우저 주소를 충분히 확인하지 못해 정책상 중단됐고, UI 클릭·입력·저장은 하지 않았습니다. 본편은 API 조회에서 공개 상태로 확인됐으며 그 설정을 변경하지 않았습니다.', '',
    '수동 연결 순서: YouTube Studio → 콘텐츠 → 각 쇼츠 선택 → 관련 동영상 → 같은 2억5천만원, 10년 뒤 자산이 달라지는 이유 본편 선택 → 저장. [YouTube 공식 안내](https://support.google.com/youtube/answer/14075157?hl=en).', '']
(RELEASE/'private_upload_status.md').write_text('\n'.join(lines),encoding='utf8')
state_path=EP/'state.json';state=read(state_path)
state['shorts_jun_v1'].update(status=completion['status'],canonical_revision='shorts-jun-v2',
    Claude_payload_question_pending=False,Claude_final_review=rel(HERE/'claude/shorts-final-v2/receipt.json'),
    youtube_upload_executed=True,completion=rel(RELEASE/'completion.json'),items=results,
    related_video_assignment=related['status'],related_video_receipt=rel(HERE/'shorts_related_video_receipt.json'))
save(state_path,state)
shelf_path=ROOT/'config/video_shelf.json';shelf=read(shelf_path)
entry=next(x for x in shelf['entries'] if x['name']=='매매전월세')
entry['status']='Jun 본편·쇼츠2편 / 양측 검수 통과 / YouTube 비공개·처리·한국어 자막 확인'
for row in results:
    label='유입' if row['id']=='funnel' else '요약'
    entry['files'][f'쇼츠_{label}.mp4']=row['video']
    entry['files'][f'쇼츠_{label}.srt']=row['subtitles']
entry['files']['쇼츠_업로드.md']=rel(RELEASE/'private_upload_status.md')
entry['files']['쇼츠_검수결과.json']=rel(RELEASE/'completion.json')
entry['shorts_youtube_urls']={r['id']:r['url'] for r in results}
save(shelf_path,shelf)
queue_path=ROOT/'config/video_production_queue_20261026.json';queue=read(queue_path)
queue['housing_choice_shorts_v2']=completion;save(queue_path,queue)
assert sha(public_path)==main['current_public_config_sha256_unchanged']
print(json.dumps({'status':completion['status'],'urls':[r['url'] for r in results],'new_TTS_calls':0,'main_visibility_changed':False}))
