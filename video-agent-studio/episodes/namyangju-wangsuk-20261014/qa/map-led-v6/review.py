import pathlib,json,re,hashlib,shutil
p=pathlib.Path(__file__).parent;e=p.parents[1];w=e/'writer/map-led-v4';s=(w/'script_v4.md').read_text(encoding='utf-8');c=json.loads((w/'captions_semantic_v4.json').read_text(encoding='utf-8'));norm=lambda x:re.sub(r'\s+','',x)
chap={m.group(1):m.group(2).split('### 화면 지시')[0].strip() for m in re.finditer(r'## (M\d{3}B?)[^\n]*\n\s*### 내레이션\s*\n(.*?)(?=\n## |\Z)',s,re.S)}
assert chap.keys()==c['chapters'].keys();entries=0
for k,cs in c['chapters'].items():
 assert norm(''.join(x['text'] for x in cs))==norm(chap[k])
 for x in cs:
  assert norm(''.join(x['lines']))==norm(x['text']) and 1<=len(x['lines'])<=2 and max(map(len,x['lines']))<=36
  assert x['start_s'] is None and x['end_s'] is None
  for term in x['protected_phrases']:assert any(term in l for l in x['lines']);entries+=1
sha=hashlib.sha256((w/'script_v4.md').read_bytes()).hexdigest()
r={'revision':'map-led-v6-script-review','checked_revision':{'script_sha256':sha,'writer':'map-led-v4','research':'outside-comparisons-v6'},'user_review_ready':True,'required_open_script_issues':0,'publication_approved':False,'new_paid_generation_authorized_by_QA':False,'caption_verification':{'chapters':len(chap),'cues':sum(len(cs) for cs in c['chapters'].values()),'exact_whitespace_normalized_script_coverage':True,'maximum_line_chars':max(len(l) for cs in c['chapters'].values() for x in cs for l in x['lines']),'protected_entries_unbroken':entries,'all_times_null':True},'scope':'변경된M000훅/M007B외부비교/M009음악지시 및 전체신규자막검수. 기존지도·왕숙원문은map-led-v5 QA계승. actual영상/음성 검수아님.','findings':[{'issue_id':'V6-QA-001','scene_id':'M007B','timecode':'미타이밍대본','severity':'required','문제':'외부지역 가격·상품·면적 혼합 가능','evidence':['창릉S5공고p5PNG 84A5층~최상층769980천원 기본형 직접확인','교산공고p1 1115세대51~59㎡민간참여공공분양 직접텍스트확인','최신대본은교산84가격차트제외 및S3이익공유가격미사용','2025.1.31공고시점차·확장옵션세금별도·최종정정미완료제한존재'],'수정안':'해당상품/층/면적/시점분리와정정확인제한유지','owner':'writer/research','status':'resolved_script_rechecked','checked_revision':sha},{'issue_id':'V6-QA-002','scene_id':'M007B','timecode':'미타이밍대본','severity':'required','문제':'입주와철도·학교목표 또는5호선도보권혼동가능','evidence':['공식고양의회HTML 창릉2030변경목표 문구확인','공식하남답변HTML 송파하남선2032목표 문구확인','교산공고p47PNG초·중신설전임시배치직접확인','대본입주2028.1/학교3월/창릉2030 및교산2029.6/철도2032별도설명','5호선은지구북측기존노선,임의역출입구핀금지'],'수정안':'목표qualified·실제통근분미확인·교산주소범위만표시유지','owner':'writer/editor','status':'resolved_script_rechecked','checked_revision':sha}],'hook_music_assessment':'7억안팎현재동네vs기다릴새집이라는선택질문으로지도해설동기명확. 기존DataCityAmbient인트로/아웃트로낮은음량/페이드지시적절. 실제20~30초/20초·ducking·BGM청취는새음성/영상후검증필요.','remaining':['최종대본·신규음성예산승인','지도등록/권리미확인홍보도면재사용금지','실제TTS/단어싱크/음악청취/연속재생미검증','새이미지GAP자동생성금지']}
(p/'findings.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
h={'revision':r['revision'],'inputs':r['checked_revision'],'outputs':['qa/map-led-v6/findings.json'],'next_owner':'director script/budget review','user_review_ready':True,'unresolved':r['remaining'],'actual_MP4':None,'new_paid_calls':False}
(p/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
o=e/'outputs/story-review-v4'
if o.exists():
 assert hashlib.sha256((o/'script_v4.md').read_bytes()).hexdigest()==sha
 for n in ['findings','handoff']:shutil.copyfile(p/f'{n}.json',o/f'qa_{n}.json')
print(sha,r['caption_verification'])
