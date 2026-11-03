"""읽기 전용 원천 점검. 출력은 이 가격 리서치 폴더에만 기록합니다."""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
EPISODE = HERE.parents[2]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def records(con, sql, parameters=None):
    result = con.execute(sql, parameters or [])
    names = [d[0] for d in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    con = duckdb.connect(':memory:')
    paths = ['master/trade_events.parquet', 'master/apt_id_map.parquet', 'web/cache/trades.parquet',
             'web/cache/apt_index.parquet', 'web/cache/complex_facts.parquet']
    files = []
    for rel in paths:
        path = ROOT / rel
        entry = {'path': rel, 'bytes': path.stat().st_size, 'sha256': sha256(path),
                 'schema': records(con, 'DESCRIBE SELECT * FROM read_parquet(?)', [str(path)])}
        if rel.endswith(('trade_events.parquet', 'trades.parquet')):
            entry['coverage'] = records(con, 'SELECT count(*) AS n, min(deal_date)::DATE AS first_contract, max(deal_date)::DATE AS last_contract FROM read_parquet(?)', [str(path)])[0]
        files.append(entry)
    scope_path = EPISODE / 'research/top20-8min-v2/price_context.json'
    scope = json.loads(scope_path.read_text(encoding='utf-8'))['geography_crosswalk']
    monthly_sql = """SELECT sigungu_code, strftime(deal_date, '%Y-%m') AS contract_month,
        count(*) AS source_n, count(*) FILTER (WHERE is_canceled IS FALSE AND cancel_date IS NULL) AS noncanceled_n,
        count(*) FILTER (WHERE is_canceled IS FALSE AND cancel_date IS NULL AND area_m2 BETWEEN 83 AND 85 AND deal_amount>0) AS area83_85_n,
        min(deal_date)::DATE AS first_contract, max(deal_date)::DATE AS last_contract
        FROM read_parquet(?) WHERE deal_date >= DATE '2026-04-01' GROUP BY 1,2 ORDER BY 1,2"""
    all_monthly = records(con, monthly_sql, [str(ROOT / paths[0])])
    region_coverage = []
    for region in scope:
        monthly = [r for r in all_monthly if r['sigungu_code'] in region['current_cache_codes']]
        region_coverage.append({**region, 'months_by_current_code': monthly,
                                'latest_observed_contract': max(str(r['last_contract']) for r in monthly)})
    with sqlite3.connect((ROOT / 'legacy/realestate.db').as_uri() + '?mode=ro', uri=True) as sqlcon:
        sqlcon.execute('PRAGMA query_only=ON')
        sqlite_tables = [r[0] for r in sqlcon.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        sqlite_schema = {name: sqlcon.execute('PRAGMA table_info("' + name + '")').fetchall() for name in ['apt_master', 'apt_external']}
    checked = datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    write('freshness.json', {'checked_at': checked, 'files': files, 'scope': region_coverage,
        'sqlite': {'path': 'legacy/realestate.db', 'open_mode': 'mode=ro; PRAGMA query_only=ON', 'tables': sqlite_tables, 'schema': sqlite_schema,
                   'finding': '거래 테이블 없음. 거래 근거는 master/trade_events.parquet이며 legacy DB는 시설·단지 보조정보입니다.'},
        'requested_window': ['2026-05-01', '2026-10-31'],
        'requested_window_gap': '원거래 전체 최신 계약일 2026-10-10. 10월11~31일은 관측되지 않아 요청한 5~10월 전체를 현재 가격으로 표시할 수 없습니다.',
        'proposed_primary_window': ['2026-04-01', '2026-09-30'],
        'completeness_limit': '달력상 종료된 6개월을 선택합니다. 지역별 원천 수집·지연신고·사후 해제의 완전성은 보장하지 않습니다.',
        'can_compute_now': ['20지역 83~85㎡ 아파트 매매 관측 중위값·표본수·거래기간', '동일 조건 단지별 중위값 및 대표 사례 후보', '원거래 해제 표시 직접 제외 및 deal_hash 근거', '실주소·좌표 매칭 상태를 구분한 지도 입력'],
        'cannot_verify_now': ['현재 판매 가능한 매물·호가', '10월 전체 거래', '최신 사후 해제 반영', '개별 거래의 중개/직거래 구분'],
        'sql': monthly_sql, 'external_data_api_called': False})
    issue = {'issue_id': 'PRICE-FRESHNESS-V3', 'scene_ids': ['S%03d' % n for n in range(3,23)],
        'problem': '요청한 5~10월 전체 거래와 현재 호가를 로컬 자료로 검증할 수 없습니다.',
        'evidence': 'freshness.json: master 최신 계약 2026-10-10, 서빙 캐시 2026-10-05. 기존 listing_evidence_v1의 현재 판매 확인 매물 0건.',
        'proposal': '4~9월 동일 조건 관측 실거래를 우선 계산하고 현재가라는 표현을 보류합니다. 무료 원천 API 갱신은 총괄의 범위 결정 이후 별도 수행합니다.',
        'impact': '20지역 가격 장면의 기준기간·표제·대본 표현. 기존 순위와 지역 범위는 유지합니다.',
        'to': ['director', 'writer', 'visual'], 'direct_message_tool_available': False}
    write('issue_PRICE-FRESHNESS-V3.json', issue)
    print(json.dumps({'freshness': str(HERE / 'freshness.json'), 'master_latest': files[0]['coverage']['last_contract'],
                      'cache_latest': files[2]['coverage']['last_contract'], 'region_count':len(scope),
                      'suggested_window': ['2026-04-01','2026-09-30']}, ensure_ascii=False, default=str))
