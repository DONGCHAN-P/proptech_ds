"""Step 2: raw XML -> staged parquet + apt_id_map

Patch v1.1 (2026-05-03):
  - 법정동코드를 진짜 umdCd(RTMS 응답)로 사용. 가짜 sha256[:5] 폐기.
  - attach_apt_id 벡터화 (per-row apply 제거, 약 10배 가속).
  - keep 컬럼에 umd_cd 보존.
"""
import sys
import hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import *
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher

print('환경 준비 완료')

SECRETS = load_secrets()

COL_RENAME_TRADE = {
    # 새 영어 필드명 (apis.data.go.kr)
    'aptNm':        'apt_name_raw',
    'aptSeq':       'apt_seq',
    'buildYear':    'build_year_raw',
    'dealYear':     'year_raw',
    'dealMonth':    'month_raw',
    'dealDay':      'day_raw',
    'umdNm':        'legal_dong_name',
    'umdCd':        'umd_cd',
    'excluUseAr':   'area_m2_raw',
    'jibun':        'jibun',
    'sggCd':        'sigungu_code',
    'floor':        'floor_raw',
    'roadNm':       'road_name',
    'roadNmBonbun': 'road_main_no',
    'cdealType':    'is_canceled_raw',   # 비어있으면 정상, 값 있으면 해제
    'cdealDay':     'cancel_date_raw',
    'dealAmount':   'deal_amount_raw',
}


def clean_trade_xml(xml_path: Path) -> pd.DataFrame:
    xml_text = xml_path.read_text(encoding='utf-8')
    root = ET.fromstring(xml_text)
    items = root.findall('.//item')
    rows = [{c.tag: (c.text or '').strip() for c in item} for item in items]
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns=COL_RENAME_TRADE)

    df['deal_amount'] = pd.to_numeric(
        df['deal_amount_raw'].str.replace(',', '', regex=False), errors='coerce'
    )
    df['build_year'] = pd.to_numeric(df.get('build_year_raw', pd.Series(dtype=str)), errors='coerce').astype('Int64')
    df['area_m2'] = pd.to_numeric(df.get('area_m2_raw', pd.Series(dtype=str)), errors='coerce')
    df['floor'] = pd.to_numeric(df.get('floor_raw', pd.Series(dtype=str)), errors='coerce').astype('Int64')

    df['deal_date'] = pd.to_datetime(
        df['year_raw'].astype(str).str.zfill(4) + '-' +
        df['month_raw'].astype(str).str.zfill(2) + '-' +
        df['day_raw'].astype(str).str.zfill(2),
        errors='coerce'
    )

    # cdealType: 비어있으면 정상거래, 값 있으면 해제
    df['is_canceled'] = df.get('is_canceled_raw', pd.Series('')).fillna('').str.strip().ne('')
    df['cancel_date'] = pd.to_datetime(
        df.get('cancel_date_raw', pd.Series(dtype=str)), format='%Y%m%d', errors='coerce'
    )
    df['pyeong_bucket'] = df['area_m2'].apply(
        lambda x: to_pyeong_bucket(x) if pd.notna(x) else None
    )
    df['area_m2_key'] = df['area_m2'].apply(
        lambda x: round(x, 2) if pd.notna(x) else None
    )
    df['apt_name_norm'] = df['apt_name_raw'].apply(normalize_apt_name)

    keep = ['sigungu_code', 'umd_cd', 'legal_dong_name', 'jibun', 'road_name', 'road_main_no',
            'apt_name_raw', 'apt_name_norm', 'apt_seq',
            'deal_date', 'deal_amount', 'area_m2', 'area_m2_key', 'pyeong_bucket',
            'floor', 'build_year', 'is_canceled', 'cancel_date']
    return df[[c for c in keep if c in df.columns]]


# Patch v1.1: 가짜 sha256[:5] 법정동코드 → RTMS 응답의 진짜 umdCd(5자리) 사용.
# 옛 함수는 호환을 위해 deprecated alias로 남김.
def make_legal_dong_code_legacy(sigungu_code: str, legal_dong_name: str) -> str:
    """[DEPRECATED] sigungu+sha256(name)[:5]. 행안부 표준 코드와 호환 안 됨."""
    import hashlib
    raw = f'{sigungu_code}|{(legal_dong_name or "").strip()}'
    h = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:5]
    return f'{sigungu_code}{h}'


