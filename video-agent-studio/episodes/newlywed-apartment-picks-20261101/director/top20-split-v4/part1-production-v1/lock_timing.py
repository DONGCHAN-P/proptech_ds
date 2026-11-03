"""Lock part 1 to measured audio and provider words, never estimated durations."""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import argparse, copy, hashlib, json, re, sys, wave

D=Path(__file__).resolve().parent; E=D.parents[2]; R=E.parents[2]
N=E/'narration/top20-split-v4/part1-v1'
sys.path.insert(0,str(E/'editor/top20-explain-v3'))
from caption_tools import make_cues, translated_index, norm

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(p):
    p=Path(p); return p if p.is_absolute() else R/p
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def stamp(): return datetime.now(timezone.utc).isoformat()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--proposal',type=Path,default=N/'timing_proposals.json');a=ap.parse_args()
    source=D/'approved_part1_scene_proposals.json'; script=read(source);auth=read(D/'production_authorization.json')
    assert sha(source)==auth['scene_json_sha256']
    tp=a.proposal; t=read(tp)
    assert t.get('timing_basis')=='actual_audio' and not t.get('is_estimate')
    assert not t.get('character_proportional_alignment_used') and not t.get('old_timing_fallback_used')
    assert t['scene_json_sha256']==sha(source) and t['script_sha256']==auth['script_md_sha256']
    wp=resolve(t['words_file']); words=read(wp)['words'];assert sha(wp)==t['words_file_sha256']
    audio=resolve(t['audio_file']);assert sha(audio)==t['audio_sha256']
    with wave.open(str(audio),'rb') as w:
        pcm={'frames':w.getnframes(),'rate':w.getframerate(),'channels':w.getnchannels(),'sample_width':w.getsampwidth()}
    total=pcm['frames']/pcm['rate'];assert total>300 and abs(total-t['total_duration_with_brand_and_hold_s'])<.001
    bysid={};groups=defaultdict(list)
    for s in t['scenes']:
        for v in s.get('sentences',[]):
            assert v['sentence_id'] not in bysid; bysid[v['sentence_id']]=v
    for w in words:groups[w['sentence_id']].append(w)
    expected=[v for s in script['scenes'] for v in s['sentences']]
    assert set(bysid)==set(groups)=={v['sentence_id'] for v in expected} and len(expected)==85
    inserts=[]
    for kind in ['intro','outro']:
        b=t['brand_'+kind]
        visual=R/'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/production-v1-jun/reusable_assets'/('brand_'+kind+'_clean_v7.mp4')
        assert visual.read_bytes()[4:8]==b'ftyp','Brand visual must be an MP4 video, not the clean brand WAV'
        inserts.append({'kind':kind,'start_s':b['start_s'],'duration_s':b['duration_s'],'source_file':str(visual),'sha256':sha(visual),
                        'audio_source_file':str(resolve(b['path'])),'audio_source_sha256':sha(resolve(b['path']))})
    assert abs(inserts[-1]['start_s']-t['last_spoken_end_s']-3)<.001
    scenes=[];caps=[];checks=[]
    for scene in script['scenes']:
        new={k:scene[k] for k in ['scene_id','title','part','scene_kind','key_message']}
        for k in ['region_id','rank']:
            if k in scene:new[k]=scene[k]
        rows=[]
        for sentence in scene['sentences']:
            sid=sentence['sentence_id']; v=bysid[sid];g=sorted(groups[sid],key=lambda x:x['start_s'])
            assert v['text']==sentence['text'],sid
            reading=v['reading_text'];assert ''.join(norm(w.get('provider_text',w['text']))for w in g)==norm(reading),sid
            cursor=0;adapt=[]
            for w in g:
                assert 0<=w['start_s']<w['end_s']<=total+.002
                row=copy.deepcopy(w);row['sentence_normalized_char_start']=cursor
                cursor+=len(norm(w.get('provider_text',w['text'])))
                row['sentence_normalized_char_end']=cursor
                row['local_start_s']=row['start_s'];row['local_end_s']=row['end_s'];adapt.append(row)
            row={k:sentence[k]for k in ['sentence_id','text','map_phase']}
            row.update(start_s=v['start_s'],end_s=v['end_s'],reading_text=reading,words=adapt)
            assert abs(row['start_s']-g[0]['start_s'])<.002 and abs(row['end_s']-g[-1]['end_s'])<.002
            anchors=[]
            # Literal source substrings map to real provider-word onsets, including spoken-out numbers.
            for m in re.finditer(r'\d[\d,]*(?:\.\d+)?(?:년|월|일|쌍|곳|억(?:[\d,]+만)?원|억원|만원|위)?|[가-힣A-Za-z0-9()]+(?:초등학교|중학교|고등학교|역)',sentence['text']):
                i=translated_index(sentence['text'],reading,len(norm(sentence['text'][:m.start()])))
                word=next((w for w in adapt if w['sentence_normalized_char_end']>i),None)
                if word:anchors.append({'text':m.group(),'start_s':word['start_s'],'basis':'literal_display_to_provider_word'})
            row['anchors']=anchors;rows.append(row)
            cs=make_cues(row,adapt,reading,maxchars=42)
            assert ' '.join(c['text']for c in cs)==sentence['text'],sid
            for c in cs:
                assert c['alignment_basis']=='provider_word_boundaries_with_explicit_display_reading_map'
                assert c['end_s']>c['start_s']
                assert not any(c['start_s']<b['start_s']+b['duration_s'] and c['end_s']>b['start_s']for b in inserts)
                caps.append(c)
            checks.append({'sentence_id':sid,'words':len(g),'reading_coverage':'exact','cues':len(cs)})
        new['sentences']=rows;new['start_s']=min(v['start_s']for v in rows);scenes.append(new)
    scenes[0]['start_s']=0
    for i,s in enumerate(scenes):
        s['end_s']=scenes[i+1]['start_s'] if i+1<len(scenes) else inserts[-1]['start_s']
        s['duration_s']=s['end_s']-s['start_s']
        assert all(s['start_s']<=v['start_s']<v['end_s']<=s['end_s']for v in s['sentences'])
    caps.sort(key=lambda x:x['start_s'])
    assert all(a['end_s']<=b['start_s']+.00001 for a,b in zip(caps,caps[1:]))
    lock={'status':'director_actual_audio_locked','part':1,'timing_locked':True,'locked_at':stamp(),
          'timing_basis':'measured_PCM_and_provider_word_boundaries_scaled_by_fixed_atempo135',
          'source_scene_json':str(source),'source_scene_json_sha256':sha(source),'script_md_sha256':auth['script_md_sha256'],
          'source_proposal':str(tp),'source_proposal_sha256':sha(tp),'source_words':str(wp),'source_words_sha256':sha(wp),
          'audio_path':audio.relative_to(R).as_posix(),'audio_sha256':sha(audio),'audio_includes_brand':True,
          'total_s':total,'last_spoken_end_s':t['last_spoken_end_s'],'brand_inserts':inserts,
          'scenes':scenes,'captions':caps,'actual_listening_performed':False,'continuous_playback_performed':False}
    out=D/'locked_timing.json';save(out,lock)
    # Standard SubRip deliverable keeps literal display text and real word boundaries.
    def ts(x):
        ms=round(x*1000); h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    (D/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{ts(c['start_s'])} --> {ts(c['end_s'])}\n{c['text']}" for i,c in enumerate(caps))+'\n',encoding='utf-8')
    report={'status':'passed','checked_at':stamp(),'sentences':len(checks),'cues':len(caps),'words':len(words),'pcm':pcm,'total_s':total,
            'locked_timing_sha256':sha(out),'outro_after_last_speech_s':inserts[-1]['start_s']-t['last_spoken_end_s'],
            'caption_brand_overlaps':0,'checks':checks,'actual_listening_performed':False}
    save(D/'actual_timing_verification.json',report)
    print(json.dumps({k:report[k]for k in ['status','sentences','cues','words','total_s','locked_timing_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
