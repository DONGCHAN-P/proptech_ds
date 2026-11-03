import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
Q=Path(__file__).resolve().parent;E=Q.parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def dump(n,d):(Q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rows=[]
for p in sorted((Q/'asr').glob('*/*.json')):
 d=read(p);rows.append(dict(paragraph_id=d['paragraph_id'],engine=d['engine'],evidence=pin(p),input=d['audio'],decoded_seconds=d['decoded_seconds'],raw_transcript=d['raw_transcript']))
assert len([r for r in rows if r['engine']=='small'])==34
followups=[dict(paragraph_id=pid,first_small=next(r['evidence'] for r in rows if r['paragraph_id']==pid and r['engine']=='small'),medium=next(r['evidence'] for r in rows if r['paragraph_id']==pid and r['engine']=='medium'),assessment=note) for pid,note in [
 ('C02P02','small이 종료연도를2016으로 인식. medium은2016년2분기~2026년2분기·11.7/6.6/4.0%·두건/30단지를 승인문과 일치하게 인식. 실제청취 없이 ASR 오인식 후보로 구분.'),
 ('C03P04','small의106900만원 인식은 medium에서1억6900만원으로 일치. 원본·첫 ASR 보존.'),
 ('C07P01','small의1억6100만원·일부 금액 끝 누락은 medium에서1억6700/2억8400/6억1400만원으로 일치.'),
 ('C08P04','small의세부백만원단위 누락은 medium에서5억6200/5억3600만원으로 일치.'),
 ('C08P05','small의투자0.8%는 medium에서연8%로 일치.')]]
amb=dict(paragraph_id='C04P01',raw_paragraph_interval_s=[22.72,23.94],approved_display='202만원',approved_spoken='이백이만 원',small_recognition='220만 원',medium_recognition='220만원',independent_Vosk_recognition='[2] 백 [2] 만원',Vosk_no_grammar=True,evidence=[r['evidence'] for r in rows if r['paragraph_id']=='C04P01'],assessment='Whisper 두 크기의 공통 숫자 정규화 불일치. 다른 계열 Vosk가202만원을 지지하여 실제 발음 오류로 확정하지 않음. 실제청취는 미확인으로 유지하며 최종 청취 때 우선 확인 권장. 자동 유료 재생성 근거로 쓰지 않음.')
result=dict(status='selected_critical_actual_Jun_ASR_complete_with_recorded_disagreement',checked_at=datetime.now(timezone.utc).isoformat(),script_sha256='0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7',timing=pin(E/'narration/jun-production-v1/final_timing.json'),paragraphs=sorted({r['paragraph_id'] for r in rows}),unique_paragraphs=34,total_native_recognizer_runs=len(rows),model_counts={k:sum(r['engine']==k for r in rows) for k in ['small','medium','vosk']},unique_audio_seconds=sum(next(r['decoded_seconds'] for r in rows if r['paragraph_id']==pid) for pid in {r['paragraph_id'] for r in rows}),property_reference='C01P04 지난 교산편 ASR 일치; 새 특정 단지/지역 조사 없음',numeric_scope='초기자금·대출·보증금·월예산·원리금·환율1.1/1.21/21%·연월복리0.5/6%·기간/표본/지역상승률·기본/민감도/절반투자금액·다음편연결',followup_review=followups,retained_recognition_disagreement=amb,confirmed_required_pronunciation_errors=[],evidence=rows,reference_or_expected_grammar_or_hotword_supplied=False,paid_calls=0,downloads=0,actual_listening=False,continuous_playback=False,overall_audio_naturalness_approved=False,interpretation='표본 실제PCM의 ASR보조 검토만. 54문단 전체 전사나 인간의 발음·속도·자연스러움 판정 아님. 원본 녹음/모든 첫 ASR 그대로 보존.')
dump('asr_review.json',result)
f=read(Q/'findings.json');r={'issue_id':'JQA-ASR-REC-001','scene_id':'C04P01','timecode':{'raw_paragraph_s':[22.72,23.94]},'severity':'recommended','문제':'202만원에 대한 ASR간 인식 불일치. 실제 핵심수치 발음 오류는 확정되지 않았고 청취는 미확인.','evidence':amb,'수정안':'실제 최종 청취가 가능해지면 해당 구간을 우선 확인. 원본·수치·대본·첫 ASR 보존; 현 근거만으로 재생성하지 않음.','owner':'video_director / video_narration','status':'open_nonblocking_ASR_disagreement','checked_revision':'jun-production-v1 / '+next(x['input']['sha256'] for x in rows if x['paragraph_id']=='C04P01')}
f['findings']=[x for x in f['findings'] if x['issue_id']!='JQA-ASR-REC-001']+[r];f['pending_checks']=['final source/encoded MP4 scene/transition/max-zoom samples','full AV decode and signal','final selected TH003 metadata and release hashes'];dump('findings.json',f);dump('issue_JQA-ASR-REC-001.json',r)
h=read(Q/'handoff.json');h.update(status='actual_Jun_timing_and_selected_ASR_ready_final_MP4_pending',outputs=h['outputs']+[str(Q/'timing_review.json'),str(Q/'asr_review.json')],validation='54문단/206큐/171발음치환 933체크 및 실제PCM·정렬791체크 통과. 실제Jun34문단47회 로컬ASR. 202만원은Whisper220/Vosk202 인식 불일치보존. 실제청취false.',unresolved=['최종MP4/인코딩프레임/전체decode·신호대기','실제청취·연속재생unchecked','202만원 ASR 불일치 비차단 권장사항'],selected_thumbnail='TH003',next_owner='video_director / video_editor → video_qa')
dump('handoff.json',h)
review=read(Q/'final_review.json');review['status']='actual_timing_ASR_pass_with_limitations_final_MP4_pending';review['coverage'].update(actual_Jun_ASR_unique_paragraphs=34,actual_Jun_ASR_runs=len(rows),timing_native_cues_checked=206,PCM54_paragraphs_and_10_chapters_checked=True);review['narration_timing_sha256']=result['timing']['sha256'];review['pending_inputs']=['actual encoded final MP4/frame evidence/full decode; metadata files now available not yet bound'];dump('final_review.json',review)
print(json.dumps({k:result[k] for k in ['status','unique_paragraphs','total_native_recognizer_runs','model_counts','unique_audio_seconds']},ensure_ascii=False))