def attach_apt_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ── 진짜 법정동코드: 시군구 5 + umdCd 5 = 10자리 ───────────────
    # umd_cd 컬럼은 clean_trade_xml에서 RTMS 응답의 umdCd를 받아둠.
    sgg = df['sigungu_code'].fillna('').astype(str).str.zfill(5).str[:5]
    umd = df.get('umd_cd', pd.Series([''] * len(df))).fillna('').astype(str).str.strip().str.zfill(5).str[:5]
    # umdCd가 비어있으면 시군구만 + '_NA' 표식 (집계 단계에서 노출)
    df['legal_dong_code'] = (sgg + umd).where(umd.ne('00000') & umd.ne(''),
                                               sgg + '_NA')

    # ── 도로명주소(앞 30자) ──────────────────────────────────────
    road_main = df.get('road_main_no', pd.Series([''] * len(df))).fillna('').astype(str)
    road_nm = df.get('road_name', pd.Series([''] * len(df))).fillna('').astype(str)
    df['road_address'] = (road_nm + ' ' + road_main).str.strip()

    # ── apt_id: SHA256 16자리. 벡터화 ─────────────────────────────
    # apt_name_norm은 clean_trade_xml에서 이미 정규화된 컬럼.
    apt_name_norm = df.get('apt_name_norm', df['apt_name_raw'].apply(normalize_apt_name))
    raw_keys = (df['legal_dong_code'].astype(str)
                + '|' + apt_name_norm.fillna('').astype(str)
                + '|' + df['road_address'].astype(str).str.slice(0, 30))

    df['apt_id'] = raw_keys.map(
        lambda k: hashlib.sha256(k.encode('utf-8')).hexdigest()[:16]
    )
    return df


def _staged_is_fresh(xml_path: Path, out_path: Path) -> bool:
    """v1.1 멱등성: staged parquet이 raw XML보다 최신이고, 같은 코드 버전으로
    만들어졌으면 재생성 건너뛰기. CODE_VERSION을 바꾸면 강제 재생성됨."""
    if not out_path.exists():
        return False
    try:
        if out_path.stat().st_mtime <= xml_path.stat().st_mtime:
            return False
        # 코드 버전 비교 (옆의 .ver 파일)
        ver_file = out_path.with_suffix('.parquet.ver')
        if not ver_file.exists():
            return False
        return ver_file.read_text().strip() == CODE_VERSION
    except Exception:
        return False


# 코드 변경 시 이 값을 올리면 모든 staged 강제 재생성. apt_id 정의 바뀔 때마다 ↑.
CODE_VERSION = 'v1.1-umd_cd'


def stage_all_raw_trade(force: bool = False) -> pd.DataFrame:
    """raw XML → staged parquet.

    force=True: 모든 파일 재처리.
    force=False(기본): staged가 raw보다 최신이고 CODE_VERSION 일치하면 skip.
    """
    results = []
    xml_files = list(DIRS['raw_trade'].rglob('*.xml'))
    print(f'처리할 XML 파일: {len(xml_files):,}개 (force={force}, code={CODE_VERSION})')

    skipped = 0
    for i, xml_path in enumerate(xml_files, 1):
        if i % 200 == 0:
            print(f'  진행: {i:,}/{len(xml_files):,} (skip: {skipped})')
        try:
            stem = xml_path.stem
            sigungu_code, ym = stem.split('_')
            yr, mo = ym[:4], ym[4:]
            out_dir = (DIRS['staged_trade'] / f'year={yr}' / f'month={mo}'
                       / f'sigungu={sigungu_code}')
            out_path = out_dir / 'part-0001.parquet'

            if not force and _staged_is_fresh(xml_path, out_path):
                skipped += 1
                results.append({'path': str(xml_path), 'rows': -1,
                                'staged': str(out_path), 'status': 'SKIP'})
                continue

            df = clean_trade_xml(xml_path)
            if len(df) == 0:
                results.append({'path': str(xml_path), 'rows': 0, 'status': 'EMPTY'})
                continue

            df = attach_apt_id(df)
            out_dir.mkdir(parents=True, exist_ok=True)
            df.to_parquet(out_path, index=False, compression='zstd')
            # 멱등성용 버전 표식
            out_path.with_suffix('.parquet.ver').write_text(CODE_VERSION)
            results.append({'path': str(xml_path), 'rows': len(df),
                            'staged': str(out_path), 'status': 'OK'})
        except Exception as e:
            results.append({'path': str(xml_path), 'rows': 0,
                            'status': 'ERROR', 'error': str(e)})

    summary = pd.DataFrame(results)
    ok = (summary.status == 'OK').sum()
    skip = (summary.status == 'SKIP').sum()
    print(f'정제 완료: OK={ok}, SKIP={skip}, 신규 행={summary[summary.status=="OK"].rows.sum():,}건')
    if (summary.status == 'ERROR').any():
        print('에러:')
        print(summary[summary.status == 'ERROR'][['path', 'error']].to_string())
    return summary


