from pathlib import Path
import re, json, hashlib

ep = Path(__file__).resolve().parents[2]
own = ep / 'writer/revision-v7'
review = ep / 'outputs/script-review-v7'
script = review / 'script_v7.md'
text = script.read_text(encoding='utf-8')
chunks = re.split(r'\n## (M\d+) ', text)[1:]
claims = {
 'M000': [],
 'M001': ['MAP4-LH-GEOMETRY','MAP4-S1-LOCATION','CN4-S4-ACCESS'],
 'M002': ['CN2-JOBS-RELOCATION'],
 'M003': ['CN-RAIL-GTX','CN-RAIL-GE','CN4-S5-SUPPLY','CN4-S1-SUPPLY','CN4-S4-SUPPLY','CN4-EXISTING-ACCESS'],
 'M004': ['PST3-S5-STAGE','PST3-S1-STAGE','PST3-S4-STAGE'],
 'M007': ['CN-PRICE-db26aa7d99fb32df','CN-PRICE-6b9e26142b9eb6a3','CN-PRICE-b0b97f17ddc24cb6','CN-PRICE-14f487c544ee4871','CN-PRICE-6d132d1b88760197','CN-PRICE-17bae9021d8588e6'],
 'M006': ['CN4-S5-SUPPLY','CN4-S1-SUPPLY','CN4-S4-SUPPLY','CN4-S6-EARLIER','CN2-S4-TYPE','CN-S3-TYPE'],
 'M005': ['CN4-S4-ACCESS','CN2-S5-SCHOOL','CN2-S4-SCHOOL','CN2-S1-SCHOOL','CN2-S1-SURROUNDINGS'],
 'M009': ['CN4-S4-ACCESS','CN4-S4-SUPPLY','PST3-S5-STAGE','PST3-S1-STAGE','PST3-S4-STAGE']
}
rate = 6372 / 786.48
scenes = []
for i in range(0,len(chunks),2):
    sid, body = chunks[i:i+2]
    sections = body.split('### ')
    narration = sections[1].split('\n\n',1)[1].strip()
    screen = sections[2].split('\n\n',1)[1].strip()
    types = [t for t in ['real_photo','data_chart','map','ai_concept','editorial_card'] if t in screen]
    cues=[]
    for paragraph in narration.split('\n'):
        # Punctuation-only segmentation is a proposal; editor must preserve number+unit and Korean meaning.
        for sentence in re.split(r'(?<=[.!?])\s+',paragraph):
            if sentence.strip(): cues.append({'text':sentence.strip(),'timing_status':'untimed','split_required_if_long':len(sentence)>42})
    scenes.append({'scene_id':sid,'chapter_index':len(scenes)+1,'message':body.split('\n',1)[0].strip('· '),'narration_text':narration,
       'claim_ids':claims[sid], 'evidence_paths':(['research/commute-v6/report.md','research/commute-v6/route_observations.json'] if sid in ['M002','M009'] else []),
       'asset_types':types,'visual_purpose':'explanation','screen_direction':screen,
       'script_revision':'script-v7','audio_revision':None,'start':None,'end':None,
       'timing_basis':'estimate_from_prior_Jun_6372_chars_786.48s','estimated_narration_seconds':round(len(narration)/rate,1),
       'status':'draft_needs_user_and_independent_review','semantic_caption_plan':cues,
       'inference_status': 'fact_plus_explicit_hypothesis' if sid in ['M001','M002','M003','M004','M007','M006','M005','M009'] else 'editorial_question'})
