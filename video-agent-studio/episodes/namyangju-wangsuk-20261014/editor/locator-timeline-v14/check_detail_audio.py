from pathlib import Path
import subprocess,json
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/locator-timeline-v14'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
def packets(p):
 r=json.loads(subprocess.check_output([str(B/'ffprobe.exe'),'-v','error','-select_streams','a:0','-show_packets','-show_data_hash','sha256','-show_entries','packet=data_hash','-of','json',str(p)]));return [x['data_hash'] for x in r['packets']]
source=packets(EP/'outputs/caption-station-v13/caption-station_v13_full.mp4');clip=packets(O/'landuse_locator_timeline_v14.mp4');starts=[i for i,v in enumerate(source) if v==clip[0]];matches=[i for i in starts if source[i:i+len(clip)]==clip];assert len(matches)==1
r={'original_aac_payload_contiguous_subsequence':True,'source_first_packet_index':matches[0],'clip_packet_count':len(clip),'source_packet_count':len(source),'retimed_audio':False,'new_audio_generation':False}
(O/'detail_audio_preservation.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
