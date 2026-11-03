"""Freeze the reviewed Jun candidate and refresh only managed shelf links."""
from pathlib import Path
import json,hashlib,os,re,datetime
OWN=Path(__file__).resolve().parent;EP=OWN.parents[1];ROOT=EP.parents[2]
OUT=EP/'outputs/jun-user-script-v1/full-film-v1'
VIDEO=OUT/'affordable_price_jun_user_script_v2.mp4'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(ROOT).as_posix()

qa=load(EP/'qa/jun-user-script-v1/full-film-v1/handoff.json')
assert not qa['required_open_issue_ids']
assert sha(VIDEO)==qa['final_media']['sha256']=='0d73a746eee4e2eb1d2e46096a8012d756fd4a19f9f8bdce6c06af3f89a5abfa'
asr=load(EP/'narration/jun-user-script-v1/asr-full-medium/summary.json')
assert all(not r['comparison']['numeric_differences'] for r in asr['rows'])
manifest=load(EP/'narration/jun-user-script-v1/narration_manifest.json')
titles=['돈을 모은 다음의 질문','집값 밖의 비용','대출의 기준','현금 1억과 2억','현금 3억부터 5억','지역과 월 상환','내 예산 정리']
body=['# 현금 1억부터 5억까지 — 내 집 예산 잡는 법','', '사용자 원고의 낭독 본문을 보존한 Jun 버전입니다.','']
for i,title in enumerate(titles,1):
    body+=['## '+str(i)+'. '+title,'']
    for p in manifest['paragraphs']:
        if p['chapter']==i:body+=[p['text'],'']
(OUT/'script_user_original.md').write_text('\n'.join(body),encoding='utf-8')
cl_response=OWN/'claude-review-v1/response.json';cl=None
if cl_response.exists():
    response=load(cl_response);text=response.get('result') or ''
    match=re.search(r'\{',text)
    if match:
        try:cl=json.JSONDecoder().raw_decode(text[match.start():])[0]
        except Exception:pass
