import json,pathlib,hashlib
from PIL import Image
V=pathlib.Path(__file__).parent;EP=V.parent;R=EP.parents[2];O=EP/'outputs/production-v1';src=R/'video/src/gyosan-production-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
geo=json.loads((V/'data.json').read_text(encoding='utf8'));reg=json.loads((V/'regional.json').read_text(encoding='utf8'))
guard=json.loads((O/'representative_guard.json').read_text(encoding='utf8'))
assets=[]
for p in sorted((O/'preflight').glob('REP*.png')):
 with Image.open(p) as im: dims=list(im.size)
 assets.append(dict(asset_id=p.stem,scene_ids=[],type='rendered_vector_board',source_or_prompt='LH 실제 기하·공공데이터 및 확인된 원문에 따른 Remotion 화면',dimensions=dims,actual_file=str(p),actual_place='하남 교산 및 인근 생활권',AI=False,usage_conditions='각 원자료 조건·출처 적용, 지도상 계획면은 운영 상태 아님',review_status='layout_guard_pass; 직접 본 프레임 범위는 self_review에 기록',sha256=sha(p)))
for p in sorted((V/'public/chapter-v8').glob('*.png')):
 with Image.open(p) as im:dims=list(im.size)
 assets.append(dict(asset_id='chapter_'+p.stem,scene_ids=[],type='ai_concept',source_or_prompt='기존 승인 창릉 최종 v8-jun 챕터 배경 재사용',dimensions=dims,actual_file=str(p),actual_place=False,AI=True,usage_conditions='AI 개념 이미지 · 실제 교산 모습 아님 표기',review_status='재사용; 신규 생성 없음'))
for p in sorted((V/'public/sources').glob('*.png')):
 with Image.open(p) as im:dims=list(im.size)
 assets.append(dict(asset_id=p.stem,scene_ids=['M004'],type='official_document_page',source_or_prompt='교산 푸르지오 더 퍼스트 A2 2025.04.24 정정 모집공고',dimensions=dims,actual_file=str(p),actual_place='하남 교산 A2',AI=False,usage_conditions='공식 공고 원본 보존 · CSS viewport로 관련 표 구간만 확대',review_status='원본 직접 확인 및 화면 확대 확인' if p.stem in ['a2_p7','a2_p8'] else '파일 존재만 확인; 본문 사용 안 함'))
assets.extend([dict(asset_id='gyosan_geometry',scene_ids=[],type='actual_plan_geometry',source_or_prompt=geo['meta'],dimensions=[1000,1000],actual_file=str(V/'public/gyosan_plan.svg'),actual_place='하남 교산',AI=False,usage_conditions='LH 공개 WFS 조회버전 · 법정 원도/정밀 측량 결과로 소개하지 않음',review_status='105176 / 759features 및 좌표·실제 렌더 확인'),dict(asset_id='regional_geometry',scene_ids=[],type='actual_map',source_or_prompt=reg['meta'],dimensions=[1000,1000],actual_file=str(V/'regional.json'),actual_place='하남·서울동남권',AI=False,usage_conditions='OSM ODbL/©OpenStreetMap contributors · SGIS/MIT · 한국부동산원2025·KRIC20260630',review_status='단지5개 이름·주소·대표좌표 일치 확인, 역점은 출입구 아님')])
(V/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf8')
labels=[('교육시설 (초1)','초등학교 예정 부지'),('교육시설 (중1)','중학교 예정 부지'),('교육시설 (고3)','고등학교 예정 부지'),('공원 (소12)','소공원 예정 부지')]
(V/'label_provenance.json').write_text(json.dumps([dict(source_name=n,display_label=l,xy=next(f['xy'] for f in geo['features'] if f['name']==n),meaning='계획 필지, 개교/개장·배정 확정 아님') for n,l in labels],ensure_ascii=False,indent=2),encoding='utf8')
review=dict(guard_pass=guard['passed'],guard_variants=len(guard['checks']),directly_viewed=['REP1_plan','REP2_jobs','REP3_rail','REP4_life','REP5_comparison','REP6_price','REP7_chapter','final preflight 008_price/014_comparison/012_supply/016_decision'],continuous_video_playback=False,audio_listened=False,known_limits=['고정 카메라, 강조선 5단계 상태의 still_motion','교통 계획역은 공식 연결 개념 재구성, 지리적 핀 아님','가격/날짜/출처는 최종 project props가 기준','A2 원문 p7/p8 화면은 표 일부 CSS viewport, 원본 보존','지도·자막의 전체 최종본 검수는 후속 QA 필요'])
(V/'self_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf8')
receipt=json.loads((O/'render_receipt.json').read_text(encoding='utf8')) if (O/'render_receipt.json').exists() else None
layout=json.loads((O/'layout_guard.json').read_text(encoding='utf8')) if (O/'layout_guard.json').exists() else None
if layout:layout={k:layout[k] for k in ['input_digest','passed','distinct_variants']}
handoff=dict(status='media_ready' if receipt else 'representative_media_ready',outputs=dict(source=str(src),renderer=str(EP/'editor/production-v1/render.cjs'),representatives=str(O/'preflight'),assets=str(V/'assets.json'),public=str(V/'public'),rendered_project=str(O/'rendered_project.json')),input_versions=dict(reference='changneung-production-v8-jun',LH=geo['meta'],atlas_sha256=reg['meta']['atlas_sha256'],source_files={str(p):sha(p) for p in src.glob('*') if p.is_file()}),validation=dict(**review,full_preflight=layout,render_receipt=receipt),affected_scenes=['all modes plan/jobs/rail/price/comparison/life/supply/decision/previous/chapter/placeholder'],unresolved=['최종 MP4 연속 재생·실제 청취는 수행하지 않음','독립 QA 및 MP4 기술검증은 후속 담당','placeholder는 이미지 제공 시만 자료 준비 영역으로 사용'],next_owner='director/editor; then independent QA')
(V/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'guard_pass':guard['passed'],'guard_variants':len(guard['checks']),'assets':len(assets),'handoff':str(V/'handoff.json')},ensure_ascii=False))
