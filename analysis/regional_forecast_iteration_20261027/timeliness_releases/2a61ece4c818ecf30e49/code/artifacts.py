"""Content identities and immutable forecast releases for repeated experiments."""
from pathlib import Path
import hashlib
import json
import pandas as pd

def digest_frame(frame):
    schema=[(str(c),str(t)) for c,t in zip(frame.columns,frame.dtypes)]
    payload=json.dumps(schema,ensure_ascii=False).encode()+pd.util.hash_pandas_object(frame,index=False).values.tobytes()
    return hashlib.sha256(payload).hexdigest()

def require_identity(recorded,current):
    if recorded!=current: raise ValueError('Producer dependency identity mismatch; rebuild explicitly')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def freeze_release(root,files,metadata):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    hashes={name:sha(path) for name,path in files.items()}
    identity={'metadata':metadata,'files':hashes}
    identifier=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    target=(root/identifier[:20]).resolve()
    if not target.is_relative_to(root): raise ValueError('Release outside root')
    manifest=target/'release.json'
    if target.exists():
        if not manifest.exists(): raise ValueError('Incomplete release; refusing overwrite')
        previous=json.loads(manifest.read_text('utf-8'))
        expected=json.loads(json.dumps({**identity,'release_id':identifier,'complete':True},default=str))
        if previous!=expected: raise ValueError('Frozen release manifest was modified')
        for name,expected in hashes.items():
            if sha(target/name)!=expected: raise ValueError('Frozen release was modified')
        return target
    target.mkdir()
    for name,source in files.items():
        dest=(target/name).resolve()
        if not dest.is_relative_to(target): raise ValueError('Invalid release filename')
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream: stream.write(Path(source).read_bytes())
        if sha(dest)!=hashes[name]: raise ValueError('Release copy mismatch')
    payload={**identity,'release_id':identifier,'complete':True}
    with manifest.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2,default=str)
    return target

def require_complete_grid(data,origins,models):
    observed=set(zip(pd.to_datetime(data.origin),data.model))
    expected={(pd.Timestamp(origin),model) for origin in origins for model in models}
    if observed!=expected or data.duplicated(['origin','model','series_id']).any():
        raise ValueError('Incomplete or duplicate origin/model/cohort grid')
