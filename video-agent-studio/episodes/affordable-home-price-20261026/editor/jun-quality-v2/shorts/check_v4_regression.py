"""Bounded v3→v4 check: original audio/text/bars/clocks, approved house only."""
from pathlib import Path
import importlib.util,json,hashlib,subprocess
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
b=module('current_shorts',H/'build_shorts.py')
old=module('preserved_shorts_v3',H/'build_shorts_v3_preserved.py')
prior=b.load(H/'versions/v3/edit_plan.json');current=b.load(H/'edit_plan.json')
assert current['revision']=='portrait-shorts-v4-wood-house'
assert current['safe_profile']==prior['safe_profile']
rectangles=[(325,536,616,761),(326,553,607,771),(295,554,646,825),(330,530,611,747),(332,535,603,745)]
mask=np.zeros((1920,1080),dtype=bool)
for x0,y0,x1,y1 in rectangles:mask[y0:y1,x0:x1]=True
results=[]
for p0,p1 in zip(prior['shorts'],current['shorts']):
    for key in ['id','ranges','captions','speech_cut_end_s','frames','duration_s','tail']:
        assert p0[key]==p1[key],(p1['id'],key)
    s0=b.OUT/(p0['name']+'.srt');s1=b.OUT/(p1['name']+'.srt')
    assert s0.read_bytes()==s1.read_bytes()
    # Encoding input WAV is byte-identical; the final AAC stream is also compared.
    w0=H/(p0['name']+'_audio.wav');w1=H/(p1['name']+'_audio.wav')
    assert b.sha(w0)==b.sha(w1)
    encoded_audio=[]
    for p in [p0,p1]:
        r=subprocess.run([str(b.FF),'-v','error','-i',str(b.OUT/(p['name']+'.mp4')),'-map','0:a:0','-c','copy','-f','adts','-'],capture_output=True)
        assert r.returncode==0,r.stderr
        encoded_audio.append(hashlib.sha256(r.stdout).hexdigest())
    assert encoded_audio[0]==encoded_audio[1]
    times=[0,.8,4.5,7.5,10,11.3,15.7,18.6,21.8,23,24.5,27.8,31.6,34.8,35.5,37.5]
    if p1['id']=='summary':times += [38.6,43.1,48.3,50.3]
    samples=[]
    for t in times:
        if t>=p1['duration_s']:continue
        x=np.asarray(old.visual(p0,t));y=np.asarray(b.visual(p1,t))
        diff=np.any(x!=y,axis=2)
        assert not np.any(diff & ~mask),(p1['id'],t,'unexpected visual change outside house slots')
        samples.append(dict(time_s=t,changed_pixels=int(diff.sum())))
    results.append(dict(id=p1['id'],exact_timing_unchanged=True,srt_byte_identical=True,source_excerpt_wav_byte_identical=True,
        final_AAC_stream_byte_identical=True,encoded_audio_sha256=encoded_audio[0],raw_composition_changes_confined_to_house_slots=True,
        inspected_source_frame_samples=samples,final_video_sha256=b.sha(b.OUT/(p1['name']+'.mp4'))))
source=Image.open(b.HOUSE_ASSET)
description=b.load(b.OUT/'publishing_metadata.json')['shorts'][0]['description']
assert '기존 Jun 내레이션을 사용한 홍보형 쇼츠입니다.' not in description
b.save(H/'v4_regression.json',dict(passed=True,source_revision=prior['revision'],target_revision=current['revision'],shorts=results,
    house_asset=dict(path=str(b.HOUSE_ASSET),sha256=b.sha(b.HOUSE_ASSET),source_mode=source.mode,source_dimensions=source.size,
        alpha_bbox=source.getchannel('A').getbbox(),fixed_container_px=b.HOUSE_MARKER_BOX,fixed_marker_px=b.house_marker().size,
        behavior='Same asset, displayed size and orientation at all price markers; centers stay in their v3 slots'),
    public_description_internal_sentence_removed=True,framework='Deliberate deterministic Pillow/FFmpeg implementation delegated by user; no migration needed',
    actual_listening=False,continuous_playback=False,independent_QA='Sagan must inspect v4 final encoded files'))
print(json.dumps(dict(status='v4_regression_passed',shorts=[dict(id=x['id'],audio_identical=x['final_AAC_stream_byte_identical'],srt_identical=x['srt_byte_identical']) for x in results],fixed_marker_px=b.house_marker().size)))
