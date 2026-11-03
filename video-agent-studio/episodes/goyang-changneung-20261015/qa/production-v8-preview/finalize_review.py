import json,hashlib,re,wave
from pathlib import Path
import numpy as np
q=Path(__file__).parent;ep=q.parents[1];out=ep/'outputs/production-v8-preview'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def norm(t):return re.sub(r'[^가-힣a-zA-Z0-9]','',t)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=rd(q/'timeline_audit.json');p=rd(out/'project_v8.json');n=rd(ep/'writer/revision-v8/narration_packet.json');seg=rd(ep/'narration/preview-v8/segments.json');m=rd(ep/'editor/production-v8-preview/semantic_mapping.json');e=rd(out/'evidence_manifest.json')
assert a['errors']==[] and a['numeric_date_unit_split_suspects']==[] and not a['caption_under_1s']
assert norm(''.join(x['text'] for x in n['scenes']))==norm(''.join(x['text'] for x in seg))
srt=(out/'changneung_v8_preview.srt').read_text(encoding='utf-8-sig').strip().split('\n\n')
assert len(srt)==len(p['captions'])==213
for x,c in zip(srt,p['captions']):assert norm(''.join(x.splitlines()[2:]))==norm(c['text'])
mapped=[x for x in p['visual_intervals'] if x.get('props',{}).get('mode')=='mapped']
ids=sorted({x['props']['replacementId'] for x in mapped})
assert len(ids)==13 and all(x.get('props',{}).get('mode')!='note' for x in p['visual_intervals'])
mapping_checks=[]
for uid,entry in m['new_unit_replacements'].items():
 actual=[x for x in p['visual_intervals'] if x['unit_id']==uid]
 assert actual and all(x['props'].get('replacementId')==entry['replacement_id'] for x in actual)
 mapping_checks.append({'unit_id':uid,'replacement_id':entry['replacement_id'],'frames':[[x['start_frame'],x['end_frame']] for x in actual]})
assert len(mapping_checks)==25 and m['source_intervals_covered']==37
cards=[x for x in p['visual_intervals'] if x['kind']=='chapter'];assert len(cards)==6 and all(x['duration_frames']==90 for x in cards)
with wave.open(str(out/'audio/narration_v8_preview.wav')) as w:
 rate=w.getframerate();channels=w.getnchannels();pcm=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).reshape(-1,channels)
signal=np.flatnonzero(np.max(np.abs(pcm.astype(np.int32)),axis=1)>32768*10**(-60/20))[-1]/rate
last=p['audio_units'][-1]
with wave.open(last['audio_path']) as lw:
 lr=lw.getframerate();lp=np.frombuffer(lw.readframes(lw.getnframes()),dtype=np.int16).astype(np.int32)
