from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
print(pq.read_schema(ROOT / 'master/trade_events.parquet'))
for city in ('busan', 'daegu', 'daejeon', 'gwangju', 'sejong'):
    folder = next((ROOT / 'raw/rtms_trade_expansion').glob(f'*/{city}'))
    files = sorted(folder.glob('*/*.xml'), reverse=True)
    for file in files:
        tree = ET.parse(file)
        item = tree.find('.//items/item')
        if item is not None:
            print(json.dumps({'city':city, 'file':file.relative_to(ROOT).as_posix(),
                              'sample':{c.tag:c.text for c in item}}, ensure_ascii=False))
            break
try:
    import matplotlib
    print('matplotlib', matplotlib.__version__)
except ImportError:
    print('matplotlib unavailable')
