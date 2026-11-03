"""사진 메타 동기화: 기존 v2를 읽고 허용된 v3 파일만 작성한다."""
import copy
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
EP = OUT.parent.parent
REV = 'top20-8min-v3'
ALLOWED = {'scene_proposals_v3.json','script_v3.md','claim_map_v3.json',
           'verification_v3.json','handoff_v3.json'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name, value):
    assert name in ALLOWED
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def chars(text): return len(re.sub(r'\s+',' ',text).strip())

base_names = ['scene_proposals.json','script_v2.md','claim_map.json','verification.json','handoff.json']
protected = {n:sha(OUT/n) for n in base_names}
base = read(OUT/'scene_proposals.json')
old_map = read(OUT/'claim_map.json')
proposal = copy.deepcopy(base)
manifest_path = EP/'visual/top20-8min-v2/photo_assets_v2.json'
if not manifest_path.exists(): manifest_path = manifest_path.with_name('photo_assets.json')
manifest = read(manifest_path)
photo_rel = manifest_path.relative_to(EP).as_posix()
photos = {a['region_id']:a for a in manifest['assets']}
assert len(photos)==20 and set(photos)=={f'R{n:02}' for n in range(1,21)}
snapshots = {str((OUT/n).relative_to(EP).as_posix()):{'sha256':protected[n],'usage':'v2 원고·연결 재사용'} for n in base_names}
for name in ['brief.json','state.json']:
    snapshots[name]={'sha256':sha(EP/name),'usage':'동시 갱신 가능한 공통파일의 해시 스냅샷만; 수치 입력으로 사용하지 않음'}
snapshots[photo_rel]={'sha256':sha(manifest_path),'photo_revision':manifest.get('photo_revision'),
                      'usage':'갱신된20행 actual_place·출처메타 연결'}
immutable = {}
for name in ['top20.json','ranks01_10_facts.json','ranks11_20_facts.json']:
    rel=f'research/top20-8min-v2/{name}'
    immutable[rel]={'sha256':sha(EP/rel),'usage':'기존 검증 수치 재사용; 재전사·새 집계 없음'}
    assert immutable[rel]['sha256']==base['input_versions'][rel]['sha256']

by_id = {s['scene_id']:s for s in proposal['scenes']}
changes=[]
def change(sid, sentence_id, new, claim, kind='editorial_connection'):
    line=next(x for x in by_id[sid]['sentences'] if x['sentence_id']==sentence_id)
    changes.append({'scene_id':sid,'sentence_id':sentence_id,'before':line['text'],'after':new,
                    'removed_claim_ids':line['claim_ids'],'new_claim_ids':[claim]})
    line.update(text=new,claim_ids=[claim],statement_type=kind)
def remove(sid, sentence_id):
    line=next(x for x in by_id[sid]['sentences'] if x['sentence_id']==sentence_id)
    changes.append({'scene_id':sid,'sentence_id':sentence_id,'before':line['text'],'after':None,
                    'removed_claim_ids':line['claim_ids'],'new_claim_ids':[]})
    by_id[sid]['sentences'].remove(line)

change('S003','S003-03','원미구 안에서도 상동처럼 구체적인 동네로 좁혀볼 수 있겠죠.','PHOTO_R20','viewer_comparison_question')
change('S012','S012-02','노원구 공릉동의 경춘선숲길처럼, 산책길이 있는 실제 장소도 함께 떠올려볼 수 있겠죠.','PHOTO_R11','viewer_comparison_question')
change('S016','S016-02','고덕역 주변에 관심이 있다면, 집에서 역까지의 동선을 추가로 살펴볼 수 있겠죠.','PHOTO_R07','viewer_comparison_question')
remove('S016','S016-03')
change('S018','S018-03','생활권은 부평역과 그 앞 거리부터 짚어볼게요.','PHOTO_R05')
change('S014','S014-02','분당에서는 삼평동 판교 일대의 업무와 생활 동선을 함께 살펴볼 수 있겠죠.','PHOTO_R09','viewer_comparison_question')
remove('S014','S014-03')
# 같은 종류의 불일치가 있는 기존 시설 문장도 사진에 확인된 지명으로만 동기화한다.
change('S009','S009-03','은평구 진관동에는 은평뉴타운이 있습니다.','PHOTO_R14','fact_or_calculation')
change('S008','S008-03','구로구에서는 신도림역 주변 같은 구체적인 생활권도 살펴볼 수 있어요.','PHOTO_R15')
change('S020','S020-02','덕양구 안에서도 삼송로처럼 구체적인 동네의 거리 모습부터 짚어볼게요.','PHOTO_R03')
change('S020','S020-03','이 동네에 관심이 간다면, 실제 거주 후보지에서 직장과 생활시설까지의 동선을 비교해볼 수 있겠죠.','PHOTO_R03','viewer_comparison_question')
change('S019','S019-03','마곡의 서울식물원에서는 야외 공간도 함께 살펴볼 수 있어요.','PHOTO_R04')
cta='다음에는 지역별 아파트 후보를 더 자세히 비교해볼 테니, 이어서 보실 분들은 구독과 좋아요 부탁드려요.'
by_id['C001']['sentences'].append({'sentence_id':'C001-07','text':cta,
    'claim_ids':['EDITORIAL-CTA-V3'],'statement_type':'editorial_cta'})
