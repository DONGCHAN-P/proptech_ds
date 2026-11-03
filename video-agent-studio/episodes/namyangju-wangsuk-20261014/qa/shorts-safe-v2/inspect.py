import json, subprocess, hashlib, sys
from pathlib import Path
from PIL import Image, ImageDraw
Q=Path(__file__).resolve().parent; E=Q.parents[1]; O=E/'outputs/shorts-safe-v2'; OLD=E/'outputs/shorts-release-v1'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
FF=str(B/'ffmpeg.exe'); FP=str(B/'ffprobe.exe')
def run(args):return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
def ah(p):return run([FF,'-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-']).stdout.decode().strip()
def shot(p,f,d):run([FF,'-y','-v','error','-ss',str(f/30),'-i',str(p),'-frames:v','1',str(d)])
def main():
 bounds=json.loads((O/'layout_bounds.json').read_text(encoding='utf8')); selected=sys.argv[1:]; results=json.loads((Q/'independent_checks.json').read_text(encoding='utf8')) if selected else []
 viewports=[(360,640),(375,812),(390,844),(393,852),(412,915),(384,854),(390,910),(768,1024),(800,1280)]
 for ident in ['01_rail','02_price','03_choice']:
  if selected and ident not in selected:continue
  results=[r for r in results if r['id']!=ident]
  p=O/f'{ident}_safe_v2.mp4'; out=Q/ident;out.mkdir(exist_ok=True)
  probe=json.loads(run([FP,'-v','error','-show_streams','-show_format','-of','json',str(p)]).stdout)
  v=next(s for s in probe['streams'] if s['codec_type']=='video'); n=int(v['nb_frames'])
  run([FF,'-v','error','-i',str(p),'-f','null','NUL'])
  cues=json.loads((O/f'{ident}_captions.json').read_text(encoding='utf8'))
  frames=sorted(set([0,1,n-2,n-1]+[x for c in cues for x in [max(0,c['from_frame']-1),c['from_frame'],min(n-1,c['to_frame'])]]))
  for f in frames:shot(p,f,out/f'f{f}.png')
  # Every cue start, plus first/last: actual encoded critical-region contact sheets.
  visual=sorted(set([0,n-1]+[c['from_frame'] for c in cues]))
  for start in range(0,len(visual),9):
   batch=visual[start:start+9]; sheet=Image.new('RGB',(1320,510*((len(batch)+2)//3)),'white');d=ImageDraw.Draw(sheet)
   for i,f in enumerate(batch):
    crop=Image.open(out/f'f{f}.png').crop((150,440,822,1170)).resize((440,478));x=i%3*440;y=i//3*510;sheet.paste(crop,(x,y+25));d.text((x+5,y+5),f'{ident} f{f} / {f/30:.3f}s',fill='black')
   sheet.save(out/f'cues_{start//9}.jpg')
  longest=max(cues,key=lambda c:len(' '.join(c['lines']))); src=Image.open(out/f"f{longest['from_frame']}.png")
  sheet=Image.new('RGB',(1440,600*3),'white'); sd=ImageDraw.Draw(sheet); cases=[]
  elems=[b for b in bounds['elements'] if b['short_id']==ident]
  for i,(vp,fit) in enumerate((vp,fit) for vp in viewports for fit in ['contain','cover']):
   w,h=vp;s=(min if fit=='contain' else max)(w/1080,h/1920);ox=(w-1080*s)/2;oy=(h-1920*s)/2
   canvas=Image.new('RGB',vp,'#222222');pic=src.resize((round(1080*s),round(1920*s)));canvas.paste(pic,(round(ox),round(oy)))
   overlay=Image.new('RGBA',vp);d=ImageDraw.Draw(overlay);d.rectangle((0,0,w,h*.14),fill=(230,40,40,180));d.rectangle((0,h*.65,w,h),fill=(230,40,40,180));d.rectangle((w-64,h*.14,w,h*.65),fill=(230,40,40,180));canvas=Image.alpha_composite(canvas.convert('RGBA'),overlay)
   failures=[]
   for b in elems:
    l,t,r,bt=b['bbox'];mapped=[l*s+ox,t*s+oy,r*s+ox,bt*s+oy]
    if not(mapped[0]>=0 and mapped[1]>=h*.14 and mapped[2]<=w-64 and mapped[3]<=h*.65):failures.append(b)
   cases.append(dict(viewport=vp,fit=fit,element_checks=len(elems),overlaps=len(failures)))
   canvas.thumbnail((240,560));x=i%6*240;y=i//6*600;sheet.paste(canvas.convert('RGB'),(x+(240-canvas.width)//2,y+30));sd.text((x+5,y+5),f'{w}x{h} {fit}',fill='black')
  sheet.save(out/'device_matrix.jpg')
  results.append(dict(id=ident,file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,frames=n,duration=float(v['duration']),resolution=[v['width'],v['height']],fps=v['r_frame_rate'],video_codec=v['codec_name'],whole_decode_pass=True,audio_packets_identical=ah(p)==ah(OLD/f'{ident}.mp4'),srt_bytes_identical=(O/f'{ident}.srt').read_bytes()==(OLD/f'{ident}.srt').read_bytes(),sample_frames=frames,cue_contact_sheets=len(range(0,len(visual),9)),longest_cue=longest,device_matrix=cases))
 (Q/'independent_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps([dict(id=r['id'],frames=r['frames'],checks=len(r['sample_frames']),overlaps=sum(c['overlaps'] for c in r['device_matrix'])) for r in results]))
if __name__=='__main__':main()
