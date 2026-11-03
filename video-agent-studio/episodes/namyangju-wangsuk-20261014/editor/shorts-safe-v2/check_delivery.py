import json,hashlib,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_safe import OUT,OLD,FF,SAFE
results=[]
for s in json.loads((OUT/'manifest.json').read_text(encoding='utf-8')):
 p=Path(s['file']); ident=s['id']
 probe=json.loads((OUT/f'{ident}_probe.json').read_text(encoding='utf-8'))
 v=next(x for x in probe['streams'] if x['codec_type']=='video')
 old=json.loads(subprocess.check_output([str(FF/'ffprobe.exe'),'-v','error','-show_streams','-of','json',str(OLD/f'{ident}.mp4')]))
 ov=next(x for x in old['streams'] if x['codec_type']=='video')
 assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1080,1920,'30/1',s['frames'])
 assert v['duration']==ov['duration']
 def ahash(path):return subprocess.check_output([str(FF/'ffmpeg.exe'),'-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-']).decode().strip()
 a,b=ahash(p),ahash(OLD/f'{ident}.mp4');assert a==b
 assert (OUT/f'{ident}.srt').read_bytes()==(OLD/f'{ident}.srt').read_bytes()
 assert (OUT/f'{ident}_decode.log').stat().st_size==0
 results.append(dict(id=ident,resolution=[1080,1920],fps='30/1',frames=v['nb_frames'],duration=v['duration'],audio_packet_hash=a,audio_identical=True,srt_bytes_identical=True,decode_errors=0))
(OUT/'technical_validation.json').write_text(json.dumps(dict(results=results,scope='technical and sampled frames; no actual listening or continuous playback'),ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: all three durations/frame counts/audio packets/SRT bytes/decode')
