from pathlib import Path
import json,subprocess
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/minimal-v12'
FF='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffprobe.exe'
def packets(p):
 return json.loads(subprocess.check_output([FF,'-v','error','-select_streams','a','-read_intervals','0%525','-show_packets','-show_data_hash','sha256','-show_entries','packet=data_hash,pts_time','-of','json',str(p)]))['packets']
a=packets(EP/'outputs/map-focus-v10/map-focus_v10_front.mp4');b=packets(O/'minimal_v12_front.mp4');ha=[p['data_hash'] for p in a];hb=[p['data_hash'] for p in b]
r={'source_packets':len(a),'final_packets':len(b),'packet_hash_lists_equal':ha==hb,'audio_reencoded':False,'original':'map-focus-v10/map-focus_v10_front.mp4','range_s':[0,525],'actual_listening':False}
(O/'audio_preservation.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
