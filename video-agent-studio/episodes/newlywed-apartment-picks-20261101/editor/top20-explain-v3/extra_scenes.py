"""Importable independent analysis scenes; no fixed scene count or Shorts side effects.

External modules may expose SCENE_RENDERERS={scene_id: callable(scene, context)}.
--scene-data accepts {"scenes": {"N003": {"type":"rank_criteria",...}}}.
Every datum is final, never count-animated. Word anchors reveal row emphasis.
"""
from pathlib import Path
import importlib.util,json

BLUE='#286cda';INK='#173348';MUTED='#536873';TEAL='#167f86'

SPECS={
 'N001':{'type':'rank_criteria','rows':[
  {'name':'인천 옛 서구','total_rank':1,'first_rank':1,'anchor':'1위부터'},
  {'name':'서울 송파구','total_rank':2,'first_rank':2,'anchor':'1위부터'},
  {'name':'고양시 덕양구','total_rank':3,'first_rank':3,'anchor':'1위부터'},
  {'name':'서울 강서구','total_rank':4,'first_rank':4,'anchor':'1위부터'},
  {'name':'안양시 동안구','total_rank':22,'first_rank':16,'first_count':6510,'anchor':'안양시 동안구'},
  {'name':'서울 마포구','total_rank':21,'first_rank':17,'first_count':6487,'anchor':'서울 마포구'}],
  'takeaway':'1–4위는 같지만, TOP20에 들어오는 지역은 달라진다'},
 'N002':{'type':'rank_criteria','rows':[
  {'name':'인천 남동구','total_rank':16,'first_rank':27,'first_count':5588,'anchor':'인천 남동구'},
  {'name':'부천시 원미구','total_rank':20,'first_rank':24,'first_count':5982,'anchor':'부천 원미구'},
  {'name':'인천 미추홀구','total_rank':10,'first_rank':20,'first_count':6162,'anchor':'인천 미추홀구'}],
  'takeaway':'어떤 부부를 세는지에 따라, 살펴볼 지역 목록도 달라진다'}
}

def rank_criteria(s,c):
    spec=s.get('visual') or c['extra_specs'][s['scene_id']]
    txt,box,tween=c['txt'],c['box'],c['tween'];P=s['scene_id'];rows=spec['rows'];ss='';an=''
    # Stable two-column row diagram: horizontal dimension is criterion, never time.
    ss+=txt('지역',100,226,560,24,700,MUTED)+txt('전체 기준',760,217,290,34,700)+txt('초혼 기준',1180,217,290,34,700,BLUE)+txt('초혼 부부 수',1580,226,250,24,700,MUTED)
    ss+=box(100,274,1735,2,'#dfe4e5',0)
    n=len(rows);step=82 if n>3 else 150;top=296 if n>3 else 315
    for i,r in enumerate(rows):
        yy=top+i*step;pid=f'{P}-row-{i}';active=r['total_rank']!=r['first_rank'];col=BLUE if active else MUTED
        # Names and total criterion stay as a reading scaffold; first criterion arrives at the spoken row.
        ss+=txt(r['name'],100,yy,610,34 if n>3 else 43,700,INK)
        ss+=txt(f'{r["total_rank"]}위',760,yy-3,220,43 if n>3 else 57,700,INK)
        ss+=box(984,yy+24,145,3,'#dfe4e5',0)
        ss+=box(984,yy+24,145,3,col,0,id=pid+'-link')
        ss+=txt(f'{r["first_rank"]}위',1180,yy-3,220,43 if n>3 else 57,700,col,id=pid+'-rank')
        at=c['exact'](s,'row_'+str(i),[r['anchor']])
        if at is not None:
            an+=tween('#'+pid+'-link',{'scaleX':0},{'scaleX':1},at,.42)+tween('#'+pid+'-rank',{'opacity':0},{'opacity':1},at,.25)
        ss+=box(100,yy+(68 if n>3 else 119),1735,1,'#dfe4e5',0)
        if 'first_count' in r:
            ss+=txt(f'{r["first_count"]:,}쌍',1560,yy+1,275,32 if n>3 else 40,700,col,id=pid+'-count')
            # N002 counts are a static evidence label, not spoken as extra narration.
            if P=='N001':
                a=c['exact'](s,'first_count_'+str(i),c['number_aliases'](r['first_count']))
                if a is not None:an+=tween('#'+pid+'-count',{'opacity':0},{'opacity':1},a,.25)
    ss+=txt(spec['takeaway'],100,829,1740,29,700,BLUE)
    # Subtitle/source rail is external. No direction arrows imply a future/year axis.
    return ss,an

def load_renderers(c,data_file=None,modules=()):
    import copy
    specs=copy.deepcopy(SPECS)
    if any(s['scene_id'] in SPECS for s in c['scenes']):
        verified=c['E']/'research/top20-enhance-v2/verified_facts.json'
        facts=json.loads(verified.read_text(encoding='utf-8-sig'));c['inputs'].append(verified)
        byid={f['claim_id']:f for f in facts['facts']}
        for sid,claims in [('N001',['ENH2-DONGAN','ENH2-MAPO']),('N002',['ENH2-NAMDONG','ENH2-WONMI','ENH2-MICHUHOL'])]:
            target_rows=specs[sid]['rows'][-len(claims):]
            for row,claim in zip(target_rows,claims):
                f=byid[claim];assert f['status']=='verified' and f['reference_date']=='2024-11-01'
                v=f['values'];assert v['denominator_regions']==53
                assert (row['total_rank'],row['first_rank'],row['first_count'])==(v['total_rank'],v['first_marriage_rank'],v['first_marriage_couples']),claim+' values differ from verified source'
                row.update(total_rank=v['total_rank'],first_rank=v['first_marriage_rank'],first_count=v['first_marriage_couples'],claim_id=claim)
        assert byid['ENH2-MEMBERSHIP']['values']['top4_unchanged']
        c['verified_analysis_revision']=facts['revision']
    if data_file:
        d=json.loads(Path(data_file).read_text(encoding='utf-8-sig'));specs.update(d.get('scenes',d))
    c['extra_specs']=specs
    def generic(s,ctx):
        spec=s.get('visual') or specs[s['scene_id']]
        if spec['type']!='rank_criteria':raise ValueError('Unknown view: '+spec['type'])
        return rank_criteria(s,ctx)
    renderers={sid:generic for sid in specs};renderers['__generic__']=generic
    for path in modules:
        p=Path(path);modspec=importlib.util.spec_from_file_location(p.stem,p);mod=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(mod)
        renderers.update(mod.SCENE_RENDERERS)
    return renderers
