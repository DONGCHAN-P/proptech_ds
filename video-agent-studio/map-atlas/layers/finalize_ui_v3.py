from pathlib import Path
import json
H=Path(__file__).resolve().parents[1]
p=H/'src/app.js';s=p.read_text(encoding='utf8')
needle="});el('found').textContent=`검색"
s=s.replace(needle,"}).sort((i,j)=>Number(items[j].name.toLowerCase()===q)-Number(items[i].name.toLowerCase()===q));el('found').textContent=`검색")
s=s.replace('if(selected!==null&&filtered.includes(selected))','if(!el(\'complex-labels\').checked&&selected!==null&&filtered.includes(selected))')
s=s.replace('let metres=1000;for(const n of [100,200,500,1000,2000,5000,10000,20000,50000])','let metres=10;for(const n of [10,20,50,100,200,500,1000,2000,5000,10000,20000,50000])')
p.write_text(s,encoding='utf8')
p=H/'src/explorer.js';s=p.read_text(encoding='utf8').replace('if(x<350||x>W-40','if(x<(W<=850?20:390)||x>W-40');p.write_text(s,encoding='utf8')
