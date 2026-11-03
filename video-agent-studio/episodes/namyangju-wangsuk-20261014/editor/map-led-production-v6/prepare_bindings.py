import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
HERE=Path(__file__).parent
manifest=json.loads((EP/'writer/map-led-v4/narration_input/manifest.json').read_text(encoding='utf-8'))
story=json.loads((EP/'writer/map-led-v4/scene_plan.json').read_text(encoding='utf-8'))
bindings=[]
for scene in story['scenes']:
    sid=scene['scene_id'];txt=(EP/f'writer/map-led-v4/narration_input/{sid}.txt').read_text(encoding='utf-8')
    default={'M000':('official_plan','overview',[]),'M001':('official_plan','overview',[]),'M002':('registered_map','jobs',['W1-A24','W1-B17']),'M003':('registered_map','transport',['W1-A24','W2-A3']),'M004':('price_comparison','price',['W1-B17','W2-A1','W2-A3']),'M005':('registered_map','life',['W1-A24','W2-A1','W2-A3']),'M006':('completion_calendar','supply',['W1-A1','W1-A2','W1-A24','W1-B17','W2-A1','W2-A3']),'M007':('price_comparison','price',['W1-B17','W2-A1','W2-A3']),'M007B':('outside_locator','outside',[]),'M008':('block_candidate','candidates',['W1-B17','W2-A3']),'M009':('registered_map','overview',[])}[sid]
    cuts=[(0,*default,'지도에서 위치와 질문을 회수')]
    extra={
      'M001':[('왕숙1은','official_plan','overview',[]),('집과 일터','registered_map','overview',['W1-A1','W1-A2','W1-A24','W1-B17','W2-A1','W2-A3'])],
      'M002':[('왕숙 도시첨단산업단지는','registered_map','jobs',['W1-A24','W1-B17']),('일정은 아직','completion_calendar','jobs',['W1-A24','W1-B17']),('이곳의 장점은','registered_map','jobs',['W1-B17'])],
      'M003':[('왕숙2는','registered_map','transport',['W2-A1','W2-A3']),('두 곳 모두','completion_calendar','transport',['W1-A24','W2-A3']),('여기에 집의 달력','completion_calendar','transport',['W1-A24','W1-B17','W2-A1','W2-A3']),('그때 비교할 기존 교통은','registered_map','transport',[]),('내 단지에서 어느 기존 역','registered_map','transport',[])],
      'M004':[('전용 84제곱미터급','price_comparison','price',['W1-B17','W2-A1','W2-A3']),('예산이 더 작다면','registered_map','price',['W1-A2','W1-A24']),('지금 읽은 84형','price_comparison','price',['W1-B17','W2-A1','W2-A3'])],
      'M005':[('왕숙1 북측 A2','registered_map','life',['W1-A2']),('남측 A24는','registered_map','life',['W1-A24','W1-B17']),('왕숙2에서는','registered_map','life',['W2-A1']),('A3은 남쪽','registered_map','life',['W2-A3']),('학교 일정도','completion_calendar','life',['W1-A1','W1-A2']),('반면 남측','completion_calendar','life',['W1-A24','W1-B17']),('왕숙2 A1도','completion_calendar','life',['W2-A1']),('상업과 공원도','registered_map','life',['W2-A3'])],
      'M006':[('지금 확인한 여섯 블록','completion_calendar','supply',['W1-A1','W1-A2']),('왕숙2 A1은','completion_calendar','supply',['W2-A1','W2-A3']),('입주가 모이면','registered_map','supply',['W1-A24','W1-B17']),('여기까지 지도를 읽으면','registered_map','overview',[])],
      'M007':[('다산롯데캐슬은','price_comparison','price',[]),('그런데 별내푸르지오는','price_comparison','price',[]),('다만 B17에는','price_comparison','price',['W1-B17']),('지금 이사를 해야','registered_map','overview',[])],
      'M009':[('왕숙','registered_map','overview',[])]
    }
    for phrase,kind,theme,focus in extra.get(sid,[]):
        if phrase not in txt:continue
        pos=txt.index(phrase)
        if pos>0:cuts.append((pos,kind,theme,focus,phrase))
    if sid=='M008':
        anchors=[('왕숙1 남측에서 먼저 B17','W1-B17'),('B17 서쪽 A24','W1-A24'),('북측 A2','W1-A2'),('왕숙2 A1','W2-A1'),('A3은 그보다','W2-A3')]
        for phrase,block in anchors:
            start=txt.index(phrase);cuts.append((start,'block_candidate','candidates',[block],phrase))
        cuts.append((txt.index('B17과 A3는'),'registered_map','candidates',['W1-B17','W2-A3'],'가구별 후보 조건을 같은 지도에서 회수'))
    elif sid=='M007B':
        cuts.append((txt.index('다만 창릉 S5'),'outside_price_comparison','outside',[],'같은84 일반분양 비교; 교산은 가격표에서 제외'))
        cuts.append((txt.index('송파와 강동'),'outside_locator','outside',[],'교산은 동남권 방향·입주와 철도 시차; 정밀핀 없음'))
    cuts.sort(key=lambda c:c[0])
    for i,(start,kind,theme,focus,purpose) in enumerate(cuts):
        end=cuts[i+1][0] if i+1<len(cuts) else len(txt)
        bindings.append({'shot_id':f'{sid}-S{i+1:02}','scene_id':sid,'script_revision':'script-v4-hook-outside','source_txt_sha256':hashlib.sha256(txt.encode('utf-8')).hexdigest(),'char_start':start,'char_end':end,'timing_basis':'exact approved TXT spans; waiting provider alignment, not character-weighted estimates','from_frame':None,'duration_frames':None,'kind':kind,'map_theme':theme,'focus_ids':focus,'purpose':purpose,'asset_ids':['PLAN_W1_ORIGINAL','PLAN_W2_ORIGINAL'] if kind=='official_plan' else ['MAP_INDEPENDENT_GUIDE_POINTS','MAP_OPERATING_RAIL'] if theme=='transport' else ['MAP_INDEPENDENT_GUIDE_POINTS'],'claim_ids':scene['claim_ids'],'relationship_geometry':'verified north/south/east/west statements rendered as nonmetric leader annotations, not invented facility coordinates','mandatory_label':'계획도 기반 배치 관계 · 정밀 경계·출입구 아님' if focus else '광역 위치/방향 수준 · 정밀 접근시간 아님'})
(HERE/'shot_templates.json').write_text(json.dumps({'revision':'map-led-v6-exact-span-shot-bindings','source_script_sha256':manifest['source_script_sha256'],'timing_locked':False,'shots':bindings},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(bindings),'explicit semantic map bindings; no final timing')
