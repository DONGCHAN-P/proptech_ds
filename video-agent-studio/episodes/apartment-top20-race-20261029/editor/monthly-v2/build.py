"""Build versioned monthly HyperFrames race; no paid calls, no old artifacts overwritten."""
from pathlib import Path
import hashlib, json, shutil
from PIL import ImageFont

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
PROJECT=HERE/'project'
ASSETS=PROJECT/'assets'
SOURCE=EP/'research/monthly-v2/data.json'

def main():
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    frames=data['frames']; complexes=data['complexes']
    assert len(frames)==235 and frames[0]['period']=='2006-12' and frames[-1]['period']=='2026-06'
    ASSETS.mkdir(parents=True,exist_ok=True)
    for name in ['Pretendard-Regular.ttf','Pretendard-Bold.ttf','gsap.min.js','original_race_pulse.wav']:
        shutil.copyfile(EP/'editor/project/assets'/name,ASSETS/name)
    for name in ['hyperframes.json','meta.json']:
        shutil.copyfile(EP/'editor/project'/name,PROJECT/name)
    registry=PROJECT/'compositions'
    registry.mkdir(exist_ok=True)
    shutil.copyfile(EP/'editor/project/compositions/bar-chart-race.html',registry/'bar-chart-race.html')
    oldlabels=json.loads((EP/'editor/labels.json').read_text(encoding='utf-8'))
    labels={}
    for cid,v in complexes.items():
        name=v.get('display_name') or v['name']; size=30
        while size>22 and ImageFont.truetype(str(ASSETS/'Pretendard-Bold.ttf'),size).getlength(name)>365:
            size-=1
        assert ImageFont.truetype(str(ASSETS/'Pretendard-Bold.ttf'),size).getlength(name)<=365,(cid,name)
        color=oldlabels.get(cid,{}).get('color') or ['#168A91','#C37835','#667CA6','#8876A5','#6A8A74','#9C736C','#7C8C50','#887D62'][int(hashlib.sha256(cid.encode()).hexdigest()[:8],16)%8]
        labels[cid]={'name':name,'full_name':v['name'],'region':v['region'],'location':v.get('location',''),'font_size':size,'color':color}
    compact=[]
    for frame in frames:
        rows=[]
        for r in frame['top']:
            rows.append({'id':r['id'],'v':r['median_manwon']/10000,'n':r['n'],'r':r['rank']-1,
                         'asof':r['quote_asof_month'],'carried':r['carried']})
        compact.append({'p':frame['period'],'rows':rows,'leader':rows[0]['id']})
    timing={'duration':56.8,'fps':60,'first_hold':2.2,'race_end':48.8,'final_hold':8.0,'CTA_start':52.8,
            'month_step':46.6/(len(frames)-1),'period_count':len(frames),
            'interpolation':'monotone cubic Hermite, C1; no monthly holds; constant carried prices',
            'label_policy':'continuous rear-label contrast 0.1..1 during overtaking, no hard label switch; entry/exit fades at bottom slot; no opaque card slicing'}
    payload={'frames':compact,'labels':labels,'timing':timing}
    (ASSETS/'race_data.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    doc=(HERE/'template.html').read_text(encoding='utf-8')
    for key,value in [('PAYLOAD',json.dumps(payload,ensure_ascii=False)),('DURATION',str(timing['duration']))]:
        doc=doc.replace('__'+key+'__',value)
    (PROJECT/'index.html').write_text(doc,encoding='utf-8')
    shutil.copyfile(HERE/'design.md',PROJECT/'BRIEF.md')
    (HERE/'timing.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2),encoding='utf-8')
    (HERE/'labels.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={'source_data':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'source_html_sha256':hashlib.sha256(doc.encode()).hexdigest(),'duration':56.8,'fps':60,
              'months':len(frames),'complexes_in_race':len(complexes),'font_sizes':sorted({v['font_size'] for v in labels.values()}),
              'new_paid_calls':0,'music':'previous original self-composed 56.8s motif; no new external music',
              'old_quarterly_version_preserved':True}
    (HERE/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__': main()
