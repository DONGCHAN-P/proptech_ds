from pathlib import Path
import subprocess,json,hashlib,shutil,numpy as np
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];E=EP/'editor/locator-timeline-v14';O=EP/'outputs/locator-timeline-v14';N=EP/'narration/region-leaders-v7'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe')
def decode(name,source,samples,volume=1,extra=None):
 target=E/(name+'.f32');args=[F,'-v','error','-y']+(extra or [])+['-i',str(source),'-vn','-af',f'aformat=sample_rates=48000:channel_layouts=stereo,volume={volume},apad=whole_len={samples},atrim=end_sample={samples}','-c:a','pcm_f32le','-f','f32le',str(target)];subprocess.run(args,check=True);assert target.stat().st_size==samples*2*4;return target
prefix=decode('prefix_audio_unchanged',EP/'outputs/caption-station-v13/caption-station_v13_full.mp4',34617600)
m8=decode('M008_new',N/'M008.mp3',7929600,.9)
m9=decode('M009_voice',N/'M009.mp3',1217600,.9)
music=decode('M009_music',ROOT/'video/public/namyangju-map-led-v6/data_city_ambient_v1.wav',1217600,extra=['-stream_loop','-1','-ss','32'])
voice=np.memmap(m9,dtype=np.float32,mode='r',shape=(1217600,2));bed=np.memmap(music,dtype=np.float32,mode='r',shape=(1217600,2));f=np.arange(1217600)//1600
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
weight=np.minimum(smooth((f+6)/12),smooth((761+12-f)/18));envelope=(.48+(.18-.48)*weight)*smooth(f/30)*smooth((760-f)/45)
mixed=np.asarray(voice+bed*envelope[:,None],dtype=np.float32);m9mix=E/'M009_mixed.f32';mixed.tofile(m9mix)
outro=decode('brand_outro_unchanged',EP/'outputs/caption-station-v13/brand_outro_v13_no_caption.mp4',480000)
raw=E/'full_audio_sample_locked.f32'
with raw.open('wb') as dest:
 for segment in [prefix,m8,m9mix,outro]:
  with segment.open('rb') as src:shutil.copyfileobj(src,dest)
assert raw.stat().st_size==44244800*8
full=np.memmap(raw,dtype=np.float32,mode='r',shape=(44244800,2));peak=float(np.max(np.abs(full)));assert peak<1,peak
prefixhash=hashlib.sha256(prefix.read_bytes()).hexdigest()
with raw.open('rb') as f:actual=hashlib.sha256(f.read(34617600*8)).hexdigest()
assert actual==prefixhash
audio=O/'full_v14_audio.m4a';subprocess.run([F,'-v','error','-y','-f','f32le','-ar','48000','-ac','2','-i',str(raw),'-c:a','aac','-b:a','192k',str(audio)],check=True)
r={'sample_rate':48000,'channels':2,'total_samples_per_channel':44244800,'total_duration_s':44244800/48000,'segments':[{'id':'original_prefix','samples':34617600,'duration_s':721.2},{'id':'new_M008','samples':7929600,'duration_s':165.2,'voice_gain':.9},{'id':'new_M009','samples':1217600,'voice_duration_s':25.36,'padding_samples':320,'padding_s':320/48000,'voice_gain':.9},{'id':'original_brand_outro','samples':480000,'duration_s':10}],'prefix_pcm_exact_equal':True,'prefix_pcm_sha256':prefixhash,'full_audio_reencoded_AAC':True,'full_AAC_packet_identity_claim':False,'pcm_peak':peak,'M009_music':{'source':'existing owned data_city_ambient_v1.wav','source_offset_s':32,'duck_gain':.18,'fade_in_s':1,'fade_out_s':1.5,'range_frames':[26592,27353],'no_overlap_with_brand':True},'actual_listening':False}
(O/'audio_mix_manifest_v14.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({'pcm_peak':peak,'samples':44244800,'prefix_pcm_exact_equal':True}))