changes.append({'scene_id':'C001','sentence_id':'C001-07','before':None,'after':cta,
                'removed_claim_ids':[],'new_claim_ids':['EDITORIAL-CTA-V3']})
changed_ids=list(dict.fromkeys(c['scene_id'] for c in changes))

claims={c['claim_id']:copy.deepcopy(c) for c in old_map['claims']}
bindings={}
for rid,a in photos.items():
    canonical=f'PHOTO_{rid}'
    src=a['source_or_prompt']
    snap=src.get('metadata_snapshot')
    source_ref={'file':photo_rel,'selector':f'assets[region_id={rid}].actual_place; address_or_area; source_or_prompt',
        'original_source_ids':[canonical], 'original_urls':[src.get('fixed_revision_url') or src.get('file_page')],
        'original_title':src.get('title'),'original_description':src.get('original_description'),
        'metadata_snapshot':None if not snap else 'visual/top20-8min-v2/'+snap,
        'photo_capture_year':a.get('photo_capture_year'),'photo_capture_date_raw':a.get('photo_capture_date_raw'),
        'evidence_location':'선택한 사진 원장의 actual_place 및 원문메타 필드; 사진 자체를 통계 근거로 사용하지 않음'}
    claims[canonical]={'claim_id':canonical,'statement':f"사진 원장의 실제 장소: {a['actual_place']}; {a['address_or_area']}.",
        'status':'supplied_photo_metadata_reused','kind':'photo_place_metadata',
        'source_refs':[source_ref],'selected_manifest_asset_id':a['asset_id'],
        'writer_review_scope':'제공된 사진 원장의 원문메타·장소 필드를 읽음. 원문 웹 재열람·사진 픽셀 재검수는 미실시.'}
    path=Path(a.get('absolute_file',''))
    if not path.is_absolute(): path=manifest_path.parent/a['actual_file']
    assert path.is_file()
    bindings[rid]={'asset_id':canonical,'selected_manifest_asset_id':a['asset_id'],
        'asset_id_policy':'최종 PHOTO_Rxx 연결 유지; 실제 v2 원장 교체 asset_id는 별도 보존',
        'actual_place':a['actual_place'],'caption':a['actual_place'],
        'actual_file':path.relative_to(EP).as_posix(),'photo_capture_year':a.get('photo_capture_year'),
        'photo_capture_date_raw':a.get('photo_capture_date_raw'),'source_claim_id':canonical,
        'source_manifest':photo_rel,'source_manifest_sha256':snapshots[photo_rel]['sha256'],
        'source_url':src.get('file_page'),'source_metadata_ref':source_ref,
        'inspection_status_from_visual':a.get('inspection',{}).get('status'),
        'writer_pixels_inspected':False,'purpose':'실제 장소·생활권 맥락; 거주규모·변화·선택 이유의 증거로 사용하지 않음',
        'date_rule':'2024.11.1 통계기준일과 촬영연도를 구분해 화면 출처에 표시; 해당 연도 현재 전경으로 일반화하지 않음'}
claims['EDITORIAL-CTA-V3']={'claim_id':'EDITORIAL-CTA-V3','statement':cta,
    'status':'user_requested_editorial','kind':'cta_next_episode_connection',
    'source_refs':[{'user_instruction':'이번 수정 지시: 구독·좋아요 및 다음 지역별 아파트 후보 분석 연결 CTA1문장'}]}

