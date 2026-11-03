from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def facts():
    import pandas as pd
    path=Path(__file__).parent/'cache/complex_facts.parquet'
    if not path.exists():return {}
    frame=pd.read_parquet(path).astype(object)
    frame=frame.where(frame.notna(),None)
    return {row['apt_id']:row for row in frame.to_dict('records')}


def lookup(apt_id):
    return facts().get(apt_id, {'household_count':None,'building_count':None})