cl_pass=bool(cl and cl.get('verdict')=='pass' and not cl.get('required'))
if cl and cl.get('required'):raise RuntimeError('Claude required findings must be resolved before delivery')
report={'revision':'jun-user-script-v1/encoded-v2','status':'local_review_candidate_complete','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'video':rel(VIDEO),'video_sha256':sha(VIDEO),'bytes':VIDEO.stat().st_size,'duration_s':714.8,'fps':30,'frames':21444,'resolution':[1920,1080],'voice':'ElevenLabs Jun','source_doc_sha256':manifest['source_doc_sha256'],'narration_paragraphs':48,'body_scenes':31,'chapter_image_cards':7,'caption_cues':156,'actual_credits':2317,'authorized_included_cap':7000,'additional_cash_krw':0,'voice_generation_calls':7,'voice_automatic_retries':0,'numeric_values_ASR_matched':119,'full_audio_ASR_seconds':679.2,'actual_encoded_frames_reviewed':280,'full_AV_decode':'pass','frame_PTS':'pass_21444','last_caption_fix':'source_and_actual_encoded_boundary_verified','outro_gap_from_provider_last_word_s':3.0066666666666606,'independent_required_open':0,'claude_review_pass':cl_pass,'claude_review_status':'pass_sampled_frames_and_script' if cl_pass else 'pending_or_unavailable','claude_review':rel(cl_response) if cl_response.exists() else None,'claude_scope':'script/synthetic calculations/6encodedframes/3sourcecontacts; no audio','actual_listening':False,'continuous_playback':False,'known_audio_listening_targets':['S21 부가세','S23 규제'],'published':False,'new_upload_performed':False,'previous_release_preserved':True,'hyperframes_usage_query':'unknown_usage_request_failed; local rendering performed','verification':{'independent_qa':rel(EP/'qa/jun-user-script-v1/full-film-v1/handoff.json'),'audio_qa':rel(EP/'qa/jun-user-script-v1/audio-alignment-v1/handoff.json'),'ASR':rel(EP/'narration/jun-user-script-v1/asr-full-medium/summary.json'),'ending_fix':rel(EP/'editor/jun-user-script-v1/full-film-v1/ending_fix_receipt.json')}}
save(OUT/'completion.json',report)
copy_source=EP/'outputs/rebuild-v2/full-film-r2-v1/music_credits.txt'
(OUT/'music_credits.txt').write_bytes(copy_source.read_bytes())
review=f'''# 현금 1억부터 5억까지 — Jun 검토본

현재 기준: `영상.mp4` · Jun 음성 · 11분54.8초 · 1920×1080 · 30fps.

사용자 원고48문단, 본문31장면, 독립 이미지 챕터7개, 자막156개를 연결했습니다. 원고 순서·말투는 보존했습니다. 실제 문자 정렬101앵커에 맞춰 계산·강조·컷을 배치했고 마지막 발화 뒤3.0067초에 승인된 아웃트로가 시작합니다.

Jun은 승인된7,000 상한 안에서2,317크레딧을 사용했습니다. 추가 결제·충전·음성 자동재시도는0입니다.

독립 검수: 전체AV디코드·21,444프레임PTS, 31장면·40배치 경계·156자막을 포함한 실제 표본280개 확인. 마지막 자막 글자/박스 종료 불일치를 수정해 실제6경계 프레임으로 재확인했습니다. 전체679.2초 로컬MEDIUM 전사에서 숫자119개의 값·단위·순서가 일치했습니다.

Claude Opus 최대추론 검수: {'원고·가상 계산·표본 화면 검수 통과, 필수 수정0건.' if cl_pass else '응답 대기 또는 실행 미완료. 통과로 기록하지 않았습니다.'} 실제 음성은 Claude에 보내지 않았습니다.

실제 청취와 연속 재생은 수행하지 않았습니다. `부가세`·`규제`의 ASR 표기 차이는 청취 권장으로 남겼으며 발음 오류로 확정하지 않았습니다. 이 파일은 로컬 검토본이며 게시 상태는 기존 기록과 구분합니다.

최종 SHA256: `{sha(VIDEO)}`

이번 Jun본의 새 업로드는 실행하지 않았습니다. 과거 비공개본·대본·썸네일과 원본은 이전 제작 경로에 보존되어 있습니다. 폴더의 과거 신생아 상품 자료와 기존 썸네일은 이번 원고의 새 제작 산출물로 해석하지 않습니다.
'''
(OUT/'검토안내.md').write_text(review,encoding='utf-8')
(OUT/'upload_status.md').write_text('# Jun 사용자 원고 버전 게시 상태\n\n현재는 로컬 검토본입니다. 이번 버전의 새 업로드는 실행하지 않았습니다. 기존 게시 정보는 director/jun-user-script-v1/prior_episode_state.json에 보존했습니다.\n',encoding='utf-8')
# Use a real encoded frame for the current preview, rather than the prior script.
preview=OWN/'claude-review-v1/S16.png'
if preview.exists():
    from PIL import Image
    Image.open(preview).convert('RGB').save(OUT/'preview.jpg',quality=94)
shelf=ROOT/'config/video_shelf.json';cfg=load(shelf)
backup=OWN/'video_shelf.before.json'
if not backup.exists():backup.write_bytes(shelf.read_bytes())
entry=next(x for x in cfg['entries'] if x['name']=='매매가격계산')
entry['files'].update({'영상.mp4':rel(VIDEO),'자막.srt':rel(OUT/'subtitles.srt'),'대본.md':rel(OUT/'script_user_original.md'),'현재대본.md':rel(OUT/'script_user_original.md'),'계산사례.json':rel(EP/'director/user-recording-v1/calculation_check.json'),'근거자료.json':rel(EP/'research/jun-user-script-v1/reviewed_claims.json'),'검수.json':rel(OUT/'completion.json'),'검토안내.md':rel(OUT/'검토안내.md'),'비공개_업로드.md':rel(OUT/'upload_status.md'),'음악출처.txt':rel(OUT/'music_credits.txt')})
if (OUT/'preview.jpg').exists():entry['files']['미리보기.jpg']=rel(OUT/'preview.jpg')
entry['status']='사용자 원고 Jun 로컬 검토본 · '+('Claude/독립 화면검수 필수 수정0' if cl_pass else '독립 화면검수 필수 수정0 · Claude 응답 대기')+' · 실제 청취/연속 재생 미실시 · 새 업로드 미실행'
entry['local_revision']=report['revision'];entry['local_video_sha256']=report['video_sha256'];save(shelf,cfg)
state=load(OWN/'state.json');state.update({'stage':'local_review_candidate_delivered','full_film_rendered':True,'final_video':rel(VIDEO),'final_video_sha256':sha(VIDEO),'film_seconds':714.8,'claude_review_pass':cl_pass,'independent_required_open':0,'actual_listening':False,'continuous_playback':False,'new_upload_authorized':False});save(OWN/'state.json',state)
main=load(EP/'state.json');main.update({'stage':state['stage'],'active_work':state,'active_tasks':[],'blocked_tasks':[],'final_video':rel(VIDEO),'final_video_sha256':sha(VIDEO),'completed_status':'local_review_candidate','final_video_duration_s':714.8,'actual_listening':False,'continuous_playback':False,'new_upload_performed':False});save(EP/'state.json',main)
print(json.dumps({'status':report['status'],'claude_review_pass':cl_pass,'video_sha256':report['video_sha256'],'next':'refresh_video_shelf.py'},ensure_ascii=False))
