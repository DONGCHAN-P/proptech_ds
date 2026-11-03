"""Conservative exact-address join to the already downloaded official complex data."""
import sys, re, json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def number(value):
    text = str(value).strip()
    return str(int(text)) if text.isdigit() else ''


def build():
    source = ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/coordinate-link-v2/official_attributes.parquet'
    facts = pd.read_parquet(source)
    facts['key'] = facts.apply(lambda r: '|'.join([str(r.SIGNGU_CD),str(r.RN).strip(),number(r.ROAD_HMNO),number(r.ROAD_VCNO) or '0']),axis=1)
    # Even equal counts at shared addresses do not establish one-to-one identity.
    unique = facts[~facts['key'].duplicated(keep=False)].set_index('key')
    apt = pd.read_parquet(ROOT/'web/cache/apt_index.parquet')
    address_counts=apt.groupby(['sigungu_code','road_address']).size()
    result=[]
    for r in apt.itertuples():
        if address_counts.get((r.sigungu_code,r.road_address),0)!=1:continue
        m=re.fullmatch(r'(.+?)\s+(\d+)(?:-(\d+))?',str(r.road_address).strip())
        if not m: continue
        key='|'.join([str(r.sigungu_code),m[1],number(m[2]),number(m[3]) or '0'])
        if key not in unique.index: continue
        f=unique.loc[key]; count=number(f.NMHSH)
        if not count or int(count)<=0: continue
        result.append(dict(apt_id=r.apt_id,household_count=int(count),building_count=int(number(f.DONG_CNT) or 0) or None,
                           household_source='한국부동산원 공동주택 단지 연계정보',household_match='시군구·도로명·건물번호 단일 일치',
                           household_record_id=str(f.HSMP_INNB)))
    output=ROOT/'web/cache/complex_facts.parquet'
    pd.DataFrame(result).to_parquet(output,index=False)
    print(json.dumps({'matched':len(result),'total':len(apt),'ambiguous_addresses_excluded':True}))


if __name__=='__main__':build()
