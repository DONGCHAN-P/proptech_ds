// Reproject the existing licensed administrative boundaries once, not inside render loops.
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const proj4=require(path.join(root,'video-agent-studio/map-atlas/vendor/proj4.js'));
proj4.defs('EPSG:5179','+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs');
const data=JSON.parse(fs.readFileSync(path.join(root,'assets/geo/sudogwon_sgg.geojson'),'utf8'));
function convert(coords){if(typeof coords[0]==='number'){const xy=proj4('EPSG:5179','EPSG:4326',coords);if(xy[0]<124||xy[0]>132||xy[1]<33||xy[1]>40)throw Error('Invalid coordinate');return xy.map(x=>+x.toFixed(6));}return coords.map(convert);}
for(const f of data.features) f.geometry.coordinates=convert(f.geometry.coordinates);
const out=path.join(root,'web/static/data');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'capital-boundaries.geojson'),JSON.stringify(data));
console.log(JSON.stringify({features:data.features.length,crs:'EPSG:4326',source_credit:data.credit}));