special_memos={
 'S003':'MAP_R20의2024 원미구와7,365쌍 유지. PHOTO_R20은 상동 도시 가로로만 표기. 부천중앙공원 라벨 삭제. 2023 비교null 유지.',
 'S012':'PHOTO_R11은 갱신 원장의 공릉동 경춘선숲길 산책로·옛 철로. 갤러리 건물·전시실·야외무대 라벨 삭제.11위와10위 차이 예고는 유지.',
 'S016':'PHOTO_R07 고덕역4번출구·주변 가로로만 표기. 일자산 라벨 삭제. 실제 경로·통근시간은 추정하지 않고 구 경계와34쌍 비교 예고 유지.',
 'S018':'MAP_R05의1만 기준·303쌍 증가 유지. PHOTO_R05는 부평역 외관·역앞 거리. 부평문화의거리·전통시장 사진으로 명명하지 않음.',
 'S014':'PHOTO_R09는2016년 삼평동 판교 겨울 거리. 캠퍼스 건물·지원시설 라벨과 정확 시설명 낭독 삭제. 업무·생활 동선 질문의 분위기 자료로 사용.',
 'S009':'MAP_R14·251쌍 차이 유지. PHOTO_R14는 진관동 은평뉴타운 전경. 은평한옥마을 라벨 삭제.',
 'S008':'MAP_R15·19쌍 차이 유지. PHOTO_R15는 신도림역1번출구·주변 가로. G밸리 실사로 표기하지 않음.',
 'S020':'MAP_R03·1만1,452쌍 유지. PHOTO_R03는 삼송로 도시풍경. 스타필드 건물·상업시설 라벨과 주소 낭독 삭제.',
 'S019':'MAP_R04·520쌍 차이 유지. PHOTO_R04는 마곡 서울식물원 야외. 온실 내부·열대전시 실물로 표기하지 않음.',
 'S021':'기존 송파 수치·석촌호수 설명 유지. PHOTO_R02 교체본은 동호 수면·벚꽃 수변 원경으로만 표기. 동호·서호 전체 구성 설명은 기존R02-F01 공식 정보레이어와 분리하며 사진의 보이는 범위를 확장하지 않음.',
 'S017':'강남 수치·34쌍 차이·9.4% 증가 설명 유지. PHOTO_R06 교체본은 양재천 영동4교 인근 수변길로 표기. 영동6교·대치교 공사나 신축 시설의 사진으로 사용하지 않음.',
 'C001':'기존 규모·변화·구성 회수 유지. 마지막 CTA1문장에 구독·좋아요와 다음 지역별 아파트 후보 비교를 연결. CTA 발화 뒤 E0013초 여백을 둠.',
}
for s in proposal['scenes']:
    s['narration_text']='\n'.join(x['text'] for x in s['sentences'])
    s['claim_ids']=list(dict.fromkeys(c for x in s['sentences'] for c in x['claim_ids']))
    s['script_revision']=REV
    if s['scene_id'] in special_memos: s['screen_memo']=special_memos[s['scene_id']]
    if s['scene_id']=='S014':s['message']='판교 일대의 업무·생활 동선을 비교 질문으로 연결한다'
    if s['region_id']:
        binding=bindings[s['region_id']]
        s['photo_binding']=binding
        s['photo_requirements']=[{'asset_id':binding['asset_id'],'place_name':binding['actual_place'],
            'status':'selected_manifest_bound_pending_independent_visual_QA',
            'selected_manifest_asset_id':binding['selected_manifest_asset_id'],
            'purpose':'실제 장소 맥락·분위기; 숫자의 근거는 기존 지도·데이터 레이어',
            'constraints':'사진은 actual_place로만 라벨링. 촬영연도와 통계연도 분리. 원장 이용조건 보존.'}]
        s['requested_photo_places']=[binding['actual_place']]
        s['asset_ids']=[x for x in s['asset_ids'] if not x.startswith('PHOTO_')]+[binding['asset_id']]
        s['asset_status']='v2_map_card_status_preserved_photo_manifest_bound_pending_independent_visual_QA'
    if s['scene_id']=='S014':s['title']='9위 성남시 분당구'

# 미수정 장면의 길이는 유지하고, 수정 장면끼리만 기존 합계 시간을 재배분한다.
affected=[s for s in proposal['scenes'] if s['scene_id'] in changed_ids]
pool=sum(s['duration_s'] for s in affected)
weights=[chars(s['narration_text']) for s in affected]
raw=[pool*w/sum(weights) for w in weights]
dur=[int(x) for x in raw]
for i in sorted(range(len(dur)),key=lambda i:raw[i]-dur[i],reverse=True)[:pool-sum(dur)]: dur[i]+=1
for s,n in zip(affected,dur):s['duration_s']=n
tick=0
for s in proposal['scenes']:
    s['start_s']=tick;s['end_s']=tick+s['duration_s'];tick=s['end_s']
