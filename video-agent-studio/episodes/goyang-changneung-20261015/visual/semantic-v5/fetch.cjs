const fs=require('fs');
const q='[out:json][timeout:25];node[railway=station](37.48,126.80,37.66,127.05);out;';
fs.writeFileSync(__dirname+'/raw/query.overpass',q);
fetch('https://overpass.private.coffee/api/interpreter',{method:'POST',headers:{'User-Agent':'ChangneungVideoGeography/1.0'},body:new URLSearchParams({data:q})}).then(r=>r.text()).then(t=>{fs.writeFileSync(__dirname+'/raw/response.txt',t);const d=JSON.parse(t);fs.writeFileSync(__dirname+'/raw/osm-wide.json',t);console.log(d.elements.filter(e=>/^(시청|광화문|종로3가|경복궁|여의도|마곡나루|강남|교대|디지털미디어시티|원흥|새절|공덕)$/.test(e.tags?.name)).map(e=>[e.id,e.tags.name,e.lon,e.lat]));});
