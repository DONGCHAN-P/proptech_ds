"""Map provided TTS raw-character timestamps to exact approved TXT spans. No API calls."""
import argparse,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True);args=parser.parse_args()
manifest_path=Path(args.manifest).resolve();manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
approved_manifest_path=EP/'writer/map-led-v4/narration_input/manifest.json'
approved_manifest=json.loads(approved_manifest_path.read_text(encoding='utf-8'))
if manifest['source_script_sha256']!=approved_manifest['source_script_sha256']:raise ValueError('Narration source script SHA is not approved current script')
if manifest['input_manifest_sha256']!=hashlib.sha256(approved_manifest_path.read_bytes()).hexdigest():raise ValueError('Narration input manifest SHA mismatch')
semantic=json.loads((EP/'writer/map-led-v4/captions_semantic_v4.json').read_text(encoding='utf-8'))
fps=30;result={};checks=[]
def local(path):
    p=Path(path)
    if p.is_absolute():return p
    return EP/p if (EP/p).exists() else manifest_path.parent/p
for chapter in manifest['chapters']:
    sid=chapter['scene_id'];meta=semantic['chapter_input_meta'][sid]
    txt=(EP/'writer/map-led-v4'/meta['path']).read_text(encoding='utf-8')
    if hashlib.sha256(txt.encode('utf-8')).hexdigest()!=meta['sha256']:raise ValueError(sid+' approved TXT SHA mismatch')
    if chapter['text_sha256']!=meta['sha256']:raise ValueError(sid+' narration TXT SHA mismatch')
    response=json.loads(local(chapter['alignment_file']).read_text(encoding='utf-8-sig'))
    alignment=response.get('alignment',response)
    if ''.join(alignment['characters'])!=txt:raise ValueError(sid+' raw alignment text differs; stop and inspect, no weighted fallback')
    audio=local(chapter['file'])
    if hashlib.sha256(audio.read_bytes()).hexdigest()!=chapter['sha256']:raise ValueError(sid+' audio SHA mismatch')
    if chapter['script_revision']!='script-v4-hook-outside':raise ValueError(sid+' wrong script revision')
    starts=alignment['character_start_times_seconds'];ends=alignment['character_end_times_seconds'];cues=[]
    for unit in semantic['chapters'][sid]:
        a,b=unit['char_start'],unit['char_end']
        if txt[a:b]!=unit['text']:raise ValueError(sid+' cue span no longer exact')
        start=max(0,math.floor(starts[a]*fps));end=math.ceil(ends[b-1]*fps)
        if ends[b-1]>chapter['pcm_duration_s']:
            over=[(ch,en) for ch,en in zip(alignment['characters'],ends) if en>chapter['pcm_duration_s']+.001]
            if ends[b-1]>chapter['pcm_duration_s']+.1001 or any(ch.isalnum() for ch,en in over):raise ValueError(sid+' voiced alignment exceeds decoded PCM duration')
            end=min(end,math.ceil(chapter['pcm_duration_s']*fps))
        cues.append({'id':unit['id'],'start_frame':start,'end_frame':end,'lines':unit['lines'],'protected_phrases':unit['protected_phrases'],'char_start':a,'char_end':b,'basis':'provided raw character timestamps mapped to exact approved TXT span; actual listening pending'})
    for i,c in enumerate(cues):
        if i+1<len(cues):c['end_frame']=min(c['end_frame'],cues[i+1]['start_frame'])
        if c['end_frame']<=c['start_frame']:raise ValueError(sid+' cue has no display frame; inspect boundary')
    result[sid]=cues;checks.append({'scene_id':sid,'exact_alignment_text':True,'exact_cue_spans':True,'cue_count':len(cues),'audio_sha256':chapter['sha256'],'final_punctuation_tail_clamped_to_pcm':max(ends)>chapter['pcm_duration_s'],'global_timestamp_offset_applied':False})
if set(result)!=set(semantic['chapters']):raise ValueError('Not all approved chapters have alignment')
out=Path(__file__).parent/'aligned_captions.json';out.write_text(json.dumps({'script_revision':'script-v4-hook-outside','caption_revision':'map-led-v4-exact-timestamp-spans','fps':fps,'chapters':result,'checks':checks,'actual_listening':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('mapped exact spans',sum(map(len,result.values())),'cues; no paid API called')
