"""Isolated regional comparison; never modifies raw files or the production master."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/housing_growth_2006/regional_expansion_v1'
OUT.mkdir(exist_ok=True)
END = pd.Period('2026Q2', freq='Q')
CITY = {'busan':'부산', 'daegu':'대구', 'daejeon':'대전', 'gwangju':'광주', 'sejong':'세종'}
ORDER = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '세종']
COLUMNS = ['apt_id', 'area_m2_key', 'deal_date', 'sigungu_code', 'deal_amount', 'area_m2', 'is_canceled', 'deal_hash']


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')


def normalize_expansion():
    cache = OUT / 'expansion_normalized.parquet'
    if cache.exists():
        return pd.read_parquet(cache), json.loads((OUT/'normalization.json').read_text(encoding='utf8'))
    rows, files, api_counts = [], [], {}
    for city, region in CITY.items():
        folder = next((ROOT/'raw/rtms_trade_expansion').glob(f'*/{city}'))
        api_counts[region] = 0
        for file in sorted(folder.glob('*/*.xml')):
            meta_path = file.parent / (file.name.split('.page')[0]+'.meta.json')
            if not meta_path.exists() or not json.loads(meta_path.read_text(encoding='utf8')).get('complete'):
                continue
            content = file.read_bytes()
            files.append((file.relative_to(ROOT).as_posix(), hashlib.sha256(content).hexdigest()))
            tree = ET.fromstring(content)
            assert tree.findtext('.//resultCode') in ('000', '00', '0'), file
            for item in tree.findall('.//items/item'):
                v = {c.tag:(c.text or '').strip() for c in item}
                api_counts[region] += 1
                try:
                    amount = int(v['dealAmount'].replace(',', ''))
                    area = float(v['excluUseAr'])
                    date = pd.Timestamp(year=int(v['dealYear']), month=int(v['dealMonth']), day=int(v['dealDay']))
                    floor = int(v.get('floor') or 0)
                except (ValueError, KeyError):
                    rows.append({'region':region, 'parse_error':True})
                    continue
                code = v.get('sggCd') or file.name[:5]
                apt = v.get('aptSeq')
                fallback = '|'.join([code, v.get('umdNm',''), v.get('jibun',''), re.sub(r'\s+', '', v.get('aptNm','')), v.get('buildYear','')])
                apt_id = 'api:' + (apt or fallback)
                key = '|'.join([apt_id, date.strftime('%Y%m%d'), str(amount), str(area), str(floor), v.get('aptDong','')])
                rows.append(dict(region=region, apt_id=apt_id, area_m2_key=round(area, 2), deal_date=date,
                                 sigungu_code=code, deal_amount=amount, area_m2=area,
                                 is_canceled=v.get('cdealType','').upper() in ('O','Y','1') or bool(v.get('cdealDay')),
                                 deal_hash=hashlib.sha256(key.encode()).hexdigest(), parse_error=False,
                                 id_fallback=not bool(apt)))
        print(f'Parsed {city}: {api_counts[region]} rows', flush=True)
    data = pd.DataFrame(rows)
    audit = {'xml_files':len(files), 'source_manifest_sha256':hashlib.sha256(json.dumps(files).encode()).hexdigest(),
             'api_rows':api_counts, 'parse_errors':int(data.parse_error.sum()),
             'fallback_id_rows':int(data.id_fallback.fillna(False).sum())}
    save_json(OUT/'source_files.json', files)
    assert audit['parse_errors'] == 0, audit
    # A canceled and an uncanceled version of the same transaction key stays canceled.
    data['is_canceled'] = data.groupby('deal_hash').is_canceled.transform('max')
    before = len(data)
    data = data.drop_duplicates('deal_hash')
    audit['duplicate_transaction_keys_removed'] = before-len(data)
    audit['canceled_after_dedup'] = int(data.is_canceled.sum())
    data.to_parquet(cache, index=False)
    save_json(OUT/'normalization.json', audit)
    return data, audit


new, normalization = normalize_expansion()
master = pq.read_table(ROOT/'master/trade_events.parquet', columns=COLUMNS).to_pandas()
master['region'] = master.sigungu_code.str[:2].map({'11':'서울','41':'경기','28':'인천'})
assert master.region.notna().all(), 'Master region scope changed; review overlap before combining'
all_data = pd.concat([master, new[COLUMNS+['region']]], ignore_index=True)
# Recompute the key for both sources, including any older normalization cache.
all_data['area_m2_key'] = all_data.area_m2.round(2)
raw_count = len(all_data)
all_data = all_data[~all_data.is_canceled.fillna(False) & (all_data.deal_amount>0) & (all_data.area_m2>0) & all_data.apt_id.notna()].drop_duplicates('deal_hash').copy()
all_data['quarter'] = all_data.deal_date.dt.to_period('Q')
all_data = all_data[all_data.quarter.between(pd.Period('2006Q1'), END)].copy()
# Keep a fixed historical Daegu boundary; do not create a city-level jump at Gunwi's transfer.
gunwi = all_data.sigungu_code.isin(['27720','47720'])
gunwi_excluded = int(gunwi.sum())
all_data = all_data[~gunwi].copy()
all_data['ppm'] = all_data.deal_amount / all_data.area_m2

coverage = all_data.groupby('region').agg(transactions=('ppm','size'), complexes=('apt_id','nunique'),
    first_date=('deal_date','min'), last_date=('deal_date','max')).reset_index()
coverage.to_csv(OUT/'analysis_coverage.csv',index=False,encoding='utf-8-sig')
volume = all_data.groupby(['region','quarter']).agg(transactions=('ppm','size'),complexes=('apt_id','nunique')).reset_index()
volume['quarter'] = volume.quarter.astype(str)
volume.to_csv(OUT/'quarterly_volume.csv', index=False, encoding='utf-8-sig')
grouped = all_data.groupby(['region','quarter','apt_id','area_m2_key']).agg(p=('ppm','median'), n=('ppm','size')).reset_index()
del all_data, master, new

all_paths, summaries, sensitivities, gaps = [], [], [], []
for minimum in (2,3,5):
    g = grouped[grouped.n>=minimum].copy()
    prev = g.copy()
    prev.quarter += 1
    matched = g.merge(prev, on=['region','quarter','apt_id','area_m2_key'], suffixes=('','_prev'))
    matched['lr'] = np.log(matched.p/matched.p_prev)
    per_complex = matched.groupby(['region','quarter','apt_id']).lr.mean().reset_index()
    stats = per_complex.groupby(['region','quarter']).agg(lr=('lr','mean'),matched_complexes=('apt_id','size')).reset_index()
    for region in ORDER:
        s = stats[(stats.region==region) & (stats.matched_complexes>=30)].set_index('quarter').sort_index()
        if END not in s.index:
            gaps.append(dict(region=region,min_trades=minimum,reason='No supported endpoint',endpoint=str(END)))
            continue
        first_return = END
        while first_return-1 in s.index:
            first_return -= 1
        baseline = first_return-1
        chain = s.loc[first_return:END]
        index = pd.Series(np.exp(chain.lr.cumsum())*100, index=chain.index)
        index.loc[baseline] = 100.
        index = index.sort_index()
        if minimum==2:
            for q,val in index.items():
                all_paths.append(dict(region=region,quarter=str(q),index=float(val),
                                      matched_complexes=None if q==baseline else int(s.loc[q,'matched_complexes'])))
        peak_window = index[(index.index>=pd.Period('2020Q1')) & (index.index<=pd.Period('2022Q4'))]
        if len(peak_window)!=12:
            gaps.append(dict(region=region,min_trades=minimum,reason='Unsupported full 2020-2022 peak window',first_contiguous_quarter=str(baseline)))
            continue
        peak_q = peak_window.idxmax()
        peak = float(index.loc[peak_q])
        after = index.loc[peak_q:]
        trough_q = after.idxmin()
        trough = float(index.loc[trough_q])
        recovered = index[(index.index>trough_q) & (index>=peak)]
        record = dict(region=region,min_trades=minimum,first_contiguous_quarter=str(baseline),last_quarter=str(END),
                      peak_quarter=str(peak_q),trough_quarter=str(trough_q),drawdown_pct=(trough/peak-1)*100,
                      first_recovery_quarter=None if recovered.empty else str(recovered.index[0]),
                      latest_vs_peak_pct=(float(index.loc[END])/peak-1)*100,
                      latest_vs_trough_pct=(float(index.loc[END])/trough-1)*100,
                      min_matched_complexes=int(chain.matched_complexes.min()),
                      latest_matched_complexes=int(chain.loc[END,'matched_complexes']))
        for years in (3,5,10):
            start = END-years*4
            record[f'cagr_{years}y_pct'] = None if start not in index else (float(index.loc[END]/index.loc[start])**(1/years)-1)*100
        sensitivities.append(record)
        if minimum==2:
            summaries.append(record)

paths = pd.DataFrame(all_paths)
paths.to_csv(OUT/'quarterly_index.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(summaries).to_csv(OUT/'regional_summary.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(sensitivities).to_csv(OUT/'sensitivity.csv',index=False,encoding='utf-8-sig')
result = dict(endpoint=str(END),raw_rows=raw_count,normalization=normalization,
              included_regions=[r for r in ORDER if r in {s['region'] for s in summaries}],
              unavailable_regions=[r for r in ORDER if r not in {s['region'] for s in summaries}],
              gunwi_excluded_transactions=gunwi_excluded,summaries=summaries,sensitivity=sensitivities,gaps=gaps,
              method='Quarterly median price/m2 within identical complex and rounded 0.01m2 area; at least 2 trades per quarter per area; mean log return within complex then equal complex weights; consecutive quarter matching; each link at least 30 complexes. Main results use only contiguous supported paths ending 2026Q2.',
              limitations=['Exploratory custom index; not an official market index or investment return.',
                           'Changing matched sample, transaction selection and survivor biases; floor, building and renovation not controlled.',
                           'History before a supported contiguous run is not connected across gaps.',
                           '2026Q3 excluded because recently collected September contracts may still have unreported transactions.',
                           'New cities are collected at different dates from the existing metropolitan master; later cancellations and revisions can differ.',
                           'Daegu excludes Gunwi in all years to preserve a fixed historical boundary.',
                           'Sejong history uses only API code36110; historical administrative coverage is not assumed complete.',
                           'Transaction key deduplication can merge genuinely identical same-day transactions; original XML is preserved.',
                           '2020-2022 maximum is the reference cycle peak; recovery means first crossing after the observed trough, not sustained recovery.',
                           '3/5/10-year CAGR uses quarter-level observations, not annual medians or month-end prices; these are not the previously rendered video figures.'])
save_json(OUT/'results.json',result)
print(json.dumps({'included':result['included_regions'],'unavailable':result['unavailable_regions'],'summaries':summaries},ensure_ascii=False,indent=2))
