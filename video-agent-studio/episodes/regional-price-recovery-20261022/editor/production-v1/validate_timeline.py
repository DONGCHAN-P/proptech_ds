"""Cross-file contract checks. Does not mutate the project or the source data."""
import hashlib, json, re
from html.parser import HTMLParser
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('rpr_build',Path(__file__).with_name('build.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
class HTML(HTMLParser):
    def __init__(self,text):super().__init__();self.elements=[];self.feed(text)
    def handle_starttag(self,tag,attrs):self.elements.append((tag,dict(attrs)))
def main():
    project=build.PROJECT;manifest=build.read(project/'beat_manifest.json');timing=build.read(project/'timing_resolved.json');scenes=build.read(build.EP/'outputs/script-review-v3/scenes_v3.json')['scenes']
    ids=[b['beat_id'] for s in scenes for b in s['beats']];assert [b['beat_id'] for b in manifest['beats']]==ids and len(ids)==39
    html=HTML((project/'index.html').read_text(encoding='utf-8'))
    mounts=[a for _,a in html.elements if 'data-composition-src'in a];assert len(mounts)==12
    end=0
    for mount,scene in zip(mounts,scenes):
        start=float(mount['data-start']);duration=float(mount['data-duration']);assert abs(start-end)<.00001;end=start+duration
        source=project/mount['data-composition-src'];page=HTML(source.read_text(encoding='utf-8'));root=next(a for _,a in page.elements if a.get('id')=='root');assert root['data-composition-id']==mount['data-composition-id']==scene['scene_id']
        assert f'window.__timelines["{scene["scene_id"]}"]' in source.read_text(encoding='utf-8')
        beats=[a for _,a in page.elements if a.get('id')in ids];assert [a['id'] for a in beats]==[b['beat_id'] for b in scene['beats']]
        for b in beats:assert 0<=float(b['data-start'])<float(b['data-start'])+float(b['data-duration'])<=duration+.00001
    assert abs(end-manifest['duration'])<.00001
    caps=[a for _,a in html.elements if a.get('id','').startswith('cap-')];assert len(caps)>39
    for i,a in enumerate(caps):
        if i:assert abs(float(caps[i-1]['data-start'])+float(caps[i-1]['data-duration'])-float(a['data-start']))<.00001,'Caption display continuity'
    # Source/header geometry is deliberately separate from graph and captions.
    text=(project/'index.html').read_text(encoding='utf-8');assert 'top:1042px' in text and 'top:922px' in text and 'top:916px' in text
    assert not any(tag=='audio' for tag,_ in html.elements) if not timing['timing_locked'] else True
    d=build.read(project/'assets/chart_data.json');assert build.digest(project/'assets/chart_data.json')==build.DATA_SHA
    assert d['series']['세종'][0]['quarter']=='2015Q1'
    assert all(x['first_return_quarter'] is None for x in d['episodes'] if x['right_censored'])
    for name in ['full2006paths','incheon2008-2016recovery','rawmedianvsindex']:
        page=(project/f'preview/{name}.html').read_text(encoding='utf-8');assert 'data-duration="8.000000"'in page
        jobs=json.loads(re.search(r'const jobs=(.*?);\nfor',page).group(1))
        for job in jobs:assert job['duration']==8 and all(x['q']<='2026Q2' for x in job['points'])
        assert '<audio' not in page
    receipt={'ok':True,'scene_count':12,'beat_count':39,'caption_count':len(caps),'timing_locked':timing['timing_locked'],'body_duration':end,'assertions':['exact approved beat order','12 matching host/inner/timeline ids','local scene windows in bounds','contiguous body mounts','continuous displayed captions','separate fixed caption/source geometry','silent previews','8 seconds each','frozen chart SHA','Sejong starts 2015Q1','censored return dates null','preview observed quarters never beyond endpoint'],'scope':'structure/data binding only; not audiovisual playback'}
    build.js(build.CHECKS/'timeline_validation.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
