from pathlib import Path
import subprocess,json,hashlib,shutil,numpy as np
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];E=EP/'editor/readability-cta-v15';O=EP/'outputs/readability-cta-v15';N=EP/'narration/cta-v8';B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe')
def decode(name,path,samples,gain=1,extra=None):
 target=E/(name+'.f32');subprocess.run([F,'-v','error','-y']+(extra or [])+['-i',str(path),'-vn','-af',f'aformat=sample_rates=48000:channel_layouts=stereo,volume={gain},apad=whole_len={samples},atrim=end_sample={samples}','-c:a','pcm_f32le','-f','f32le',str(target)],check=True);assert target.stat().st_size==samples*8;return target
prefix=decode('v14_existing_audio_preserved',EP/'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4',43764800)
voice=decode('M010_voice_full_pcm',N/'M010.mp3',489600,.9)
bed=decode('M010_owned_bed',ROOT/'video/public/namyangju-map-led-v6/data_city_ambient_v1.wav',489600,extra=['-stream_loop','-1','-ss','32'])
v=np.memmap(voice,dtype=np.float32,mode='r',shape=(489600,2));m=np.memmap(bed,dtype=np.float32,mode='r',shape=(489600,2));f=np.arange(489600)/1600
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
env=.18*smooth(f/15)*smooth((305-f)/23);mixed=np.asarray(v+m*env[:,None],dtype=np.float32);cta=E/'M010_mix.f32';mixed.tofile(cta)
outro=decode('existing_brand_outro',EP/'outputs/caption-station-v13/brand_outro_v13_no_caption.mp4',480000)
raw=E/'full_audio_v15.f32'
with raw.open('wb') as out:
 for p in [prefix,cta,outro]:
  with p.open('rb') as src:shutil.copyfileobj(src,out)
assert raw.stat().st_size==44734400*8
with raw.open('rb') as src:prefix_actual=hashlib.sha256(src.read(43764800*8)).hexdigest()
expected=hashlib.sha256(prefix.read_bytes()).hexdigest();assert expected==prefix_actual
x=np.memmap(raw,dtype=np.float32,mode='r',shape=(44734400,2));peak=float(np.abs(x).max());assert peak<1
subprocess.run([F,'-v','error','-y','-f','f32le','-ar','48000','-ac','2','-i',str(raw),'-c:a','aac','-b:a','192k',str(O/'full_v15_audio.m4a')],check=True)
r={'sample_rate':48000,'channels':2,'total_samples_per_channel':44734400,'duration_s':44734400/48000,'existing_v14_0_to_27353_PCM_exact_preserved':True,'prefix_pcm_sha256':expected,'original_301_cues_and_narration_preserved':True,'CTA_source_PCM_s':7.44,'CTA_voice_gain':.9,'CTA_total_visual_s':10.2,'CTA_tail_silence_after_PCM_s':2.76,'provider_last_spoken_character_end_relative_s':7.2,'hold_after_last_spoken_character_s':3,'hold_basis':'provider alignment not actual listening','outro_from_frame':27659,'outro_frames':300,'full_AAC_reencoded':True,'full_AAC_packet_identity_claim':False,'PCM_peak':peak,'CTA_music_gain':.18,'CTA_music_no_overlap_with_brand':True,'actual_listening':False}
(O/'audio_mix_manifest_v15.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({'samples':44734400,'peak':peak,'existing_PCM_preserved':True}))
