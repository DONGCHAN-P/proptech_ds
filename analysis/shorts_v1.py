import json, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'video/out/shorts-v1'
OUT.mkdir(parents=True, exist_ok=True)
FF=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
PROBE=FF.with_name('ffprobe.exe')
timeline=json.loads((ROOT/'video/out/newtown-v13-timing.json').read_text(encoding='utf-8'))
bykey={x['key']:x for x in timeline}
specs=[
 dict(id='dongtan-gap',title='같은 동탄, 같은 84㎡인데 왜 가격이 다를까?',head=['같은 동탄 84㎡','가격의 중심은 어디?'],keys=['distribution','quartiles'],summary=['대장 단지 ≠ 도시 전체','같은 면적의 거래 분포를 비교','생활권·단지별 조건까지 확인']),
 dict(id='gtx-alone',title='GTX만 생기면 신도시 가격도 같아질까?',head=['GTX만 생기면','가격도 같아질까?'],keys=['after-4','rail-counter'],summary=['철도는 중요한 조건','일자리·출발 가격·공급도 함께','광교·동탄·운정 비교']),
 dict(id='five-questions',title='신도시 청약 전, 이 5가지를 확인하세요',head=['신도시 청약 전','확인할 5가지'],keys=['after-8','timing'],summary=['① 일자리  ② 입주 시점 철도','③ 분양가  ④ 생활 시설','⑤ 같은 생활권의 공급'])
]
fontpath='C:/Windows/Fonts/malgunbd.ttf'
def font(n): return ImageFont.truetype(fontpath,n)
for s in specs:
 im=Image.new('RGB',(1080,1920),'#101827'); d=ImageDraw.Draw(im)
 d.text((70,110),'데이터로보는부동산',font=font(33),fill='#A4B1C1')
 for i,line in enumerate(s['head']):d.text((70,235+i*100),line,font=font(68),fill='#F5F0E8')
 d.rounded_rectangle((70,1160,1010,1540),radius=25,fill='#1C293B')
 for i,line in enumerate(s['summary']):d.text((105,1210+i*90),line,font=font(43),fill='#F5F0E8')
 d.text((70,1650),'실거래가로 보는 신도시 선택 기준',font=font(37),fill='#70B9F2')
 d.text((70,1720),'전체 분석은 채널의 본편에서',font=font(35),fill='#B7C3D2')
 d.text((70,1800),'표본·기간·출처는 본편 설명 참고',font=font(28),fill='#94A2B5')
 bg=OUT/(s['id']+'-layout.png'); im.save(bg)
 segments=[]
 for j,key in enumerate(s['keys']):
  row=bykey[key]; seg=OUT/(s['id']+f'-part{j}.mp4'); segments.append(seg)
  cmd=[str(FF),'-y','-ss',str(row['start']),'-i',str(ROOT/'video/out/newtown-v13-release-review.mp4'),'-loop','1','-i',str(bg),'-filter_complex','[0:v]scale=1080:608,setsar=1[src];[1:v][src]overlay=0:490:shortest=1[v]','-map','[v]','-map','0:a','-t',str(row['end']-row['start']),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k',str(seg)]
  subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=(OUT/(s['id']+f'-part{j}.log')).open('w'))
 listing=OUT/(s['id']+'-concat.txt'); listing.write_text('\n'.join("file '"+str(x).replace('\\','/')+"'" for x in segments),encoding='utf-8')
 final=OUT/(s['id']+'.mp4')
 subprocess.run([str(FF),'-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(final)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 raw=subprocess.check_output([str(PROBE),'-v','error','-show_streams','-show_format','-of','json',str(final)])
 s['probe']=json.loads(raw);s['path']=str(final.relative_to(ROOT));s['source_intervals']=[{'key':k,'start':bykey[k]['start'],'end':bykey[k]['end']} for k in s['keys']]
 s['description']='광교·동탄 실거래가 비교에서 찾은 신도시 선택 기준입니다. 지역 전체 수익률이나 미래 가격 예측이 아닙니다. 전체 분석과 상세 출처는 채널 본편 설명에서 확인하세요. #신도시 #부동산 #실거래가'
 for t in [2,12, s['probe']['format']['duration'] and float(s['probe']['format']['duration'])-2]:
  subprocess.run([str(FF),'-y','-ss',str(t),'-i',str(final),'-frames:v','1',str(OUT/(s['id']+f'-qa-{int(t)}.png'))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 print('DONE',s['id'],flush=True)
(OUT/'metadata.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2),encoding='utf-8')
