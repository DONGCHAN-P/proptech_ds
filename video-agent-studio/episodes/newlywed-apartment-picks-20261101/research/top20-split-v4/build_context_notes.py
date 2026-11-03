from pathlib import Path
import json,math,sys
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
sys.path.insert(0,str(R/'tools/gis_vendor'))
from pyproj import Transformer
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    reps=read(E/'research/top20-explain-v3/prices/final-api-20261103-v2/representatives.json')['rows'];tr=Transformer.from_crs(4326,5179,always_xy=True)
    rows=[]
    for rep in reps:
        rid=rep['region_id'];c=read(E/'visual/top20-split-v4/atlas-context'/f'{rid}_context.json');centre=tr.transform(float(rep['longitude']),float(rep['latitude']))
        station=[];seen=set()
        for s in sorted(c['stations'],key=lambda x:math.dist(x['xy'],centre)):
            if s['name'] in seen:continue
            seen.add(s['name']);distance=math.dist(s['xy'],centre)
            if distance<=2500:station.append({'name':s['name'],'line':s['line'],'straight_distance_m':round(distance),'source_record_date':s['date']})
            if len(station)==3:break
        school=[]
        for s in sorted(c['schools'],key=lambda x:math.dist(x['xy'],centre)):
            distance=math.dist(s['xy'],centre)
            if distance<=1500:school.append({'name':s['name'],'grade':s['grade'],'straight_distance_m':round(distance),'source_record_date':s['date']})
            if len(school)==4:break
        rows.append({'region_id':rid,'representative':rep['apt_name_raw'],'stations_shown_near_representative':station,'schools_shown_near_representative':school,'usage':'지도 위치 설명에 사용. 학교 배정이나 도보시간·완전한 최인접역 판정은 제공하지 않음. 기관 자료의 표시 대상 안에서의 직선거리.'})
    (D/'context_notes.json').write_text(json.dumps({'regions':rows,'school_source':'한국교육시설안전원 학구도안내서비스 공개 위치자료','station_source':'KRIC 전체 도시철도역사정보20260630; 원자료 일부 누락'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('20 region map-reading notes prepared')
if __name__=='__main__':main()