proposal.update(revision=REV,status='review_draft_pending_new_user_script_approval',
    base_script_revision=base['revision'],input_versions={**copy.deepcopy(base['input_versions']),**snapshots},
    immutable_statistical_inputs=immutable,changed_narration_scene_ids=changed_ids,
    photo_binding_manifest=photo_rel,photo_binding_count=20,
    duration_method='v2 미수정 장면의 길이 유지, 수정 장면의 기존 합계만 문자량 비례 재배분. 합계480초 estimate·음성 미확정.',
    photo_asset_id_policy='PHOTO_Rxx를 최종 연결ID로 유지; 원장 ALT01 교체ID·파일·actual_place는 photo_binding에 보존')
for key in ['G밸리','고양대로 1955','서수원칠보체육관']:
    proposal['pronunciation_dictionary'].pop(key,None)

used={c for s in proposal['scenes'] for x in s['sentences'] for c in x['claim_ids']}
used.update(f'PHOTO_R{n:02}' for n in range(1,21))
def expand(cid):
    for dep in claims[cid].get('input_claim_ids',[]):
        if dep not in used:used.add(dep);expand(dep)
for cid in list(used):expand(cid)
def sources(cid):
    out=[{'raw_claim_id':cid,**ref} for ref in claims[cid]['source_refs']]
    for dep in claims[cid].get('input_claim_ids',[]):out+=sources(dep)
    return list({json.dumps(x,sort_keys=True,ensure_ascii=False):x for x in out}.values())
old_lines={x['sentence_id']:x for x in old_map['sentences']}
lines=[]
for s in proposal['scenes']:
    for line in s['sentences']:
        q=copy.deepcopy(old_lines.get(line['sentence_id'],{}));q.update(copy.deepcopy(line))
        evidence=[ref for cid in line['claim_ids'] for ref in sources(cid)]
        q.update(scene_id=s['scene_id'],region_id=s['region_id'],raw_source_claim_ids=line['claim_ids'],
            source_evidence=evidence,resolved_raw_source_claim_ids=list(dict.fromkeys(x['raw_claim_id'] for x in evidence)),
            photo_context_source_ids=[] if not s['region_id'] else [f"PHOTO_{s['region_id']}"],
            photo_binding=s.get('photo_binding'),photo_requirements=s.get('photo_requirements',[]),
            map_requirement=s['map_requirements'],asset_ids=s['asset_ids'],material_types=s['material_types'],
            visual_anchor=line['text'],visual_action=s['screen_memo'],
            evidence_scope='v2 수치·검증 사실 재사용. v3는 사진 원장 actual_place·원문메타 연결과 수정 문장·CTA 자체 점검만 수행.')
        lines.append(q)
claimmap=copy.deepcopy(old_map)
claimmap.update(revision=REV,input_versions=proposal['input_versions'],immutable_statistical_inputs=immutable,
    claims=[claims[c] for c in sorted(used)],sentences=lines,photo_bindings=list(bindings.values()),
    sentence_changes=changes,removed_unused_claim_ids=sorted(set(c['claim_id'] for c in old_map['claims'])-used),
    supplemental_facts_used=[],
    verification_boundary='v2 불변 수치 검증 재사용. 변경 문장·사진 원문메타 연결·CTA 확인; 새 원문 리서치·픽셀 재검수·전체 독립QA 미실시.',
    media_review={'selected_photo_manifest':photo_rel,'bound_photos':20,
        'photos_pixels_inspected_by_writer':False,'map_pixels_inspected_by_writer':False,
        'supplied_metadata_fields_read':True,'independent_visual_QA_performed_by_writer':False})

spoken='\n\n'.join(s['narration_text'] for s in proposal['scenes'] if s['narration_text'])
n=chars(spoken);n0=len(re.sub(r'\s+','',spoken))
def stamp(n):return f'{n//60:02}:{n%60:02}'
md=['# 신혼부부가 많이 사는 수도권 TOP20','',
    '> v3 검토 초안 · 사용자 새 대본 승인 대기',
    '> 목표8분. 합계480초는 estimate이며 실제 오디오 기반으로 확정하지 않았습니다.',
    f'> 낭독문 {n:,}자(공백 포함·줄바꿈 정규화), {n0:,}자(공백 제외). 제목·메모 제외.','',
    '## 낭독','']
