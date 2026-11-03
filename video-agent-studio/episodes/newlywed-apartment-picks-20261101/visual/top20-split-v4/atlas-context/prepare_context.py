"""Clip reusable source layers to the twenty existing statistical districts."""
from pathlib import Path
from collections import defaultdict
import gzip,json,hashlib,sys,math
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
sys.path.insert(0,str(R/'tools/gis_vendor'))
from pyproj import Transformer
sys.path.insert(0,str(E/'research/top20-explain-v3/prices'))
from calculate_prices import in_geojson
AT=R/'video-agent-studio/map-atlas';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,d):(D/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def main():
    points=read(E/'research/top20-split-v4/prices/complex_prices.json')['rows']
    rank=read(E/'research/top20-8min-v2/top20.json')['regions']
    schools=read(AT/'layers/processed/education.json');stations=read(AT/'layers/processed/transit.json');routes=read(AT/'layers/processed/overlays.json')
    ll=Transformer.from_crs(5179,4326,always_xy=True);xy=Transformer.from_crs(4326,5179,always_xy=True)
    results=[]
    for r in rank:
        rid=r['region_id'];bound=json.loads(gzip.decompress((E/'research/top20-explain-v3/prices/snapshots'/f'boundary_{rid}_20241001.geojson.gz').read_bytes()))
        def allpts(g):
            c=g['coordinates']
            if g['type']=='Polygon':return [p for ring in c for p in ring]
            return [p for poly in c for ring in poly for p in ring]
        coords=[p for f in bound['features'] for p in allpts(f['geometry'])];projected=[xy.transform(*p) for p in coords]
        bbox=[min(p[0] for p in projected),min(p[1] for p in projected),max(p[0] for p in projected),max(p[1] for p in projected)]
        inside=lambda p:any(in_geojson(*ll.transform(*p),f['geometry']) for f in bound['features'])
        within=lambda p:bbox[0]-700<=p[0]<=bbox[2]+700 and bbox[1]-700<=p[1]<=bbox[3]+700
        sc=[{**s,'inside_region':inside(s['xy']),'lonlat':ll.transform(*s['xy'])} for s in schools['schools'] if within(s['xy']) and s.get('operation')=='운영']
        st=[{**s,'inside_region':inside(s['xy']),'lonlat':ll.transform(*s['xy'])} for s in stations['stations'] if within(s['xy'])]
        routeparts=[]
        for rt in routes['routes']:
            segments=[]
            for seg in rt['segments']:
                # Keep actual consecutive coordinates; never connect separated runs across the viewport.
                run=[]
                for p in seg:
                    if within(p):run.append(p)
                    else:
                        if len(run)>1:segments.append(run)
                        run=[]
                if len(run)>1:segments.append(run)
            if segments:routeparts.append({'name':rt['name'],'color':rt['color'],'segments':segments})
        data={'region':r,'bounds_5179':bbox,'boundary':bound,'schools':sc,'stations':st,'rail_routes':routeparts,
              'complex_points':[p for p in points if p['region_id']==rid and p['coordinate_verified']]}
        save(f'{rid}_context.json',data)
        results.append({'region_id':rid,'schools_in_region':sum(s['inside_region'] for s in sc),'stations_records_in_region':sum(s['inside_region'] for s in st),'distinct_station_names_in_region':len({s['name'] for s in st if s['inside_region']}),'route_groups':len(routeparts),'price_points':len(data['complex_points']),'bbox_5179':bbox})
    save('coverage.json',{'regions':results,'source_metadata':{'education':schools['meta'],'stations':stations['meta'],'rails':routes['meta']},'missing_layers':['roads','water_and_parks','commercial_nodes'],'station_coverage':'source is incomplete; station count is not a total-network statistic','schools_semantics':'actual operating school locations; no assignment inference','paid_calls':0,'external_calls':0})
    print(json.dumps({'regions':len(results),'schools':sum(x['schools_in_region'] for x in results),'station_records':sum(x['stations_records_in_region'] for x in results),'price_points':sum(x['price_points'] for x in results)},ensure_ascii=False))
if __name__=='__main__':main()
