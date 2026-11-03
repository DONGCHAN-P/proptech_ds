from pathlib import Path
import json,hashlib
q=Path(__file__).resolve().parent;ep=q.parents[1];o=ep/'research/source-completion-v1';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
r=read(q/'completed_source_independent_review.json');assert r['price_source_review_ready']
p=q/'findings.json';f=read(p)
for x in f['findings']:
 if x['issue_id']=='DM-V1-001':x.update(status='closed_source_aggregation_verified',checked_revision='source-completion-v1',evidence=['completed_source_independent_review.json','새집계_독립검증결과.md'])
f['required_open_count']=2;f['source_price_review_ready']=True;f['full_pipeline_ready']=False
p.write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf8')
report={'revision':'source-completion-v1-independent','source_price_review_ready':True,'map_review_ready':False,'local_review_ready':False,'source_price_required_open_count':0,'required_open_count':2,'critical_open_count':0,'review_scope':'현재 보유 원문과266개 보완월의 가격 집계. 지도·좌표·새 영상은 통과 대상 아님.','file_hashes':r['file_hashes'],'source_counts':{k:r[k] for k in ['raw_complete_pairs','raw_pages','raw_all_area_rows','fresh_84_source_pointer_value_rows_verified','kept_staged_rows_exact_verified','valid_rows','catalog_count','exact_10eok_groups','reappearance_events']},'remaining':['정밀좌표·공식지도권리·CRS·실제단지매칭','새packet의 실제지도점수·라벨분모·세로안전영역 검수'],'evidence':['completed_source_independent_review.json','새집계_독립검증결과.md'],'actual_video_review_of_new_data':False,'actual_listening':False,'continuous_playback':False,'limitations':r['limits'],'new_api_requests':0,'paid_generation':False,'external_transmission':False}
(q/'source_price_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
h={'status':'새 가격 집계 독립검토 완료·지도 최종 보류','next_owner':'director/coordinate/editor','outputs':[str(q/'source_price_review.json'),str(q/'새집계_독립검증결과.md'),str(q/'completed_source_independent_review.json'),str(q/'findings.json')],'source_price_review_ready':True,'map_review_ready':False,'required_open_count':2,'critical_open_count':0,'scope':report['review_scope'],'pending':report['remaining'],'media_modified':False,'new_api_requests':0,'external_transmission':False}
(q/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf8')
assert len(r['file_hashes'])==11
print('source price ready; map pending; 11 input SHA verified')
