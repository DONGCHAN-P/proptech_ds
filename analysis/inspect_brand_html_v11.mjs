import fs from 'node:fs/promises';
for(const id of ['asml','lam','gg','lg','sk']){const h=await fs.readFile('video/public/brands-v11/'+id+'.html','utf8');const urls=[...new Set([...h.matchAll(/(?:src|href)=["']([^"']+)["']/gi)].map(m=>m[1]).filter(x=>/logo|\.svg|\.png/i.test(x)))];console.log(id+' '+JSON.stringify(urls.slice(0,22)));}
const h=await fs.readFile('video/public/brands-v11/samsung.html','utf8'),svg=[...h.matchAll(/<svg\b[^>]*>[\s\S]*?<\/svg>/gi)][1][0];await fs.writeFile('video/public/brands-v11/samsung.svg',svg.replace('fill="currentColor"','fill="#1428A0"'));
