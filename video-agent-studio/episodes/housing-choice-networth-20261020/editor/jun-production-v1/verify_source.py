"""Validate every current cue, alignment-bound anchor, EDL, asset, and source clock."""
import json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import HERE,EP,ROOT,OUT,OLD,CUES,AUDIO,TIMED,read,sha,dump,resolve,skeleton,SCRIPT_SHA
def main():
    plan=read(OUT/'render_plan.json');timing=read(EP/plan['caption_timing_path']);edl=read(OUT/'assembly_edl.json')
    all_cues=[];rows=[];required=[]
    for ch in plan['chapters']:
        n=ch['chapter'];folder=OUT/ch['project'];t=read(folder/'timing.json');old=read(OLD/ch['project']/'timing.json');a=read(folder/'anchor_audit.json')
        s=(folder/'index.html').read_text(encoding='utf8');src=(OLD/ch['project']/'index.html').read_text(encoding='utf8')
        assert skeleton(s)==skeleton(src),'Non-timing picture differs'
        assert len(CUES.findall(s))==len(t['cues']) and len(t['cues'])==len(old['cues'])
        for node,c in zip(CUES.findall(s),t['cues']):
            start=float(re.search(r'data-start="([^"]+)"',node)[1]);duration=float(re.search(r'data-duration="([^"]+)"',node)[1])
            assert abs(start-c['start_s'])<1e-6
            if n==1 and c['paragraph']==0:assert start+duration<=edl['hook_cut_s']+1e-6,'Stale hook caption would return after brand intro'
        assert not re.search(r'data-playback-rate|timeScale\(|atempo',s),'Unexpected speech speed change'
        for asset in (OLD/ch['project']/'assets').rglob('*'):
            if asset.is_file() and asset.name not in ['narration.wav','music-bed.wav']:assert sha(asset)==sha(folder/'assets'/asset.relative_to(OLD/ch['project']/'assets'))
        original=next(x for x in timing['chapters'] if x['chapter']==n)
        assert sha(folder/'assets/narration.wav')==original['audio_sha256']
        prev=0
        for c in t['cues']:
            assert prev<=c['start_s']<c['end_s']<=t['total_seconds'];prev=c['end_s']
            assert any(s['start_s']<=c['start_s']<s['end_s'] for s in t['scenes'])
            off=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==n and o['local_start_s']<=c['start_s']<o['local_end_s'])
            start,end=c['start_s']+off,c['end_s']+off
            assert not any(start<i['end_s']-1e-6 and end>i['start_s']+1e-6 for i in edl['caption_hidden_intervals'])
            all_cues.append({'chapter':n,'cue_id':c['id'],'global_start_s':start,'global_end_s':end,'text':c['text']})
        assert all(0<=a['time_s']<t['total_seconds'] for a in a['anchors'])
        rows.append({'chapter':n,'html_sha256':sha(folder/'index.html'),'timing_sha256':sha(folder/'timing.json'),'anchors':len(a['anchors']),'captions':len(t['cues']),'all_caption_source_points_checked':True,'frozen_non_timing_picture_preserved':True,'voice_PCM_identical_to_narrator':True})
    assert len(all_cues)==206 and all(b['global_start_s']>=a['global_end_s'] for a,b in zip(all_cues,all_cues[1:]))
    assert edl['intro_video_frames']==150 and edl['outro_video_frames']==300 and 3-1e-6<=edl['outro_delay_from_last_speech_s']<3+1/30+1e-5
    assert len(re.findall(r'^\d+\n', (OUT/'captions_measured.srt').read_text(encoding='utf8'),re.M))==206
    dump(HERE/'static_checks.json',{'status':'pass','script_sha256':SCRIPT_SHA,'caption_timing_sha256':plan['caption_timing_sha256'],'chapters':rows,'cue_count':206,'scope':'all source cue points and frozen content/geometry/PCM; not encoded visual quality or listening','required_issues':required})
    dump(OUT/'global_cue_points.json',{'cues':all_cues})
    print(json.dumps({'status':'pass','chapters':len(rows),'cues':len(all_cues)}))
if __name__=='__main__':main()
