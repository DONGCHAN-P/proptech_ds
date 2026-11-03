import fs from 'node:fs/promises';
const intro=JSON.parse(await fs.readFile('video/public/pilot-v1/plan.json','utf8')).segments.map(s=>({...s,frames:Math.ceil((s.duration+1.2)*30)}));
const extra=JSON.parse(await fs.readFile('video/public/pilot-v5/plan.json','utf8')).segments;
const after=JSON.parse(await fs.readFile('video/public/pilot-v6/plan.json','utf8')).segments;
let at=0;const rows=[...intro,...extra,...after].map((s,i)=>{const r={index:i,title:s.title||s.text,start:at/30,end:(at+s.frames)/30,text:s.text};at+=s.frames;return r});
function fmt(t){const ms=Math.round(t*1000);return `${String(Math.floor(ms/3600000)).padStart(2,'0')}:${String(Math.floor(ms/60000)%60).padStart(2,'0')}:${String(Math.floor(ms/1000)%60).padStart(2,'0')},${String(ms%1000).padStart(3,'0')}`;}
await fs.writeFile('video/out/newtown-v6.srt',rows.map((r,i)=>`${i+1}\n${fmt(r.start+.2)} --> ${fmt(r.end-.5)}\n${r.text}\n`).join('\n'));
await fs.writeFile('video/out/newtown-v6-timing.json',JSON.stringify(rows,null,2));
console.log(JSON.stringify(rows.map(r=>({i:r.index,start:r.start,title:r.title})),null,2));
