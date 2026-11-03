"""Finalize only the exact, actually reviewed local rebuild; preserve prior releases."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent;EP=D.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(ROOT).as_posix()
def pin(p):return {'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
full=EP/'outputs/rebuild-v2/full-film-r2-v1';movie=full/'affordable_home_price_rebuild_r2_v1.mp4';srt=full/'captions_global.srt'
native=EP/'qa/rebuild-v2/media-qa/final_review.json';handoff=EP/'qa/rebuild-v2/media-qa/final_handoff.json'
claude=D/'claude/media-r2-v1/review.json';receipt=D/'claude/media-r2-v1/receipt.json'
nr,nh,cr,rc=map(read,[native,handoff,claude,receipt])
assert nr['approved'] is True and nr['required_count']==0 and nh['approved'] is True
assert cr['approved'] is True and not cr['required_issues'] and rc['approved'] is True
assert sha(movie)==nh['mp4']['sha256']==nr['input_versions']['mp4']['sha256']==cr['artifact_sha256']==rc['artifact_sha256']=='55d8626a5eff6ea43da064a44d9999133e09dc635a6b3f6e67a6f5025b64b761'
assert sha(srt)==nh['srt']['sha256']==nr['input_versions']['srt']['sha256']
script=D/'frozen-script-v3-r2/script_v3_r2.md';scenes=D/'frozen-script-v3-r2/scenes_v3_r2.json'
assert sha(script)==nh['input_versions']['script_md_sha256'] and sha(scenes)==nh['input_versions']['scenes_json_sha256']
assert read(D/'claude/script-v3-r2-round2/receipt.json')['approved'] is True
out=EP/'outputs/rebuild-v2';completion=out/'completion.json';guide=out/'검토안내.md'
assert not completion.exists()
result={'status':'completed_local_review_version','episode_id':EP.name,'at_utc':datetime.now(timezone.utc).isoformat(),
 'video':pin(movie),'srt':pin(srt),'script':pin(script),'scenes':pin(scenes),'duration_s':1121.8,'frames':33654,'resolution':[1920,1080],'fps':30,
 'reviews':{'native':pin(native),'native_handoff':pin(handoff),'Claude':pin(claude),'Claude_receipt':pin(receipt),'parent':pin(D/'parent_visual_review.json')},
 'required_open':0,'approval_scope':'대본·표본 육안·자막/전환·전체 프레임 및 AV 기술 검사','native_coverage':nh['coverage'],
 'voice':{'provider':'free Edge TTS','voice':'ko-KR-InJoonNeural','rate':'+0%','new_paid_generation':False,'actual_listening':False,'speech_naturalness':'unchecked'},
 'continuous_playback':False,'Claude_recommendations':cr['recommended'],'all_source_and_prior_media_preserved':True,
 'new_upload_executed':False,'previous_private_video_id_preserved':'szSvG_2IehY','shelf_refresh':'pending'}
save(completion,result)
guide.write_text('매매가격 계산편 재제작본 · 18분 42초\n\n'
 '클로드 Opus/max와 대본을 수정하고, 한 가구의 현금→비용→필요대출→월 예산을 따라가는 34장면으로 다시 제작했습니다. 의미 단위 자막 169개, 서로 다른 주제 전환 이미지 8개를 사용했습니다.\n\n'
 f'- [새 영상]({movie.as_posix()})\n- [수정 대본]({script.as_posix()})\n- [검수 기록]({completion.as_posix()})\n\n'
 '클로드와 독립 검수에서 해당 범위의 필수 미해결 이슈는 0건입니다. 독립 검수는 793프레임을 추출해 414개 고유 프레임을 육안으로 확인했고, 모든 자막 중간 화면·43개 컷 경계·34개 장면의 시작/중간/끝을 포함했습니다. 전체 AV 디코드와 33,654프레임의 시간표 검사도 통과했습니다.\n\n'
 '음성은 무료 InJoon입니다. 실제 청취와 연속 재생은 실시하지 않았습니다. 발음·음성 자연스러움·체감 음량은 미확인으로 기록했습니다.\n\n'
 '이번 재제작본은 로컬 파일입니다. 기존 YouTube 비공개본 szSvG_2IehY와 원본·음성·출처·승인 기록은 보존했습니다.\n\n'
 f'음악 출처: [{full.joinpath("music_credits.txt").name}]({full.joinpath("music_credits.txt").as_posix()})\n',encoding='utf-8')
cfgpath=ROOT/'config/video_shelf.json';cfg=read(cfgpath)
entry=next(e for e in cfg['entries'] if e['workspace']==rel(EP))
save(D/'delivery/previous_shelf_entry.json',entry)
old=dict(entry['files'])
entry['files'].update({'이전_비공개_영상.mp4':old['영상.mp4'],'이전_자막.srt':old['자막.srt'],'이전_대본_v2.md':old['현재대본.md'],
 '이전_비공개_업로드.md':old['비공개_업로드.md'],'영상.mp4':rel(movie),'자막.srt':rel(srt),'대본.md':rel(script),'현재대본.md':rel(script),
 '검수.json':rel(completion),'검토안내.md':rel(guide),'비공개_업로드.md':rel(guide),'미리보기.jpg':rel(D/'media-input-v1/R001-critical.jpg'),'음악출처.txt':rel(full/'music_credits.txt')})
entry['status']='재제작본 로컬 완료 · Claude/독립 화면검수 통과 · 무료 음성 · 기존 비공개본 보존'
entry['local_revision']='rebuild-v2/script-v3-r2';entry['local_video_sha256']=sha(movie)
save(cfgpath,cfg)
subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],check=True,cwd=ROOT)
alias=ROOT/'영상'/entry['name']/'영상.mp4';assert alias.samefile(movie) and sha(alias)==result['video']['sha256']
result['shelf_refresh']='verified';result['short_video_path']=rel(alias);save(completion,result)
prepath=D/'episode_preflight.json';pre=read(prepath)
pre['status']='completed_local_review_version'
media=read(EP/'director/production-v1/media_assets.json')['assets']
pre['baseline'].update(current_video=rel(movie),brand_intro=media[0]['path'],brand_outro=media[1]['path'],bgm=media[2]['path'])
pre['channel_style_contract']['baseline_primary']=pre['baseline']['previous_video']
pre['channel_style_contract']['baseline_primary_sha256']=pre['baseline']['sha256']
pre['story'].update(previous_episode_reference='매매·전세·월세의 동일 2억5천만원/월300만원 사례',next_episode_promise='정한 예산에서 지역·단지를 가격·일자리 접근성·교통·생활 여건으로 비교',each_section_answers=['구입 시 필요한 현금','비용과 감면','대출 제약','매달 상환과 저축','가격/상품/금리 조건 변화'],candidate_scope='A/B 가상가구의 서울84㎡ 매수 예산')
pre['facts_required']=['공식 정책 적용일/요건','LTV/DSR/DTI와 상품한도','취득세/교육세/중개보수/기타 계획비용','신생아60회 뒤 잔액과 잔여300개월','가상 사례 계산 원장과 출처/권리 기록']
pre['approvals']['script'].update(status='current_direct_user_rewrite_request_exact_artifact_locked_by_actual_reviews',artifact_hashes={'markdown':sha(script),'scenes':sha(scenes)})
pre['approvals']['completed'].update(status='local_review_version_completed',artifact_hashes={'mp4':sha(movie),'srt':sha(srt)})
pre['change_control'].update(unchanged_audio_reused=False,changed_scene_ids=[s['id'] for s in read(scenes)['scenes']],single_timing_lock=rel(EP/'narration/rebuild-v2/audio-r2-recovered/final_timing.json'),package_frozen_before_hash=True)
pre['qa'].update(timeline_font_bbox_and_stroke_all_cases='pass_in_measured_source_samples',actual_encoded_frames='793_extracted_414_native_manually_viewed',all_cut_boundaries_no_flash='pass_43_sampled_boundaries',semantic_caption_original_text_match='pass_169',protected_numbers_units_names='pass',caption_box_exceptions='pass',last_speech_plus_three_seconds='pass',full_decode='pass',caption_display_mapping_and_numeric_value_match='pass_in_declared_scope',required_open_issues=0,evidence_paths=[rel(native),rel(receipt),rel(completion)])
for k in ['inset_matches_spoken_region','station_locations','leaders_do_not_cross','actual_block_plan_and_locator','district_area_vs_planned_station_distinguished']:pre['qa'][k]='not_applicable_no_geographic_map'
pre['vertical_video']['status']='not_applicable_16_9_longform';pre['representative_style_QA']='passed_exact_R003_R006_R030_v3'
pre['release'].update(longform=rel(movie),actual_platform_privacy='new_version_not_uploaded_previous_private_preserved',processing='not_applicable_local_rebuild',studio_copyright='not_checked_new_upload_not_executed')
save(prepath,pre)
planpath=D/'design_and_plan.json';plan=read(planpath);plan['status']='completed_local_review_version'
for t in plan['tasks']:t['status']='complete_in_declared_scope'
plan['final_outputs']=[rel(movie),rel(srt),rel(script),rel(completion)];save(planpath,plan)
statepath=EP/'state.json';state=read(statepath)
state['rebuild_v2'].update(status='completed_local_review_version',completion=rel(completion),short_video_path=rel(alias),native_full_media_review='approved_required0',Claude_media_review='approved_required0',required_open=0,new_upload_executed=False,actual_listening=False,continuous_playback=False)
save(statepath,state)
print(json.dumps({'status':result['status'],'video':str(alias),'mp4_sha256':sha(alias),'both_reviewed_required_open':0,'new_upload_executed':False},ensure_ascii=False))