for s in proposal['scenes']:
    if s['narration_text']:
        label=f" / {s['region_id']}" if s['region_id'] else ''
        md += [f"### {s['scene_id']}{label} · {s['title']}",'',s['narration_text'],'']
md += ['## 화면 메모 — 낭독하지 않음','',
    f'사진 연결 기준: `{photo_rel}`의20행. PHOTO_Rxx 연결ID는 유지하며 실제 교체ID와 파일은 장면표에 기록했습니다. 사진은 actual_place와 촬영연도로 표기합니다. writer는 픽셀·권리를 새로 검수하지 않았습니다.','',
    '| 장면 | 잠정 구간 | 화면 |','|---|---|---|']
for s in proposal['scenes']:
    memo=s['screen_memo']
    if s['region_id']:
        a=bindings[s['region_id']];memo+=f" / 사진 {a['asset_id']}: {a['actual_place']} ({a['photo_capture_year'] or '촬영연도 미상'})."
    md.append(f"| {s['scene_id']} | {stamp(s['start_s'])}–{stamp(s['end_s'])} estimate | {memo} |")
md += ['', '## narration 인계 — 낭독하지 않음','',
    '음성 미선택·미생성. 숫자·단위·증가/감소 방향과 v2 강조어를 유지합니다. 새 대본 승인 후 실제 오디오로 타임록을 제안합니다.','',
    '| 표기 | 읽기 |','|---|---|']
md += [f'| {k} | {v} |' for k,v in proposal['pronunciation_dictionary'].items()]
md += ['', '강조어: '+' / '.join(proposal['emphasis_words']),'',
    '## 수정·검증 범위 — 낭독하지 않음','',
    '- 사진과 시설명이 어긋나는 문장만 사진 원장의 지명 또는 생활권 질문으로 바꾸고, 분당의 캠퍼스 시설명을 삭제했습니다.',
    '- C001 마지막에 구독·좋아요와 다음 지역별 아파트 후보 비교를 연결하는 CTA 한 문장을 추가했습니다.',
    '- 순위·수치·2024 구역·지도 상태·verified 수치의 근거는 v2에서 재사용했습니다. 원미2023 비교값은 null을 유지합니다.',
    '- 새 대본 승인·독립 검수는 대기 상태입니다. 실제 오디오·청취·연속 재생·유료 생성·외부 전송·렌더·업로드는 수행하지 않았습니다.','']
(OUT/'script_v3.md').write_text('\n'.join(md),encoding='utf-8')
write('scene_proposals_v3.json',proposal);write('claim_map_v3.json',claimmap)

# 변경 구간만 원고·메타와 대조. 불변 통계의 원문 재검수는 반복하지 않는다.
before={s['scene_id']:s for s in base['scenes']}
assert 3800<=n<=4300,n
assert [s['region_id'] for s in proposal['scenes'] if s['region_id']]==[f'R{n:02}' for n in range(20,0,-1)]
assert tick==480 and proposal['scenes'][-1]['duration_s']==3
assert all(s['audio_revision'] is None and s['timing_status']=='provisional_audio_unconfirmed' for s in proposal['scenes'])
for s in proposal['scenes']:
    b=before[s['scene_id']]
    assert s['rank']==b['rank'] and s['map_requirements']==b['map_requirements']
    assert s['asset_ids'][:len(b['asset_ids'])]==b['asset_ids']
    if s['scene_id'] not in changed_ids:assert s['sentences']==b['sentences'] and s['duration_s']==b['duration_s']
    for old in b['sentences']:
        if not any(x['sentence_id']==old['sentence_id'] for x in changes):
            assert old in s['sentences']
