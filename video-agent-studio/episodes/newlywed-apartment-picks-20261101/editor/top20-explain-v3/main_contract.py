"""승인 receipt와 실제 타이밍 계약. 옛 음성/추정시간 fallback이 없습니다."""
from pathlib import Path
import copy,hashlib,json,math,re
from caption_tools import norm

H=Path(__file__).resolve().parent;E=H.parents[1];R=E.parents[2]
JSON_SHA='8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e'
MD_SHA='4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(p):
    p=Path(p)
    return p if p.is_absolute() else R/p
def save(p,v):
    p=Path(p).resolve()
    if not p.is_relative_to(H):raise ValueError('편집 담당 폴더 밖 쓰기 금지')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,s):
    p=Path(p).resolve()
    if not p.is_relative_to(H):raise ValueError('편집 담당 폴더 밖 쓰기 금지')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')

def approved(approval,authorization,json_sha,md_sha):
    for receipt in [approval,authorization]:
        if receipt.get('gate')!='script' or not receipt.get('decision_id'):
            raise ValueError('명시적 script 승인 receipt가 없습니다.')
        if receipt.get('scene_json_sha256')!=json_sha or receipt.get('script_md_sha256')!=md_sha:
            raise ValueError('승인 대상 원고 SHA가 다릅니다.')
    if approval['decision_id']!=authorization['decision_id']:raise ValueError('승인 결정ID 불일치')
    if (json_sha,md_sha)!=(JSON_SHA,MD_SHA):raise ValueError('이번 승인 v6 이외 원고입니다.')
    return True

