"""Package observed ASR/native evidence and explicit human follow-up needs.

The dispositions below are a review of the saved transcripts, not listening.
No audio or source content is changed.
"""
import sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
from prepare import EP,ROOT,read,pin,dump,sha
from checks import numbers
from run_asr import gate

def main():
    cfg=read(QA/'config.json');g=gate(cfg)
    small={};medium={};cues={}
    for p in sorted((QA/'runs').glob('ch*-small-*/report.json')):
        d=read(p)
        for c in d['comparisons']:small[c['scene_id']]={'report':pin(p),'chapter':d['chapter'],**c}
    for p in sorted((QA/'runs').glob('ch*-medium-*/*/comparison.json')):
        d=read(p);medium[d['scene_id']]={'report':pin(p),**d}
    for p in sorted((QA/'cue_rechecks').glob('*/review.json')):
        d=read(p);cues[d['cue_id']]={'report':pin(p),**d}
    assert len(small)==45 and len(medium)==19 and len(cues)==8
    ready=read(QA/'readiness.json');progress=read(QA/'progress.json')
    assert progress['chapters_completed']==10
    for c in ready['chapters']:
        for key in ['audio','chapter_json']:assert sha(Path(c[key]['path']))==c[key]['sha256']
    classifications={
        'S003':('closed_small_ASR_discrepancy','Medium recovers 6억원 and the exact date.'),
        'S012':('closed_small_ASR_spelling','Medium recovers both DTI occurrences and 40/60 percent.'),
        'S014':('required_numeric_and_acronym_verification','5억103만원 versus repeated 5억130만원; DSR also degraded. No listening confirmation.'),
        'S018':('closed_low_text_score','All money/rates agree in both models; mixed numeral representations depress character similarity. Remaining spellings are not confirmed speech errors.'),
        'S019':('required_numeric_verification','4902만원 remains ambiguous; short-cue decoding also invents amount-unit normalizations. Use full-paragraph evidence, not majority voting.'),
        'S022':('closed_small_numeric_discrepancies','Medium recovers 3억9074만원 and 2574만원.'),
        'S024':('required_numeric_verification','Medium recovers 5억103만원 here but both paragraph passes render 10억2902만원 as 10억2900만원. Short cue renders 2900위만; unresolved numeral spelling.'),
        'S027':('closed_small_numeric_discrepancy','Medium recovers 5억1100만원. All protected numeric values agree. 신원/신혼 spelling remains an unconfirmed orthographic observation.'),
        'S028':('closed_small_coreterm_spelling','Medium recovers 보금자리론 occurrences and all values.'),
        'S030':('required_acronym_verification','DSR becomes 대살 across small, medium paragraph and medium cue. DTI is recovered in paragraph medium.'),
        'S031':('closed_ASR_unit_and_spelling','Medium cue recovers 1개월 and 6개월. 보금자리론은/보금자리로는 is a connected-speech orthography alternative, not proof of missing speech.'),
        'S032':('closed_numeric_checks_orthographic_observation','All newborn individual/combined income, age and date values agree. 디딤돌을/디딤도를 is a connected-speech orthographic alternative; no listening error established.'),
        'S033':('closed_small_numeric_discrepancy','Medium recovers 3억9074만원.'),
        'S034':('closed_small_numeric_discrepancy','Medium recovers 3.65 percent; 2.9 percent,162.6만원,0.75 percentage point and dates agree.'),
        'S034R':('closed_small_numeric_discrepancies','Medium recovers 3억4676만원 and176.4만원, with60payments/remaining300months preserved.'),
        'S035':('closed_low_text_score','All numeric values and meaning of conditional loan ceiling remain in medium; low raw similarity reflects number formats.'),
        'S036':('closed_ASR_unit_spelling','Medium cue recovers1개월; other values agree.'),
        'S037':('closed_small_numeric_discrepancy','Medium recovers6억8019만원.'),
        'S040':('closed_low_text_score','Medium retains same initial principal/new360months and all 4-to-6 percent payment/savings figures.'),
    }
    rows=[]
    for sid,s in small.items():
        m=medium.get(sid);status,note=classifications.get(sid,('no_automatic_numeric_coreterm_discrepancy','Full small paragraph comparison; no model discrepancy in extracted numeric/core terms. This is not listening approval.'))
        rows.append({'scene_id':sid,'chapter':s['chapter'],'status':status,'review_note':note,'expected_display':s['expected_display'],'expected_spoken':s['expected_spoken'],'small_transcript':s['transcript'],'small_numbers':s['recognized_numbers'],'small_numeric_differences':s['numeric_differences'],'small_coreterm_differences':s['coreterm_differences'],'small_report':s['report'],'medium_transcript':m['medium_transcript'] if m else None,'medium_numbers':m['medium_comparison']['recognized_numbers'] if m else None,'medium_numeric_differences':m['medium_comparison']['numeric_differences'] if m else None,'medium_coreterm_differences':m['medium_comparison']['coreterm_differences'] if m else None,'medium_report':m['report'] if m else None,'cue_rechecks':[c['report'] for c in cues.values() if c['scene_id']==sid]})
    dump(QA/'two_model_comparison.json',{'script_sha256':cfg['script_sha256'],'currency':'KRW','rows':rows,'actual_listening':False,'reference_used_as_prompt_or_hotwords':False})

    numcases=[]
    for sid,cid,label,expected,smallvalue,mediumvalue in [
        ('S014','C04_S014Q003','DSR 대출 한도',501030000,501300000,501300000),
        ('S019','C05_S019Q003','12억원 집 거래비용',49020000,None,49200000),
        ('S024','C06_S024Q004','12억원 집 필요 대출',1029020000,1029000000,1029000000),
    ]:
        s,m,c=small[sid],medium[sid],cues[cid]
        numcases.append({'scene_id':sid,'cue_id':cid,'chapter':s['chapter'],'start_s':c['native_cue']['start_s'],'end_s':c['native_cue']['end_s'],'label':label,'expected_display':c['native_cue']['text'],'expected_value_krw':expected,'small_unambiguous_value_krw':smallvalue,'medium_paragraph_value_krw':mediumvalue,'small_transcript':s['transcript'],'medium_paragraph_transcript':m['medium_transcript'],'medium_cue_transcript':c['medium_transcript'],'audio_sha256':c['source_audio']['sha256'],'evidence':[s['report'],m['report'],c['report']],'actual_listening_error_confirmed':False})
    numcases[1]['small_surface_note']='Raw4,900 이만 원 is mixed-script ambiguous notation. The heuristic parser overwrites adjacent numeral pieces and reports20000; that parser value is invalid evidence for an actual spoken amount. Cue-only decoder additionally scales3615만원 to3615000원 despite both paragraph passes retaining3615만원. Do not escalate that new cue-only unit hallucination as an audio error.'
    required=[
        {'id':'ASR-A2-NUM-001','severity':'required','status':'unresolved_automatic_evidence_requires_pronunciation_verification','title':'금액 3곳의 실제 발음 확인 필요','evidence':numcases,'revision':'청취 가능한 담당자가 정확한 기존 WAV의 세 큐를 원문과 대조해 확인 기록을 남긴다. ASR 두 모델은 계열이 같아 일치 오인식도 가능하다. 현재 오류 확정이나 자동 통과 판정은 하지 않는다.','fix':'명료한 원문 발음이 확인되면 해당 청취 근거로 종결할 수 있다. 불명료가 확인되면 총괄·narrator가 원문 숫자를 유지하여 낭독층만 보완하고 변경 오디오 SHA에 한정해 재검증한다. QA는 TTS나 원문을 변경하지 않는다.'},
        {'id':'ASR-A2-TERM-001','severity':'required','status':'unresolved_core_acronym_evidence','title':'DSR 두 큐의 식별 가능성 확인 필요','evidence':[{'cue_id':cid,'scene_id':cues[cid]['scene_id'],'chapter':cues[cid]['chapter'],'start_s':cues[cid]['native_cue']['start_s'],'end_s':cues[cid]['native_cue']['end_s'],'expected':cues[cid]['native_cue']['spoken_text'],'small':small[cues[cid]['scene_id']]['transcript'],'medium_paragraph':medium[cues[cid]['scene_id']]['medium_transcript'],'medium_cue':cues[cid]['medium_transcript'],'report':cues[cid]['report'],'actual_listening_error_confirmed':False} for cid in ['C04_S014Q003','C07_S030Q004']],'revision':'S014의 D설상, S030의 대살·디타이 전사를 실제 핵심 약어 발음과 대조한다. DTI 문단 전사는 medium에서 회복되므로 DTI 전체를 오류로 확대하지 않는다.','fix':'해당 DSR 두 큐만 청취 가능한 담당자에게 반환한다. 명료성 확인 근거 또는 승인된 낭독층 보완 후 해당 SHA 전사 근거로 종결하며, 다른 문단은 재생성하지 않는다.'},
    ]
    reportpaths=[Path(r['report']['path']) for r in progress['reports']]
    reports=[read(p) for p in reportpaths]
    focuses=[
        ('A cash/reserve/purchase fund',['S004','S005']),
        ('A LTV40/70/enduser60; DSR40;DTI40/60',['S008','S011','S012']),
        ('A actual4/stress7/30years and3percentage point',['S013']),
        ('fees1074/3615/4902만원',['S019']),
        ('required390740000KRW',['S021','S022','S027','S033']),
        ('DSR rounded5억103만원',['S014','S024']),
        ('B income80000000/assets250000000;individual130000000 AND combined200000000;ageunder2',['S026','S032']),
        ('B product ceilings320000000/420000000/400000000',['S027','S028','S033']),
        ('B reset162.6->176.4만원,2.9/3.65percent,.75percentage point,60payments,balance3억4676만원,remaining300',['S034','S034R']),
        ('A price680190000vs565860000;monthly300=170+100+30',['S037','S038','S039']),
        ('A same initial principal/new360 at4vs6percent',['S040']),
    ]
    dump(QA/'core_checks.json',{'currency':'KRW','authority':'Pinned writer display/reading and protected numeric ledger; no new financial or policy calculation','checks':[{'focus':label,'scene_ids':ids,'results':[next(r for r in rows if r['scene_id']==sid) for sid in ids]} for label,ids in focuses],'actual_listening':False})
    ownfiles=['checks.py','prepare.py','run_asr.py','run_targeted_medium.py','recheck_cues.py','build_review.py','test_checks.py','tests.json','config.json','expected.json','preparation_proof.json','readiness.json','progress.json','two_model_comparison.json','core_checks.json','README.md']
    finaltiming=EP/'narration/production-injoon-v2/final_timing.json'
    assert sha(finaltiming)=='67d7e97351b9a6b9ef4ae71410cfab798d1ab120b792ff924ccc3c11051c16a4'
    review={'task':'affordable-home-price offline local ASR actual narration v2','at_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':cfg['script_sha256'],'final_timing':pin(finaltiming),'approved':False,'approval_scope':'ASR numeric/core-term evidence closure; not actual listening, naturalness, visuals or final media','critical_issues':[],'required_issues':required,'recommended_issues':[],'confirmed_audio_pronunciation_errors':0,'two_model_comparison':pin(QA/'two_model_comparison.json'),'core_checks':pin(QA/'core_checks.json'),'gate':g,'coverage':{'episode_id':EP.name,'actual_chapters_small_ASR':10,'actual_scene_paragraphs_compared':45,'actual_input_PCM_seconds':sum(c['total_seconds'] for c in ready['chapters']),'actual_ASR_decoded_seconds':sum(d['ASR_input_seconds'] for d in reports),'resampling_duration_delta_s':sum(d['ASR_input_seconds'] for d in reports)-sum(c['total_seconds'] for c in ready['chapters']),'native_words':1633,'meaning_cues':150,'protected_source_occurrences':187,'protected_source_coverage_basis':'Exact writer spans, display/spoken numeric parity, native words, cue source spans and chapter PCM byte conservation. Not187 independently heard pronunciations.','small_full_chapter_no_VAD':True,'targeted_medium_paragraphs':19,'additional_medium_native_cue_contexts':8,'full_episode_medium_run':False,'actual_audio_SHA_before_and_after_verified':True,'native_boundaries_source_and_PCM_verified':True,'source_audio_modified':False,'old_episode_audio_or_transcripts_reused':False,'actual_listening':False,'continuous_playback':False,'audio_naturalness_approved':False,'BGM_or_final_mix_checked':False,'source_visual_or_encoded_video_checked':False,'external_audio_transmission':False,'network_ASR_calls':0,'paid_calls':0,'new_packages_or_weights_downloaded':False},'DSP':{'scope':'All10chapter PCM full sample arrays; not final BGM mix','sample_rate':24000,'channels':1,'sample_bits':16,'maximum_sample_peak':max(d['DSP']['sample_peak'] for d in reports),'clipped_samples':sum(d['DSP']['clipped_samples'] for d in reports),'final_chapter_tail_from_max_native_and_PCM_s':ready['chapters'][-1]['tail_from_last_spoken_s']},'limitations':['ASR is not listening; common model family and decoding contexts can share mistakes.','Raw character similarity changes when spoken Korean numerals become Arabic notation.','Word timestamps can place a word outside its paragraph. C10 다음 exists in the raw full segment; its per-paragraph omission is an assignment artifact, not a confirmed missing word.','Numeric extraction is heuristic, not a Korean morphological parser. It can misparse mixed-script values and ordinary 이사 일정 as a number; curated protected ledger spans and exact source remain authoritative.','A short cue can hallucinate units even with0.4s context; retain all raw outputs and prefer full paragraph evidence when judging the need for verification.','Source/native conservation and no waveform clipping do not establish perceived naturalness or intelligibility.'],'model_runtime':{'requested':'cpu/int8','actual':'int8_float32','versions':reports[0]['versions'],'models':cfg['models'],'reference_used_as_prompt_or_hotwords':False,'initial_prompt':None,'hotwords':None},'evidence':{n:pin(QA/n) for n in ownfiles},'chapter_reports':[pin(p) for p in reportpaths],'medium_reports':[m['report'] for m in medium.values()],'cue_reports':[c['report'] for c in cues.values()]}
    dump(QA/'review.json',review)
    hand=read(QA/'handoff.json');hand.update(status='actual_small_complete_targeted_medium_complete_followup_required',audio_approved=False,approved=False,required_issues=[{'id':x['id'],'title':x['title'],'evidence':str(QA/'review.json'),'revision':x['revision'],'fix':x['fix']} for x in required],critical_issues=[],completed_small_chapters=10,completed_medium_paragraphs=19,completed_medium_cue_contexts=8,review=pin(QA/'review.json'),comparison=pin(QA/'two_model_comparison.json'),core_checks=pin(QA/'core_checks.json'),note='Preparation passed. ASR evidence remains unclosed for3amounts and2DSR cues. No listening error confirmed; no TTS/source/audio changes performed.',at_utc=datetime.now(timezone.utc).isoformat())
    dump(QA/'handoff.json',hand)
    print({'review':str(QA/'review.json'),'approved':False,'critical':0,'required':len(required),'small_chapters':10,'medium_paragraphs':19,'medium_cues':8})
if __name__=='__main__':main()
