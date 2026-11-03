from pathlib import Path
import json
q=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
r=read(q/'official_coordinate_independent_review.json');assert r['draw_candidates']==8288 and r['excluded']==884 and r['strict_same_input_row_parcel_and_name_errors']==[]
f=read(q/'findings.json')
for x in f['findings']:
 if x['issue_id']=='DM-V1-002':
  x.update(status='source_join_native_points_verified_final_renderer_contract_pending',checked_revision='coordinate-link-v2')
  x['문제']='공식 원문 연결·원투영 대표점은 검증됐으나 실제 renderer가 원투영 직접 계약을 사용하거나 독립변환 검증을 반영했는지 확인 전임'
  x['수정안']='공식ID 조인한 x_5179/y_5179를 동일CRS 배경에 직접 사용하고 actual frame·입력 receipt로 확인. 기존 lonlat 경로 유지 시 독립변환 검증 필요'
  x['evidence']=['공식좌표_독립검토결과.md','official_coordinate_independent_review.json','native_coordinate_audit.json']
f['official_coordinate_source_join_ready']=True;f['native_5179_point_use_ready']=True;f['full_pipeline_ready']=False
(q/'findings.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf8')
h={'status':'가격집계·공식좌표원문연결 검토 완료·최종지도 보류','next_owner':'director/editor','outputs':[str(q/'공식좌표_독립검토결과.md'),str(q/'official_coordinate_independent_review.json'),str(q/'native_coordinate_audit.json'),str(q/'source_price_review.json'),str(q/'findings.json')],'source_price_review_ready':True,'official_coordinate_source_join_ready':True,'native_5179_point_use_ready':True,'lonlat_transform_independently_verified':False,'full_map_review_ready':False,'required_open_count':2,'critical_open_count':0,'scope':'공식ZIP·DBF/SHP 원문 파싱과PNU/정확이름/레코드/공유ID제외·native내부점 검증. 실제새지도프레임은 아직 미검수.','pending':['EPSG5179 직접 입력계약과 배경좌표 일치 또는 독립lonlat변환 검증','새packet 실제draw·숫자분모·세로안전영역 검수'],'limits':r['limitations'],'media_modified':False,'new_api_requests':0,'external_transmission':False,'new_installation':False}
(q/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf8')
print('official source join and native points verified; final map pending')
