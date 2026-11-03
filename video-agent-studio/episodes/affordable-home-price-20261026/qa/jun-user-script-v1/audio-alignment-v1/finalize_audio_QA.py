"""현재 단계의 음성/정렬 QA 보고서만 작성한다. 이전 QA는 변경하지 않는다."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
OWN=Path(__file__).resolve().parent
EP=OWN.parents[2]
ROOT=EP.parents[2]
N=EP/'narration/jun-user-script-v1'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
put=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=read(OWN/'alignment_evidence.json');s=read(OWN/'ASR_evidence.json')
assert a['failed_checks']==s['failed_checks']==[]
refs={x['path']:x for x in a['checked_file_hashes']+s['checked_file_hashes']}
for p in [N/'align_scenes.py',N/'asr_samples.py']:
    refs[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
for x in refs.values():assert sha(ROOT/x['path'])==x['sha256'],x['path']+' changed after evidence capture'
cue_map={c['cue_id']:c for c in a['captions']}
targets=[]
for target in s['possible_manual_listening_targets']:
    cue=cue_map[target['cue_id']]
    targets.append({**target,'timecode':{'basis':'원본 장 WAV 기준 제공자 문자 경계. 최종 MP4 타임코드 아님.','chapter_WAV':f'narration/jun-user-script-v1/paragraphs/{target["chapter"]}P01/audio.wav','source_chapter_start_s':cue['source_chapter_start_s'],'source_chapter_end_s':cue['source_chapter_end_s'],'scene_local_start_s':cue['scene_start_s'],'scene_local_end_s':cue['scene_end_s']},'provider_char_range':cue['provider_char_range']})
issue={
 'issue_id':'JUN-AUD-001','scene_id':['S21','S23'],'timecode':[t['timecode'] for t in targets],'severity':'recommended',
 '문제':'전체 MEDIUM ASR에서 비수치 핵심 용어 2곳의 표기 차이가 남아 있다. 실제 발음 오류·단어 누락으로 확정하지 않았으며 실제 청취는 미수행이다.',
 'evidence':{'ASR_receipt':rel(OWN/'ASR_evidence.json'),'targets':targets,'ASR_full_summary_sha256':refs[rel(N/'asr-full-medium/summary.json')]['sha256'],'numeric_context':'전체 7장119개 숫자 값·단위·순서 독립 대조 일치; 기존 SMALL의 숫자 차이는 MEDIUM에서 재현되지 않음.','confidence':'ASR 불확실성만 확인. 실제 청취에 의한 음성 결함 판단 아님.'},
 '수정안':{'owner_action':'제시된 원본 WAV 두 구간을 실제 청취할 수 있는 담당자가 확인한다. 원문대로 들리면 ASR 오인으로 닫고, 실제 용어 누락·변형이 들리면 해당 문장과 종속 정렬/자막/앵커만 수정 제안한다. 이 QA에서는 유료 재생성·외부 전송을 수행하지 않는다.','exact_expected_phrases':['일반과세 중개사의 부가세까지 가정하면 약 290만 원이고요.','그래서 내가 생애최초인지, 해당 지역과 주택에 어떤 규제가 적용되는지부터 확인해야 합니다.'],'gate':'권장 청취 확인이며 이번 정렬/수치 대조의 필수 실패로 판정하지 않음.'},
 'owner':'narration/director','status':'open_ASR_uncertainty_actual_listening_unchecked',
 'checked_revision':{'scene_alignment_sha256':refs[rel(N/'scene_alignment.json')]['sha256'],'asr_full_medium_summary_sha256':refs[rel(N/'asr-full-medium/summary.json')]['sha256']}}
put(OWN/'issue_JUN-AUD-001.json',issue)
input_versions={name:refs[rel(N/name)]['sha256'] for name in ['generation_input.json','narration_manifest.json','caption_plan.json','generation_ledger.json','scene_alignment.json','alignment_receipt.json','voice_signal.json','align_scenes.py','asr_samples.py','asr-full-medium/summary.json']}
findings={
 'task_id':'JUN-US1-ACTUAL-AUDIO-ALIGNMENT-QA','role':'qa','checked_at_utc':datetime.now(timezone.utc).isoformat(),
 'status':'scoped_audio_alignment_QA_pass_ASR_supported_actual_listening_unchecked',
 'summary':{'critical_open':0,'required_open':0,'recommended_ASR_uncertainty_open':1,'confirmed_material_missing_words_or_numbers':0,'full_episode_ASR_seconds':679.2,'actual_listening_seconds':0,'continuous_playback_seconds':0,'final_MP4_checked':False},
 'findings':[issue],
 'input_revisions':input_versions,
 'original_read_display_links':{'result':'pass','basis':'현재 generation_input/narration_manifest/caption_plan/scene_plan SHA가 이전 독립 입력 QA와 동일. 값/단위/말투/순서 보존 근거를 계승하고, 그 동일 읽기문이 실제 각 요청 receipt 및 제공자 characters 전체와 일치하는지 새로 확인.','source_doc_sha256':'f28deb75e0a271e30e3d29dbe52291ef30e28b0ef0bfc2648ad98bbd652e6a73','inherited_evidence':'qa/jun-user-script-v1/findings.json','source_policy_or_DOCX_survey_repeated':False},
 'request_and_PCM_checks':{'result':'pass','evidence':rel(OWN/'alignment_evidence.json'),'complete_requests':7,'receipt_artifacts_SHA_checked':28,'input_characters':5797,'actual_credits':2317,'authorized_cap':7000,'WAV_total_s':679.2,'WAV_total_samples':sum(x['pcm_samples'] for x in a['audio_rows']),'format':'PCM s16le mono 44100 Hz','clipped_samples':0,'DSP_scope':'실제 7개 raw WAV 샘플 레벨 peak/RMS/정수 full-scale 표본 검사. 최종 믹스·주관 음질·발음 검수 아님.','chapter_results':a['audio_rows']},
 'alignment_checks':{'result':'pass','independent_checks_passed':14,'scene_count':31,'paragraph_count':48,'caption_count':156,'beat_count':101,'evidence':rel(OWN/'alignment_evidence.json'),
   'scene_cut_coverage':'31개 소스 컷 범위가 7장 PCM의 샘플0..끝을 누락/중복 없이 덮음. 제공자 alnum 문자 구간이 컷을 가로지르거나 자기 장면 밖으로 나가지 않음.',
   'cut_truth_limit':'이는 소스 WAV+제공자 문자 배열상 검사. 실제로 렌더된 31개 컷 파일·최종 믹스의 단어/호흡 잘림은 미확인. 실제 청취나 파형만으로 단어 무결성을 확정한 검사가 아님.',
   'beats':'101개 원문 literal anchor의 실제 원문 위치를 읽기문 확장 범위로 연결하여 provider_char_start/end 및 시작/끝 시간을 전량 대조. 비례 시간 배분·예상 시간 사용 없음.',
   'captions':'156개 표시문/줄/원문 범위/순서를 승인된 caption_plan과 대조하고, 숫자/약어 확장 전체를 덮는 실제 제공자 문자 인덱스의 시간과 대조. 큐 중첩 없음.',
   'terminal_clamps':a['decoder_clamps'],'terminal_clamp_rule':'각 장 마지막 마침표 1개만 PCM 끝보다80ms 늦게 끝남. raw provider 배열 SHA/값은 보존되어 있고 파생 정렬에서 PCM 경계로 clamp. 숫자/단어 문자에는 적용되지 않음. 예상 발화시간으로 바꾼 것이 아님.',
   'last_spoken_end_semantics':'산출물 last_spoken_end_s는 제공자 배열의 마지막 alnum 문자 종료값이다. 실제 청취로 마지막 발화를 확인한 값이라는 뜻은 아님.'},
 'ASR_checks':{'result':'pass_with_ASR_word_uncertainty','evidence':rel(OWN/'ASR_evidence.json'),'source_hash_linked_full_chapters':7,'full_coverage_seconds':679.2,'cached_model':'MEDIUM','cached_model_sha256_declared':s['full_coverage']['model_declared_sha256'],'model_binary_rehashed':False,'cached_numeric_differences_each_chapter':{r['chapter']:r['numeric_differences_cached'] for r in s['chapters']},'independent_numeric_values_units_order':{'tokens':119,'equal':True,'chapter_counts':{r['chapter']:r['reference_number_count'] for r in s['chapters']}},'small_vs_medium':'既存SMALL4抜粋105秒の数字差とMEDIUM3抜粋93.88秒を同一PCMから比較。数字差はMEDIUMで再現せず、全7章MEDIUMも値一致。','cached_sample_PCM_checks':7,'unprompted_basis':s['full_coverage']['unprompted_configuration_basis'],'QA_new_ASR_runs':0,'actual_hearing_performed':False,'material_omission_conclusion':'ASR全体と原稿の差分から文/数字の明白な欠落は検出しなかった。実際の全発話を聴取確認した結論ではない。'},
 'coverage':{'source_audio_WAV_full_signal_and_sample_count':{'chapters':7,'seconds':679.2},'provider_character_arrays':{'chapters':7,'request_characters_with_separators':5797},'original_paragraph_arrays':48,'all_literal_beats':101,'all_caption_time_boundaries':156,'cached_full_ASR_read_and_compared':{'chapters':7,'seconds':679.2},'continuous_playback':'unchecked_not_performed','actual_listening':'unchecked_not_performed','naturalness_prosody':'unchecked_not_performed','final_scene_cut_audio_or_final_MP4':'unchecked_separate_phase','prototype_pixel_QA_repeated':False},
 'checked_file_hashes':list(refs.values()),
 'ownership':'qa/jun-user-script-v1/audio-alignment-v1/만 작성. 이전 QA·제작 파일·state/scenes/decisions 수정 없음.',
 'external_or_paid_actions':{'paid_calls_by_QA':0,'authenticated_requests_by_QA':0,'external_transmissions_by_QA':0,'new_ASR_by_QA':0},
 'next_role':'director/narration','next_actions':['권장 ASR 용어 두 구간을 실제 청취할 수 있는 담당자가 확인.','최종 MP4가 지정되면 별도 단계에서 실제 인코딩 장면·경계·음성 접합·자막을 검수. 이 패킷을 전체 영상 통과로 사용하지 않음.']}
findings['ASR_checks']['small_vs_medium']='기존 SMALL 4개 발췌105초의 숫자 차이와 MEDIUM 3개 발췌93.88초를 같은 소스 PCM에 연결해 확인. 숫자 차이는 MEDIUM에서 재현되지 않았고 전체7장 MEDIUM도 값이 일치함.'
findings['ASR_checks']['material_omission_conclusion']='ASR 전체와 원고의 차분에서 문장/숫자의 명백한 누락은 검출하지 못함. 실제 전체 발화를 청취 확인한 결론이 아님.'
put(OWN/'findings.json',findings)
handoff={
 'task_id':findings['task_id'],'role':'qa','status':'completed_bounded_audio_alignment_QA','input_revisions':input_versions,
 'outputs':[rel(OWN/name) for name in ['findings.json','alignment_evidence.json','ASR_evidence.json','issue_JUN-AUD-001.json']],
 'affected_scene_ids':[s['scene_id'] for s in a['scenes']],
 'checks':[{'check':'7요청/28artifact SHA 및 WAV679.2초/29952720샘플/클리핑0','result':'pass','evidence':rel(OWN/'alignment_evidence.json')},{'check':'31소스컷/48문단/156자막/101beat 제공자 인덱스·시간 전량','result':'pass_source_native_array_scope','evidence':rel(OWN/'alignment_evidence.json')},{'check':'7장679.2초 캐시 MEDIUM 및119개 숫자 독립 대조','result':'pass_ASR_support_only','evidence':rel(OWN/'ASR_evidence.json')},{'check':'실제 청취/연속 재생/최종31컷 음향/최종MP4','result':'unchecked','evidence':None}],
 'open_issue_ids':['JUN-AUD-001'],'required_open_issue_ids':[],
 'next_role':'director/narration','next_actions':findings['next_actions'],
 'summary':'독립14검사 통과. 7요청2317크레딧/679.2초 PCM·SHA·클리핑0, 31소스컷48문단156큐101앵커의 실제 제공자 배열 연결 확인. 장말 마침표만80ms clamp, raw 보존. 전체7장 MEDIUM679.2초 및119숫자 값/단위/순서 일치. 필수미해결0; ASR 용어2곳 청취 권장1건. 실제 청취/연속재생/최종컷·MP4 미수행. 제작·과거QA·상태 파일 수정 및 새 유료/인증/외부 요청 없음.',
 'authority':'제작 완료/청취/최종 영상 통과 승인 아님. 현재 작업은 읽기 전용 음성/정렬 QA이며 소유 QA 폴더만 작성.',
 'checked_file_hashes':{'reference':rel(OWN/'findings.json'),'count':len(refs)}}
put(OWN/'handoff.json',handoff)
# 기록된 새 산출물 자체도 실제 재열람하여 스키마·참조·상태 확인.
for name in ['findings.json','handoff.json','issue_JUN-AUD-001.json','alignment_evidence.json','ASR_evidence.json']:read(OWN/name)
required={'issue_id','scene_id','timecode','severity','문제','evidence','수정안','owner','status','checked_revision'}
assert all(required<=x.keys() for x in read(OWN/'findings.json')['findings'])
assert all((ROOT/p).is_file() for p in read(OWN/'handoff.json')['outputs'])
print(json.dumps({'summary':findings['summary'],'manual_targets':targets,'checked_hashes':len(refs),'findings_sha256':sha(OWN/'findings.json'),'handoff_sha256':sha(OWN/'handoff.json')},ensure_ascii=False))
