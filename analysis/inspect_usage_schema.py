from pathlib import Path
import json,sqlite3
f=next(Path('C:/Users/e2ken/.codex/sessions/2026/10/14').glob('*01a13a00*.jsonl'))
records=[]
for line in f.open(encoding='utf8'):
    d=json.loads(line)
    if d.get('type')=='token_usage_record': records.append(d)
for d in [records[0],records[-1]]: print(json.dumps(d,ensure_ascii=False)[:3500])
c=sqlite3.connect('file:C:/Users/e2ken/.codex/state_5.sqlite?mode=ro',uri=True)
print('tables',c.execute("select name from sqlite_master where type='table'").fetchall())
print('threadcols',c.execute('pragma table_info(threads)').fetchall())
