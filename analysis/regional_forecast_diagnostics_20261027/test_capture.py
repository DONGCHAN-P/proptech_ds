from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
from capture_inputs import audit_rent

def test_empty_placeholder_is_counted_as_invalid_not_as_observation(tmp_path):
    folder=tmp_path/'2026/08/11110';folder.mkdir(parents=True)
    (folder/'empty.parquet').write_bytes(b'')
    pd.DataFrame({'deposit':[100.]}).to_parquet(folder/'valid.parquet',index=False)
    audit=audit_rent(tmp_path)
    block=audit['months']['2026/08']
    assert block['files']==2 and block['valid_files']==1 and block['rows']==1
    assert block['invalid_files']==1
    assert audit['invalid_paths']==['2026/08/11110/empty.parquet']
