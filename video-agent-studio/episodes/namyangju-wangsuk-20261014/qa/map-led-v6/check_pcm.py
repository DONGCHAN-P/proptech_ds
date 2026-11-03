import pathlib,json,subprocess
p=pathlib.Path(__file__).parent;e=p.parents[1];m=json.loads((e/'narration/alignment_manifest_v2.json').read_text(encoding='utf-8'));ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';rows=[]
for ch in m['chapters']:
 raw=subprocess.check_output([ff,'-v','error','-i',str(e/ch['file']),'-f','s16le','-ac','1','-ar','48000','pipe:1'])
 actual=len(raw)/96000;assert abs(actual-ch['pcm_duration_s'])<.00001
 rows.append({'scene_id':ch['scene_id'],'decoded_pcm_s':actual,'manifest_matches':True})
(p/'pcm_independent_check.json').write_text(json.dumps({'chapters':rows,'total_s':sum(r['decoded_pcm_s'] for r in rows),'actual_listening':False},indent=2),encoding='utf-8');print('11 files PCM match',sum(r['decoded_pcm_s'] for r in rows))
