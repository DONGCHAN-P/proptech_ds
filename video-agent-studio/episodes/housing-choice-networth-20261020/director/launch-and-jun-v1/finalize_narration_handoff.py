"""Formal local timing delivery after generation agent capacity interruption."""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
EP=HERE.parents[1]
OWN=EP/'narration/jun-production-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def rel(p):return p.relative_to(ROOT).as_posix()
ledger=read(OWN/'generation_ledger.json');timing=read(OWN/'final_timing.json');valid=read(OWN/'technical_validation.json')
assert ledger['status']=='all54_generated_measured_alignment_validated_not_listened'
assert len(ledger['requests'])==54 and all(r['status']=='complete' and r['charge_known'] for r in ledger['requests'])
assert len(set(r['response_headers']['request-id'] for r in ledger['requests']))==54
assert ledger['actual_credits']==sum(r['actual_credits'] for r in ledger['requests'])==3577
assert ledger['actual_credits']<=10739 and ledger['reserved_pending_credits']==0
assert ledger['automatic_retries']==ledger['topup_calls']==ledger['overage_calls']==0
assert valid['status']=='passed_technical_only_not_listened' and valid['final_timing_sha256']==sha(OWN/'final_timing.json')
assert valid['cues']==206 and valid['paragraphs']==54 and valid['saturated_samples']==0
files=['final_timing.json','technical_validation.json','body_mono.wav','display_spoken_mapping.json','alignment_padding.json','timing_delta.json','generation_ledger.json']
files += [f'chapter_{n:02}.wav' for n in range(1,11)]
outputs=[{'path':rel(OWN/name),'sha256':sha(OWN/name)} for name in files]
handoff={'task_id':'housing-choice-Jun-v1-narration','status':'completed_local_measurement_and_alignment_not_listened',
         'role':'video_narration; final local measurement transferred to director after agent capacity failure',
         'script_revision':'script-final-v6','script_sha256':timing['script_sha256'],
         'audio_revision':'jun-production-v1','outputs':outputs,'chapters':10,'paragraphs':54,'cues':206,
         'body_seconds':timing['body_seconds'],'actual_provider_header_credits':3577,'included_credit_cap':10739,
         'additional_cash_usd':0,'topup_calls':0,'overage_calls':0,'automatic_paid_retries':0,
         'voice':timing['voice'],'actual_listening':False,'continuous_playback':False,
         'technical_required_open':[],'independent_numeric_ASR_and_final_media_QA':'separate QA role in progress',
         'timing_basis':'actual decoded PCM + exact provider characters mapped to fixed206 display cues; no speedstretch',
         'changed_scene_ids':[f'C{n:02}' for n in range(1,11)],'next_owner':'video_editor',
         'transfer_record':rel(HERE/'narration_ownership_transfer.json'),'created_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
assert not (OWN/'handoff.json').exists()
save(OWN/'handoff.json',handoff)
save(HERE/'timing_lock.json',{'status':'locked_measured_Jun_body_for_editor','script_sha256':timing['script_sha256'],
     'final_timing':rel(OWN/'final_timing.json'),'final_timing_sha256':sha(OWN/'final_timing.json'),
     'narrator_handoff':rel(OWN/'handoff.json'),'narrator_handoff_sha256':sha(OWN/'handoff.json'),
     'body_seconds':timing['body_seconds'],'brand_and_final_film_offsets_owner':'video_editor',
     'actual_listening':False,'at_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
print(json.dumps({'narration_handoff':rel(OWN/'handoff.json'),'body_seconds':timing['body_seconds'],
                  'actual_credits':3577,'new_TTS_calls':0,'cues':206},ensure_ascii=False))
