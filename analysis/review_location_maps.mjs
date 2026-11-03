import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
const bin='video/node_modules/@remotion/compositor-win32-x64-msvc/',input='video/out/location-maps-preview.mp4',dir='video/out/qa-location-maps';fs.mkdirSync(dir,{recursive:true});
const times=[1,8,14,20];for(const t of times)execFileSync(bin+'ffmpeg.exe',['-v','error','-ss',String(t),'-i',input,'-frames:v','1','-y',dir+'/frame-'+t+'.png']);
const probe=JSON.parse(execFileSync(bin+'ffprobe.exe',['-v','error','-show_entries','stream=codec_name,width,height,duration','-show_entries','format=duration,size','-of','json',input],{encoding:'utf8'}));fs.writeFileSync(dir+'/technical.json',JSON.stringify({probe,frames_inspected:times,continuous_playback:false,audio:'silent map motion preview by design'},null,2));console.log(JSON.stringify(probe));
