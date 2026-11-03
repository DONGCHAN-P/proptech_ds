from pathlib import Path
import json,hashlib,math
e=Path(__file__).resolve().parent.parent
m=json.loads((e/'writer/map-led-v4/narration_input/manifest.json').read_text(encoding='utf-8'))
base=e/'writer/map-led-v4'
total=0
for c in m['chapters']:
 data=(base/c['path']).read_bytes();text=data.decode('utf-8')
 assert hashlib.sha256(data).hexdigest()==c['sha256']
 assert len(text)==c['characters'];total+=len(text)
assert total==6879
pre=json.loads((e/'narration/preflight_v2.json').read_text(encoding='utf-8'))
reserve=math.ceil(total*.2)
b={'revision':'budget-v2-script-v4','script_revision':'script-v4-hook-outside','source_script_sha256':m['source_script_sha256'],'narration_manifest':'writer/map-led-v4/narration_input/manifest.json','voice':'Jun - Clear Korean Lecturer','voice_id':'4p6UA7mnodF5q7JFFrnW','model':'eleven_v4','chapter_count':len(m['chapters']),'input_characters':total,'correction_character_cap':reserve,'total_submitted_character_cap':total+reserve,'actual_credit_hard_cap':total+reserve,'conservative_estimate':'1 credit per input character; verify model/voice rate <=1 before each request; actual promotional discounts not assumed','included_credit_balance_checked':pre['subscription']['remaining'],'additional_cash_usd_cap':0,'overage_or_topup_authorized':False,'generation_authorized':False,'automatic_retry':False,'corrections':'Only affected chapters; maximum reserve, same voice/script version. Ambiguous or failed request must be reconciled before any retry.','other_external_generation_usd_cap':0,'bgm':'Existing owned Data City Ambient v1; no purchase or paid generation','render':'Local existing Remotion; no cloud render purchase','tts_timing_method':'Prefer ElevenLabs with-timestamps output; preserve provider alignment and validate original-text mapping; do not silently label estimates as aligned.','tts_timing_reference':'https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps/'}
(e/'narration/budget_proposal_v2.json').write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'characters':total,'reserve':reserve,'credit_cap':total+reserve,'included_remaining':pre['subscription']['remaining'],'additional_cash_usd':0}))