def load_inputs():
    script_file=H/'input_snapshot/scene_proposals_v6.json';md_file=H/'input_snapshot/script_v6.md'
    approval_file=E/'director/top20-explain-v3/script_approval.json';auth_file=E/'director/top20-explain-v3/production_authorization.json'
    approval=read(approval_file);authorization=read(auth_file)
    approved(approval,authorization,sha(script_file),sha(md_file))
    script=read(script_file);scenes=script['scenes']
    if len(scenes)!=26 or sum(len(s['sentences']) for s in scenes)!=133:raise ValueError('26장면/133문장 원고가 아닙니다.')
    if any(not st.get('text') or st.get('display_text') is None for s in scenes for st in s['sentences']):raise ValueError('확정 본문 누락')
    price_file=E/'director/top20-explain-v3/price_panel_data.json';pd=read(price_file)
    if pd['source_file']!='research/top20-explain-v3/prices/final-api-20261103-v2/map_price_inputs.json':raise ValueError('정상행 보존v2 원팩만 허용')
    upstream=E/pd['source_file'];qa_file=E/'qa/top20-explain-v3/price_panel_verification.json';qa=read(qa_file)
    if sha(upstream)!=pd['source_sha256'] or qa['status']!='passed' or qa['price_panel_sha256']!=sha(price_file):raise ValueError('확정가격·독립검수 SHA 불일치')
    map_file=E/'visual/top20-explain-v3/maps/map_assets.json';maps=read(map_file)
    if maps['source_price_panel_sha256']!=sha(price_file):raise ValueError('지도와 가격 SHA 불일치')
    photo_file=E/'visual/top20-8min-v2/photo_assets_v2.json';photos={p['region_id']:p for p in read(photo_file)['assets']}
    panels={p['region_id']:p for p in pd['regions']};map_by={m['region_id']:m for m in maps['assets']}
    facts_file=E/'research/top20-8min-v2/combined_facts.json';facts=read(facts_file);regions={r['region_id']:r for r in facts['regions']}
    if len(photos)!=20 or len(panels)!=20 or len(map_by)!=20:raise ValueError('20개 사진/가격/지도 누락')
    bindings={};assets=[]
    for s in scenes:
        rid=s.get('region_id')
        if not rid:continue
        p=photos[rid];original=s['photo_binding'];row=panels[rid];m=map_by[rid];marker=m.get('marker') or {};rep=row['representative']
        if original.get('asset_id')!=p['asset_id'] or (original.get('sha256') and original['sha256']!=p['sha256']):raise ValueError('승인 사진 연결 불일치: '+rid)
        if sha(p['absolute_file'])!=p['sha256']:raise ValueError('사진 바이트 변경: '+rid)
        if s.get('price_panel_data')!=row:raise ValueError('canonical과 현재 가격패널 불일치: '+rid)
        if m.get('marker_status')!='verified_coordinate_inside_region' or marker.get('point_inside_real_region') is not True or rep['coordinate_status']!='verified' or any(marker.get(a)!=rep.get(b)for a,b in [('apt_id','apt_id'),('lat','lat'),('lng','lng')]):raise ValueError('검증핀 승계 조건 불일치: '+rid)
        mp=E/m['file']
        if sha(mp)!=m['sha256']:raise ValueError('가격지도 SVG 변경: '+rid)
        bindings[s['scene_id']]={'region_id':rid,'asset_id':p['asset_id'],'sha256':p['sha256'],'status':'verified','place':p['actual_place'],'show_license':True,'capture_year':p['photo_capture_year'],'license':p['license'],'use':'지역 특징·실제 장소 자료사진. 가격 사례 단지의 전경으로 사용하지 않음.'}
        assets.extend([{'source':str(p['absolute_file']),'sha256':p['sha256'],'dest':rid+'.jpg','kind':'photo','region_id':rid},{'source':str(mp),'sha256':m['sha256'],'dest':rid+'_price_map.svg','kind':'price_map','region_id':rid}])
    for name in ['top20_overview.svg','Pretendard-Regular.woff2','Pretendard-Bold.woff2','gsap.min.js']:
        p=H/'spec/assets'/name;assets.append({'source':str(p),'sha256':sha(p),'dest':name,'kind':'inherited_style_or_geometry'})
    brand_file=E/'editor/top20-enhance-v2/reusable_media.json';brands=read(brand_file)
    for kind in ['intro','outro']:
        b=next(v for v in brands['assets'] if v['asset_id']=='channel_brand_'+kind+'_clean_v7');p=R/b['path']
        if sha(p)!=b['sha256']:raise ValueError('기존 승인 브랜드 변경: '+kind)
        assets.append({'source':str(p),'sha256':b['sha256'],'dest':'brand_'+kind+'.mp4','kind':'brand','brand_kind':kind,'duration_s':float(b['probe']['format']['duration'])})
    inputs=[script_file,md_file,approval_file,auth_file,price_file,upstream,qa_file,map_file,photo_file,facts_file,brand_file,H/'spec/assets/top20_overview.svg',H/'render_contract.json']
    inputs += [H/n for n in ['build_main.py','main_contract.py','main_primitives.py','main_layouts.py','v3_visuals.py','phase_timing.py','caption_tools.py','caption_backgrounds.py','quality_main.py']]
    return dict(script=script,script_file=script_file,md_file=md_file,approval=approval,authorization=authorization,scenes=scenes,photos=photos,panels=panels,map_assets=map_by,regions=regions,bindings=bindings,assets=assets,inputs=inputs)

