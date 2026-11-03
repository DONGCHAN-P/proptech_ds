import json,hashlib,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[2];n=p/'narration/cta-v8'
text=(p/'outputs/story-review-v8/M010_cta.txt').read_text(encoding='utf8')
literal='영상이 만족스러웠다면 구독과 좋아요 버튼 한번씩 눌러주시면 감사하겠습니다. 시청해주셔서 대단히 감사합니다.'
assert text==literal and len(text)==59
a=json.loads((n/'M010.alignment.json').read_text(encoding='utf8'));assert ''.join(a['characters'])==text
c=json.loads((n/'M010.captions_timed.json').read_text(encoding='utf8'))['cues'];assert len(c)==4
for cue in c:
 assert text[cue['char_start']:cue['char_end']]==cue['text']
 assert cue['start_s']==a['character_start_times_seconds'][cue['char_start']]
 assert cue['end_s']==min(7.44,a['character_end_times_seconds'][cue['char_end']-1])
i=max(i for i,x in enumerate(a['characters']) if x.isalnum())
assert a['characters'][i]=='다' and a['character_end_times_seconds'][i]==7.2
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
pcm=subprocess.run([ff,'-v','error','-i',str(n/'M010.mp3'),'-f','s16le','-ac','1','-ar','48000','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
duration=len(pcm)/96000;assert duration==7.44
r={'user_literal_exact':True,'characters':59,'new_cues':4,'new_voice_sha256':hashlib.sha256((n/'M010.mp3').read_bytes()).hexdigest(),'independent_pcm_duration_s':duration,'last_spoken_character':'다','provider_last_spoken_end_s':7.2,'acoustic_speech_end_verified':False,'root_canonical_outro_frame':27659,'provider_end_frame':27569,'hold_frames':90,'preserved_pcm_duration_s':7.44,'extra_padding_s':2.76,'actual_listening':False,'continuous_playback':False,'manifest_old_PCM_plus3s_override':'Root timing_lock_v15 overrides narration handoff safest PCM+3s suggestion'}
(Path(__file__).parent/'cta_alignment_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(r,ensure_ascii=True))
