// OSM interactive viewport only. No prefetch, offline package, or tile export.
const tileCache=new Map;
function drawBasemap(){
 if(!el('basemap')?.checked||location.protocol==='file:'||typeof proj4==='undefined')return false;
 const def='+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs';
 const ll=p=>proj4(def,'EPSG:4326',p),toScreen=(lon,lat)=>xy(...proj4('EPSG:4326',def,[lon,lat]));
 const center=ll([view.x,view.y]),z=Math.max(6,Math.min(18,Math.ceil(Math.log2(156543.03392*Math.cos(center[1]*Math.PI/180)*view.s)))),n=2**z;
 const tile=([lon,lat])=>[(lon+180)/360*n,(1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)/2*n];
 const corners=[[0,0],[W,0],[0,H],[W,H]].map(([x,y])=>tile(ll([view.x+(x-W/2)/view.s,view.y-(y-H/2)/view.s])));
 const minX=Math.floor(Math.min(...corners.map(p=>p[0]))),maxX=Math.floor(Math.max(...corners.map(p=>p[0]))),minY=Math.floor(Math.min(...corners.map(p=>p[1]))),maxY=Math.floor(Math.max(...corners.map(p=>p[1])));
 if((maxX-minX+1)*(maxY-minY+1)>90)return false;
 const point=(x,y)=>toScreen(x/n*360-180,Math.atan(Math.sinh(Math.PI*(1-2*y/n)))*180/Math.PI);
 function triangle(img,p,q,r,second){ctx.save();ctx.beginPath();ctx.moveTo(...p);ctx.lineTo(...q);ctx.lineTo(...r);ctx.closePath();ctx.clip();if(!second)ctx.transform((q[0]-p[0])/256,(q[1]-p[1])/256,(r[0]-p[0])/256,(r[1]-p[1])/256,p[0],p[1]);else ctx.transform((p[0]-q[0])/256,(p[1]-q[1])/256,(p[0]-r[0])/256,(p[1]-r[1])/256,q[0]+r[0]-p[0],q[1]+r[1]-p[1]);ctx.drawImage(img,0,0,256,256);ctx.restore()}
 for(let x=minX;x<=maxX;x++)for(let y=minY;y<=maxY;y++){if(x<0||y<0||x>=n||y>=n)continue;const key=`${z}/${x}/${y}`;let image=tileCache.get(key);if(!image){image=new Image;image.onload=()=>requestAnimationFrame(draw);image.onerror=()=>{image.failed=true;el('basemap-note').textContent='배경지도를 불러오지 못했습니다. 단지·학교·역은 계속 사용할 수 있습니다.'};image.src=(CONFIG.tileUrl||'https://tile.openstreetmap.org/{z}/{x}/{y}.png').replace('{z}',z).replace('{x}',x).replace('{y}',y);tileCache.set(key,image)}if(image.complete&&image.naturalWidth){const a=point(x,y),b=point(x+1,y),c=point(x,y+1),d=point(x+1,y+1);triangle(image,a,b,c,false);triangle(image,d,c,b,true)}}
 while(tileCache.size>250)tileCache.delete(tileCache.keys().next().value);
 return true;
}
