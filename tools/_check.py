from pathlib import Path
import datetime, json

files = sorted(
    Path('raw/rtms_trade').rglob('*.xml'),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)[:5]

print("=== 최근 수정된 XML ===")
for f in files:
    t = datetime.datetime.fromtimestamp(f.stat().st_mtime)
    print(f"{t.strftime('%H:%M:%S')}  {f.parent.parent.name}/{f.parent.name}/{f.name}  {f.stat().st_size}B")

# meta.json에서 mock=False인 파일 수
meta_files = list(Path('raw/rtms_trade').rglob('*.meta.json'))
real_count = sum(
    1 for m in meta_files
    if not json.loads(m.read_text(encoding='utf-8')).get('mock', True)
)
print(f"\n실제 수집된 파일: {real_count} / {len(meta_files)}")
