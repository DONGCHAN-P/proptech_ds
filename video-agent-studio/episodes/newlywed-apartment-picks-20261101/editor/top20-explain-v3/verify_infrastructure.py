"""합성 단어 메타데이터로 전환 로직을 검사합니다. 실제 음성 검수를 뜻하지 않습니다."""
from pathlib import Path
import copy,hashlib,json,sys,re
sys.path.insert(0,str(Path(__file__).resolve().parent))
from phase_timing import price_phase
from v3_visuals import exact_price
from caption_tools import split_semantic,set_protected_phrases,norm

H=Path(__file__).resolve().parent;E=H.parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def check(name,value):
    checks.append({'검사':name,'통과':bool(value)})
    assert value,name
def rejected(scene,words):
    try:price_phase(scene,words,True)
    except ValueError:return True
    return False

s={'scene_id':'TEST','duration_s':20,'sentences':[{'sentence_id':x} for x in ['A','B','P','Q']],
   'screen_beats':[{'purpose':'regional_and_complex_price','sentence_ids':['P','Q']}]}
w={sid:[{'scene_id':'TEST','text':sid,'local_start_s':a,'local_end_s':b}] for sid,a,b in [('A',0,3),('B',3,9.25),('P',10,14),('Q',14,18)]}
phase=price_phase(s,w,True)
check('가격 첫 단어10초·특징 마지막 단어9.25초; 사진은10초까지 유지',phase['switch_s']==10 and phase['feature_last_word_end_s']==9.25)
bad=copy.deepcopy(w);bad['B'][0]['local_end_s']=10.1
check('특징 낭독 중 가격 전환 거부',rejected(s,bad))
bad=copy.deepcopy(w);del bad['P']
check('실제 가격 원발화 단어 누락 거부',rejected(s,bad))
bad=copy.deepcopy(w);bad['P'][0]['scene_id']='OLD'
check('이전/다른 장면의 단어 거부',rejected(s,bad))
bad=copy.deepcopy(w);bad['P'][0]['local_start_s']=float('nan')
check('잘못된 숫자 타이밍 거부',rejected(s,bad))
for raw,expected in [(303000,'30억 3,000만원'),(319500,'31억 9,500만원'),('100000.5','10억 0.5만원'),('123456.75','12억 3,456.75만원'),(0,'0만원')]:
    check('원수치 반올림 없음 '+str(raw),exact_price(raw)==expected)
name='용인기흥효성해링턴플레이스';set_protected_phrases([name,'검증용 긴 단지명'])
text=f'{name}의 실거래 중위값은 31억 9,500만원이며 1,234건입니다.'
cues=split_semantic(text,24)
check('의미 자막 내용 손실 없음',norm(''.join(cues))==norm(text))
check('억·만원 숫자를 다른 큐로 자르지 않음',any('31억 9,500만원' in c for c in cues))
check('긴 단지명 자체를 자르지 않음',any(name in c for c in cues))
text='검증용 긴 단지명은 10억 0.5만원입니다.'
check('공백 있는 단지명 보호',any('검증용 긴 단지명' in c for c in split_semantic(text,8)))
text='지역 거래 1,381건의 중위값은 6억2,000만원입니다.'
check('숫자 뒤 조사·어미에 잘못된 공백을 추가하지 않음',' '.join(split_semantic(text,19))==text)

pd=read(E/'director/top20-explain-v3/price_panel_data.json');md=read(E/'visual/top20-explain-v3/maps/map_assets.json');qa=read(E/'qa/top20-explain-v3/price_panel_verification.json')
check('정상행 보존v2만 연결',pd['source_file']=='research/top20-explain-v3/prices/final-api-20261103-v2/map_price_inputs.json')
check('원팩SHA 연결',sha(E/pd['source_file'])==pd['source_sha256'])
check('지도 및 독립 가격검수SHA 연결',sha(E/'director/top20-explain-v3/price_panel_data.json')==md['source_price_panel_sha256']==qa['price_panel_sha256'] and qa['status']=='passed')
check('20지역·20지도·총거래14,303건',len(pd['regions'])==len(md['assets'])==20 and sum(r['n'] for r in pd['regions'])==14303)
manifest=read(H/'input_manifest.json')
check('모든 생성기 입력SHA 확인',all(sha(v['path'])==v['sha256'] for v in manifest['inputs']))
check('v3 지도20개 원본 바이트 보존',sum('price_map' in r for r in manifest['assets'])==20 and all(r.get('price_map_sha256')==r.get('original_map_sha256') for r in manifest['assets'] if 'price_map' in r))
for rid in ['R06','R18','R01']:
    r=next(r for r in pd['regions'] if r['region_id']==rid);q=H/f'spec/representatives/{r["scene_id"]}/index.html';html=q.read_text(encoding='utf-8')
    check('실값·명칭·각자n HTML 연결 '+rid,all(x in html for x in [exact_price(r['median_manwon']),exact_price(r['representative']['median_manwon']),r['representative']['apt_name'],f"지역 거래 {r['n']:,}건",f"단지 거래 {r['representative']['n']:,}건"]))
for q in (H/'spec/scenes').glob('S*.html'):
    check('본문 통계청/국가데이터처 반복 없음 '+q.stem,'통계청' not in q.read_text(encoding='utf-8') and '국가데이터처' not in q.read_text(encoding='utf-8'))
mapping=read(H/'spec/caption_mapping.json');script=read(H/'input_snapshot/scene_proposals_v6.json')
check('지정 최종 sceneJSON SHA',mapping['source_script_sha256']=='8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e')
check('지정 최종 MD SHA',mapping['source_markdown_sha256']=='4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38')
selected=set(mapping['selected_scene_ids']);expected={st['sentence_id']:st.get('display_text') or st['text'] for s in script['scenes'] if s['scene_id'] in selected for st in s['sentences'] if st.get('text')}
grouped={};rows=[]
for c in mapping['cues']:grouped.setdefault(c['sentence_id'],[]).append(c)
check('자막 sentence_id 집합 정확 일치',set(expected)==set(grouped))
for sid,text in expected.items():
 actual=' '.join(v['text'] for v in sorted(grouped[sid],key=lambda v:v['start_s']))
 good=actual==text;rows.append({'sentence_id':sid,'expected_display_text':text,'actual_cue_join':actual,'exact_match':good})
check('최종 display_text와 자막 cue 결합 글자·띄어쓰기·수치 정확 일치',all(v['exact_match'] for v in rows))
(H/'caption_integrity.json').write_text(json.dumps({'status':'passed','source_script_sha256':mapping['source_script_sha256'],'source_markdown_sha256':mapping['source_markdown_sha256'],'scene_count':len(selected),'sentence_count':len(expected),'cue_count':len(mapping['cues']),'timing_locked':False,'actual_listening_performed':False,'검사범위':'선택한 대표7장면의 sentence_id/display_text 완전 일치. 본편 전체 생성·실제 발화 정렬 검사는 아님.','sentences':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
receipt={'status':'passed','통과수':len(checks),'checks':checks,'검수범위':'로컬 함수·입력 무결성·HTML 데이터 연결; 독립 가격 재집계·실제 음성 청취·MP4 재생 아님','actual_listening_performed':False,'continuous_playback_performed':False}
(H/'infrastructure_verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'통과수':len(checks),'실제음성':False,'결과':'infrastructure_verification.json'},ensure_ascii=False))
