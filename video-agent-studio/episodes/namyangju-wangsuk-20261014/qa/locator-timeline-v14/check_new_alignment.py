import json,hashlib,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[2];out=[]
for sid,duration in [('M008',165.2),('M009',25.36)]:
 base=p/'narration/region-leaders-v7'
 raw=(p/('outputs/story-review-v7/'+sid+'.txt')).read_bytes();text=raw.decode('utf8').replace('\r\n','\n')
 a=json.loads((base/(sid+'.alignment.json')).read_text(encoding='utf8'))
 c=json.loads((base/(sid+'.captions_timed.json')).read_text(encoding='utf8'))['cues']
 assert ''.join(a['characters'])==text
 previous_end=0
 for cue in c:
  assert text[cue['char_start']:cue['char_end']]==cue['text']
  assert cue['start_s']==a['character_start_times_seconds'][cue['char_start']]
  assert cue['end_s']==min(duration,a['character_end_times_seconds'][cue['char_end']-1])
  assert previous_end<=cue['start_s']<=cue['end_s']<=duration
  previous_end=cue['end_s']
 overruns=[{'i':i,'char':ch,'end':e} for i,(ch,e) in enumerate(zip(a['characters'],a['character_end_times_seconds'])) if e>duration]
 assert len(overruns)==1 and overruns[0]['char']=='.'
 ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
 pcm=subprocess.run([ff,'-v','error','-i',str(base/(sid+'.mp3')),'-f','s16le','-ac','1','-ar','48000','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
 measured=len(pcm)/96000
 assert abs(measured-duration)<0.000001
 out.append({'scene_id':sid,'characters':len(text),'cues':len(c),'raw_txt_sha256':hashlib.sha256(raw).hexdigest(),'normalized_post_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'mp3_sha256':hashlib.sha256((base/(sid+'.mp3')).read_bytes()).hexdigest(),'exact_character_and_72cue_span_alignment':True,'raw_alignment_pcm_tail_overruns':overruns,'pcm_duration_s_from_manifest':duration,'independent_decoded_pcm_s':measured})
r={'chapters':out,'total_characters':sum(x['characters'] for x in out),'total_cues':sum(x['cues'] for x in out),'actual_listening':False,'naturalness_verified':False,'pcm_independently_decoded':True}
(Path(__file__).parent/'new_alignment_review.json').write_text(json.dumps(r,indent=2),encoding='utf8')
print(json.dumps(r))
