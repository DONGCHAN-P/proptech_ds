"""Reproducible local-only checks/render/decode. Render requires parent visual-QA receipt."""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_ui as u
import pipeline_native_v4 as p
p.b=u.b
u.b.FILENAMES=dict(zip(u.IDS,['short01_promo_Jun_ui_v2.mp4','short02_ranks20_16_Jun_ui_v2.mp4','short03_ranks15_11_Jun_ui_v2.mp4']))
def check(project):
    manifest=u.b.read(project/'input_manifest.json')
    proofs=u.b.read(u.H/'representative_proofs.json')
    times=[x['time_s']for x in proofs if x['short_id']==manifest['short_id']]
    u.save(project/'caption_visibility_checks.json',{'representative_times_s':times,'single_caption_track':True,'rail_policy':'only child of active cue','source_srt_sha256':u.b.sha(project/'captions.srt')})
    return p.check(project)
def gate():
    receipt=u.H/'representative_qa_pass.json'
    if not receipt.exists():raise RuntimeError('Parent representative visual QA pass required; full render held')
    d=u.b.read(receipt)
    if d.get('passed') is not True:raise RuntimeError('Representative visual QA did not pass')
    return d
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['check','render','verify','deliver']);parser.add_argument('--short',choices=u.IDS);a=parser.parse_args()
    for sid in ([a.short]if a.short else u.IDS):
        project=u.H/sid
        if a.action=='check':check(project)
        elif a.action=='verify':p.verify(project)
        elif a.action=='render':gate();p.render(project)
        else:gate();p.render(project);p.verify(project)
