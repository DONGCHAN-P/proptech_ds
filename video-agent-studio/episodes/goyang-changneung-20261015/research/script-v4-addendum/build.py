from pathlib import Path
import json, sys, hashlib
P=Path(__file__).parent; E=P.parents[1]
sys.path.insert(0,str(E.parent/'namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps'))
import pymupdf
sources=json.loads((E/'research/production-v2/sources.json').read_text(encoding='utf-8'))['sources']
by={Path(s['file']).name:s for s in sources}
evidence=[]
for name,pages in [('s5_corrected.pdf',[3]),('s4_latest.pdf',[3]),('s1_full.pdf',[4,43])]:
    f=E/'research/production-v2/raw'/name; d=pymupdf.open(f)
    for page in pages:
        t=d[page].get_text(); (P/f'{name[:-4]}_p{page+1}.txt').write_text(t,encoding='utf-8')
        evidence.append({'file':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'pdf_page':page+1,'source_url':by[name]['url']})
facts=[]
def add(cid,text,name,page,date,**kw):
    facts.append({'claim_id':cid,'statement':text,'source_url':by[name]['url'],'source_file':by[name]['file'],'evidence_location':page,'as_of':date,'checked_on':'2026-10-16','status':'verified',**kw})
add('CN4-S5-SUPPLY','S5 공고 공급규모 759세대, 입주예정 2028.01.','s5_corrected.pdf','PDF p4 공급규모·공급대상 표','2025-01-31',units=759,move_in_target='2028-01',development_status='approved_plan')
add('CN4-S1-SUPPLY','S1 공고 공급규모 494세대, 입주예정 2029.05.','s1_full.pdf','PDF p5 공급규모·입주예정 문장','2026-04-30',units=494,move_in_target='2029-05',development_status='approved_plan')
add('CN4-S4-SUPPLY','S4 공고 공급규모 1,024세대, 입주예정 2030.03.','s4_latest.pdf','PDF p4 공급규모·공급대상 표','2026-06-30',units=1024,move_in_target='2030-03',development_status='approved_plan')
add('CN4-S6-EARLIER','같은 S5·S6 정정공고의 S6는 430세대, 2027.12 입주예정이다. S5를 창릉 전체 첫 입주라고 단정할 수 없다.','s5_corrected.pdf','PDF p4 S6 공급규모·공급대상 표','2025-01-31',units=430,move_in_target='2027-12',development_status='approved_plan',affected_claim_ids=['CN2-S5-MOVE'],affected_scene_ids=['M005','M006','M008'])
facts.append({'claim_id':'CN4-S4-ACCESS','statement':'LH는 S3·S4의 원흥지구 인접 및 덕양로 건너 기존 상업시설 이용을 설명한다. 이는 원흥역까지 걸어서 가는 동선이나 분 단위 역 접근시간을 뜻하지 않는다.','source_url':'https://xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?board_seq=466&mCode=MN024&mgr_seq=12&mode=view&page=1','source_file':'research/raw/s3s4_lh_20260703.html','evidence_location':'S3·S4 입지 설명; 기존 CN-S34-LIFE 재사용','as_of':'2026-07-03','checked_on':'2026-10-16','status':'qualified','development_status':'operating'})
facts.append({'claim_id':'CN4-EXISTING-ACCESS','statement':'LX 교통안내는 원흥역 2번출구 95번→도래울마을5·6단지, 3번출구 046·075B·024A·024B→2·3단지, 행신역1번출구024A·024B→5·6단지를 안내한다.','source_url':'https://lx.or.kr/ngyeonggi/sub04.do','evidence_location':'교통안내 버스; 웹 재조회 lines78–82','as_of':'안내 작성일 미표시','checked_on':'2026-10-16','status':'qualified','development_status':'operating','limits':'현재 공개 안내의 기존 생활권 연결이다. 각 단지 출입구 정차·입주시 노선·배차 확정 아님. 10분은 LX 차량 안내여서 버스 소요시간으로 쓰지 않음.'})
out={'revision':'script-v4-addendum','checked_on':'2026-10-16','scope':'기존 원자료 재사용, 3후보 부분합 및 같은 공고의 S6 보조사례. 창릉 전체/주변지역 공급 총조사 아님.','facts':facts,'selected_three_year_table':[{'year':2028,'blocks':['S5'],'units':759},{'year':2029,'blocks':['S1'],'units':494},{'year':2030,'blocks':['S4'],'units':1024}],'selected_three_total':2277,'aggregation':'759+494+1024. 공고상 단지 공급규모를 입주예정연도로 배치한 세 사례 부분합. 확정 실입주량·본청약 신규모집분·지역전체물량 아님.','unverified':['S1/S4/S5 출입구부터 기존 역까지 실제 보행·버스 소요시간','각 단지 입주시 버스노선·배차·정류장 위치','창릉 및 고양 주변 모든 사업지의 연도별 입주물량','공고 이후 입주예정 변경 여부를 모든 블록 전수 확인한 최신 총괄표'],'source_access_notes':['LX와 S5 공고 페이지 웹 재조회 성공','S1/S4 PDF 웹 도구 읽기 실패. 기존 공식 다운로드 원본을 로컬 PDF 재추출·해시 확인하여 사용. 최신 게시본과 동일하다는 새 단정은 하지 않음.'],'evidence':evidence}
(P/'facts_addendum.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('facts',len(facts),'selected_three_total',out['selected_three_total'],'evidence',len(evidence))
