/* External tiles are optional for geographic context; never cache/export OSM tiles. */
window.JIPMap = {
  add(map, options) {
    let fallback=null, failures=0, complete=false;
    map.createPane('jipBoundaries').style.zIndex=201;
    const info=L.control({position:'bottomleft'});
    info.onAdd=()=>{const d=L.DomUtil.create('div','jg-map-fallback');d.style.cssText='background:#fffffff0;color:#57516f;padding:5px 9px;border-radius:7px;font:11px sans-serif;max-width:230px';d.textContent='외부 배경 연결 중 · 행정경계도 준비';return d;};info.addTo(map);
    fetch('/data/capital-boundaries.geojson').then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{fallback=L.geoJSON(data,{pane:'jipBoundaries',style:{color:'#b4acc9',weight:1,fillColor:'#eeeaf4',fillOpacity:.9},onEachFeature:(f,l)=>l.bindTooltip(f.properties.name,{sticky:true})});if(!complete||failures)fallback.addTo(map);map.attributionControl?.addAttribution('경계: SGIS · statgarten/maps MIT');info.getContainer().textContent=failures?'외부 배경 연결 불가 · 행정경계도 표시':'행정경계도 · 상세 도로는 외부 지도 연결 필요';}).catch(()=>{info.getContainer().textContent='기본 지도 연결 불가 · 위치 표식만 표시';});
    const tiles=L.tileLayer(options.url,{attribution:options.attribution,maxZoom:options.maxZoom||19,subdomains:options.subdomains||'abc',referrerPolicy:'origin'});
    tiles.on('tileerror',()=>{failures++;if(fallback&&!map.hasLayer(fallback))fallback.addTo(map);info.addTo(map);if(map.hasLayer(tiles))map.removeLayer(tiles);info.getContainer().textContent='외부 배경 연결 불가 · 행정경계도 표시';});
    tiles.on('load',()=>{complete=true;if(!failures){if(fallback)map.removeLayer(fallback);map.removeControl(info);}});
    tiles.addTo(map);
    return tiles;
  }
};
