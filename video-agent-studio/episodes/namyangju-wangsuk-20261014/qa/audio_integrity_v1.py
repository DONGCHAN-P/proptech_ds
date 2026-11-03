import pathlib,json,subprocess,hashlib
r=pathlib.Path(__file__).resolve().parent.parent
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
scenes=json.loads((r/'scenes.json').read_text(encoding='utf-8'))['scenes']
actual={x['scene_id']:x for x in json.loads((r/'editor/render_v1/timing_actual.json').read_text(encoding='utf-8'))}
results=[]
for s in scenes:
 sid=s['scene_id'];p=r/'narration/audio-v1'/f'{sid}.mp3';meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
 pcm=subprocess.check_output([ff,'-v','error','-i',str(p),'-f','s16le','-ac','1','-ar','48000','-'])
 duration=len(pcm)/96000
 results.append({'scene_id':sid,'decoded_pcm_s':duration,'render_audio_s':actual[sid]['actual_audio_duration_s'],'video_segment_s':actual[sid]['end_s']-actual[sid]['start_s'],'audio_sha_match':hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256'],'approved_text_sha_match':hashlib.sha256(s['narration_text'].encode()).hexdigest()==meta['text_sha256']})
(r/'qa/video_v1/audio_integrity.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results))
