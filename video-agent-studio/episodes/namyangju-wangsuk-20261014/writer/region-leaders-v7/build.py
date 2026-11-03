from pathlib import Path
import hashlib, json, re, math

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/story-review-v7'
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(ROOT/'outputs/story-review-v6/script_v6.md').read_text(encoding='utf-8-sig')
OUT.mkdir(parents=True,exist_ok=True)
chapters=[]
for scene,title in [('M008','지도 분석으로 고른 권역별 대장 후보'),('M009','내 생활에서 우선순위가 바뀌는 조건')]:
    raw=(HERE/f'{scene}_segments.txt').read_text(encoding='utf-8').strip()
    assert '[' not in raw,'Unresolved research placeholder'
    paragraphs=raw.split('\n\n')
    text='\n\n'.join(p.replace('|',' ') for p in paragraphs)
    cues=[];cursor=0
    for p in paragraphs:
        for s in p.split('|'):
            start=text.index(s,cursor);end=start+len(s)
            assert text[start:end]==s
            cues.append({'cue_id':f'{scene}-V7-{len(cues)+1:02d}','text':s,'lines':[s],'char_start':start,'char_end':end,'start_s':None,'end_s':None})
            cursor=end
    path=OUT/f'{scene}.txt';path.write_text(text,encoding='utf-8')
    (OUT/f'{scene}_semantic_captions.json').write_text(json.dumps({'scene_id':scene,'script_revision':'script-v7-region-leaders','timing_status':'untimed_semantic_draft','cues':cues},ensure_ascii=False,indent=2),encoding='utf-8')
    screen=(HERE/f'{scene}_screen.md').read_text(encoding='utf-8').strip()
    section=f'## {scene} — {title}\n\n### 내레이션\n\n{text}\n\n### 화면 지시\n\n{screen}\n\n'
    old=re.sub(r'## '+scene+r' — .*?(?=\n## )',lambda m:section.rstrip()+'\n',old,flags=re.S)
    chapters.append({'scene_id':scene,'path':f'outputs/story-review-v7/{scene}.txt','characters':len(text),'sha256':sha(path.read_bytes()),'cue_count':len(cues)})
old=old.replace('# 왕숙 토지계획도 읽기 — 전편 연결·시리즈 예고·기존 브랜드 복원 대본 v6','# 왕숙 토지계획도 읽기 — 지도 결론과 권역별 대장 후보 대본 v7',1)
old=re.sub(r'^상태:.*$', '상태: 사용자 검토 대기. M008·M009만 새 원고로 교체했다. M000~M007B 내레이션은 v6와 동일하며 기존 음성을 재사용한다. 새 후반 음성은 별도 대본·예산 승인 전 생성하지 않는다.', old,count=1,flags=re.M)
old=re.sub(r'^- M008:.*$', '- M008: research/region-leaders-v14의 일반형 후보 유형·제한·가격·지도 근거 및 기존 map-led-v5·alternatives-v5 근거. 권역별 대장 후보는 조건부 입지 해석이며 미래 시세선두 확정 아님. 신혼희망타운 A2·A24는 후보군에서 제외. 전매제한과 실제 거래 가능 시점은 별도 확인.',old,flags=re.M)
old=old.replace('- 본문·분양가·조건부 후보의 결론은 변경하지 않는다. 지도 용도 사전과 후반 편집은 v8 수정 범위로 계속 진행한다.','- v7에서는 M008·M009의 후보 결론만 일반형 아파트 권역별 비교로 교체한다. 이전 v6 주석을 새 후보 승인으로 보지 않는다.')
old=old.replace('흰 자막 박스는 인트로 구간에도 유지하되 내레이션이 없으면 글자만 비운다.','흰 자막 박스는 본문 음성이 나오는 동안 유지한다. 무음 도입부와 기존 5초 브랜드 인트로·10초 아웃트로에는 자막 박스를 표시하지 않는다.')
old=old.replace('왕숙2 A1 84A5층이상693,630,000원·A3 732,450,000원','왕숙2 A1 84A5층이상693,630,000원·A3 84A1 전용84.75㎡ 5층~최상층732,450,000원')
source=(ROOT/'outputs/story-review-v6/script_v6.md').read_text(encoding='utf-8-sig')
def narr(s):
    return {m.group(1):re.search(r'### 내레이션\n\n(.*?)(?=\n\n### 화면 지시)',m.group(2),re.S).group(1) for m in re.finditer(r'## (M\d+[A-Z]?) — ([\s\S]*?)(?=\n## |\Z)',s)}
a,b=narr(source),narr(old)
assert len(a)==len(b)==11
unchanged=[k for k in a if k not in ['M008','M009']]
assert all(a[k]==b[k] for k in unchanged)
assert 'A24' not in b['M008']+b['M009'] and 'A2' not in b['M008']+b['M009']
script=OUT/'script_v7.md';script.write_text(old,encoding='utf-8')
chars=sum(c['characters'] for c in chapters);reserve=math.ceil(chars*.2)
manifest={'script_revision':'script-v7-region-leaders','source_script_sha256':sha(script.read_bytes()),'changed_scene_ids':['M008','M009'],'unchanged_narration_scene_ids':unchanged,'unchanged_narration_verified':True,'chapters':chapters,'new_input_characters':chars,'correction_character_reserve_20pct':reserve,'submitted_character_and_credit_cap_proposal':chars+reserve,'additional_cash_usd':0,'generation_authorized':False,'estimated_duration_s_range':[round(chars/8.5),round(chars/7.5)],'duration_basis':'estimate_only_based_on_existing_Korean_narration_pacing_not_measured'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
