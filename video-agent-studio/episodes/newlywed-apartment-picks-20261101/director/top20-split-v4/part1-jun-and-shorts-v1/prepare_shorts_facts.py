"""Extract the exact accepted chart values; no new statistics or narration."""
from pathlib import Path
import re,json,html,hashlib
D=Path(__file__).resolve().parent;E=D.parents[2]
def main():
    rows=[];photos=json.loads((E/'visual/top20-split-v4/photo-transitions-v1/assets_v2.json').read_text(encoding='utf-8'));by={int(x['rank']):x for x in photos}
    for rank in range(20,10,-1):
        p=E/f'editor/top20-split-v4/part1-production-v1/final-v3/scenes/P01-R{rank}.html';s=p.read_text(encoding='utf-8')
        fields={name:[html.unescape(re.sub('<[^>]+>','',x))for x in re.findall('class="'+name+r'"[^>]*>(.*?)</div>',s)]for name in ['price-name','price-value','price-n','pane-title']}
        assert len(fields['price-name'])==len(fields['price-value'])==2,(rank,fields)
        pct=re.findall(r'--pct:([0-9.]+)%',s)
        rows.append({'rank':rank,'region_id':f'R{rank}','title':fields['pane-title'][0],
                     'rows':[{'label':fields['price-name'][i],'value':fields['price-value'][i],'sample':fields['price-n'][i],'bar_fraction':float(pct[i])/100}for i in range(2)],
                     'source_file':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'photo':by[rank]})
    (D/'shorts_visual_facts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:x[k]for k in ['rank','title','rows']}for x in rows],ensure_ascii=False))
if __name__=='__main__':main()
