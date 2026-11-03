"""RPR-P1-REQ-01: scoped source/dynamic-unit check and actual Incheon v3 decode."""
import hashlib,importlib.util,json,re,subprocess
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;REPO=EP.parents[2];OUT=EP/'outputs/production-v1-jun';P=OUT/'project';C=OUT/'checks/fix_req01'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def run(cmd):
    r=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace');assert r.returncode==0,r.stderr[-2500:];return r.stdout,r.stderr
def jobs(p):return json.loads(re.search(r'const jobs=(.*?);\nfor',Path(p).read_text(encoding='utf-8')).group(1))
def main():
    before=read(C/'before.json');qa=read(EP/'qa/production-v1/findings.json');ids=next(x for x in qa['findings'] if x['issue_id']=='RPR-P1-REQ-01')['evidence']['affected_authored_beats']
    expected={f'{(P/"compositions"/(b.split("-")[0]+".html")).relative_to(REPO).as_posix()}' for b in ids}|{(P/'preview/incheon2008-2016recovery.html').relative_to(REPO).as_posix()}
    changed={p for p,h in before['project'].items() if sha(REPO/p)!=h};assert changed==expected,(changed,expected)
    assert all(sha(REPO/p)==h for p,h in before['preserved_evidence'].items()),'Original MP4/QA evidence changed'
    unitchecks=[]
    for b in ids:
        job=next(j for j in jobs(P/'compositions'/f'{b.split("-")[0]}.html') if j['id']==b+'-c1');assert job['unit']=='2006Q1=100';unitchecks.append({'beat_id':b,'unit':job['unit']})
    spec=importlib.util.spec_from_file_location('rpr',ED/'build.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);data=read(P/'assets/chart_data.json');dynamic=[]
    for region in data['regions']:
        e=next(e for e in data['episodes'] if e['region']==region);a=mod.Art('test-'+region);mod.episode_chart(a,data,region,e['peak_quarter']);unit=a.drivers[0]['unit'];assert unit==data['series'][region][0]['quarter']+'=100';dynamic.append({'region':region,'supported_start':data['series'][region][0]['quarter'],'unit':unit})
    assert next(x['unit'] for x in dynamic if x['region']=='세종')=='2015Q1=100'
    old=jobs(C/'incheon_v2_source.html');new=jobs(P/'preview/incheon2008-2016recovery.html');assert all(x['points']==y['points'] and x['start']==y['start'] and x['duration']==y['duration'] for x,y in zip(old,new))
    dump(C/'scope_and_units.json',{'ok':True,'affected_beats':unitchecks,'dynamic_supported_start_tests':dynamic,'changed_project_files':sorted(changed),'unchanged_two_preview_html_and_mp4':True,'preserved_original_mp4_and_qa_hashes':before['preserved_evidence'],'same_price_and_drawdown_points_and_timing_as_v2':True,'REC02':'S004-P2 remains six panels plus two endpoint number highlights, not an authored one/two-panel enlargement; recommendation remains open.'})
    m=read(OUT/'reusable_assets/manifest.json');ff,probe=m['ffmpeg'],m['ffprobe'];video=OUT/'previews/incheon2008-2016recovery_provisional_v3.mp4'
    raw,_=run([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',video]);meta=json.loads(raw);dump(C/'incheon_v3_ffprobe.json',meta)
    v=next(s for s in meta['streams'] if s['codec_type']=='video');audio=[s for s in meta['streams'] if s['codec_type']=='audio'];assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_read_frames']))==(1920,1080,'30/1',240);assert not audio and abs(float(v['duration'])-8)<.034
    _,err=run([ff,'-v','error','-i',video,'-map','0:v:0','-f','null','-']);assert not err.strip();(C/'incheon_v3_decode.txt').write_text('exit=0\n'+err,encoding='utf-8')
    dest=C/'encoded';dest.mkdir(exist_ok=True);frames=[]
    for t in [2,4,7]:
        file=dest/f'incheon_v3_{t}s.png';run([ff,'-y','-v','error','-ss',t,'-i',video,'-frames:v','1',file]);assert file.is_file();frames.append({'time_seconds':t,'path':file.relative_to(REPO).as_posix(),'sha256':sha(file)})
    report={'ok':True,'file':video.relative_to(REPO).as_posix(),'sha256':sha(video),'duration_seconds':8,'resolution':[1920,1080],'fps':'30/1','decoded_frames':240,'audio_streams':0,'full_decode':'pass','frames':frames,'actual_listening':False,'continuous_playback':False,'visual_review':'pending direct PNG inspection'};dump(C/'technical.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
