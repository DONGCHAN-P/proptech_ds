import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const e={};for(const l of (await fs.readFile('.env','utf8')).split(/\r?\n/)){const m=l.match(/^\s*([A-Z_0-9]+)\s*=\s*(.*?)\s*$/);if(m)e[m[1]]=m[2].replace(/^(['"])(.*)\1$/,'$2');}
const dir='video/public/pilot-v1';await fs.mkdir(dir,{recursive:true});
const lines=[
'이천십칠 년, 사억 팔천만 원대에 분양한 아파트가 있습니다.',
'올해 유월, 같은 면적이 이십이억 이천오백만 원에 거래됐습니다. 분양가의 사 점 육 배입니다.',
'이천이십사 년, 이 아파트 한 채를 분양가 그대로 다시 판다고 하자, 이백구십사만 명이 청약에 몰렸습니다.',
'화성 동탄의 동탄역 롯데캐슬 이야기입니다.',
'그런데 같은 시기에 생긴 신도시 중에는, 분양가 근처에서 십 년째 머문 곳도 있습니다.',
'오늘은 이 차이를 데이터로 쪼개 보겠습니다. 그리고 이 기준으로 앞으로 나올 후보 신도시도 함께 살펴보겠습니다.'
];
const cfg=JSON.parse(await fs.readFile('config/tts.json','utf8'));const segments=[];
for(let i=0;i<lines.length;i++){const file='voice-'+i+'.mp3',dest=dir+'/'+file;try{await fs.access(dest);}catch{const r=await fetch('https://api.elevenlabs.io/v1/text-to-speech/'+cfg.voice_id+'?output_format=mp3_44100_128',{method:'POST',headers:{'xi-api-key':e.ELEVENLABS_API_KEY,'Content-Type':'application/json'},body:JSON.stringify({text:lines[i],model_id:cfg.model}),signal:AbortSignal.timeout(90000)});if(!r.ok)throw Error('TTS HTTP '+r.status);await fs.writeFile(dest,Buffer.from(await r.arrayBuffer()));}const duration=Number(execFileSync('video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe',['-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',dest],{encoding:'utf8'}).trim());segments.push({text:lines[i],file,duration,frames:Math.ceil((duration+.5)*30)});console.log('voice '+i+' '+duration+'s');}
await fs.writeFile(dir+'/plan.json',JSON.stringify({fps:30,width:1920,height:1080,segments,voice:cfg.voice_name,model:cfg.model},null,2));
const h={Authorization:'Bearer '+(e.RUNWAY_API_KEY||e.RUNWAYML_API_SECRET),'X-Runway-Version':'2024-11-06','Content-Type':'application/json'};
let task;try{task=JSON.parse(await fs.readFile(dir+'/runway-task.json','utf8'));}catch{const prompt='Premium editorial miniature city made from matte ivory architectural blocks on a deep midnight navy tabletop, soft amber light travels from a railway station along a clean glowing transit line toward residential towers. Slow cinematic lateral camera move with subtle parallax. Abstract conceptual city, not an actual location, no letters, no logos, no numbers, no people. Elegant restrained documentary visual, realistic materials and soft shadows, stable geometric buildings, wide landscape composition with generous negative space.';const r=await fetch('https://api.dev.runwayml.com/v1/text_to_video',{method:'POST',headers:h,body:JSON.stringify({model:'gen4.5',promptText:prompt,ratio:'1280:720',duration:5}),signal:AbortSignal.timeout(60000)});task=await r.json();if(!r.ok)throw Error('Runway HTTP '+r.status+' '+JSON.stringify(task));await fs.writeFile(dir+'/runway-task.json',JSON.stringify(task));await fs.writeFile(dir+'/city.license.json',JSON.stringify({source:'Runway',model:'gen4.5',prompt,generated_at:new Date().toISOString(),credit:'AI 생성 개념 영상 · 실제 지역 모습 아님',estimated_credits:60},null,2));}
try{await fs.access(dir+'/city.mp4');console.log('Runway cached');process.exit(0);}catch{}
for(let n=0;n<90;n++){const r=await fetch('https://api.dev.runwayml.com/v1/tasks/'+task.id,{headers:h,signal:AbortSignal.timeout(30000)});const j=await r.json();console.log('Runway '+j.status);if(j.status==='SUCCEEDED'){const file=await fetch(j.output[0]);await fs.writeFile(dir+'/city.mp4',Buffer.from(await file.arrayBuffer()));console.log('Runway saved');break;}if(['FAILED','CANCELLED'].includes(j.status))throw Error('Runway '+j.status);await new Promise(resolve=>setTimeout(resolve,10000));}

