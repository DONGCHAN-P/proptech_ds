"""Freeze exact user-script inputs and an auditable pronunciation-only variant.

Local preparation only; the separately staged account query has GET endpoints only.
"""
from pathlib import Path
import hashlib
import json
import math
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
OUT = EP / 'narration/jun-user-script-v1'
INPUT = EP / 'director/user-recording-v1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sino(digits):
    digits = digits.replace(',', '')
    if '.' in digits:
        integer, decimal = digits.split('.')
        return sino(integer) + '점' + ''.join('영일이삼사오육칠팔구'[int(c)] for c in decimal)
    n = int(digits)
    if n == 0:
        return '영'
    assert n < 10000, f'New large number requires explicit review: {digits}'
    parts = []
    for divisor, unit in [(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
        q, n = divmod(n, divisor)
        if q:
            parts.append(('' if q == 1 and unit else '영일이삼사오육칠팔구'[q]) + unit)
    return ''.join(parts)

source = read(INPUT/'source_extracted.json')
plan = read(INPUT/'scene_plan.json')
assert source['sha256'] == plan['source_sha256'] == 'f28deb75e0a271e30e3d29dbe52291ef30e28b0ef0bfc2648ad98bbd652e6a73'
source_doc = INPUT/'source/현금_1억부터_5억까지_내집마련_유튜브_대본.docx'
assert sha(source_doc) == source['sha256']
by_id = {p['id']:p['text'] for p in source['paragraphs']}
paragraphs = []
for scene in plan['scenes']:
    assert scene['narration_text'] == '\n\n'.join(by_id[i] for i in scene['paragraph_ids']) or re.sub(r'\s+','',scene['narration_text']) == re.sub(r'\s+','', ''.join(by_id[i] for i in scene['paragraph_ids']))
    for pid in scene['paragraph_ids']:
        text = by_id[pid]
        pattern = re.compile(r'LTV|DSR|\d[\d,]*(?:\.\d+)?')
        parts, cursor = [], 0
        for m in pattern.finditer(text):
            if m.start() > cursor:
                parts.append({'original':text[cursor:m.start()], 'spoken':text[cursor:m.start()], 'kind':'literal'})
            spoken = {'LTV':'엘티브이','DSR':'디에스알'}.get(m.group())
            if spoken is None:
                spoken = sino(m.group())
            parts.append({'original':m.group(), 'spoken':spoken, 'kind':'pronunciation_only', 'source_start':m.start(), 'source_end':m.end()})
            cursor = m.end()
        if cursor < len(text):
            parts.append({'original':text[cursor:], 'spoken':text[cursor:], 'kind':'literal'})
        assert ''.join(p['original'] for p in parts) == text
        spoken_text = ''.join(p['spoken'] for p in parts)
        assert not re.search(r'\d|LTV|DSR', spoken_text)
        paragraphs.append({'paragraph_id':pid,'scene_id':scene['scene_id'],'chapter':scene['chapter'],'text':text,'spoken_text':spoken_text,'display_mapping':parts,'characters':len(text),'spoken_characters':len(spoken_text),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'spoken_sha256':hashlib.sha256(spoken_text.encode()).hexdigest()})
assert len(paragraphs) == 48 and len({p['paragraph_id'] for p in paragraphs}) == 48
OUT.mkdir(parents=True, exist_ok=True)
for filename, field in [('narration_body.txt','text'),('spoken_body.txt','spoken_text')]:
    (OUT/filename).write_text('\n\n'.join(p[field] for p in paragraphs)+'\n',encoding='utf-8')
manifest = {'revision':'jun-user-script-v1','status':'prepared_not_generated_pending_budget_and_material_fact_clearance','source_doc_sha256':sha(source_doc),'scene_plan_sha256':sha(INPUT/'scene_plan.json'),'source_paragraphs':48,'scene_count':31,'input_characters':sum(p['characters'] for p in paragraphs),'spoken_characters':sum(p['spoken_characters'] for p in paragraphs),'separators_billed':False,'paragraphs':paragraphs,'tts_post_calls':0,'paid_generation_calls':0,'automatic_retries':0,'input_policy':'Exact source wording preserved. Only numbers/Latin abbreviations expanded for reading. Optional guide rewrites not silently applied.'}
chapters = []
for ch in range(1,8):
    selected = [p for p in paragraphs if p['chapter'] == ch]
    text = '\n\n'.join(p['spoken_text'] for p in selected)
    ch_path = OUT/f'inputs/C{ch:02}.txt'
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_bytes(text.encode('utf-8'))
    text_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert sha(ch_path)==text_sha256
    chapters.append({'chapter':ch,'chapter_id':f'C{ch:02}','paragraph_ids':[p['paragraph_id'] for p in selected],'text':text,'characters':len(text),'path':str(ch_path.relative_to(ROOT)).replace('\\','/'),'sha256':text_sha256})
manifest['chapters'] = chapters
manifest['generation_requests_planned'] = 7
manifest['billed_input_characters'] = sum(c['characters'] for c in chapters)
manifest['separators_billed'] = True
put(OUT/'narration_manifest.json',manifest)
original_query = ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/narration/jun-replacement-v1/account_readonly.mjs'
(OUT/'account_readonly.mjs').write_bytes(original_query.read_bytes())
put(OWN/'preparation_receipt.json',{'created_at_utc':datetime.now(timezone.utc).isoformat(),'script':str(source_doc.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(source_doc),'manifest_path':str((OUT/'narration_manifest.json').relative_to(ROOT)).replace('\\','/'),'manifest_sha256':sha(OUT/'narration_manifest.json'),'body_characters':manifest['input_characters'],'spoken_characters':manifest['spoken_characters'],'paragraphs':48,'scenes':31,'tts_post_calls':0,'timing_locked':False,'user_instruction':'이번까지는 JUN으로 진행하고 대본에 맞춰서 영상생성','paid_budget_status':'new_episode_budget_cap_not_yet_approved','upload_authorized_by_this_request':False})
account_file = OUT/'account_readonly.json'
if account_file.exists():
    account = read(account_file)
    rates = account.get('model', {}).get('model_rates', {})
    voice_rate = (account.get('voice') or {}).get('sharing', {}).get('rate')
    factors = [rates.get('character_cost_multiplier'),rates.get('cost_discount_multiplier'),voice_rate]
    unit = math.prod(factors) if all(isinstance(v,(int,float)) and v > 0 for v in factors) else None
    remaining = (account.get('subscription') or {}).get('included_remaining')
    count = manifest['billed_input_characters']
    cfg = read(ROOT/'config/tts.json')
    cap = 7000
    budget = {'revision':'jun-user-script-v1','status':'prepared_pending_user_budget_cap_approval','source_doc_sha256':sha(source_doc),'manifest_sha256':sha(OUT/'narration_manifest.json'),'input_characters_original':manifest['input_characters'],'input_characters_spoken_without_separators':manifest['spoken_characters'],'input_characters_to_send':count,'chapter_requests':7,'provider':'elevenlabs','voice_name':cfg['voice_name'],'voice_id':cfg['voice_id'],'model':cfg['model'],'speed':(account.get('voice') or {}).get('settings',{}).get('speed'),'credits_per_character_estimate':unit,'estimated_first_pass_credits':math.ceil(count*unit) if unit is not None else None,'included_credit_cap_proposed':cap,'included_remaining':remaining,'cap_fits_included':remaining is not None and remaining >= cap,'revision_headroom_credits':cap-math.ceil(count*unit) if unit is not None else None,'additional_cash_cap_krw':0,'top_up_authorized':False,'automatic_retries':0,'generation_authorized':False,'account_snapshot_sha256':sha(account_file),'account_checked_at_utc':account.get('checked_at_utc'),'overage_disabled':all((account.get('subscription') or {}).get(k) is False for k in ['can_extend_character_limit','allowed_to_extend_character_limit']) and (account.get('subscription') or {}).get('max_credit_limit_extension')==0,'estimate_basis':'Live model multiplier × discount multiplier × voice rate; actual post-generation usage must be reconciled. Exact chapter text including separators counted. Total budget includes any approved corrections; no automatic retry.'}
    put(OUT/'budget_proposal.json',budget)
    print(json.dumps({'budget':{k:budget[k] for k in ['input_characters_to_send','estimated_first_pass_credits','included_credit_cap_proposed','included_remaining','cap_fits_included','overage_disabled']}},ensure_ascii=False))
print(json.dumps({k:manifest[k] for k in ['status','source_paragraphs','scene_count','input_characters','spoken_characters','tts_post_calls']},ensure_ascii=False))
