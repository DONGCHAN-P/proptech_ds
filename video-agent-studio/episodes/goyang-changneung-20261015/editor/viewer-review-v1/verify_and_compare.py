from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw,ImageFont
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/viewer-review-v1';Q=EP/'qa/viewer-review-v1';B=R/'video/node_modules/@remotion/compositor-win32-x64-msvc';F=B/'ffmpeg.exe';P=B/'ffprobe.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((R/'video/src/changneung-v6/data.json').read_text(encoding='utf-8'));prices={i:next(x for x in data['prices'] if x.get('price',{}).get('scope','').startswith(i)) for i in ['S5','S1','S4']}
expected={'S5':776598000,'S1':790380000,'S4':873329000}
for k,x in prices.items():
 p=x['price'];assert p['amount_krw']+p['balcony_extension_krw']==expected[k]==p['basic_plus_balcony_krw']
assert [f"{expected[k]/1e8:.2f}" for k in ['S5','S1','S4']]==['7.77','7.90','8.73'];assert expected['S4']-expected['S5']==96731000
assert 759+494==1253 and 759+494+1024==2277 and 430+759+494+1024!=2277
z=subprocess.run([str(P),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(O/'supply_motion_demo_6s.mp4')],stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert z.returncode==0 and not z.stderr.strip();probe=json.loads(z.stdout);v=next(x for x in probe['streams'] if x['codec_type']=='video');assert(v['width'],v['height'],v['avg_frame_rate'],int(v['nb_read_frames']))==(1920,1080,'30/1',180);assert not any(x['codec_type']=='audio' for x in probe['streams'])
motion=[]
for f in [15,60,110,165]:
 out=O/f'motion_f{f:03d}.png';z=subprocess.run([str(F),'-v','error','-y','-ss',f'{f/30:.9f}','-i',str(O/'supply_motion_demo_6s.mp4'),'-frames:v','1',str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert z.returncode==0;motion.append({'frame_target':f,'file':out.name,'sha256':sha(out)})
font_path=Path('C:/Windows/Fonts/malgun.ttf');font=ImageFont.truetype(str(font_path),18) if font_path.exists() else ImageFont.load_default();small=ImageFont.truetype(str(font_path),14) if font_path.exists() else font
comparisons=[];pairs=[('price','0395s.jpg','price_s4.png','가격 · 기존 395초와 S4 추가부담 시안 (강조 상태는 다름)'),('supply','0610s.jpg','supply_s4.png','공급 · 기존 610초와 S4 누적 완료 시안'),('family','0804s.jpg','family_dates.png','가족 달력 · 기존 804초와 날짜 입력 시안')]
for name,before,after,label in pairs:
 b=Image.open(Q/'frames'/before).convert('RGB').resize((512,288),Image.Resampling.LANCZOS);a=Image.open(O/after).convert('RGB').resize((512,288),Image.Resampling.LANCZOS)
 b.save(O/f'mobile_{name}_before_512.png');a.save(O/f'mobile_{name}_after_512.png');sheet=Image.new('RGB',(1048,355),'#f6f4ef');draw=ImageDraw.Draw(sheet);draw.text((12,5),label,font=font,fill='#173348');draw.text((12,33),'기존 r4 실제 MP4 프레임',font=small,fill='#637580');draw.text((536,33),'개선 대표 시안 · 본편 미적용',font=small,fill='#286cda');sheet.paste(b,(12,62));sheet.paste(a,(536,62));file=f'compare_mobile_{name}.png';sheet.save(O/file);comparisons.append({'kind':name,'before_actual_frame':before,'after_proposal':after,'file':file,'each_panel_pixels':[512,288],'note':'price focus differs; this compares hierarchy/readability, not identical narration frames' if name=='price' else 'representative layout comparison; not timing-aligned replacement'})
baseline=EP/'outputs/production-v6-preview/changneung_full_v6_preview_r4.mp4';assert sha(baseline)=='645e2f927da976899737e3813d2e7f4eb28bf3ca51a0e103a51c43ec09b32f06'
receipt={'status':'actual_representative_renders_and_mobile_comparisons_generated','baseline_r4_unchanged_sha256':sha(baseline),'price_exact_krw':expected,'price_summary_eok':['7.77','7.90','8.73'],'s4_minus_s5_krw':96731000,'s4_rounded_extra_manwon':9700,'supply_steps':[759,1253,2277],'s6_430_excluded_from_2277':True,'family_placeholder':'YYYY.MM only; no invented individual dates, school grade or living-cost values','retained_family_events':['S5 2028.01 예정','S1 2029.05 예정','S4 2030.03 예정','GTX-A 창릉역 2030년 예정·월 미정','고양은평선 2031.12 목표'],'comparisons':comparisons,'motion':{'file':'supply_motion_demo_6s.mp4','sha256':sha(O/'supply_motion_demo_6s.mp4'),'probe':probe,'decoded_video_frames':180,'audio_streams':0,'decode_exit_code':0,'decode_stderr_empty':True,'not_narration_timing_locked':True,'actual_frames':motion},'actual_listening':False,'continuous_human_playback':False,'visual_review_pending':True}
(O/'validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print('Exact values, 180 decoded motion frames, unchanged r4, three 512px comparisons verified')
