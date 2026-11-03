from pathlib import Path
import json,sys,hashlib,re
P=Path(__file__).parent;R=P/'raw';sys.path.insert(0,str(P.parents[2]/'namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps'));import pymupdf
def w(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=json.loads((P/'download_manifest.json').read_text(encoding='utf-8'));src=[]
for j,x in enumerate(manifest):
 if x['status']=='downloaded':src.append({'source_id':'PV2-S'+str(j+1).zfill(2),**x,'rights':'연구용 원문 보존·사실추출. 상업 영상 원도면/이미지 재사용 허락은 미확인','published_on':None,'as_of':'문서내 공고일/개별 주장 참조'})
w('sources.json',{'checked_on':'2026-10-16','sources':src,'baseline':'../sources.json','note':'S1 s1_notice.pdf는 축약1p, s1_full.pdf가 공식홈페이지 원본52p. 혼동금지'})
by={Path(x['file']).name:x for x in src};facts=[]
def add(i,s,file,page,status='verified',asof=None,**kw):
 x=by[file];facts.append({'claim_id':i,'statement':s,'source_id':x['source_id'],'source_url':x['url'],'local_path':x['file'],'evidence_location':page,'published_on':asof,'as_of':asof,'checked_on':'2026-10-16','status':status,'use':'대본·비교·지도 근거','rights':x['rights'],**kw})
def price(scope,area,money,ext,date):return {'statistic':'특정 타입·층구간 공고기본가격','scope':scope,'exclusive_area_sqm':area,'floor':'5층~최상층/5층이상','amount_krw':money,'balcony_extension_krw':ext,'basic_plus_balcony_krw':money+ext,'unit':'원','period':date,'transaction_type':'일반공공분양 최초공급, 실거래아님','sample_size':None,'aggregation':'단일타입 층구간 공고금액; 확장포함합계는 두공고항목 단순합','cancelled_transactions':'해당없음','excluded':['유상옵션','취득세·인지세등'],'comparison_caution':'분양연도·면적·입주월다름. 기존단지실거래와총자금조건차이표시'}
add('CN2-S5-CORRECTION','S5 정정공고는 공급규모10개동을13개동으로 고치고 마이너스옵션 욕실 비데 설명을 수정했다.','s5_corrected.html','공고내용 정정사항',asof='2025-01-31')
add('CN2-S5-PRICE','정정PDF의 S5 84A84.64㎡ 5층~최상층 기본형은7억6,998만원, 발코니확장은661만8천원이다. 합계7억7,659만8천원이며 옵션·세금 별도다.','s5_corrected.pdf','p4면적,p5기본가격,p8발코니',asof='2025-01-31',price=price('S5 84A',84.64,769980000,6618000,'2025-01-31'))
add('CN2-S5-SCHOOL','정정PDF 학교표는 가칭5유·5초2028.03목표,3중·2고미정이다. 최신교육청 개교확정과 동일하지 않다.','s5_corrected.pdf','p45 학교표','qualified',asof='2025-01-31',target_date='2028-03',development_status='approved_plan')
add('CN2-S5-MOVE','S5 정정공고 안내 입주예정은2028.01이며 접수마감이다.','s5_corrected.html','공고상태·공급정보',asof='2025-01-31',target_date='2028-01',development_status='construction')
add('CN2-S4-TYPE','S4 최신정정PDF는 일반공공분양1024호, 전매제한은당첨자발표일부터3년, 거주의무는거주의무개시일부터3년이다.','s4_latest.pdf','p2규제표,p4공급내역',asof='2026-06-30',candidate_general_market=True,caution='개별예외와법령변경은별도.입주월에3년더해자유매매연도만들지않음')
add('CN2-S4-PRICE','S4 정정공고84AH84.90㎡5층~최상층 기본형8억6,719만원, 확장613만9천원으로 합계8억7,332만9천원이다.','s4_latest.pdf','p4면적,p6공급가격,p7발코니',asof='2026-06-30',price=price('S4 84AH',84.90,867190000,6139000,'2026-06-30'),visual_evidence='raw/s4_price_p6.png 실제열람')
add('CN2-S4-MOVE','S4 입주예정은2030.03이며 공정에따라변경가능하다.','s4_latest.pdf','p4 공급규모',asof='2026-06-30',target_date='2030-03',development_status='construction')
add('CN2-S4-SCHOOL','S4 최신정정공고학교표는가칭6유·6초2030.03을안내하나설립/개교시기변경가능조건이있다.','s4_latest.pdf','p47 학교개교시기','qualified',asof='2026-06-30',target_date='2030-03',development_status='approved_plan')
add('CN2-S1-TYPE','S1 우미린그레니티는LH·민간공동시행 민간참여공공분양494호, 전매제한3년이다.','s1_full.pdf','p1공급개요·p4~5 사업설명',asof='2026-04-30',candidate_general_market=True,caution='거주의무는이번텍스트에서명확한기간근거미확보.없음으로단정금지')
add('CN2-S1-PRICE','S1 84A84.99㎡5층이상 기본가7억8,340만원,확장698만원으로합계7억9,038만원이다.','s1_full.pdf','p4면적,p6기본가격,p7확장',asof='2026-04-30',price=price('S1 84A',84.99,783400000,6980000,'2026-04-30'),visual_evidence='raw/s1_price_p6.png 실제열람')
add('CN2-S1-MOVE','S1입주예정은2029.05이며공정에따라변경가능하다.','s1_full.pdf','p4 입주예정시기',asof='2026-04-30',target_date='2029-05',development_status='construction')
add('CN2-S1-SCHOOL','S1남측에학교·유치원용지가계획돼있으나가칭7유·7초개교시기는미정이다.','s1_full.pdf','p43 학교/인접시설','qualified',asof='2026-04-30',target_date=None,development_status='approved_plan')
add('CN2-S1-SURROUNDINGS','S1공고는동측녹지·하천·단독주택,남측공원·학교·유치원용지,서측녹지·공동주택,북측공동주택등을안내한다.','s1_full.pdf','p43 인접시설','qualified',asof='2026-04-30',caution='계획변경가능/상업시설개점일·실제보행경로확정아님')
add('CN2-JOBS-RELOCATION','LH는창릉지구내공장제조·물류유통등약300여기업이전을위한기업이전단지조성을계획한다고발표했다. 기업이전기반마련은현재모든사업장입주완료가아니다.','jobs_lh.html','기업이전단지보도 본문','qualified',asof='2024',development_status='approved_plan',caution='신규대기업300개유치·고용확정·현행기업리스트로전환금지')
w('facts.json',{'revision':'production-v2','checked_on':'2026-10-16','facts':facts,'baseline_reuse':'research-v1 중철도최신LH2026.09.30/상품S3구분유지,새확정아님','gaps':['최신지구계획변경고시정본','예정역중심/출입구정밀좌표','원도면상업영상이용조건','S1거주의무명시근거','학교최신교육청확정']})
blocks=[{'block_id':'changneung-S1','region':'서측분리권역','housing':'민간참여일반공공분양','candidate':'조건부권역후보','strengths':['84기본+확장약7.904억 공고근거','2029.05입주예정','남측공원·초교·유치원계획'],'weaknesses':['가칭7초·7유개교미정','신규철도입주전확정이용아님','기존학교배치/통근확인필요'],'claims':['CN2-S1-PRICE','CN2-S1-MOVE','CN2-S1-SCHOOL','CN2-S1-SURROUNDINGS']},{'block_id':'changneung-S5','region':'중앙서측첫입주권역','housing':'일반공공분양','candidate':'조건부권역후보','strengths':['2028.01이른입주예정','84기본+확장약7.766억 공고근거'],'weaknesses':['GTX2030/은평선2031.12와시차','학교2028.03원공고목표재확인','상가공원입주후일부설치가능'],'claims':['CN2-S5-PRICE','CN2-S5-MOVE','CN2-S5-SCHOOL']},{'block_id':'changneung-S4','region':'원흥기존생활권접점/서측','housing':'일반공공분양','candidate':'조건부권역후보','strengths':['원흥기존생활시설접점은v1 LH근거','학교목표2030.03과입주예정월동일'],'weaknesses':['84기본+확장약8.733억으로다른후보와예산차','학교목표확정아님','입주2030.03에도은평선개통전'],'claims':['CN2-S4-PRICE','CN2-S4-MOVE','CN2-S4-SCHOOL','CN2-S4-TYPE']},{'block_id':'changneung-S3','candidate':'일반매매후보제외','housing':'이익공유형','claims':['v1:CN-S3-TYPE']}]
w('landuse_blocks.json',{'blocks':blocks,'geometry':'공식원도면상의상대위치만.정밀폴리곤없음','baseline_map':'../raw/s5_landuse_20250131.jpg','rights':'상업영상원본전체표시도자동승인아님.이용허락명시근거미확보','render_policy':'자료권리확인전은별도자체관계도설계;원도면모사·트레이싱자유이용으로간주금지.계획역은근거있는예상영역만','ranking':'수익/가격순위아님.권역별조건비교'})
events=[('S5입주','2028-01','CN2-S5-MOVE'),('S5인근5유·5초','2028-03','CN2-S5-SCHOOL'),('S1입주','2029-05','CN2-S1-MOVE'),('S4입주','2030-03','CN2-S4-MOVE'),('S4인근6유·6초','2030-03','CN2-S4-SCHOOL'),('GTX-A창릉역','2030','v1:CN-RAIL-GTX'),('고양은평선착공','2027-01','v1:CN-RAIL-GE'),('고양은평선개통','2031-12','v1:CN-RAIL-GE'),('S1인근7유·7초',None,'CN2-S1-SCHOOL')]
w('calendar.json',{'events':[{'name':a,'date':b,'claim_id':c,'certainty':'예정/목표.공고시점계획이며보장아님','checked_on':'2026-10-16'}for a,b,c in events],'rail_reuse':'v1공식LH2026.09.30확인자료.새개통상태단정아님','do_not':'입주일과철도/개교일한날짜로통합금지'})
print('sources',len(src),'claims',len(facts),'blocks',len(blocks))
