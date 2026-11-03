import pathlib,json,re,sys,xml.etree.ElementTree as ET,statistics,hashlib
p=pathlib.Path(__file__).parent;ep=p.parent.parent;repo=ep.parents[2]
def save(n,v):(p/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
analysis=json.loads((ep/'research/map-led-v5/analysis.json').read_text(encoding='utf-8'));by={b['candidate_id']:b for b in analysis['blocks']};dl=json.loads((ep/'research/map-led-v5/pdf_downloads.json').read_text(encoding='utf-8'));urls={z['file']:z['url']for z in dl}
rawcheck=[]
for name in ['다산롯데캐슬','별내푸르지오','별내자이더스타']:
 rows=[];files=[]
 for month in ['07','08','09']:
  f=repo/f'raw/rtms_trade/2026/{month}/41360_2026{month}.xml';files.append(dict(path=str(f.relative_to(repo)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
  for z in ET.parse(f).findall('.//item'):
   t=lambda k:(z.findtext(k)or'').strip()
   if t('aptNm')!=name:continue
   if t('cdealDay')or t('cdealType')in['O','Y']:continue
   if not(83<=float(t('excluUseAr'))<85 and int(t('floor'))>=5):continue
   rows.append(dict(price_manwon=int(t('dealAmount').replace(',','')),area_m2=float(t('excluUseAr')),floor=int(t('floor')),date=f"{int(t('dealYear')):04d}-{int(t('dealMonth')):02d}-{int(t('dealDay')):02d}"))
  
 rawcheck.append(dict(name=name,n=len(rows),median_manwon=statistics.median([r['price_manwon']for r in rows]),files=files,rows=rows))
save('raw_xml_independent_recheck.json',dict(checked_on='2026-10-15',groups=rawcheck,filter='same original XML;83<=area<85,floor>=5,cdealDayblank,cdealType notO/Y',fresh_api=False))
rows=[]
for cid in ['W1-A1','W1-B17','W2-A1','W2-A3']:
 b=by[cid];name=cid.lower().replace('-','_')+'_notice.pdf';text=(ep/'research/map-led-v5'/name.replace('.pdf','.txt')).read_text(encoding='utf-8');residence=5 if cid=='W2-A1'else 3 if cid=='W2-A3'else None
 e=dict(id=cid,region='왕숙1 북부'if cid=='W1-A1'else'왕숙1 남부'if cid=='W1-B17'else'왕숙2',program=b['housing_program'],exclusion_result='not_newlywed_or_public_rental; ordinary public sale',households=b['households_total'],types=b['size_classes'],move_in_target=b['move_in_target'],restrictions=dict(resale_years=3,start_basis='당첨자발표일',residence_years=residence,residence_status='공고상 의무기간 명시'if residence else'공고 제한표와 전체텍스트에 별도 거주의무 표기 없음; 면제 일반법률추론과 구분',resale_registration_exception='전매제한 기간 내 소유권이전등기 완료 시 기간 경과 간주 조항 공고에 명시',current_trade_status='접수종료·전매제한등존재; 현재자유전매가능으로표현금지',general_market_timing='전매제한 해제·거주의무 해당시 충족·부기등기말소 등 실제 양도조건 충족 후; 달력상 일괄확정일 아님'),school=b['school'],school_gap=b['school_gap'],strength=b['strength'],tradeoff=b['tradeoff'],source_file='research/map-led-v5/'+name,source_url=urls[name],source_date=b['publication_date'],checked_on='2026-10-15',source_pages=dict(restrictions=2 if cid.startswith('W2')else 3,schools=b['school_page'],environment=b['environment_page']),conditional_role='북부59㎡일반형보완후보;84㎡대장비교대상은아님'if cid=='W1-A1'else'입지·시점·양도조건충족후일반매매시장을가정한조건부후보')
 if cid=='W1-B17':e['price_example']=b['comparable_84_example']
 if cid=='W2-A1':e['price_example']=dict(type='84A',area_m2=84.67,floor='5층이상',price_won=693630000,source_page=6,basis='기본형;확장옵션세금별도')
 if cid=='W2-A3':e['price_example']=dict(type='84A1',area_m2=84.75,floor='5층~최상층',price_won=732450000,source_page=6,basis='기본형;확장옵션세금별도')
 rows.append(e)
north_url='https://www.prugio.com/hb/2025/wangsuk/assets/pdf/%EC%9E%85%EC%A3%BC%EC%9E%90%EB%AA%A8%EC%A7%91%EA%B3%B5%EA%B3%A0%EC%A0%84%EB%AC%B8.pdf'
for id,h,move,price in [('W1-B1',560,'2028-05',600666000),('W1-B2',587,'2028-06',584623000)]:
 rows.append(dict(id=id,region='왕숙1 북부',brand='왕숙 푸르지오 더 퍼스트 '+('1단지'if id.endswith('1')else'2단지'),program='민간참여 공공분양',households=h,types=['74㎡','84㎡'],move_in_target=move,price_example=dict(type='84A',area_m2=84.92,floor='5층이상',price_won=price,balcony_extension_won=8455000,source_page=6,extension_page=8,basis='기본형;확장·옵션·세금별도'),restrictions=dict(resale_years=3,start_basis='당첨자발표일',residence_years=3,residence_rule='최초입주가능일부터3년이내입주후3년연속거주',current_trade_status='접수종료; 현재 자유매매/즉시 전매 가능 아님',general_market_timing='전매·거주조건 실제충족과양도관련등기확인후;2028입주가정즉시3년거주시에도2031년경이후조건부이지확정거래개시일아님'),schools=dict(kindergarten='왕숙1유',elementary='왕숙1초',middle='왕숙2중',target='2028-03',qualification='관할교육청학생배치·설립계획변경가능, 실제개교·횡단동선별도확인'),school_gap='공고목표상 학교가 입주보다2~3개월앞섬',strength='74/84㎡ 일반형·브랜드·2개블록1147세대규모·북부학교/공원계획을함께검토가능',tradeoff='왕숙1남부GTXB왕숙역직접역세권으로오인금지;9호선등계획교통을현재교통처럼계산금지;3년거주의무;B1/B2단독우위미확인',conditional_role='북부일반형공동주목후보; 동별학교·공원·정류장동선검증전단독대장선정유보',source_url=north_url,lh_listing_url='https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?panId=0000060927&ccrCnntSysDsCd=02&mi=1027',source_file='research/region-leaders-v14/north_b1b2_notice.pdf',source_date='2025-07-29',source_pages=dict(supply=1,restriction_table=3,price=6,extension=8,school=43),checked_on='2026-10-15',amendment_status='공식시행사현재다운로드PDF확인;LH페이지JS정정버튼템플릿존재만으로실정정발생을단정안함;추가정정내용미확정'))
for r in rows:
 if r['id']in['W1-B1','W1-B2']:
  r['verified_spatial_relation']='공고 본단지서측:녹지·공원·초등학교초1·유치원유1·고등학교고1용지계획;학교가기존운영중이거나안전보행직결된다는뜻아님'
  r['source_pages']['environment']=42;r['source_pages']['move_in_explicit_note']=40
save('candidates.json',dict(revision='region-leaders-v14',candidates=rows,excluded=['W1-A2/W1-A24 신혼희망타운','공공임대·수익공유특수상품','공급유형미확정토지계획도블록'],selection=dict(north='B1/B2 공동 주목 후보;1위 단독결정 유보',south='B17:74/84일반형+남부계획역/산업기능,학교개교시차·계획교통리스크함께',w2='A3 중심성·일패계획방향 vs A1 가격/학교/빠른입주;A1거주의무5년/A3 3년차이',meaning='미래가격/상승률예측또는현재즉시매매가능단지추천아님'),law_source='https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=02&joNo=0057&lsiSeq=289171&urlMode=lsScJoRltInfoR',legal_qualification='각공고조건을설명한연구자료;실제양도시점은향후법령/개별충족/등기를확인'))
save('locator_transform.json',dict(coordinates='official A1 pamphlet p5 PDF source-native points; not GIS',whole_viewBox_pdf=[790,119,370,710],north=dict(dimensions=[1280,1981],pdf_clip=[930,120,1085,360],x_formula='930+x*155/1280',y_formula='120+y*240/1981'),south=dict(dimensions=[1654,1504],pdf_clip=[830,500,1160,800],x_formula='830+x*330/1654',y_formula='500+y*300/1504'),policy='same exactsourcePDFcoordinates can union owngeometry; intermediateuntracedarea mustnot inventparcels; original copyright plan not implicitly derivative-licensed'))
facts=[]
for r in rows:facts.append(dict(claim_id='V14-'+r['id'],sentence=r['region']+' '+r['id']+'은 '+r['program']+'이며 공고상 전매3년'+('·거주'+str(r['restrictions']['residence_years'])+'년'if r['restrictions']['residence_years']else'으로 제한표에 별도 거주의무는 표기되지 않았다')+'이다.',source_url=r['source_url'],source_file=r['source_file'],evidence_location=r['source_pages'],reference_date=r['source_date'],verified_on='2026-10-15',status='qualified'))
facts.append(dict(claim_id='V14-NORTH-SPATIAL',sentence='B1/B2공고는본단지서측에녹지·공원·초1·유1·고1용지계획을명시한다.',source_url=north_url,source_file='research/region-leaders-v14/north_b1b2_notice.pdf',evidence_location='p42사업지및단지주변현황;p43학교설립표',reference_date='2025-07-29',verified_on='2026-10-15',status='qualified'))
for g in rawcheck:facts.append(dict(claim_id='V14-PRICE-'+g['name'],sentence=g['name']+'의조건일치보존XML표본중위는'+str(g['median_manwon']/10000)+'억원(n='+str(g['n'])+')이다.',source_url='https://rt.molit.go.kr/',evidence_location='raw_xml_independent_recheck.json original3XMLrows/hash',reference_date='2026-07~09;collected2026-10-13',verified_on='2026-10-15',status='qualified',statistic='median',scope=g['name'],area_filter='83<=area<85',floor='>=5',sample_count=g['n'],transaction_type='매매',unit='억원',cancellation='수집XML취소표시제외;이후갱신미확인'))
save('facts.json',dict(claims=facts))
save('handoff.json',dict(status='ready',outputs=['price_map.json','price_rows_rechecked.json','raw_xml_independent_recheck.json','candidates.json','restriction_source_excerpts.json','locator_transform.json','facts.json','north_b1b2_notice.pdf','north_b1b2_notice.txt','downloads.json'],validation=['3원본MLIT XML독립재집계→11/16/22와10.95/6.775/11.85재현','3실단지OSMpolygon과MLIT주소매칭','북부B1/B2공식53p공고확보및공급/가격/확장/학교/제한직접텍스트확인','현전매가능/미래일반매매대상구분','W1source-native두판동일PDF변환인계'],unresolved=['B1/B2개별우위유보','정정공고추가내용최종계약전확인필요','현재최신API취소갱신미조회','임의자유매매개시일계산금지'],next_assignees=['/root/map_led_narration_v2','/root/rail_route_editor','/root/fact_review','/root']))
print('ready',len(rows),'candidates; raw XML stats',[(g['name'],g['n'],g['median_manwon'])for g in rawcheck])