assert all(claims[cid]==old for old in old_map['claims'] if (cid:=old['claim_id']) in used and old['kind']=='direct_calculation')
assert claimmap['comparisons_2023_2024']==old_map['comparisons_2023_2024']
assert len([x for x in lines if x['statement_type']=='editorial_cta'])==1
assert by_id['C001']['sentences'][-1]['text']==cta
assert all(word not in spoken for word in ['부천중앙공원','일자산','부평문화의거리','경춘선숲길 갤러리','스타트업 캠퍼스','은평한옥마을','G밸리','스타필드','온실'])
assert all(protected[x]==sha(OUT/x) for x in protected)
written_md=(OUT/'script_v3.md').read_text(encoding='utf-8')
section=written_md.split('## 낭독\n\n',1)[1].split('## 화면 메모',1)[0]
parts=re.split(r'^### ([A-Z]\d{3}).*\n\n',section,flags=re.M)
back={parts[i]:parts[i+1].strip() for i in range(1,len(parts),2)}
assert all(back[s['scene_id']]==s['narration_text'] for s in proposal['scenes'] if s['narration_text'])
verification={'revision':REV,'status':'passed_scoped_self_check_not_independent_QA',
    'scope':'사진 불일치 수정문장·메타 연결·CTA·저장본 동기화; v2 통계검수는 해시 일치로 재사용',
    'changed_narration_scene_ids':changed_ids,'sentence_changes':changes,
    'narration_characters':{'with_spaces_normalized':n,'without_whitespace':n0},
    'rank_order_20_to_1_preserved':True,'rank_count':20,'missing_ranks':[],'duplicate_ranks':[],
    'count_claims_and_derived_statistics_unchanged':True,'map_requirements_and_existing_asset_ids_unchanged':True,
    'immutable_statistical_inputs':immutable,'photo_manifest':photo_rel,'photo_count':20,
    'canonical_photo_ids':[f'PHOTO_R{n:02}' for n in range(1,21)],
    'replacement_asset_ids':{r:a['asset_id'] for r,a in photos.items() if a['asset_id']!=f'PHOTO_{r}'},
    'removed_facility_names_absent_from_narration':True,'cta_sentences_added':1,
    'saved_markdown_matches_scene_proposals':True,'estimated_total_s':480,'audio_confirmed':False,
    'v2_protected_hashes':protected,'v2_preserved':True,'input_snapshots':snapshots,
    'independent_qa_performed':False,'photos_pixels_inspected_by_writer':False,
    'audio_created':False,'paid_generation':False,'external_transfer':False,'render':False,'upload':False,
    'checked_at':datetime.now(timezone(timedelta(hours=9))).isoformat()}
write('verification_v3.json',verification)
files=['script_v3.md','scene_proposals_v3.json','claim_map_v3.json','verification_v3.json','build_v3.py']
handoff={'task_id':'writer-photo-sync-v3','role':'writer','revision':REV,
    'status':'review_draft_pending_new_user_script_approval',
    'summary':f'v2 보존. 사진 v2 원장20행 연결. 불일치 시설명은 실제 지명·생활권 질문으로 수정하고 CTA1문장 추가. 낭독 {n}자(공백 포함). 20→1·수치·구역·지도 상태 유지. 480초 estimate·오디오 미확정. 새 대본 승인 대기.',
    'input_revisions':snapshots,'immutable_statistical_inputs':immutable,
    'outputs':[{'path':(OUT/x).relative_to(EP).as_posix(),'sha256':sha(OUT/x),'bytes':(OUT/x).stat().st_size} for x in files],
    'affected_scene_ids':changed_ids,'photo_metadata_synced_scene_ids':[s['scene_id'] for s in proposal['scenes'] if s['region_id']],
    'checks':[{'check':'수정문장·삭제된시설claim·사진20행·CTA1문장·v2보존·480초합계','result':'passed_scoped_self_check','evidence':'writer/top20-8min-v2/verification_v3.json'}],
    'unresolved':['이 v3 대본의 사용자 승인','visual 담당의 교체사진 최종·독립 검수 상태 확인','승인 후 실제 음성에 따른 타임록'],
    'photo_asset_id_policy':proposal['photo_asset_id_policy'],
    'verification_reuse':'2024값·19지역증감·구성 계산은 불변 입력 SHA 일치로 v2 자체점검 재사용; 전체 원문 재검수 미실시',
    'next_role':'director: v3 검토초안 전달 및 새 script 결정; visual: 실제 사진라벨/연도·교체본 확인',
    'shared_files_written':False,'existing_v2_files_written':False,
    'authorization':{'audio':False,'paid_generation':False,'external_transfer':False,'render':False,'upload':False}}
write('handoff_v3.json',handoff)
for name in ALLOWED:
    if name.endswith('.json'):read(OUT/name)
assert all(sha(EP/x['path'])==x['sha256'] for x in handoff['outputs'])
assert all(protected[x]==sha(OUT/x) for x in protected)
print(json.dumps({'status':'scoped_v3_written_and_checked','characters':n,'characters_without_whitespace':n0,
    'changed_narration_scenes':changed_ids,'photo_manifest':photo_rel,'photos':20,
    'ranks':20,'estimated_seconds':480,'v2_preserved':True,'user_script_approval':'pending'},ensure_ascii=False))
