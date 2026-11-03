"""Readable script/price packet for the scoped script approval gate; no synthesis."""
from pathlib import Path
import hashlib,json,re

D=Path(__file__).resolve().parent; E=D.parents[1]; R=E.parents[2]
W=E/'writer/top20-explain-v3'; OUT=E/'outputs/top20-explain-v3/script-review'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=W/'scene_proposals_v6.json'; doc=read(source); prices=read(D/'price_panel_data.json')
    sentences=[s for scene in doc['scenes'] for s in scene.get('sentences',[])]
    assert sentences and all(isinstance(s.get('text'),str) and s['text'].strip() for s in sentences)
    assert all(not re.search(r'요[.!?]?$',s['text'].strip()) for s in sentences)
    text='\n'.join(s['text'] for s in sentences)
    assert all(token in text for token in ['2024년','2026년','국가데이터처'])
    assert len([s for s in doc['scenes']if s.get('region_id')])==20
    lines=['# 신혼부부가 많이 사는 수도권 TOP20','',
           '지역 설명·최근 실거래를 보강한 대본 v6입니다. 낭독 순서대로 정리한 검토용 원고입니다.','',
           '거주 통계: 2024년 11월 1일 · 가격: 2026년 5~10월 계약분, 11월 3일 조회 · 전용83~85㎡. 10월 신고는 진행 중입니다.','']
    for scene in doc['scenes']:
        if not scene.get('sentences'):continue
        lines.extend(['## '+scene['title'],''])
        lines.extend([s['text']+'\n' for s in scene['sentences']])
    OUT.mkdir(parents=True,exist_ok=True)
    script=OUT/'검토용_대본_v6.md';script.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    table=['# 지역별 실거래·단지 사례 기준표','',
           '2026년5~10월 계약분을 11월3일 조회했습니다. 전용83~85㎡·전체 층·중개 및 직거래를 포함하고 해제 표시 행을 제외했습니다. 10월 신고는 진행 중입니다.','',
           '중위값은 조건에 맞는 개별 거래금액을 정렬한 가운데 값입니다. 지역 값과 단지 사례 값은 각각의 표본으로 계산했습니다.','',
           '|순위|지역|지역 중위값·거래 수|단지 사례·법정동|단지 중위값·거래 수|',
           '|---:|---|---|---|---|']
    for p in sorted(prices['regions'],key=lambda r:-r['rank']):
        a=p['representative']
        label='인천 옛 서구(현 서해구·검단구)' if p['region_id']=='R01' else p['province']+' '+p['region']
        table.append(f'|{p["rank"]}|{label}|{p["display_price"]} · {p["n"]:,}건|{a["apt_name"]} · {a["legal_dong_name"]}|{a["display_price"]} · {a["n"]:,}건|')
    table.extend(['','대표 단지는 공식 주소·명칭·좌표를 확인하고 같은 조건의 거래가5건 이상 있는 사례에서 골랐습니다. 가격과 건수는 위 표의 해당 단지 자체 표본입니다.','',
                  '원출처: [국가데이터처 2024년 신혼부부통계](https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3), [국토교통부 아파트 매매 실거래 API](https://www.data.go.kr/data/15126468/openapi.do). 지역 특징의 세부 원문과 확인 범위는 research/top20-explain-v3/regions/facts.json에 기록했습니다.'])
    basis=OUT/'지역별_가격기준표.md';basis.write_text('\n'.join(table)+'\n',encoding='utf-8')
    manifest={'status':'ready_for_script_review_not_approved','source_scene_proposals_sha256':sha(source),'production_script_sha256':sha(W/'script_v6.md'),
              'price_panel_sha256':sha(D/'price_panel_data.json'),'sentence_count':len(sentences),
              'spoken_characters':sum(len(s['text'])for s in sentences),
              'new_tts_generated':False,'full_video_rendered':False,'uploaded':False,'cash_cost_krw':0,
              'files':[{'path':str(p.relative_to(R)).replace('\\','/'),'sha256':sha(p)}for p in [script,basis]]}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items()if k!='files'},ensure_ascii=False))

if __name__=='__main__':main()
