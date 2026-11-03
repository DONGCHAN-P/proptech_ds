import pathlib,json,re,hashlib
p=pathlib.Path(__file__).parent;e=p.parents[1]
caps=json.loads((e/'writer/semantic-captions-v4/captions.json').read_text(encoding='utf-8'));script=(e/'writer/script_v2.md').read_text(encoding='utf-8')
norm=lambda s:re.sub(r'\s+','',s)
chap={m.group(1):m.group(2).split('### 화면 지시')[0].strip() for m in re.finditer(r'## (S00[1-8])[^\n]*\n\s*### 내레이션\s*\n(.*?)(?=\n## |\Z)',script,re.S)}
checks=[];bad=[]
for s,cs in caps['chapters'].items():
 assert norm(''.join(c['text'] for c in cs))==norm(chap[s]),s
 for i,c in enumerate(cs):
  assert norm(''.join(c['lines']))==norm(c['text'])
  assert 1<=len(c['lines'])<=2 and max(map(len,c['lines']))<=36
  assert c['end_s']>c['start_s']
  if i:assert abs(cs[i-1]['end_s']-c['start_s'])<.00001
 checks.append({'scene_id':s,'exact_coverage':True,'cues':len(cs)})
review=json.loads((e/'writer/semantic-captions-v4/semantic_qa.json').read_text(encoding='utf-8'))
for q in review['protected_phrase_checks']:
 cs=caps['chapters'][q['scene_id']];phrase=q['phrase'];expected=chap[q['scene_id']].count(phrase)
 assert sum(c['text'].count(phrase) for c in cs)==expected
 assert sum(l.count(phrase) for c in cs for l in c['lines'])==expected
old=json.loads(pathlib.Path('video/src/namyangju-v2/project.json').read_text(encoding='utf-8'))['captions']
examples=[]
phrases=['8만 114세대','1만 5천955세대','6만 4천159세대','4억 9천304만 원','6억 9천363만 원','5억 2천634만 원','7억 3천245만 원','8천500억 원','1조 8천993억 원','2029년 3월','왕숙2 A1','별내별가람역','4호선 진접선','59A','5층 이상 기준층']
for phrase in phrases:
 for s,cs in caps['chapters'].items():
  new=[c for c in cs if phrase in c['text']]
  if new:
   src=norm(''.join(c['text'] for c in old[s]));k=src.find(norm(phrase));cursor=0;pieces=[]
   for c in old[s]:
    n=len(norm(c['text']))
    if k>=0 and cursor<k+len(norm(phrase)) and cursor+n>k:pieces.append(c['text'])
    cursor+=n
   examples.append({'phrase':phrase,'scene_id':s,'old_cues':pieces,'new_cue':new[0]['text'],'new_lines':new[0]['lines']});break
r={'revision':'semantic-context-v4','source_gate':'caption_data_pass_pending_editor_integration_and_actual_MP4','script_sha256':hashlib.sha256(script.encode()).hexdigest(),'chapters':checks,'total_cues':sum(len(v) for v in caps['chapters'].values()),'independently_rechecked_protected_occurrences':sum(x['occurrences'] for x in review['protected_phrase_checks']),'maximum_line_chars':max(len(l) for cs in caps['chapters'].values() for c in cs for l in c['lines']),'representative_old_new':examples,'manual_semantic_review':'302 cue editorial listing read; clauses/sentence boundaries preserve numeric/name information. S001-C016 and S002-C022 adjectival clauses continue into next cue, but understandable phrase boundaries; no standalone particle or numerical fragment found.','actual_listening':False,'forced_alignment':False,'timing':'글자 비중 추정값; 의미 분할 통과와 실제 음성 싱크는 별도','required_issues':[]}
(p/'source_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(r['total_cues'],r['independently_rechecked_protected_occurrences'],len(examples))
