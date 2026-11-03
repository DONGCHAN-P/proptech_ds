"""Bounded cached vector-only OSM queries; no map tiles, credentials, or paid APIs."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,time,hashlib,urllib.request,urllib.parse,sys
D=Path(__file__).resolve().parent;R=D.parents[5]
sys.path.insert(0,str(R/'tools/gis_vendor'))
from pyproj import Transformer
RAW=D/'osm';RAW.mkdir(exist_ok=True)
ENDPOINT='https://maps.mail.ru/osm/tools/overpass/api/interpreter'
def main():
    global ENDPOINT
    ap=argparse.ArgumentParser();ap.add_argument('--regions',nargs='+',default=['R20','R02','R01']);ap.add_argument('--get',action='store_true');ap.add_argument('--simple',action='store_true');ap.add_argument('--endpoint',choices=[ENDPOINT,'https://overpass.private.coffee/api/interpreter','https://overpass-api.de/api/interpreter'],default=ENDPOINT);args=ap.parse_args()
    ENDPOINT=args.endpoint
    toLL=Transformer.from_crs(5179,4326,always_xy=True)
    ledger=json.loads((RAW/'ledger.json').read_text(encoding='utf-8')) if (RAW/'ledger.json').exists() else []
    for rid in args.regions:
        target=RAW/f'{rid}.json'
        if target.exists():print(rid+' cached',flush=True);continue
        d=json.loads((D/f'{rid}_context.json').read_text(encoding='utf-8'))
        a,b,c,e=d['bounds_5179'];west,south=toLL.transform(a-500,b-500);east,north=toLL.transform(c+500,e+500)
        bbox=f'{south:.6f},{west:.6f},{north:.6f},{east:.6f}'
        ep=D.parents[2]
        reps=json.loads((ep/'research/top20-explain-v3/prices/final-api-20261103-v2/representatives.json').read_text(encoding='utf-8'))['rows']
        rep=next(r for r in reps if r['region_id']==rid)
        detail_xy=Transformer.from_crs(4326,5179,always_xy=True).transform(float(rep['longitude']),float(rep['latitude']))
        dw,ds=toLL.transform(detail_xy[0]-1600,detail_xy[1]-1300);de,dn=toLL.transform(detail_xy[0]+1600,detail_xy[1]+1300)
        detail=f'{ds:.6f},{dw:.6f},{dn:.6f},{de:.6f}'
        q=f'''[out:json][timeout:40][maxsize:67108864];(
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({bbox});
way["highway"~"^(residential|unclassified|living_street|service)$"]({detail});
way["natural"="water"]({bbox});way["waterway"~"^(river|canal|stream)$"]({bbox});
way["leisure"~"^(park|garden)$"]({bbox});way["landuse"~"^(retail|commercial)$"]({bbox});
nwr["shop"~"^(mall|department_store|supermarket)$"]({bbox});nwr["amenity"="marketplace"]({bbox});
);out tags geom;'''
        if args.simple:
            q=f'''[out:json][timeout:25][maxsize:33554432];(
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({bbox});
way["waterway"~"^(river|canal|stream)$"]({bbox});way["leisure"="park"]({bbox});
node["shop"~"^(mall|department_store|supermarket)$"]({bbox});way["shop"~"^(mall|department_store|supermarket)$"]({bbox});
node["amenity"="marketplace"]({bbox});way["amenity"="marketplace"]({bbox});
);out tags geom;'''
        (RAW/f'{rid}.overpassql').write_text(q,encoding='utf-8')
        start=time.monotonic();record={'region_id':rid,'endpoint':ENDPOINT,'query_sha256':hashlib.sha256(q.encode()).hexdigest(),'requested_at':datetime.now(timezone.utc).isoformat(),'bbox':[south,west,north,east],'paid':False,'retry_count':0}
        try:
            encoded=urllib.parse.urlencode({'data':q})
            req=urllib.request.Request(ENDPOINT+('?' + encoded if args.get else ''),data=None if args.get else encoded.encode(),headers={'User-Agent':'JipgorithmVideoResearch/1.0 (offline vector maps; limited20districtqueries)','Content-Type':'application/x-www-form-urlencoded'})
            record['method']='GET' if args.get else 'POST'
            with urllib.request.urlopen(req,timeout=60) as response:raw=response.read(40*1024*1024+1)
            assert len(raw)<=40*1024*1024,'Unexpected oversized response'
            result=json.loads(raw)
            if result.get('remark'):raise RuntimeError(result['remark'])
            assert isinstance(result.get('elements'),list)
            target.write_bytes(raw);record.update(status='ok',bytes=len(raw),elements=len(result['elements']),response_sha256=hashlib.sha256(raw).hexdigest(),osm_base=result.get('osm3s',{}).get('timestamp_osm_base'))
            print(json.dumps({k:record[k] for k in ['region_id','status','elements','bytes']},ensure_ascii=False),flush=True)
        except Exception as error:
            record.update(status='failed',error_type=type(error).__name__,error=str(error)[:300])
            if hasattr(error,'read'):
                record['public_error_body']=error.read(1200).decode('utf-8',errors='replace')
            print(json.dumps(record,ensure_ascii=False),flush=True)
        record['elapsed_s']=time.monotonic()-start;ledger.append(record)
        (RAW/'ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        time.sleep(1.1)
if __name__=='__main__':main()