signal_final=last['start_frame']/30+np.flatnonzero(np.abs(lp)>32768*10**(-60/20))[-1]/lr
coverage={'scene_order':a['scene_order'],'cuts':len(e['cuts']),'motion_and_controls':len(e['motions']),'boundaries':len(e['boundaries']),'actual_encoded_sample_total':len(e['cuts'])+len(e['motions'])+len(e['boundaries']),'contact_sheets_viewed':35,'mobile512_actual_samples_viewed':32,'actual_listening':False,'continuous_human_playback':False,'inside_unit_actual_word_alignment':False}
report={'status':'passed_with_limits','checked_revision':a['final_sha256'],'file':'outputs/production-v8-preview/changneung_full_v8_preview.mp4','bytes':(out/'changneung_full_v8_preview.mp4').stat().st_size,'script_sha256':p['script_sha256'],'approval_decision':'7d9fc3575dff','required_unresolved':[],'critical_open':[],'coverage':coverage,'technical_independent':{'exit_code':0,'stderr':'','method':'local ffprobe count_frames complete video/audio decode','video_frames':31790,'audio_frames':49672,'duration_s':1059.666667,'video':'H264 1920x1080 30fps','audio':'AAC 48000Hz 2ch','sha_match':True},'timing':{'measured_pcm_units':143,'caption_cues':213,'minimum_caption_s':a['minimum_caption_s'],'subsecond_captions':0,'numeric_date_currency_code_split_suspects':[],'max_pcm_frame_rounding_error_s':a['max_rounding_error_s'],'script_packet_segments_captions_srt_normalized_text_match':True,'visual_timeline_contiguous':True,'chapter_cards':cards,'raw_pcm_last_signal_minus60_s':float(signal),'inserted_brand_and_cards_s':23,'final_pcm_signal_s':float(signal_final),'outro_start_s':p['outro_start']/30,'gap_signal_to_outro_s':p['outro_start']/30-float(signal_final),'signal_not_listening':True},'replacement_verification':{'source_note_intervals_covered':37,'new_semantic_narration_units':24,'plus_last_hold':True,'mapped_visual_intervals':len(mapped),'replacement_ids':ids,'large_text_note_fallback':0,'unit_mapping_independently_compared':mapping_checks},'visual_results':[
 'M000 candidate_question: 실제3후보계획면과확인공고가,전편자료,clean5초intro; 질문을임의미래가격으로확정하지않음(cut01)',
 'M001 전체지도/주거상업공원일자리한큐·S5→S4→S1강조 일치(cut01–02/motion01–02)',
 'M002 현재대표좌표·조회08:00/대기6+경로88=94분/15통근값·목적지절별강조 및 실제출입구아님(cut02–04/motion02–03)',
 'M003 운영3·6호선/입주3예정/GTX2030월미정/고양은평2031.12목표; rail_entry_evidence·가격기대/취득부담분리실구현(cut04–05/motion03–06)',
 'M004 기본원문867190000+확장6139000=873329000/시점타입층·옵션세금별도/정확차이82949000≈8300만원/입지차익단정없음; 5가격관련대체원문지도실구현(cut05–07/motion06–09)',
 'M007 2026Q3·83이상85미만·5층이상·해제제외,6중위값내림차순11.275/9.2/8.5/8.45/8.375/7.45와거래6/11/3/17/20/11,실제대표점·단지별초점(cut07–09/motion10–12)',
 'M006 S6별도430/3후보2277부분합,생활수요·매매임대대안2branch선진행/각기산사건3년·S3LH구조(cut09–11/motion12–15)',
 'M005 실제S4상업/초6유6/공원필지강조·학교보조, 학교3곳locator/목표미정 구분·날짜단위보호(cut11–12/motion15–16)',
 'M009 S4가격수준후보≠상승률/S5경쟁/S1관찰,원문사실과해석구분·시리즈CTA실제창릉자료/교산임의지도없음(cut12–14/motion16–18)',
 '6AI개념챕터01~06/각90f,실제창릉아님표시/본문근거지도역할분리,전후경계·본문흰박스·하단출처/brand·무자막hold박스없음(boundary01–03)',
 '모든실제표본에서새겹침·잘림·단위분리·맥락오인필수결함없음. 32모바일에서핵심숫자/본문자막/제목읽힘'
 ],'limits':['실제청취·연속인간재생미실시. 핵심수치발음/음질/단어급동기미검증','PCMunit경계는실측,내부자막·초점은텍스트가중추정으로forcedalignment아님','표본프레임은전프레임시각검수가아님; 모션표본에의도적정지control포함.초단위seek경계1f반올림가능','512px에서출처/원문세부표시는작고핵심값을재표기해확인','무료Heami rate0검토본이며Jun최종음성아님. 불변가격/좌표/공식원문근거는v7/v8대표QA승계; 새외부전수조사없음'],'guide_refs':['WORKFLOW.md','agents/video_qa.toml','guides/제작_기본가이드.md','guides/사용자_피드백_이력.md','guides/호출_효율_운영.md','config/video_call_policy.json'],'paid_api_or_upload_performed_by_qa':False}
assert report['checked_revision']=='5131dbfe48a203ffa13d3ca9104c23baf9d53038880b8b99b4f4266eb39567c8'
wr(q/'findings.json',[]);wr(q/'final_review.json',report)
wr(q/'handoff.json',{'status':'passed_with_limits','outputs':['qa/production-v8-preview/final_review.json','qa/production-v8-preview/findings.json','qa/production-v8-preview/timeline_audit.json'],'input_versions':{'video_sha256':report['checked_revision'],'script_sha256':p['script_sha256'],'audio_revision':'preview-v8 / 143 measured PCM units'},'required_unresolved':[],'actual_listening':False,'continuous_human_playback':False,'next_owner':'director completed review gate; upload not authorized'})
print(json.dumps({'status':report['status'],'required_unresolved':[],'sha256':report['checked_revision'],'replacement_ids':len(ids),'caption_count':213,'signal_gap_s':report['timing']['gap_signal_to_outro_s']},ensure_ascii=False))
