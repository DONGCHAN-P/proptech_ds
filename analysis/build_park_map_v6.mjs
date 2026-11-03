import fs from 'node:fs/promises';
const z=15,n=2**z,lon=127.064,lat=37.284;
const px=(lon+180)/360*n*256,py=(1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)/2*n*256;
const x0=Math.floor(px/256)-2,y0=Math.floor(py/256)-1,dir='video/public/maps-v6';await fs.mkdir(dir,{recursive:true});
for(let y=0;y<3;y++)for(let x=0;x<4;x++){const path=`${dir}/${x}-${y}.png`;try{await fs.access(path);}catch{const r=await fetch(`https://tile.openstreetmap.org/${z}/${x0+x}/${y0+y}.png`,{headers:{'User-Agent':'RealestateVideoResearch/1.0 (local educational production)'},signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error('Tile HTTP '+r.status);await fs.writeFile(path,Buffer.from(await r.arrayBuffer()));}}
await fs.writeFile(dir+'/map.json',JSON.stringify({z,x0,y0,cropY:64,width:1024,height:640,credit:'© OpenStreetMap contributors'},null,2));console.log('12 detailed map tiles ready');
