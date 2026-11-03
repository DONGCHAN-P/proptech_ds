"""Insert only two new free narration sentences, keeping all baseline audio."""
from pathlib import Path
from collections import defaultdict
import copy,hashlib,json,math,subprocess,sys,wave
import numpy as np
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
sys.path.insert(0,str(E/'editor/top20-explain-v3'))
from caption_tools import make_cues
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pcm(p):
    z=subprocess.run([str(FF),'-v','error','-i',str(p),'-vn','-ar','48000','-ac','2','-f','s16le','-'],capture_output=True,check=True)
    return np.frombuffer(z.stdout,dtype='<i2').reshape(-1,2)
def wav(p,a):
    with wave.open(str(p),'wb')as w:w.setparams((2,2,48000,0,'NONE','none'));w.writeframes(np.asarray(a,dtype='<i2').tobytes())
def main():
    a=read(D/'production_authorization.json');t=read(R/a['baseline_timing']);n=read(E/'narration/top20-split-v4/map-clean-v1/timing_proposals.json')
    assert sha(R/n['audio_path'])==n['audio_sha256'] and n['script_sha256']==a['script_sha256']
    assert sha(R/a['baseline_audio'])==a['baseline_audio_sha256']
    plan=read(D/'transition_plan.json');cut=plan['insert_at_s'];lead=.3
    frames=math.ceil((lead+n['total_s'])*30);insert=frames/30
    assert abs(insert-plan['insert_duration_s'])<1e-8
    assert t['intro_sentences'][5]['end_s']<cut<t['intro_sentences'][6]['start_s']
    raw=pcm(R/n['audio_path']);voice=np.zeros((frames*1600,2),dtype=np.int16)
    first=round(lead*48000);voice[first:first+len(raw)]=raw
    out=D/'media';out.mkdir(exist_ok=True);wav(out/'criteria_voice_48k.wav',voice)
    media=read(R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json')
    music=next(x for x in media['assets']if x['asset_id']=='existing_channel_bgm');assert sha(R/music['path'])==music['sha256']
    bed=out/'criteria_music.wav'
    subprocess.run([str(FF),'-v','error','-y','-stream_loop','-1','-i',str(R/music['path']),'-t',str(insert),'-af',f'volume=0.045,afade=t=in:st=0:d=0.15,afade=t=out:st={insert-.22}:d=0.22','-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)],check=True)
    mixed=voice.astype(np.int32)+pcm(bed)[:len(voice)].astype(np.int32);assert np.abs(mixed).max()<32767
    wav(out/'criteria_mixed.wav',mixed)
    old=pcm(R/a['baseline_audio']);at=round(cut*48000);master=np.vstack([old[:at],mixed.astype(np.int16),old[at:]])
    wav(out/'master_audio.wav',master)
    assert np.array_equal(master[:at],old[:at]) and np.array_equal(master[at+len(voice):],old[at:])
    words=defaultdict(list)
    for w in read(R/n['words_file'])['words']:words[w['sentence_id']].append(copy.deepcopy(w))
    local_sentences=[];local_cues=[]
    for row in n['sentences']:
        s=copy.deepcopy(row);s['start_s']+=lead;s['end_s']+=lead;s['words']=words[s['sentence_id']]
        for w in s['words']:
            for k in ['start_s','end_s','local_start_s','local_end_s','global_start_s','global_end_s']:
                if k in w:w[k]+=lead
        local_sentences.append(s);cs=make_cues(s,s['words'],s['reading_text'],maxchars=42)
        assert ' '.join(c['text']for c in cs)==s['text'];local_cues+=cs
    captions=[]
    for c in t['captions']:
        assert c['end_s']<=cut or c['start_s']>=cut
        delta=insert if c['start_s']>=cut else 0;captions.append(dict(c,start_s=c['start_s']+delta,end_s=c['end_s']+delta))
    captions +=[dict(c,start_s=c['start_s']+cut,end_s=c['end_s']+cut)for c in local_cues]
    captions.sort(key=lambda c:c['start_s'])
    assert all(c['end_s']<=captions[i+1]['start_s']+.001 for i,c in enumerate(captions[:-1]))
    body=copy.deepcopy(t['body_scenes'])
    for scene in body:
        for k in ['start_s','end_s']:scene[k]+=insert
        for s in scene['sentences']:
            ws=s.get('words',[]);offset=s['start_s']-min(w['start_s']for w in ws) if ws else 0
            for w in ws:
                for k in ['start_s','end_s','local_start_s','local_end_s','global_start_s','global_end_s']:
                    if k in w:w[k]+=offset+insert
            s['start_s']+=insert;s['end_s']+=insert
    lock={'status':'actual_audio_locked','revision':'map-clean-v1','script_decision_id':a['decision_id'],
          'baseline_video':a['baseline_video'],'baseline_video_sha256':a['baseline_sha256'],
          'insert_at_s':cut,'insert_duration_s':insert,'criteria_lead_s':lead,
          'criteria_sentences_local':local_sentences,'criteria_captions_local':local_cues,
          'criteria_sentences':[dict(s,start_s=s['start_s']+cut,end_s=s['end_s']+cut)for s in local_sentences],
          'captions':captions,'body_scenes':body,'transition_plan':plan,
          'total_frames':t['total_frames']+frames,'total_s':t['total_s']+insert,
          'master_audio':str(out/'master_audio.wav'),'master_audio_sha256':sha(out/'master_audio.wav'),
          'brand_intro':t['brand_intro'],'brand_outro':dict(t['brand_outro'],start_s=t['brand_outro']['start_s']+insert),
          'last_spoken_end_s':t['last_spoken_end_s']+insert,'old_audio_pcm_unchanged_outside_insertion':True,
          'actual_listening':False,'cash_cap_krw':0}
    save(D/'locked_timing.json',lock)
    def ts(v):
        z=round(v*1000);h,z=divmod(z,3600000);m,z=divmod(z,60000);s,z=divmod(z,1000);return f'{h:02d}:{m:02d}:{s:02d},{z:03d}'
    (D/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{ts(c['start_s'])} --> {ts(c['end_s'])}\n{c['text']}"for i,c in enumerate(captions))+'\n',encoding='utf-8')
    receipt={'status':'passed','insert_s':insert,'total_s':lock['total_s'],'total_frames':lock['total_frames'],
             'new_sentences':2,'full_sentences':90,'captions':len(captions),'master_audio_sha256':lock['master_audio_sha256'],
             'baseline_audio_pcm_exact_outside_insertion':True,'peak_pcm':int(np.abs(master.astype(np.int32)).max()),'cash_cost_krw':0}
    save(D/'media_receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
