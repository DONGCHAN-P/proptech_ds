"""Offline all-scene glyph/geometry preflight; explicitly synthetic, no MP4/audio."""
import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline as p
from frozen_graphics import make_scene


class VisibleText(HTMLParser):
    def __init__(self):super().__init__();self.text=[]
    def handle_data(self,data):self.text.append(data)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--script',required=True);parser.add_argument('--run',required=True)
    args=parser.parse_args();script_file=p.source(args.script);script=p.read(script_file)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',args.run):raise ValueError('Unsafe run')
    run=p.owned(p.OUT/args.run)
    if run.exists():raise ValueError('Preserve existing source preflight; use a new version')
    packet=p.read(p.EP/'research/verified_case_packet.json');newborn=p.read(p.EP/'research/newborn_policy_addendum_v2.json')
    override_path=p.EP/'director/rebuild-v2/visual_overrides.json';override=p.read(override_path)
    if len(script['scenes'])!=34:raise ValueError('Expected exact frozen 34-scene package')
    ids=[s['id'] for s in script['scenes']]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate scene ID')
    original=p.read(p.EP/'director/rebuild-v2/frozen-script-v3/scenes_v3.json')
    old32=next(s for s in original['scenes'] if s['id']=='R032');new32=next(s for s in script['scenes'] if s['id']=='R032')
    if any(old32[k]!=new32[k] for k in ['id','title','narration','beats']):raise ValueError('R032 override needs parent rebase for changed scene')
    rows=[];screen_findings=[]
    for scene in script['scenes']:
        g=make_scene(scene,packet,newborn);sid=scene['id']
        if sid=='R032':
            g['source_recipe'].update(visual_override=p.pin(override_path),override_applied='A monthly budget from R031; same original principals, 4/6 percent, each 360 months; no newborn balance')
        if len(g['stages'])!=len(scene['beats']):raise ValueError('One stage per authored anchor required: '+sid)
        text=VisibleText();text.feed(g['html']);screen=' '.join(text.text)
        for pattern in [r'아님',r'아닌',r'실행 승인 표시는',r'해당 챕터',r'나열 없음',r'R\d{3}',r'\?{2,}',r'\ufffd']:
            if re.search(pattern,screen):screen_findings.append({'scene_id':sid,'pattern':pattern})
        beats=[]
        for i,(stage,writer_beat) in enumerate(zip(g['stages'],scene['beats'])):
            anchor=writer_beat['anchor'];count=scene['narration'].count(anchor)
            if count!=1:raise ValueError('Literal anchor must be unique: '+sid+' '+anchor)
            start=scene['narration'].index(anchor)
            beats.append({**stage,'beat_index':i,'anchor':anchor,'action':writer_beat['action'],'char_start':start,'char_end':start+len(anchor),'start_s':.5+i*2,'end_s':1.3+i*2,'cue_ids':[],'timing_basis':'synthetic_design_clock_not_actual_cue'})
        folder=run/'scenes'/sid;voice={'duration_s':len(beats)*2+1,'last_speech_end_s':None,'cues':[],'audio_path':None}
        p.emit_project(folder,scene,voice,g,beats,'금융위원회·주택도시기금·한국주택금융공사 / 2026.10.26 · '+', '.join(scene['source_ids']),template=True)
        model=p.read(folder/'scene.json');model.update(provisional_design_only=True,actual_cue_timing=False,script_sha256=p.sha(script_file),required_assets=g.get('required_assets',[]),information_source='frozen r2 title/narration/individual beat actions; not generic data_chart label')
        p.dump(folder/'scene.json',model)
        rows.append({'scene_id':sid,'chapter':scene['chapter'],'kind':g['kind'],'beat_count':len(beats),'html_sha256':p.sha(folder/'index.html'),'source_recipe':g['source_recipe'],'required_assets':g.get('required_assets',[])})
    inputs=[p.pin(script_file),p.pin(override_path),p.pin(p.EP/'research/verified_case_packet.json'),p.pin(p.EP/'research/newborn_policy_addendum_v2.json')]
    p.dump(run/'preparation_manifest.json',{'status':'all_34_source_prepared_geometry_pending','provisional_design_only':True,'script':p.pin(script_file),'inputs':inputs,'scene_order':ids,'scenes':rows,'screen_restrictions_findings':screen_findings,'actual_audio':False,'actual_cue_timing':False,'MP4_rendered':False})
    if screen_findings:raise ValueError('Onscreen wording findings: '+json.dumps(screen_findings,ensure_ascii=False))
    subprocess.run(['node',str(p.HERE/'verify_templates.cjs'),str(run)],check=True,env=p.ENV)
    receipt=p.read(run/'geometry_receipt.json')
    p.dump(p.HERE/'all34_preflight.json',{'status':receipt['status'],'script':p.pin(script_file),'visual_override':p.pin(override_path),'source_preparation':str(run),'scene_count':34,'different_recipe_kinds':len({r['kind'] for r in rows}),'source_order':ids,'stage_count':sum(r['beat_count'] for r in rows),'provisional_design_only':True,'actual_cue_timing':False,'actual_listening':False,'continuous_playback':False,'MP4_rendered':False})


if __name__=='__main__':main()
