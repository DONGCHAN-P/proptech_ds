const fs=require('fs'),path=require('path'),crypto=require('crypto');
const e=path.resolve(__dirname,'../..'),r=path.resolve(e,'../../..'),pub=path.join(r,'video/public/changneung-v3'),src=path.join(r,'video/src/changneung-v3');
fs.mkdirSync(pub,{recursive:true});fs.mkdirSync(src,{recursive:true});
const read=p=>JSON.parse(fs.readFileSync(path.join(e,p),'utf8').replace(/^\uFEFF/,''));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const geo=read('visual/geographic-v1/osm_subset.geojson'),loc=read('visual/geographic-v1/locations.json');
const maps=[{id:'commute',bbox:[126.79,37.57,126.95,37.663]},{id:'life',bbox:[126.852,37.621,126.892,37.657]},{id:'alternatives',bbox:[126.843,37.626,126.922,37.660]}];
const W=1400,H=560;
const railColors={'3호선':'#dc8839','서울 지하철 3호선':'#dc8839','일산선':'#dc8839','6호선':'#b68a35','경의본선':'#459488','경의선':'#459488','용산선':'#459488','인천국제공항선':'#5899bc','서해선':'#8fa94c','수도권광역급행철도에이선':'#8e649a'};
function projection(b){const [w,s,e,n]=b,k=Math.min((W-80)/((e-w)*.792),(H-50)/(n-s));return ([lon,lat])=>[W/2+(lon-(w+e)/2)*.792*k,H/2+((n+s)/2-lat)*k]}
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
for(const m of maps){
 const pr=projection(m.bbox);m.width=W;m.height=H;m.stations=loc.filter(x=>x.coordinate_basis==='station node').map(x=>({...x,p:pr([x.lon,x.lat])}));
 m.places=loc.filter(x=>x.coordinate_basis!=='station node').map(x=>({...x,p:pr([x.lon,x.lat])}));
 const pth=cs=>cs.map((v,i)=>{const [x,y]=pr(v);return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`}).join(' ');
 const paths=[];m.rail=[];m.roads=[];m.polygons=[];
 for(const f of geo.features){const t=f.properties,g=f.geometry;if(g.type==='Point')continue;const cs=g.type==='Polygon'?g.coordinates[0]:g.coordinates;
 if(!cs.some(c=>{const [x,y]=pr(c);return x>-100&&x<W+100&&y>-100&&y<H+100}))continue;
 const d=pth(cs);
 if(g.type==='Polygon'){const name=t.name||'',ikea=name==='IKEA',item={id:f.id,name,d,fill:ikea?'#e9bd68':'#ead9b0'};m.polygons.push(item);paths.push(`<path d="${d}Z" fill="${item.fill}" fill-opacity=".8" stroke="#fff" stroke-width="2"/>`);}
 else if(t.waterway)paths.push(`<path d="${d}" fill="none" stroke="#a9cfda" stroke-width="3"/>`);
 else if(t.highway){const major=['motorway','trunk','primary'].includes(t.highway);paths.push(`<path d="${d}" fill="none" stroke="${major?'#d3c9b5':'#ded8ca'}" stroke-width="${major?2.6:1.1}"/>`);if(['덕양로','도래울로','권율대로','서오릉로'].includes(t.name))m.roads.push({name:t.name,d,p:pr(cs[Math.floor(cs.length/2)])});}
 else if(['rail','subway'].includes(t.railway)&&!['yard','siding'].includes(t.service)){const col=railColors[t.name]||'#9daab0';paths.push(`<path d="${d}" fill="none" stroke="${col}" stroke-opacity=".34" stroke-width="2"/>`);m.rail.push({name:t.name||'',d,color:col});}
 }
 fs.writeFileSync(path.join(pub,`map_${m.id}.svg`),`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="#eeede5"/><g>${paths.join('')}</g></svg>`);
}
const price=read('research/price-stage-v3/facts.json'),alternatives=read('research/prices-v2/facts.json');
const data={revision:'production-v3',maps,locations:loc,prices:price.facts.filter(x=>x.price),alternatives:alternatives.facts,calendar:read('research/production-v2/calendar.json').events};
fs.writeFileSync(path.join(src,'data.json'),JSON.stringify(data));
const copies=[['research/map-clearance-v1/raw/eum_lots_overall_20251224.jpg','official_whole_20251224.jpg'],['outputs/editor-preflight-v1/brand_intro_generic_v1.mp4','brand_intro.mp4'],['outputs/editor-preflight-v1/brand_outro_generic_v1.mp4','brand_outro.mp4'],['visual/photo-v3/wonheung_1.jpg','wonheung_1.jpg'],['visual/photo-v3/wonheung_2.jpg','wonheung_2.jpg'],['outputs/channel-style-v1/W15_50.png','previous_wangsuk.png']];
for(const [input,name] of copies)fs.copyFileSync(path.join(e,input),path.join(pub,name));
for(const name of ['Pretendard-Regular.woff2','Pretendard-Bold.woff2','data_city_ambient_v1.wav','data_city_ambient_v1.license.json'])fs.copyFileSync(path.join(r,'video/public/namyangju-map-led-v6',name),path.join(pub,name));
fs.copyFileSync(path.join(e,'visual/geographic-v1/osm_subset.geojson'),path.join(pub,'osm_subset.geojson'));
fs.copyFileSync(path.join(e,'visual/geographic-v1/rights_and_sources.json'),path.join(pub,'map_rights_and_sources.json'));
fs.writeFileSync(path.join(pub,'README_ODbL.txt'),'Geographic data © OpenStreetMap contributors. Derived database osm_subset.geojson under ODbL 1.0. https://www.openstreetmap.org/copyright https://opendatacommons.org/licenses/odbl/1-0/\nOfficial whole plan: 국토교통부 고시2025-813호(2025.12.24), 토지이음, 공공누리3유형. Image preserved whole; no crop, trace or overpaint. https://www.eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=628391\n');
const inputs=['visual/geographic-v1/osm_subset.geojson','visual/geographic-v1/locations.json','visual/geographic-v1/rights_and_sources.json','research/price-stage-v3/facts.json','research/prices-v2/facts.json','research/production-v2/calendar.json','research/map-clearance-v1/raw/eum_lots_overall_20251224.jpg'];
fs.mkdirSync(path.join(e,'outputs/production-v3'),{recursive:true});
fs.writeFileSync(path.join(e,'outputs/production-v3/assets_manifest.json'),JSON.stringify({revision:'production-v3',inputs:inputs.map(p=>({path:p,sha256:sha(path.join(e,p))})),generated_maps:maps.map(m=>({id:m.id,bbox:m.bbox,projection:'local equirectangular .792 cosine factor, north up',file:`video/public/changneung-v3/map_${m.id}.svg`,sha256:sha(path.join(pub,`map_${m.id}.svg`))})),new_ai_generation:0,photo_count:0,official_plan:'whole unmodified fit only; not OSM-derived',full_video_rendered:false},null,2));
console.log('Prepared 3 geographic bases, source-backed price/calendar data, whole official plan and existing brand assets.');
