from pathlib import Path
import json,hashlib,shutil,os
from datetime import datetime,timezone
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OWN=Path(__file__).parent
OUT=EP/'outputs/jun-quality-v2/main';RELEASE=EP/'outputs/jun-quality-v2/release'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
VIDEO=OUT/'affordable_home_price_jun_quality_v3.mp4'
tech=read(OWN/'encoded_checks/technical_report.json')
visual=read(OWN/'encoded_checks/visual_review.json')
shortqa=read(EP/'qa/jun-quality-v2/shorts-review/handoff.json')
s18qa=read(EP/'qa/jun-quality-v2/final-main-s18-review.json')
assert tech['sha256']==sha(VIDEO) and tech['whole_AV_decode_pass'] and tech['audio_PCM_identical_to_approved_baseline']
assert visual['video_sha256']==sha(VIDEO) and visual['required_open']==[]
assert shortqa['required_open']==0
assert s18qa['checked_revision']['sha256']==sha(VIDEO) and s18qa['required_open_in_scope']==0
thumb=EP/'outputs/jun-quality-v2/thumbnail/thumbnail.png'
assert sha(thumb)==read(EP/'qa/jun-quality-v2/shorts-review/thumbnail_review.json')['sha256']
shorts=EP/'outputs/jun-quality-v2/shorts'
shortfiles=[shorts/'01_promo_jun_v4.mp4',shorts/'02_summary_jun_v4.mp4']
for x in read(shorts/'final_outputs.json')['deliverables']:
    assert sha(ROOT/x['path'])==x['sha256']
old=EP/'outputs/jun-user-script-v1/full-film-v1'
for name in ['script_user_original.md','music_credits.txt']:shutil.copyfile(old/name,OUT/name)
preview=ROOT/next(r['path'] for r in tech['frames'] if 'S24_end' in r['labels'])
shutil.copyfile(preview,OUT/'preview.jpg')
record={'revision':'jun-quality-v2/encoded-v3','status':'local_files_ready_external_steps_pending','created_at_utc':datetime.now(timezone.utc).isoformat(),
 'video':rel(VIDEO),'video_sha256':sha(VIDEO),'duration_s':714.8,'frames':21444,'fps':30,'resolution':[1920,1080],
 'voice':'ElevenLabs Jun','voice_regenerated':False,'approved_audio_AAC_identical':tech['AAC_identical'],'approved_audio_PCM_identical':True,
 'original_paragraphs':48,'body_scenes':31,'chapter_images':7,'caption_cues':156,'SRT_unchanged':True,
 'whole_AV_decode':'pass','PTS':'all_21444_pass','actual_encoded_samples':tech['sample_count'],'actual_frame_visual_review':visual,
 'independent_source_and_shorts_required_open':0,'thumbnail':rel(thumb),'shorts':[{'path':rel(p),'sha256':sha(p)} for p in shortfiles],
 'additional_paid_generation_calls':0,'additional_cash_krw':0,'claude_final_review_pass':False,'private_upload_authorized':True,'new_upload_performed':False,
 'actual_listening':False,'continuous_playback':False,'external_status':rel(OWN/'external_status.json'),
 'verification':{'technical':rel(OWN/'encoded_checks/technical_report.json'),'independent_source':rel(EP/'qa/jun-quality-v2/baseline_findings.json'),'independent_shorts':rel(EP/'qa/jun-quality-v2/shorts-review/handoff.json'),'S18_correction':rel(EP/'editor/jun-quality-v2/main/patch-S18/final_correction_receipt.json'),'S18_independent_encoded_review':rel(EP/'qa/jun-quality-v2/final-main-s18-review.json')}}
