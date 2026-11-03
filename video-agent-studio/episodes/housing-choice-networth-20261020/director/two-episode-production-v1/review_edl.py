"""Check measured brand edits and subtitle offsets independently of the editor."""
import argparse
import array
import hashlib
import json
import re
import wave
from pathlib import Path

EP=Path(__file__).resolve().parents[2]
ROOT=EP.parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--source-dir',default='outputs/private-production-v1')
parser.add_argument('--receipt',default='edl_review.json')
parser.add_argument('--timing',default='narration/free-tts-v1/final_timing.json')
args=parser.parse_args()
OUT=(EP/args.source_dir).resolve()
receipt=(Path(__file__).parent/args.receipt).resolve()
assert OUT.is_relative_to(EP) and receipt.is_relative_to(Path(__file__).parent)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
timing_path=(EP/args.timing).resolve()
assert timing_path.is_relative_to(EP) and timing_path.is_file()
timing=read(timing_path)
edl=read(OUT/'assembly_edl.json')
assert edl['status']=='measured_audio_units'
fps=edl['fps']
previous=0
for segment in edl['segments']:
    assert abs(segment['global_start_s']-previous)<1e-6
    length=segment['source_end_s']-segment['source_start_s']
    assert abs(segment['global_end_s']-segment['global_start_s']-length)<1e-6
    assert abs(length*fps-round(length*fps))<1e-5
    previous=segment['global_end_s']
assert abs(previous-edl['total_seconds'])<1e-6
expected=[]
for chapter in timing['chapters']:
    for cue in chapter['cues']:
        matches=[m for m in edl['offset_map'] if m['chapter']==chapter['chapter'] and cue['start_s']>=m['local_start_s']-1e-6 and cue['end_s']<=m['local_end_s']+1e-6]
        assert len(matches)==1, f"Cue crosses an edit: {cue['id']}"
        offset=matches[0]['global_offset_s']
        expected.append((cue['start_s']+offset,cue['end_s']+offset,cue['text']))
caption_path=OUT/edl['captions']
def seconds(value):
    h,m,s=re.split('[:,]',value)[:3]
    ms=value.split(',')[1]
    return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
actual=[]
for block in re.split(r'\n\s*\n',caption_path.read_text(encoding='utf-8-sig').strip()):
    lines=block.splitlines()
    start,end=lines[1].split(' --> ')
    actual.append((seconds(start),seconds(end),' '.join(lines[2:])))
assert len(expected)==len(actual)==sum(len(c['cues']) for c in timing['chapters'])
errors=[]
for i,(a,b) in enumerate(zip(expected,actual)):
    assert re.sub(r'\s','',a[2])==re.sub(r'\s','',b[2]),f'Caption text {i}'
    assert b[0]<b[1] and (i==0 or b[0]>=actual[i-1][1])
    errors.extend((abs(a[0]-b[0]),abs(a[1]-b[1])))
    assert max(errors[-2:])<=.0011
    for interval in edl['caption_hidden_intervals']:
        assert b[1]<=interval['start_s']+.0011 or b[0]>=interval['end_s']-.0011
cut=edl['hook_cut_s']
with wave.open(str(ROOT/timing['chapters'][0]['audio_file'])) as audio:
    assert audio.getnchannels()==1 and audio.getsampwidth()==2
    rate=audio.getframerate()
    pcm=array.array('h',audio.readframes(audio.getnframes()))
next_cue=min(c['start_s'] for c in timing['chapters'][0]['cues'] if c['start_s']>cut)
last_signal=max(i for i in range(int((cut-2)*rate),int((next_cue-.1)*rate)) if abs(pcm[i])>=33)/rate
assert last_signal<cut
last=timing['chapters'][-1]
last_offset=next(m['global_offset_s'] for m in edl['offset_map'] if m['chapter']==10)
outro=next(s['global_start_s'] for s in edl['segments'] if s['id']=='clean_brand_outro')
tail=outro-(last_offset+last['last_speech_end_s'])
assert tail>=3
report={'status':'passed_source_timing_and_subtitle_plan','script_sha256':timing['script_sha256'],
    'timing_sha256':hashlib.sha256(timing_path.read_bytes()).hexdigest(),
    'edl_sha256':hashlib.sha256((OUT/'assembly_edl.json').read_bytes()).hexdigest(),
    'subtitles_sha256':hashlib.sha256(caption_path.read_bytes()).hexdigest(),
    'checked_cues':len(actual),'max_caption_rounding_error_s':max(errors),
    'hook_cut_s':cut,'last_hook_pcm_signal_end_s':last_signal,
    'hook_cut_has_low_amplitude_gap':True,'tail_after_last_speech_s':tail,
    'planned_total_seconds':edl['total_seconds'],
    'actual_listening':False,'continuous_playback':False,'encoded_media_checked':False}
receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
