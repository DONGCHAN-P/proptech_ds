from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
import pytest
from artifacts import digest_frame,require_identity,freeze_release,require_complete_grid
import json

def test_future_target_revision_changes_identity():
    d=pd.DataFrame({'month':['2026-07'],'log_change':[.01]})
    old=digest_frame(d)
    d.loc[0,'log_change']=.02
    assert old!=digest_frame(d)

def test_renamed_feature_changes_identity():
    d=pd.DataFrame({'a':[1.]})
    assert digest_frame(d)!=digest_frame(d.rename(columns={'a':'b'}))

def test_mismatched_specs_are_refused_by_consumer():
    with pytest.raises(ValueError,match='identity'):
        require_identity({'model':'old'},{'model':'new'})

def test_releases_preserve_old_forecast_bytes(tmp_path):
    source=tmp_path/'pred.csv';source.write_text('first','utf-8')
    a=freeze_release(tmp_path/'releases',{'pred.csv':source},{'config':'a'})
    source.write_text('second','utf-8')
    b=freeze_release(tmp_path/'releases',{'pred.csv':source},{'config':'b'})
    assert a!=b and (a/'pred.csv').read_text('utf-8')=='first'
    assert (b/'pred.csv').read_text('utf-8')=='second'

def test_tampered_completed_release_is_not_silently_replaced(tmp_path):
    source=tmp_path/'p.csv';source.write_text('first','utf-8')
    a=freeze_release(tmp_path/'releases',{'p.csv':source},{})
    (a/'p.csv').write_text('tampered','utf-8')
    with pytest.raises(ValueError,match='modified'):
        freeze_release(tmp_path/'releases',{'p.csv':source},{})

def test_tampered_manifest_metadata_is_rejected(tmp_path):
    source=tmp_path/'p.csv';source.write_text('first','utf-8')
    release=freeze_release(tmp_path/'releases',{'p.csv':source},{'as_of':'2026'})
    manifest=release/'release.json';data=json.loads(manifest.read_text('utf-8'))
    data['metadata']['as_of']='2099';manifest.write_text(json.dumps(data),'utf-8')
    with pytest.raises(ValueError,match='manifest'):
        freeze_release(tmp_path/'releases',{'p.csv':source},{'as_of':'2026'})

def test_missing_origin_and_partial_model_grid_are_rejected():
    dates=pd.to_datetime(['2020-01-01','2020-07-01'])
    full=pd.DataFrame([dict(origin=d,model=m,series_id='a') for d in dates for m in ['x','y']])
    require_complete_grid(full,dates,['x','y'])
    for missing in [full.iloc[:2],full.iloc[:-1]]:
        with pytest.raises(ValueError,match='grid'):
            require_complete_grid(missing,dates,['x','y'])
