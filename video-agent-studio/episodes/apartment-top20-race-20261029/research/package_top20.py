"""집계 결과를 렌더/대본용 계약과 원명 매핑, 주장 목록으로 묶는다."""
from pathlib import Path
import collections
import hashlib
import json
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
EP=OUT.parent


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf8'))


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')


def main():
    c,a=read('calculation.json'),read('row_accounting.json')
    complexes=c['complexes']
    districts={'11110':'종로구','11170':'용산구','11200':'성동구','11410':'서대문구','11440':'마포구',
        '11470':'양천구','11500':'강서구','11530':'구로구','11560':'영등포구','11590':'동작구',
        '11650':'서초구','11680':'강남구','11710':'송파구','41135':'성남시 분당구','41290':'과천시'}
    shorten={'대치우성아파트1동,2동,3동,5동,6동,7동':'대치우성아파트',
        '푸른마을아파트101동~111동':'푸른마을아파트','현대14차(203,204,205,206동)':'현대14차'}
    duplicates=collections.Counter(v['name'] for v in complexes.values())
    names=[]
    for i,v in complexes.items():
        v['location']=' '.join([v['region'],districts[v['sigungu_code']],v['legal_dong_name']])
        v['display_name']=shorten.get(v['name'],v['name'])
        if duplicates[v['name']]>1:
            v['display_name']+=' · '+v['legal_dong_name']
        v['display_name_status']='proposed_short_label' if v['display_name']!=v['name'] else 'reported_name_whitespace_normalized'
        v['display_name_basis']='원명에서 열거된 동 번호만 생략; 동명은 법정동으로 구분. 원명은 name/original_names에 보존.'
        names.append(dict(id=i,name=v['name'],display_name=v['display_name'],location=v['location'],
            region=v['region'],build_year=v['build_year'],apt_seq=v['apt_seq'],
            display_name_status=v['display_name_status'],original_names=' | '.join(v['original_names'])))
    pd.DataFrame(names).to_csv(OUT/'name_mapping.csv',index=False,encoding='utf-8-sig')
    frames=c['frames']
    flat=[]
    for f in frames:
        for r in f['top']:
            for k in ('name','display_name','location','region'):
                r[k]=complexes[r['id']][k]
            r['claim_id']='P_'+f['period']+'_'+r['id'].replace(':','_').replace('-','_')
            flat.append(dict(period=f['period'],window_start=f['window_start'],window_end=f['window_end'],**r))
        f['top20']=f['top']
    for key in ('entry_events','leader_changes'):
        for r in c[key]:
            r['name']=complexes[r['id']]['name']
            r['display_name']=complexes[r['id']]['display_name']
            r['location']=complexes[r['id']]['location']
    entries=[e for e in c['entry_events'] if e['event']!='initial']
    first_entries=[e for e in entries if e['event']=='first_entry']
    reentries=[e for e in entries if e['event']=='reentry']
    changes=c['leader_changes'][1:]
    biggest=[]
    for f in frames:
        for r in f['rank_changes']:
            if r['rank_gain']>0:
                biggest.append(dict(period=f['period'],name=complexes[r['id']]['name'],**r))
    biggest=sorted(biggest,key=lambda r:(-r['rank_gain'],r['period'],r['id']))[:10]
    selected=['2006Q4','2010Q4','2016Q3','2022Q4','2023Q1','2023Q3','2025Q4','2026Q2']
    def entry_reason(e):
        t=frames[[f['period'] for f in frames].index(e['period'])-1]
        return dict(**e,interpretation='TOP20 첫 등장 또는 재진입; 준공·입주 또는 가격 상승의 단독 증거가 아님',previous_period=t['period'])
    summary=dict(frame_count=len(frames),displayed_rows=len(flat),ever_top20_complexes=len(complexes),
        initial_complexes=20,first_entry_events=len(first_entries),reentry_events=len(reentries),
        total_entry_events_after_initial=len(entries),leader_change_count=len(changes),
        unique_leaders=len({r['id'] for r in c['leader_changes']}),
        initial_leader=c['leader_changes'][0],leader_changes=changes,
        largest_upward_rank_moves=biggest,entry_events=[entry_reason(x) for x in entries],
        final_top20=frames[-1]['top'],
        eligible_complexes_first=frames[0]['eligible_complexes'],eligible_complexes_last=frames[-1]['eligible_complexes'],
        candidate_regions=sorted({v['region'] for v in complexes.values()}),
        all_time_collected_complexes=a['included_complexes'],included_transactions=a['included_rows'])
    limitations=[
        '대상은 서울·경기·인천·부산·대구·대전·세종에서 수집된 식별 가능 단지다. 전국 전체, 전 지역 전수 수집을 뜻하지 않는다. 광주 등 나머지 지역은 제외된다.',
        '공통 관측 종료는 2026-06-30(2026Q2)이다. 파일별 수집일은 서로 다르며 2026-10-29에 전 거래를 최신 재조회한 자료가 아니다.',
        '수도권 과거 캐시의 수집시각 범위는 기존 기록상 2026-04-30~2026-10-13이다. 전체 266개 지역·월만 신규 보완됐으며 나머지 과거 변경·취소가 완전히 갱신됐다고 가정하지 않는다.',
        '확장 자료는 기존 전처리에서 거래키 중복 제거 39,041건과 취소 우선 처리가 적용됐다. 실제 동일 조건의 복수 거래가 합쳐졌을 수 있다. 이번 분석에서는 중복 제거를 추가하지 않았다.',
        '수도권 원행 multiplicity는 보존했다. 확장 자료와 기존 처리 차이가 있어 표본 수가 완전히 동일한 수집·중복 처리 조건은 아니다.',
        '대구는 군위 코드 27720/47720을 제외한 고정 경계, 세종은 36110 API 이력 범위다. 과거 행정구역 전체의 완전성을 가정하지 않는다.',
        '각 분기말 최근 4개 분기 개별 유효 매매 총액의 중위값이다. 분기 중위값의 평균, 최고가, ㎡당 가격 또는 동일 주택 가격지수가 아니다.',
        '전용 84㎡ 이상 85㎡ 미만을 합쳤다. 층·동·세부 면적·입주권 등 거래 구성이나 거래유형별 시장/직거래를 별도 통제하지 않았다. 등기 완료 여부도 추가 제한하지 않았다.',
        '공식 API 신고 단지명을 공백 정규화해 사용했다. 외부 단지대장으로 현재 공식 명칭을 새로 대조하지 않았다. 짧은 표시명은 제안이며 원명을 보존한다.',
        '연속 창은 3분기를 공유한다. 진입·퇴장은 가격뿐 아니라 거래 5건 충족, 창 밖 거래 이탈, 표본 구성 변화로 발생할 수 있다.',
        '3/5/10건 민감도는 마지막 시점과 본편 1위 교체 시점만 본편 직전 순위를 동률 기준으로 비교했다. 각 기준으로 독립적인 79분기 레이스를 만든 결과가 아니다.'
    ]
    data=dict(meta=dict(measure='trailing_4_quarter_transaction_price_median_manwon',statistic='median',
        area_min=84,area_max_exclusive=85,min_n=5,window_quarters=4,
        regions=['서울','경기','인천','부산','대구','대전','세종'],first_period='2006Q4',last_period='2026Q2',
        transaction_period_start='2006-01-01',observation_end='2026-06-30',checked_at='2026-10-29',
        transaction_type='아파트 매매 신고; API에 포함된 거래를 거래방식/등기여부 추가 제한 없이 사용',
        unit='만원/채',aggregation='각 창 안의 개별 거래금액을 정렬; 홀수 가운데값, 짝수 두 가운데값 산술평균',
        scope='7개 수집 지역의 식별 가능한 전체 수집 단지에서 분기마다 재선정',
        tie_rule='중위금액 내림차순 → 직전 분기 TOP20 순위 오름차순(직전 TOP20 밖은 동일 무한순위) → canonical ID 사전순; 최초 시점은 canonical ID',
        cancellation_policy='수도권 included_price_analysis=true 및 is_canceled=false; 확장 기존 거래키별 취소 우선 정규화 후 is_canceled=false',
        identity_policy='수도권 complex_id=rtms:aptSeq; 확장 api:aptSeq→rtms:aptSeq; fallback/불확실 ID 제외',
        actual_collected_complexes=a['included_complexes'],actual_included_transactions=a['included_rows'],
        collection_asof='파일별 상이; 공통 최신 재조회일 없음',limitations=limitations),
        complexes=complexes,frames=frames,summary=summary)
    save('data.json',data)
    pd.DataFrame(flat).to_csv(OUT/'top20_quarterly.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(c['entry_events']).to_csv(OUT/'entry_events.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(c['leader_changes']).to_csv(OUT/'leader_changes.csv',index=False,encoding='utf-8-sig')
    save('sensitivity.json',dict(scope='endpoint_and_main_leader_change_periods_only',results=c['sensitivity']))
    source_paths=[x['path'] for x in a['source_inputs'][:2]]
    comparisons=dict(statistic='최근 4분기 개별 거래 매매총액 중위값',geographic_scope=data['meta']['scope'],
        area='84 <= 전용면적 < 85㎡',transaction_type=data['meta']['transaction_type'],unit='만원/채',
        aggregation=data['meta']['aggregation'],cancellations=data['meta']['cancellation_policy'],minimum_n=5)
    facts=[]
    for r in flat:
        sentence=f"{r['period']} {r['location']} {r['name']}: {r['window_start']}~{r['window_end']} 전용 84㎡대 매매 {r['n']}건의 중위금액 {r['median_manwon']:g}만원, 수집 대상 단지 중 {r['rank']}위."
        facts.append(dict(claim_id=r['claim_id'],sentence=sentence,source_files=source_paths,
            evidence_location=f"top20_quarterly.csv: period={r['period']}, id={r['id']}; median_evidence.csv 동일 키", 
            reference_date=str(pd.Period(r['period']).end_time.date()),checked_at='2026-10-29',
            status='qualified',verification_note='로컬 집계 완료; 별도 알고리즘 검산 전',
            complex_id=r['id'],n=r['n'],median_manwon=r['median_manwon'],period=r['period'],
            window_start=r['window_start'],window_end=r['window_end'],conditions=comparisons))
    for number,text in enumerate(limitations,1):
        facts.append(dict(claim_id=f'METHOD_{number:02d}',sentence=text,source_files=source_paths,
            evidence_location='row_accounting.json; data.json:meta; 원자료 기존 전처리 코드 regional_expansion_v1.py',
            reference_date='2026-06-30',checked_at='2026-10-29',status='qualified'))
    save('facts.json',dict(revision='v1',scope='로컬 스냅샷에서 관찰한 집계; 외부 최신 사실 확인 없음',facts=facts))
    preflight=dict(episode_id=EP.name,role='research',template='templates/episode_preflight.json',
        applied_items=['price_area_floor_period_cancellation_sample_statistic','protected_numbers_units_names','raw_research_retention'],
        question='전용 84㎡대 단지별 중위 매매가격 TOP20은 분기마다 어떻게 바뀌었나?',
        scope='research 폴더의 데이터·팩트·핸드오프만 작성',
        episode_specific_choices=['79개 분기별 TOP20 재선정','최소 5건','기존 수집분만 로컬 이용'],
        not_applicable=['신도시 개발·역·도면','음성 생성·타이밍·렌더·업로드'],
        actual_listening_performed=False,continuous_playback_performed=False,
        paid_calls=0,network_calls=0,external_transfers=0,independent_qa_performed=False)
    save('research_preflight.json',preflight)
    notes=[f"계약기간 2006-01-01~2026-06-30, 79개 분기, {a['included_rows']:,}건·{a['included_complexes']:,}개 단지.",
        f"TOP20에 한 번이라도 등장한 단지는 {len(complexes)}개. 초기 20개 이후 신규 진입 {len(first_entries)}건, 재진입 {len(reentries)}건. 1위 교체 {len(changes)}회.",
        '최신 관측 창은 2025Q3~2026Q2. 원자료 수집일은 파일별로 다름. 전 지역 완전 수집으로 표현하지 말 것.',
        '이벤트는 TOP20 첫 등장/재진입이며 준공·입주 이벤트로 바꾸지 말 것. 동률·표본 탈락만으로도 순위가 바뀔 수 있음.',
        '장문 표시명 제안과 원명은 name_mapping.csv에 1:1 매핑. 현대14차의 원명은 현대14차(203,204,205,206동).',
        '민감도는 endpoint와 본편 1위 교체 순간에만 수행. 끝점 5건/10건 포함 여부에 따른 해석은 sensitivity.json 확인.',
        '다음 담당은 writer/visual, 최종 제작 전 독립 QA. 이 세션의 별도 알고리즘 검산은 독립 담당 검수를 대체하지 않음.']
    save('writer_handoff.json',dict(verified_claims='facts.json에서 검산 후 verified 상태인 가격 주장',
        comparison_conditions=comparisons,notes=notes,unverified=['현재 단지대장 명칭 대조','후속 취소/수정 반영','미수집 지역 순위','가격 변화 원인'],
        relevant_events=changes,proposed_focus_periods=selected))
    print(json.dumps(dict(packaged_frames=len(frames),price_claims=len(flat),ever_top20=len(complexes),
        first_entries=len(first_entries),reentries=len(reentries),leader_changes=len(changes)),ensure_ascii=False))


if __name__=='__main__':
    main()