save(OUT/'completion.json',record)
review='''# 내 집 예산 영상 — 화면 개선본

현재 영상.mp4는 Jun 음성을 보존한 11분54.8초 화면 개선본입니다. 선·화살표 접점과 분수 정렬을 고치고, 설명 중 제목만 남던 구간에 대상을 먼저 표시했습니다. 문자 카드 중심의 여덟 장면을 돈·주택·심사·생활비 흐름으로 바꿨고, 비용 계산은 준비금 전체를 나누는 도식으로 이어집니다. 첫 계산 뒤와 마지막에는 구독·좋아요 안내를 넣었습니다.

썸네일과 역할이 다른 쇼츠 두 편을 함께 준비했습니다. 쇼츠_홍보.mp4는 38.17초, 쇼츠_핵심요약.mp4는 51.47초입니다. 모두 별도 세로 화면, 기존 Jun 발췌 음성, 의미 단위 자막으로 구성했습니다.

최종 본편의 전체 영상·오디오 디코드, 21,444프레임 시간표, 156개 자막 표본을 확인했습니다. 승인된 이전 Jun본과 AAC·PCM이 동일하며 원고와 자막 시간표를 유지했습니다. 실제 인코딩 프레임과 독립 소스·쇼츠·썸네일 검수의 미해결 필수 수정은 0건입니다. 실제 청취와 전체 연속 재생은 수행하지 않았습니다.

Claude Desktop Opus 최대에 기준본 화면과 개선안을 전송했지만 답변·수정본 최종 승인을 확인하지 못했습니다. Windows 컴퓨터 제어는 현재 브라우저 URL을 확인하지 못해 종료되었습니다. YouTube API는 기존 인증이 만료 또는 취소되어 비공개 업로드를 수행하지 못했습니다. 새 업로드·공개 전환·기존 영상 삭제는 0건입니다.

로컬 결과물 제작과 외부 최종 검수·업로드의 상태를 구분해 두었습니다. 재개 시 파일을 다시 만들 필요 없이 이 버전과 검수 기록부터 이어가면 됩니다. 추가 유료 생성·결제·충전은 0입니다.
'''
(OUT/'검토안내.md').write_text(review,encoding='utf-8')
(RELEASE/'upload_status.md').write_text('# 비공개 업로드 대기\n\n사용자 비공개 업로드 권한은 확인되어 있습니다. 기존 YouTube 인증 invalid_grant와 Windows 컴퓨터 제어 종료로 이번 본편 및 쇼츠 2편의 새 업로드는 미실행입니다. Claude의 수정본 최종 검수도 미확인입니다. 기존 채널·승인 범위를 유지해 인증을 복구하고 최종 검수를 이어갑니다. 공개 범위를 임의로 바꾸지 않습니다.\n',encoding='utf-8')
manifest={'status':'pending_external_review_and_auth','user_private_upload_authorized':True,'youtube_channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','privacy':'private','uploads_performed':0,
 'main':{'video':rel(VIDEO),'sha256':sha(VIDEO),'thumbnail':rel(thumb),'thumbnail_sha256':sha(thumb),'subtitles':rel(OUT/'subtitles.srt'),'subtitles_sha256':sha(OUT/'subtitles.srt'),'metadata':rel(RELEASE/'main_metadata.json')},
 'shorts':[{'video':rel(p),'sha256':sha(p),'subtitles':rel(p.with_suffix('.srt'))} for p in shortfiles],
 'shorts_metadata':rel(RELEASE/'shorts_metadata.json'),'external_status':rel(OWN/'external_status.json'),'review_report':rel(OUT/'completion.json'),
 'no_duplicate_upload_rule':'Read saved receipts/channel state before uploading; ambiguous prior upload requires investigation, no blind retry.'}
save(RELEASE/'upload_manifest.json',manifest)
shelf=ROOT/'config/video_shelf.json';cfg=read(shelf);backup=OWN/'video_shelf.before.json'
if not backup.exists():backup.write_bytes(shelf.read_bytes())
entry=next(e for e in cfg['entries'] if e['name']=='매매가격계산')
entry['files'].update({'영상.mp4':rel(VIDEO),'자막.srt':rel(OUT/'subtitles.srt'),'현재대본.md':rel(OUT/'script_user_original.md'),'대본.md':rel(OUT/'script_user_original.md'),
 '썸네일.png':rel(thumb),'쇼츠_홍보.mp4':rel(shortfiles[0]),'쇼츠_홍보.srt':rel(shortfiles[0].with_suffix('.srt')),'쇼츠_핵심요약.mp4':rel(shortfiles[1]),'쇼츠_핵심요약.srt':rel(shortfiles[1].with_suffix('.srt')),
 '검수.json':rel(OUT/'completion.json'),'검토안내.md':rel(OUT/'검토안내.md'),'미리보기.jpg':rel(OUT/'preview.jpg'),'비공개_업로드.md':rel(RELEASE/'upload_status.md'),'유튜브_설명.txt':rel(RELEASE/'description.txt'),'제작_판단.md':rel(OWN/'research_and_edit_decisions.md'),'음악출처.txt':rel(OUT/'music_credits.txt')})
entry.update(status='Jun 화면 개선본·쇼츠 2편·썸네일 로컬 준비 / Claude 최종 확인·비공개 업로드 대기',local_revision=record['revision'],local_video_sha256=record['video_sha256']);save(shelf,cfg)
state=read(EP/'state.json');state.update(stage='local_quality_files_ready_external_steps_pending',active_revision='jun-quality-v2',active_tasks=[],blocked_tasks=[{'task':'Claude final review','reason':'Windows computer-use URL policy enforcement stop'},{'task':'private upload main and 2Shorts','reason':'YouTube OAuth invalid_grant; browser fallback ended'}],final_video=rel(VIDEO),final_video_sha256=record['video_sha256'],final_video_duration_s=714.8,new_upload_performed=False,private_upload_authorized=True,public_release_authorized=False,updated_at=record['created_at_utc'])
state['active_work']={'revision':record['revision'],'final_video':rel(VIDEO),'voice_preserved':True,'actual_listening':False,'continuous_playback':False,'local_report':rel(OUT/'completion.json'),'private_upload_authorized':True,'new_upload_performed':False,'claude_final_review_pass':False,'shorts':[rel(p) for p in shortfiles],'thumbnail':rel(thumb)}
save(EP/'state.json',state)
print(json.dumps({'status':record['status'],'video_sha256':record['video_sha256'],'next':'refresh_video_shelf.py'},ensure_ascii=False))
