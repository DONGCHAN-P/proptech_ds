from pathlib import Path
import json,subprocess,hashlib,collections
from PIL import Image,ImageOps,ImageDraw
H=Path(__file__).resolve().parent;EP=H.parents[1];R=EP.parents[2]
O=EP/'outputs/production-v6-preview';video=O/'changneung_full_v6_preview_r4.mp4'
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
H.mkdir(parents=True,exist_ok=True);(H/'frames').mkdir(exist_ok=True)
p=json.loads((O/'project_r4.json').read_text(encoding='utf8'))
times=[1,18,60,124,186,273,314,395,468,610,689,804,863,918]
images=[]
for t in times:
 dst=H/'frames'/f'{t:04d}s.jpg'
 z=subprocess.run([str(F),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(dst)],capture_output=True)
 if z.returncode:raise RuntimeError(z.stderr.decode(errors='replace'))
 im=Image.open(dst).convert('RGB');im.thumbnail((1280,720));im.save(dst,quality=88)
 images.append({'time_s':t,'image':str(dst.relative_to(H))})
dur=collections.defaultdict(float);runs=[]
for x in p['intervals']:
 props={k:v for k,v in x['props'].items() if k not in ['caption','motionFrame']}
 key=json.dumps(props,ensure_ascii=False,sort_keys=True);n=x['duration_frames']/30
 dur[props['board']]+=n
 if runs and key==runs[-1]['key'] and runs[-1]['end_frame']==x['start_frame']:runs[-1]['end_frame']=x['end_frame']
 else:runs.append({'key':key,'props':props,'start_frame':x['start_frame'],'end_frame':x['end_frame']})
long=[]
for x in runs:
 seconds=(x['end_frame']-x['start_frame'])/30
 if seconds>=15:long.append({'start_s':x['start_frame']/30,'end_s':x['end_frame']/30,'duration_s':seconds,'visual':x['props']})
long.sort(key=lambda x:x['duration_s'],reverse=True)
stats={'source':str(video.relative_to(R)),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'duration_s':p['duration_frames']/30,'scene_times':p['scenes'],'board_duration_s':dict(dur),'long_visual_runs':long[:16],'definition':'same board and focus props despite caption changes; short entrance motion not continuous movement','frames':images,'actual_listening':False,'continuous_playback':False}
(H/'evidence.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
thumbs=Image.new('RGB',(1024,680),'#dddddd');draw=ImageDraw.Draw(thumbs)
for i,t in enumerate([186,395,468,689]):
 im=Image.open(H/'frames'/f'{t:04d}s.jpg');im=im.resize((512,288));x=(i%2)*512;y=(i//2)*340
 thumbs.paste(im,(x,y+24));draw.text((x+8,y+6),f'{t//60:02d}:{t%60:02d} - 512px mobile width',fill='black')
thumbs.save(H/'mobile_readability.jpg',quality=90)
script=(EP/'outputs/script-review-v6/script_v6.md').read_text(encoding='utf8')
srt=(O/'changneung_v6_preview_r4.srt').read_text(encoding='utf8')
(H/'context.txt').write_text('검토 범위: 실제 MP4에서 시간지정 프레임14장, 모바일축소4장, 실제 자막 및 편집타임라인 통계. 연속 시청·실제 청취 아님. 무료 Heami TTS 검토본이므로 최종 Jun의 자연스러움과 속도는 평가 불가. 기술오류 검사와 시청자 몰입/이해도 평가를 구별. 과거 철회된 지도 줌/급전환·반복펄스 부활 금지. 크림/Pretendard/파랑/고정흰자막 및 실제토지계획도/locator 계승. 사용자 핵심: 정보제공, 지도/사진/도식 내용에맞게변경, 시리즈연결, 10분이상. 사실·핵심결론·새음성변경은새script/budget검토필요.\n\n[실제 자막]\n'+srt+'\n\n[타임라인 통계]\n'+json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'frames':len(images),'duration_s':stats['duration_s'],'longest_visual_runs':long[:5]},ensure_ascii=False))