chars=sum(len(s['narration_text']) for s in scenes)
def write(name,value,folder=own):
    (folder/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=hashlib.sha256(script.read_bytes()).hexdigest()
write('scene_proposals.json',{'revision':'script-v7','status':'proposal_only','script_sha256':sha,'sequence':[s['scene_id'] for s in scenes],
    'shared_visual_direction':text.split('## 공통 화면 지침',1)[1].split('## M000',1)[0].strip(),
    'chapter_card_policy':'independent numbered title card before each chapter, sufficient reading time; permanent top-right label is separate',
    'source_position':'fixed separate region below semantic subtitles',
    'removed_scene_ids':['M008'],'scenes':scenes})
write('narration_packet.json',{'revision':'script-v7','status':'draft_do_not_generate','characters_including_spaces':chars,
    'prior_Jun_evidence':'narration/audio-v3/handoff.json','prior_characters':6372,'prior_decoded_duration_seconds':786.48,
    'estimated_narration_seconds':round(chars/rate,1),'estimated_final_seconds':round(chars/rate+18,1),
    'estimate_limit':'Prior character/duration ratio only; pace/numerals differ. No v7 voice generated, listened to, or timing locked.',
    'pronunciations':{'S1':'에스 원','S4':'에스 포','S5':'에스 파이브','S3':'에스 쓰리','S6':'에스 식스','GTX-A':'지티엑스 에이','LH':'엘에이치','MBC':'엠비씨','LG':'엘지','84㎡':'팔십사 제곱미터','27대1':'이십칠 대 일','S-클래스':'에스 클래스'},
    'emphasis':['대장 후보','진입가격','기존 수요 접점','현재 교통','계획','부분합','가설'],
    'direction':'구어체·문장 끝 훈계 억양 금지·가격과 단위를 붙여 낭독·정보 문장 사이 짧은 호흡',
    'scenes':[{'scene_id':s['scene_id'],'text':s['narration_text']} for s in scenes]})
inputs=['outputs/script-review-v6/script_v6.md','brief.json','state.json','research/production-v2/facts.json','research/script-v4-addendum/facts_addendum.json','research/prices-v2/comparisons.json','research/commute-v6/report.md','research/commute-v6/route_observations.json','research/revision-v7/facts.json','narration/audio-v3/handoff.json','visual/semantic-v5/verified_missing_locations.json']
write('input_manifest.json',{'inputs':[{'path':p,'sha256':hashlib.sha256((ep/p).read_bytes()).hexdigest()} for p in inputs]})
forbidden=['보십시오','내 이사 달력','훈계']
checks={'scene_count':len(scenes),'narration_characters':chars,'removed_M008':all(s['scene_id']!='M008' for s in scenes),
    'forbidden_narration_terms':{term:sum(s['narration_text'].count(term) for s in scenes) for term in forbidden},
    'number_of_n_equals':sum(s['narration_text'].count('n=') for s in scenes),
    'all_scenes_have_visual_types':all(s['asset_types'] for s in scenes),'estimated_final_over_600s':chars/rate+18>=600,
    'script_sha256':sha,'actual_v7_voice_generated':False,'actual_listening':False,'continuous_video_review':False,
    'independent_review':'pending','candidate_liquidity_claim':'potential only; actual S4 future trading not verified'}
write('validation.json',checks)
write('handoff.json',{'task_id':'writer-v7','role':'writer','status':'draft_needs_review','input_revisions':{'script':'v6','research':'production-v2/prices-v2/script-v4-addendum/commute-v6/revision-v7'},
    'outputs':['outputs/script-review-v7/script_v7.md','writer/revision-v7/scene_proposals.json','writer/revision-v7/narration_packet.json','writer/revision-v7/input_manifest.json','writer/revision-v7/validation.json','outputs/script-review-v7/changes_v7.md'],
    'affected_scene_ids':[s['scene_id'] for s in scenes]+['M008'],
    'checks':[{'check':'text structure/character count/estimate','result':'pass','evidence':'writer/revision-v7/validation.json'},
      {'check':'independent content review/user script approval','result':'pending','evidence':None}],
    'open_issue_ids':[],'resolved_issue_ids':['V7-HOBAN-COORD'],'next_role':'director_then_independent_qa',
    'limits':['No state/scenes/decisions changed','No paid generation/render','No inherited approval','Hoban uses official address locator, not centroid/boundary/entrance']})
print(json.dumps(checks,ensure_ascii=False))
