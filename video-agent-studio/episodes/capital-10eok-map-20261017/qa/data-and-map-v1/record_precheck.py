from pathlib import Path
import json,hashlib,statistics
q=Path(__file__).resolve().parent;ep=q.parents[1];root=ep.parents[2];o=ep/'outputs/map-preview-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=read(ep/'research/annual-map-v1/map_packet_v1.json');receipt=read(o/'preview_receipt.json');checks=[]
for fr in receipt['actual_data_frames']:
 y=fr['year'];eligible=[c for c in packet['complexes'] if y>=int(c['first_valid_trade_year'])]
 counts={s:sum(c['years'][str(y)]['status']==s for c in eligible) for s in ['under','over','no_trade']}
 assert counts['under']==fr['drawn']['under']==fr['map_eligible_under']
 assert counts['under']+counts['over']==fr['map_eligible_observed']
 checks.append({'year':y,'map_scope_counts':counts,'all_data_under':fr['source_statistics']['under'],'map_under':counts['under'],'scope_consistent_in_receipt':True})
cfg=read(root/'config/vertical_video_safe_area.json');r=cfg['profiles'][cfg['default_profile']]['critical_rect'];bounds=read(o/'layout_bounds.json');fails=[]
for b in bounds['elements']:
 l,t,rr,bb=b['bbox']
 if not (l>=r['left'] and t>=r['top'] and rr<=r['right'] and bb<=r['bottom']):fails.append(b['name'])
assert not fails
# 수용기준의 경계 예시이며 새 파이프라인 실행 검증을 대신하지 않는다.
fixture=[{'prices_manwon':p,'median':statistics.median(p),'expected':('under' if statistics.median(p)<=100000 else 'over')} for p in [[99999],[100000],[100001],[99999,100001],[100000,100002]]]
audit={'scope':'구 시안 packet의 자체 집합·receipt 및 bbox 대조. 가격 원천 완전성·좌표 정밀도 통과 아님.','packet_sha256':sha(ep/'research/annual-map-v1/map_packet_v1.json'),'counts':checks,'bbox_count':len(bounds['elements']),'bbox_failures':fails,'safe_config_sha256':sha(root/'config/vertical_video_safe_area.json'),'threshold_acceptance_examples':fixture,'full_pipeline_ready':False}
(q/'packet_and_layout_precheck.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
findings=[{'issue_id':f'DM-V1-{i:03}','scene_id':scene,'severity':'required','owner':owner} for i,scene,owner in [(1,'data','data'),(2,'map','research/visual'),(3,'layout','editor')]]
ko=[('원천 잘림·기존 최고가 중복처리 때문에 구 packet은 최종 가격 결론 근거가 아님','266개 월 전체 보완·교체와 새 집계 결과 확인'),('후보 좌표 정밀도·경계 CRS·재사용 권리 검증 미완료','공식 원본·권리·canonical 매칭과 실제 다중 앵커 변환 대조'),('큰 숫자와 지도상 대상 집합의 분모가 다르게 제시됨','지도 eligible 기준으로 주값 통일 또는 전체/지도 범위를 명확히 분리')]
for f,(problem,fix) in zip(findings,ko):
 f.update(timecode='사전검토·시안 00:00/00:02/00:04',문제=problem,수정안=fix,evidence=['독립검토와_v2수용기준.md','packet_and_layout_precheck.json','actual_4.png'],status='open_for_v2',checked_revision='annual-map-v1/style-preview-v1')
(q/'findings.json').write_text(json.dumps({'required_open_count':3,'critical_open_count':0,'full_pipeline_ready':False,'findings':findings},ensure_ascii=False,indent=2),encoding='utf8')
h={'status':'독립 사전검토 완료·최종 통과 보류','next_owner':'director/data/visual','outputs':[str(q/'독립검토와_v2수용기준.md'),str(q/'pilot_independent_recount.json'),str(q/'packet_and_layout_precheck.json'),str(q/'preview_technical.json'),str(q/'findings.json')],'verified_scope':'파일럿 두 지역·월 1123/2049행 독립 재계수, 시안 packet receipt 집합 및36개 bbox대조, 6초 MP4 전체decode와4시점 직접 열람.','pending':'전체 보완·재집계·공식 좌표/CRS/권리·새packet·최종영상 검수','preview_sha256':sha(o/'style_preview_6s.mp4'),'full_price_conclusion_verified':False,'complete_complex_coverage_verified':False,'coordinates_precision_verified':False,'actual_listening':False,'continuous_playback':False,'media_modified':False,'new_paid_calls':0,'external_transmission':False}
(q/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'map_counts':checks,'bbox_failures':fails,'ready':False}))