def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def normalize_director_lock(original):
    T=copy.deepcopy(original)
    if T.get('lock_owner')!='director' or T.get('old_timing_fallback_used') is not False or T.get('is_estimate') is not False:raise ValueError('총괄의 새 실제 lock이 아닙니다.')
    if not T.get('audio_revision','').startswith('top20-explain-v3-v6-'):raise ValueError('다른 버전의 음성입니다.')
    T['revision']='top20-explain-v3'
    if 'sentence_time_base' not in T:
        for s in T['scenes']:
            for st in s['sentence_times']:
                if st.get('local_start_s')!=st.get('start_s') or st.get('local_end_s')!=st.get('end_s'):raise ValueError('문장 local 시간 기준이 불명확합니다.')
        T['sentence_time_base']='scene_local'
    source=resolve(T['source_timing'])
    if sha(source)!=T['source_timing_sha256']:raise ValueError('원narration proposal SHA 불일치')
    proposal=read(source)
    if proposal.get('scene_json_sha256')!=JSON_SHA or proposal.get('script_sha256')!=MD_SHA:raise ValueError('원narration proposal 원고SHA 불일치')
    readings={st['sentence_id']:st['reading_text']for s in proposal['scenes']for st in s.get('sentence_times',[])}
    for s in T['scenes']:
        for st in s['sentence_times']:st['reading_text']=readings[st['sentence_id']]
    if not T.get('inserts'):
        T['inserts']=[dict(kind='intro' if v['id']=='brand_intro' else 'outro',start_s=v['start_s'],duration_s=v['duration_s'],source_file=str(resolve(v['path'])),sha256=v['sha256'])for v in T['brand_visuals']]
    if T.get('audio_file')!=T.get('full_brand_audio_file'):raise ValueError('전체 브랜드 포함 음성 연결이 불명확합니다.')
    T['audio_includes_brand']=True
    T['_normalization_source']=str(source)
    return T

