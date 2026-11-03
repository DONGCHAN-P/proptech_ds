import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
Q=Path(__file__).resolve().parent;E=Q.parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def dump(n,d):(Q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=read(Q/'asr_review.json');t=read(Q/'timing_review.json');pre=read(Q/'text_precheck.json')
assert t['status']==pre['status']=='pass' and not t['failures'] and not a['confirmed_required_pronunciation_errors']
timing=E/'narration/jun-production-v1/final_timing.json';assert sha(timing)==t['timing']['sha256']==a['timing']['sha256']=='6336849ba8fd0e422a5f8a6140db9ff485226c7f8dad7a2951fae80b37638f95'
body=E/'narration/jun-production-v1/body_mono.wav';assert sha(body)==t['body']['sha256']
for r in a['evidence']:
 assert sha(Path(r['input']['path']))==r['input']['sha256'] and sha(Path(r['evidence']['path']))==r['evidence']['sha256']
numeric=[]
for pid in a['paragraphs']:
 evidence=[x for x in a['evidence'] if x['paragraph_id']==pid]
 numeric.append(dict(paragraph_id=pid,status='ASR_supports_approved_values_with_retained_cross_engine_disagreement' if pid=='C04P01' else 'reviewed_ASR_supporting_evidence_no_confirmed_numeric_error',engines=[x['engine'] for x in evidence],audio=evidence[0]['input'],evidence=[x['evidence'] for x in evidence]))
review=dict(role='video_qa',revision='jun-production-v1-audio-review',approved=True,status='pass_with_explicit_ASR_and_listening_limits',approval_scope='確定SHA Jun原音PCM・全206文字整列と固定本文・選択34文段のローカルASR補助検証のみ'.replace('確定SHA Jun原音PCM・全206文字整列と固定本文・選択34文段のローカルASR補助検証のみ','확정 SHA Jun 원본 PCM·전체206 문자정렬/고정본문 및 선택34문단의 로컬ASR 보조 검수. 실제 청취·자연스러움·최종 인코딩 믹스 승인은 포함하지 않음.'),checked_at=datetime.now(timezone.utc).isoformat(),required_issues=[],critical_issues=[],recommended_issues=[a['retained_recognition_disagreement']],script_sha256=t['script_sha256'],audio_revision='jun-production-v1',audio_sha256=sha(body),body_audio=pin(body),timing_sha256=sha(timing),final_timing=pin(timing),chapter_audio=[dict(chapter=c['chapter'],**c['audio']) for c in t['chapters']],raw_paragraph_audio=[dict(paragraph_id=p['paragraph_id'],**p['audio']) for p in t['paragraphs']],sampled_ids=a['paragraphs'],sampled_paragraphs=34,ASR_engines=[dict(name='faster-whisper-small',runs=34),dict(name='faster-whisper-medium',runs=6),dict(name='Vosk-small-ko-0.22',runs=7)],ASR_runs=47,ASR_unique_input_seconds=a['unique_audio_seconds'],numericchecks=numeric,source_pronunciation_substitutions=171,all_source_numeric_mapping_values_preserved=True,all206_cue_text_segmentation_and_native_bounds_preserved=True,all54_rawPCM_retained_without_clipping=True,alignment_overhang_handled='원본 공급자 시각 유지. ~80ms 정렬 초과는 장 결합의 명시적 무음으로만 확보; 원발화 절삭·속도조정 없음.',credits_not_a_quality_evidence=True,first_ASR_receipts_preserved=True,expected_grammars_or_hotwords=False,new_downloads=0,paid_ASR_calls=0,evidencepaths=[pin(Q/'asr_review.json'),pin(Q/'timing_review.json'),pin(Q/'text_precheck.json')],actual_listening=False,continuous_playback=False,actual_number_pronunciation_verified_by_listening=False,speech_naturalness='unchecked',final_encoded_audio_mix_verified=False,coverage=dict(raw_PCM_all54_paragraphs_and_10chapter_concatenation=True,native_cues_checked=206,independent_timing_checks=791,independent_text_checks=933,ASR_full_54_paragraph_transcription=False,ASR_inputs_all_samples_processed=True),remaining='최종 MP4 전체AV decode·믹스 신호·인코딩 프레임과 최종 SHA 별도 검수 필요. C04P01 202만원의 Whisper220/Vosk202 차이는 비차단 ASR 불일치로 보존하며 청취 확인으로 닫았다고 주장하지 않음.')
dump('audio_review.json',review)
h=read(Q/'handoff.json');h['audio_review']=pin(Q/'audio_review.json');h['status']='independent_audio_evidence_ready_final_MP4_QA_pending';dump('handoff.json',h)
print(json.dumps(dict(approved=review['approved'],required_issues=review['required_issues'],audio_sha256=review['audio_sha256'],timing_sha256=review['timing_sha256'],output=str(Q/'audio_review.json')),ensure_ascii=False))
