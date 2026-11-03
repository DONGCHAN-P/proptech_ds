import json,hashlib
from pathlib import Path
q=Path(__file__).parent; ep=q.parents[1]; out=ep/'outputs/production-v7-preview'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=rd(out/'project_v7.json'); a=rd(q/'timeline_audit.json'); e=rd(out/'evidence_manifest.json')
finding={'issue_id':'QAV7-P01','scene_id':'M001_005','timecode':'00:01:26.900–00:01:27.600 (f2607–2628)','severity':'required','문제':'공원, 단독 의미미완성 0.7초 자막으로 깜박임 우려','evidence':'project captions 및 actual cut02 f2617; 새 최종본 국소 병합 대기','수정안':'해당 음성unit 안에서 앞뒤 의미절과 병합; 원문/음성/전체타임록 유지','owner':'editor_v6','status':'open','checked_revision':a['final_sha256']}
wr(q/'findings.json',[finding])
r={'status':'pending_local_revision','checked_revision':a['final_sha256'],'file':'outputs/production-v7-preview/changneung_full_v7_preview.mp4','bytes':49349844,'script_sha256':p['script_sha256'],'approval_decision':'2f76a375b4a4','required_unresolved':['QAV7-P01'],'critical_open':[],
 'technical_independent':{'command':'ffprobe -v error -count_frames -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels,nb_read_frames -show_entries format=duration,size -of json final.mp4','exit_code':0,'stderr':'','video_frames':31426,'audio_frames':49104,'duration_s':1047.533333,'video':'H264 1920x1080 30fps','audio':'AAC 48000Hz 2ch','sha_match':True},
 'coverage':{'all_scenes':['M000','M001','M002','M003','M004','M007','M006','M005','M009'],'cut_samples':228,'motion_samples':205,'boundary_samples':39,'total_supplied_actual_samples':472,'contact_sheets_viewed':31,'mobile512_viewed':20,'independently_extracted_full_png':[24722,31058,31125,31126],'continuous_human_playback':False,'actual_listening':False,'audio_phoneme_accuracy':'unchecked','subtitle_inside_unit_actual_speech_alignment':'unchecked; measured PCM unit boundaries with text-weight internal estimates'},
 'timing_checks':{'measured_pcm_units':143,'caption_cues':219,'unit_max_rounding_error_s':a['max_rounding_error_s'],'caption_text_complete':True,'caption_bounds_contiguous':True,'numeric_date_unit_split_suspects':[],'visual_timeline_contiguous':True,'chapter_cards':6,'each_chapter_duration_frames':90,'raw_narration_last_signal_over_minus60_s':1011.5334693877551,'inserted_intro_and_cards_s':23,'final_signal_end_s':1034.5334693877551,'outro_start_s':1037.5333333333333,'signal_to_outro_s':2.999863945578227,'signal_method':'WAV int16 amplitude>-60dBFS; PCM threshold result, not actual listening'},
 'scene_evidence':[
  {'scene':'M000','sheets':'cut01/motion01/boundary01','checked':'가격성장성 질문·전편자료·브랜드 삽입 clean; 본문흰박스/출처분리'},
  {'scene':'M001','sheets':'cut01–02/motion01–02','checked':'운영역과 계획영역 구분, S5→S4→S1 강조 일치. 단독공원 큐만 필수수정'},
  {'scene':'M002','sheets':'cut02–04','checked':'01 독립카드, 15분값/대표좌표·현재Google예상조건, 목적지별광화문/상암/여의도/LG/강남 강조'},
  {'scene':'M003','sheets':'cut04–05/motion02–05','checked':'02 교통카드/운영3·6호선/GTX2030 월미정·고양은평2031.12목표/입주예정 비교, 개인이사달력 없음'},
  {'scene':'M004','sheets':'cut06–07/motion05–06','checked':'03 가격카드/S5·S1·S4 공고기본가+확장·시점/타입조건·차액9700·8300만원/84AH 5층기본형867190000+확장6139000=873329000; 미래수익가설 구분'},
  {'scene':'M007','sheets':'cut07–09/motion06–08','checked':'04 비교카드/2026Q3 전용83이상85미만 5층이상 해제제외/중위값11.275·9.2·8.5·8.45·8.375·7.45 내림차순, n6·11·3·17·20·11/지도실제대표점과각설명단지 강조'},
  {'scene':'M006','sheets':'cut09–11/motion08–11','checked':'05 공급카드/S6별도430,비교3후보2277/생활수요·매매임대대안2분기선진행/전매발표일3년과거주의무개시일3년 별도·S3LH구조'},
  {'scene':'M005','sheets':'cut11–12/motion11–12/actual_f24722.png','checked':'06 생활시설카드/학교보조·S5초5유5 2028.03목표,S4초6유6 2030.03목표,S1초7유7미정/locator·확대 범위·계획표시·자막 날짜보호'},
  {'scene':'M009','sheets':'cut12–15/motion12–13/boundary03/actual_f31058·31125·31126','checked':'S4가격수준후보≠상승률최고/S5경쟁후보/S1관찰/원문사실과판단구분/단지초점·약3초무자막hold·clean outro'}],
 'verified_guides':['WORKFLOW.md','agents/video_qa.toml','guides/제작_기본가이드.md 최신2026-10-18','guides/사용자_피드백_이력.md 관련최신항목','guides/호출_효율_운영.md','config/video_call_policy.json'],
 'reuse':'qa/revision-v7 대본/대표시각팩의 동일 출처·집계·좌표근거 재사용. 새 본편타임록/실제encoded 출력은 별도 전범위 표본 확인',
 'limitations':['실제청취·연속인간재생 미실시; 발음/노이즈/단어급자막동기는 미검증','초 단위 seek 샘플은 경계에서 1f 반올림 가능, 타임록확인은 project 기준; 시청맥락에 영향있는새잘림/급컷 발견없음','모션205에는 의도적 정지상태도 포함. 선진행/확대/선택변화를 단계별 비교했으며 전표본동적이라고 주장하지 않음','512px 출처·원문표세부는 작음; 핵심값재표기와본문자막 확인','무료 Heami rate0 검토본, 최종 Jun 음성/길이 아님; 원문취득/권리·정정본 검증 한계는기존연구팩승계'],
 'external_paid_or_upload_performed':False}
wr(q/'final_review.json',r)
wr(q/'handoff.json',{'status':r['status'],'outputs':['qa/production-v7-preview/final_review.json','qa/production-v7-preview/findings.json','qa/production-v7-preview/timeline_audit.json'],'input_versions':{'video_sha256':a['final_sha256'],'script_sha256':p['script_sha256'],'narration':'preview-v7 / 143 measured PCM units'},'required_unresolved':['QAV7-P01'],'affected_scenes':['M001_005'],'next_owner':'editor_v6 local subtitle merge then QA local evidence + new full decode','actual_listening':False,'continuous_human_playback':False})
print('pending QAV7-P01; evidence and timeline audit recorded')