def validate_lock(T,data):
    if T.get('revision')!='top20-explain-v3' or T.get('timing_locked') is not True or T.get('timing_basis')!='actual_audio':raise ValueError('이번 v3 실제 음성 타임록만 허용합니다. preview/추정/옛v2 fallback 없음')
    if T.get('scene_json_sha256')!=JSON_SHA or (T.get('script_md_sha256') or T.get('script_sha256'))!=MD_SHA:raise ValueError('실측 타임록의 승인 원고SHA 불일치')
    expected=[s['scene_id'] for s in data['scenes']]
    if [s['scene_id'] for s in T.get('scenes',[])]!=expected:raise ValueError('타임록에 canonical26장면 순서가 필요합니다.')
    if T.get('sentence_time_base') not in ['scene_local','global']:raise ValueError('문장시간 기준을 명시해 주십시오.')
    wp=resolve(T['words_file'])
    if sha(wp)!=T.get('words_file_sha256'):raise ValueError('실측 단어파일SHA 불일치')
    words=read(wp)['words'];grouped={}
    required=['scene_id','sentence_id','text','local_start_s','local_end_s','sentence_normalized_char_start','sentence_normalized_char_end']
    for w in words:
        if any(k not in w for k in required):raise ValueError('원발화 단어 필수필드 누락')
        if not finite(w['local_start_s']) or not finite(w['local_end_s']) or not 0<=w['local_start_s']<w['local_end_s']:raise ValueError('원발화 단어 시간 범위 오류')
        grouped.setdefault(w['sentence_id'],[]).append(w)
    approved_sentences={st['sentence_id']:st for s in data['scenes'] for st in s['sentences']}
    if set(grouped)!=set(approved_sentences):raise ValueError('실제words의133개 sentence_id 집합 불일치')
    resolved=[];readings={};last_word=0
    for source,lock in zip(data['scenes'],T['scenes']):
        sid=source['scene_id'];start,end=lock.get('start_s'),lock.get('end_s')
        if not finite(start) or not finite(end) or not 0<=start<end:raise ValueError('실측 장면 범위 오류: '+sid)
        scene=copy.deepcopy(source);scene.update(start_s=start,end_s=end,duration_s=end-start,anchors={})
        sent=lock.get('sentence_times') or lock.get('sentences') or []
        if [v['sentence_id'] for v in sent]!=[v['sentence_id']for v in source['sentences']]:raise ValueError('실측 문장ID/순서 누락: '+sid)
        scene['sentence_times']=[]
        for original,actual in zip(source['sentences'],sent):
            st=copy.deepcopy(original);st['text']=original['display_text'];st['reading_text']=actual.get('reading_text') or original['reading_text']
            offset=start if T['sentence_time_base']=='global' else 0
            st['start_s']=actual['start_s']-offset;st['end_s']=actual['end_s']-offset
            if not 0<=st['start_s']<st['end_s']<=end-start+.002:raise ValueError('문장시간 범위 오류: '+st['sentence_id'])
            ws=sorted(grouped[st['sentence_id']],key=lambda w:w['local_start_s']);reading=norm(st['reading_text'])
            if norm(''.join(w['text']for w in ws))!=reading:raise ValueError('새 실제 낭독문과 단어원문 불일치: '+st['sentence_id'])
            if ws[0]['sentence_normalized_char_start']!=0 or ws[-1]['sentence_normalized_char_end']!=len(reading):raise ValueError('단어의 문장 문자범위가 완전하지 않습니다: '+st['sentence_id'])
            for i,w in enumerate(ws):
                if w['scene_id']!=sid or not st['start_s']-.003<=w['local_start_s']<w['local_end_s']<=st['end_s']+.003:raise ValueError('단어/장면/문장 범위 불일치')
                if i and (w['local_start_s']<ws[i-1]['local_end_s']-.003 or w['sentence_normalized_char_start']!=ws[i-1]['sentence_normalized_char_end']):raise ValueError('단어 겹침 또는 문자범위 단절')
            grouped[st['sentence_id']]=ws;readings[st['sentence_id']]=st['reading_text'];last_word=max(last_word,start+ws[-1]['local_end_s']);scene['sentence_times'].append(st)
        resolved.append(scene)
    inserts=T.get('inserts') or []
    if sorted(v.get('kind')for v in inserts)!=['intro','outro']:raise ValueError('실제 intro/outro 삽입시간이 필요합니다.')
    for v in inserts:
        asset=next(a for a in data['assets']if a.get('brand_kind')==v['kind'])
        if v.get('sha256')!=asset['sha256'] or sha(resolve(v['source_file']))!=asset['sha256']:raise ValueError('브랜드 원본 SHA 불일치')
        if not finite(v['start_s']) or not finite(v['duration_s']) or v['duration_s']<=0 or abs(v['duration_s']-asset['duration_s'])>1/30+.003:raise ValueError('브랜드 실제 길이/시작 오류')
    intro=next(v for v in inserts if v['kind']=='intro');outro=next(v for v in inserts if v['kind']=='outro')
    if abs(intro['start_s']-resolved[0]['end_s'])>.003 or abs(intro['start_s']+intro['duration_s']-resolved[1]['start_s'])>.003:raise ValueError('도입부 브랜드 위치 불일치')
    if abs(T.get('last_speech_end_s',-1)-last_word)>.003 or abs(resolved[-1]['end_s']-last_word-3)>.003:raise ValueError('마지막 실제 단어+3초 유지 규칙 불일치')
    if abs(outro['start_s']-resolved[-1]['end_s'])>.003:raise ValueError('E001 이후 outro 위치 불일치')
    windows=sorted([(s['start_s'],s['end_s'])for s in resolved]+[(v['start_s'],v['start_s']+v['duration_s'])for v in inserts])
    cursor=0
    for a,b in windows:
        if abs(a-cursor)>.003:raise ValueError('실제 타임라인에 미명시 빈구간/겹침이 있습니다.')
        cursor=b
    audio=resolve(T.get('audio_mix_file') or T['audio_file']);digest=T.get('audio_mix_sha256') if T.get('audio_mix_file') else T.get('audio_sha256')
    if not digest or sha(audio)!=digest:raise ValueError('실제 전체 음성파일SHA 불일치')
    if T.get('audio_mix_file') and T.get('audio_includes_brand') is not True:raise ValueError('믹스의 브랜드소리 포함 여부를 명시해 주십시오.')
    return dict(scenes=resolved,word_groups=grouped,readings=readings,last_word=last_word,total_s=cursor,inserts=inserts,words_path=wp,audio_path=audio)
