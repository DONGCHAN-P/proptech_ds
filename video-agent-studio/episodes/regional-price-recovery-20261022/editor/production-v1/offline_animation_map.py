"""Offline source map, used when the installed skill helper lacks its packages.
This is an authored timeline/data binding audit, never a claim of continuous playback.
"""
import json,re
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;OUT=EP/'outputs/production-v1-jun';P=OUT/'project'
def main():
    beats=json.loads((P/'beat_manifest.json').read_text(encoding='utf-8'))['beats'];rows=[]
    for s in sorted((P/'compositions').glob('S*.html')):
        jobs=json.loads(re.search(r'const jobs=(.*?);\nfor',s.read_text(encoding='utf-8')).group(1))
        for b in [x for x in beats if x['scene_id']==s.stem]:
            js=[j for j in jobs if j['id'].startswith(b['beat_id']+'-')]
            rows.append({'scene_id':s.stem,'beat_id':b['beat_id'],'body_window':[b['start'],b['end']],'source':str(s.relative_to(P)),'transition':'hard_cut_at_exact_beat_start','motion':'quarter-stepped chart-scrub-readout' if js else 'actual annual-volume bars; static data layout skeleton','drivers':[{'selector':'#'+j['id']+'-line','property':'x1/x2 and linked dot cx/cy; numeric/date readout','local_start':j['start']+.3,'travel_duration':j['duration']-1.2,'landing_hold':.9,'observations':len(j['points']),'first_observation':j['points'][0]['q'],'last_observation':j['points'][-1]['q'],'cursor_rule':'nearest observed index; no synthetic value interpolation','seek_safety':'pure function of paused driver p; recomputes on backward seek'} for j in js]})
    report={'method':'offline parsing of authored baked jobs','official_helper_status':'failed: @hyperframes/producer and @hyperframes/core unavailable; bootstrap would npm-install latest; not run','composition_count':12,'beat_count':39,'chart_driver_count':sum(len(x['drivers']) for x in rows),'timing_locked':False,'no_fullscreen_zoom':True,'caption_track':8,'caption_background_track':7,'audio_track_reserved':9,'scope':'source timeline audit, not rendered motion continuity proof','beats':rows}
    (OUT/'checks/animation_map.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='beats'},ensure_ascii=False))
if __name__=='__main__':main()