def build_apt_id_map(min_score: float = 0.85) -> pd.DataFrame:
    trade_files = list(DIRS['staged_trade'].rglob('*.parquet'))
    if not trade_files:
        print('staged 거래 파일 없음')
        return pd.DataFrame()

    print(f'staged 파일 로드 중... ({len(trade_files):,}개)')
    dfs = [pd.read_parquet(p) for p in trade_files]
    df_trade = pd.concat(dfs, ignore_index=True)

    apt_unique = (
        df_trade
        .groupby(['apt_id', 'sigungu_code', 'legal_dong_code',
                  'legal_dong_name', 'apt_name_norm', 'road_address'])
        .size()
        .reset_index(name='trade_count')
    )
    print(f'거래 단지 수: {len(apt_unique):,}')

    apt_snaps = sorted(DIRS['staged_apt_info'].glob('snapshot=*.parquet'))
    if not apt_snaps:
        print('K-apt 스냅샷 없음. RTMS 단독으로 생성.')
        df_map = apt_unique.copy()
        df_map['kapt_code'] = None
        df_map['match_score'] = 0.0
        df_map['match_status'] = 'rtms_only'
        return df_map

    df_kapt = pd.read_parquet(apt_snaps[-1])
    df_kapt['kapt_name_norm'] = df_kapt['kaptName'].apply(normalize_apt_name)

    matches = []
    for _, row in apt_unique.iterrows():
        candidates = df_kapt[df_kapt['sigungu_code'] == row['sigungu_code']]
        if len(candidates) == 0:
            matches.append({**row.to_dict(), 'kapt_code': None,
                            'match_score': 0.0, 'match_status': 'no_candidate'})
            continue
        candidates = candidates.copy()
        candidates['score'] = candidates['kapt_name_norm'].apply(
            lambda x: SequenceMatcher(None, row['apt_name_norm'], x).ratio()
        )
        best = candidates.loc[candidates['score'].idxmax()]
        if best['score'] >= min_score:
            status = 'auto_matched'
        elif best['score'] >= 0.70:
            status = 'review_needed'
        else:
            status = 'rtms_only'
        matches.append({
            **row.to_dict(),
            'kapt_code': best['kaptCode'] if status != 'rtms_only' else None,
            'match_score': float(best['score']),
            'match_status': status,
        })

    df_map = pd.DataFrame(matches)
    print('\n매칭 결과:')
    print(df_map['match_status'].value_counts())
    return df_map


# ── 실행 ──────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true',
                        help='멱등성 우회. apt_id 정의 바꾼 후 첫 실행 시 권장.')
    parser.add_argument('--skip-map', action='store_true',
                        help='apt_id_map 빌드 건너뛰기 (stage만)')
    args = parser.parse_args()

    print('\n=== Step 2-1: raw XML -> staged parquet ===')
    stage_summary = stage_all_raw_trade(force=args.force)

    if args.skip_map:
        print('\n=== Step 2-2 skipped (--skip-map) ===')
    else:
        print('\n=== Step 2-2: apt_id_map 빌드 ===')
        df_apt_map = build_apt_id_map()

        if len(df_apt_map) > 0:
            out_path = DIRS['master'] / 'apt_id_map.parquet'
            df_apt_map.to_parquet(out_path, index=False, compression='zstd')
            print(f'\napt_id_map 저장: {out_path} ({len(df_apt_map):,}개 단지)')

            review = df_apt_map[df_apt_map['match_status'] == 'review_needed']
            if len(review) > 0:
                log_path = DIRS['logs'] / f'apt_match_review_{datetime.now().strftime("%Y%m%d")}.csv'
                review.to_csv(log_path, index=False, encoding='utf-8-sig')
                print(f'검수 큐 저장: {log_path} ({len(review)}건)')

    print('\nStep 2 완료.')
