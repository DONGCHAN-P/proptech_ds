"""Verify unchanged source body PCM and hash-bound prior QA without reaggregating data."""
import pathlib,sys,json,hashlib,subprocess,wave
from datetime import datetime,timezone
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];ROOT=E.parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/deps'))
import numpy as np
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
lock=read(E/'director/top20-split-v4/part1-intro-v3/locked_timing.json')
src=pathlib.Path(lock['original_video']);master=pathlib.Path(lock['master_audio'])
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
r=subprocess.run([str(FF),'-v','error','-xerror','-i',str(src),'-vn','-ar','48000','-ac','2','-c:a','pcm_s16le','-f','s16le','-'],capture_output=True)
assert r.returncode==0,r.stderr.decode(errors='replace')
old=np.frombuffer(r.stdout,dtype='<i2').reshape(-1,2)
with wave.open(str(master),'rb') as w:
    fmt=dict(rate=w.getframerate(),channels=w.getnchannels(),width=w.getsampwidth(),frames=w.getnframes())
    new=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)
assert fmt['rate']==48000 and fmt['channels']==2 and fmt['width']==2
cut=lock['old_body_cut_frame']*1600;intro=round(lock['intro_end_s']*48000)
body=old[cut:];actual=new[intro:];n=min(len(body),len(actual))
after=np.array_equal(body[480:n],actual[480:n]);first=np.rint(body[:480].astype(float)*np.linspace(0,1,480)[:,None]).astype(np.int16)
fade=np.array_equal(first,actual[:480])
suffix_missing=len(body)-n
tail_padding=actual[n:]
basepath=E/'qa/top20-split-v4/part1-production-v1/final_review.json';base=read(basepath)
reuse=[]
for row in base['reused_QA']:
    p=pathlib.Path(row['path']);actual_hash=sha(p)
    reuse.append(dict(path=str(p),expected_sha256=row['sha256'],actual_sha256=actual_hash,match=actual_hash==row['sha256']))
pass_all=after and fade and suffix_missing<=1024 and (not tail_padding.size or np.all(tail_padding==0)) and all(x['match'] for x in reuse) and sha(src)==lock['original_video_sha256'] and sha(master)==lock['master_audio_sha256']
report=dict(checked_at=datetime.now(timezone.utc).isoformat(),status='passed_source_body_reuse' if pass_all else 'required_correction',scope='master PCM source equality + prior QA SHA bindings; encoded video equality pending',original_video_sha256=sha(src),master_audio_sha256=sha(master),master_format=fmt,body_cut_old_frame=lock['old_body_cut_frame'],body_cut_old_s=lock['old_body_cut_s'],new_body_start_s=lock['intro_end_s'],PCM=dict(old_decode_frames=len(old),new_master_frames=len(new),compared_body_frames=n,compared_body_duration_s=n/48000,after_first_10ms_exact=bool(after),first_10ms_exact_expected_music_only_fade=bool(fade),different_samples_after_10ms=int(np.count_nonzero(body[480:n]!=actual[480:n])),original_end_frames_omitted=suffix_missing,added_zero_padding_frames=len(tail_padding),limitations='Speech-free gap supported by locked native first body word; no actual listening.'),baseline_QA=dict(path=str(basepath),sha256=sha(basepath),video_sha256=base['video_sha256'],status=base['status'],required_open_count=base['required_open_count'],critical_open_count=base['critical_open_count']),prior_QA_hash_validation=reuse,source_watchlist_retained=base['source_watchlist_retained'],full_old_body_ASR_repeated=False,price_reaggregation_performed=False,map_geometry_revalidated=False,actual_listening=False,continuous_playback=False)
(Q/'body_source_reuse_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],PCM=report['PCM'],reused_QA_hashes=len(reuse)),ensure_ascii=False))
