from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
PROJECT = Path('C:/projects/realestate_reco')
NOTE = ROOT.parent / 'supply_redevelopment_rental.md'
DATE = '2026-10-23'

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

papers = [
    dict(paper_id='P1', title='지방시도별 민간부문주택인허가물량의 가격탄력성 추정 - 지역별 비교와 내생성 제어를 위한 도구변수 적용 -', authors=['박천규'], year=2023,
         publication='부동산분석 9(3):1-16', doi='10.30902/jrea.2023.9.3.1', url='https://www.ejrea.org/archive/view_article?pid=jrea-9-3-1',
         reading_scope='HTML main text I-IV, notes; tables 1-3 text cells; not PDF page inspection',
         locators=['III.1: actual period 2007.12-2022.12; 12-month moving-average private for-sale permits', 'III.2, table 2: Daegu price coefficient 4.6687, SE 0.3489; Daejeon 2.6439, SE 0.4952', 'IV: limitations and instrument exclusion concerns'],
         short_excerpt='인허가와 준공과의 시차가 큰 특성',
         sample='13 non-capital provinces/metropolitan cities, 181 monthly observations each', method='2SLS; price instruments include Jeonse index and household credit-risk index',
         outcome='12-month moving average of private for-sale housing permits; all housing, not apartment completions',
         limits=['Seoul/Gyeonggi not in sample','IV relevance is not proof of exclusion','smoothed series and monthly interpolation','not net stock elasticity']),
    dict(paper_id='P2', title='재건축사업으로 인한 이주가 주택가격에 미치는 영향: 서울 가락시영아파트 사례', authors=['서문규','정재엽','이효중'], year=2026,
         publication='국토계획 61(4):215-227; 2026-08-31', doi='10.17208/jkpa.2026.08.61.4.215', url='https://www.kpaj.or.kr/_PR/view/?aidx=50743&bidx=4543',
         reading_scope='HTML main text I-V and notes; table captions and narrative explanations; table image cells not inspected',
         locators=['III.1-2: 2012.8-2013.5 relocation; 2011Q1-2014Q4 price panel; 916 destination neighborhoods; 59m2 apartments', 'III.3: log(1+x) for logged variables; 2009Q3-2011Q4 destination shares', 'IV.3, table 5 narrative: positive IV estimates; transmission mechanism not directly tested', 'V: interrupted first relocation and external-validity limits'],
         short_excerpt='구체적인 전달경로 자체를 직접 검증한 것은 아니라는',
         sample='916 actual destination administrative neighborhoods, 2011Q1-2014Q4; exact regression N not transcribed from image table', method='Shift-share 2SLS; pre-relocation shares times quarterly source outflows; district and quarter effects',
         outcome='mean and median 59m2 apartment sale prices and monthly-equivalent rents, including converted Jeonse/semi-Jeonse',
         limits=['Single event','Historical shares may contain persistent destination trends','log(1+x) is not exact raw-variable elasticity at low counts','Rental-to-purchase mediation not identified','table-image SE/N not checked']),
    dict(paper_id='P3', title='정비사업이 인근 지역의 전세 가격에 미치는 영향', authors=['유건호','강명구'], year=2025,
         publication='주택금융연구 9(1):135-157', doi='10.52344/hfr.2025.9.1.135', url='https://researcher.hf.go.kr/researcher/sub04/sub05_3.do?articleNo=592609&attachNo=91197&mode=download',
         reading_scope='Selected original PDF text: printed pp135-137,140-155, relevant methods/results/limitations and tables1-6; not full-issue reading or visual table QA',
         locators=['Printed pp143-146, tables1-4: data and event samples', 'Printed pp147-149: equations and pseudo-repeat units, 337745 pairs, WLS', 'Printed p153, table6: q3,0-1km beta -7.80e-6 SE1.83e-6; q12 beta11.56e-6 SE2.33e-6', 'Printed p155: internal-project samples not excluded; amenity/supply pathways not separated; reverse causality'],
         pdf_page_number_rule='Zero-based PDF page = printed page - 1',
         short_excerpt='정비사업 내부 지역을 제외하지 못했기에',
         sample='Seoul 2017-2023 new Jeonse contracts 859255; pseudo-repeat pairs337745; 192 demolition-proxy approvals and193 completion approvals2015-2023', method='Modified repeat-sales WLS, distance and event-time interactions; project approval proxies',
         outcome='log change in Jeonse deposit per square meter for apartment groups matched by complex, area band and floor band',
         limits=['Matched groups are not the same individual dwelling','Management-disposal approval not actual exit date','Inside redevelopment boundary not removed','Time-varying omitted variables and reverse causality','No separate causal identification of amenities']),
    dict(paper_id='P4', title='한국의 주택건설투자의 결정요인 분석', authors=['오지윤'], year=2018,
         publication='경제분석 24(4):71-100', doi='10.23299/bokeri.2018.24.4.003', url='https://www.bok.or.kr/imer/bbs/P0000556/view.do?menuNo=500783&nttId=10049161&pageIndex=3',
         metadata_url='https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002416667',
         reading_scope='Official BOK author summary and KCI bibliographic record only; PDF fetch via web failed, no full-text claim',
         locators=['BOK official summary, first and second paragraphs; registered2018-12-31', 'Full analysis1988Q1-2017Q3; later subperiod2006Q1-2017Q3 in summary'],
         short_excerpt='후기에는 공급 측 요인',
         sample='Nationwide quarterly1988Q1-2017Q3; exact regression N unverified', method='Instrumental-variable analysis as described in official summary; detailed exclusion restrictions unverified',
         outcome='housing construction investment, not completed apartment unit counts',
         limits=['No separate Seoul/Gyeonggi identification','Full PDF methods/tables not read','Later-period insignificant price response is not proof of zero causal effect']),
    dict(paper_id='P5', title='동태적 패널모형을 활용한 시군구별 미분양률 영향요인 분석: 신규주택 공급 방식의 차별적 영향', authors=['손요엘','이예정','양희진'], year=2025,
         publication='국토계획 60(7):161-172; 2025-12-31', doi='10.17208/jkpa.2025.12.60.7.161', url='https://www.kpaj.or.kr/_PR/view/?aidx=47897&bidx=4316',
         reading_scope='HTML main text I-VI; variable definitions, table3 narrative and limitations; table image cells not inspected',
         locators=['IV.2: 229 municipalities,2015-2023, descriptive N2061', 'IV.2: new-unit share = apartment stock built within5years / total apartment stock', 'V: metropolitan versus non-metropolitan model results; table3 prose', 'VI: omitted time-varying policy effects and long-duration-unsold-market limits'],
         short_excerpt='시계열 변화에 따른 정책적 요인을 반영하지 못하였다',
         sample='229 municipalities2015-2023; descriptive2061 municipality-years; fitted model N not transcribed', method='System GMM using internal lags, Sargan and AR(2) tests',
         outcome='annual-average unsold units divided by multifamily stock, distinct from vacant or unoccupied units',
         limits=['Supply location selection endogenous','Internal-lag instruments depend on moment assumptions','No explicit policy-history controls','Capital-region result not Seoul-vs-Gyeonggi result','Regional price-index levels do not measure cross-city absolute prices']),
    dict(paper_id='P6', title='한국의 신규 주택공급 가격탄력성 변화: 시도별 패널데이터 분석', authors=['이진웅'], year=2024,
         publication='국제경제연구 30(3):1-28', doi='10.17298/kky.2024.30.3.001', url='https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003121629',
         reading_scope='Author abstract, bibliographic metadata and keywords only; DOI full-text link inaccessible via web',
         locators=['Author abstract:2004-2022 province panel;2004-2012 versus2013+ comparison', 'Keywords:system GMM indication; details unverified'],
         short_excerpt='가격탄력성의 시간별 추이',
         sample='Korean province panel2004-2022; exact province coverage and N unverified', method='System-GMM keyword; equation and instrument details unverified',
         outcome='new housing supply elasticity; supply stage unverified from full text',
         limits=['Regulation definitions unverified','Supply stage, SE and exact N unverified','Abstract possibility language not established cause','No abstract coefficients adopted as video values']),
]
for p in papers:
    p['checked_on'] = DATE
    p['as_of'] = DATE
save('sources.json', {'task_id':'RPR-LIT-20261023','papers':papers,'copyright':'Only short excerpts retained; full acquired reading caches are temporary and removed after reading.'})

claims = [
    ('SUP-F01','P1','지방 민간분양 인허가의 가격 반응은 지역별 차이를 보인다는 연구 보고를 확인했다. 서울·경기 탄력성을 추정한 결과는 아니다.'),
    ('SUP-F02','P2','가락시영 재건축 이주의 목적지 임대·매매가격에 양의 IV 결과가 보고되었다. 전세에서 매수로 이동한 경로가 직접 식별된 것은 아니다.'),
    ('SUP-F03','P3','서울 정비사업의 준공 주변 전세 반응은 상대 시점에 따라 부호가 다르게 보고되며, 인과와 내부표본 오염의 한계가 남는다.'),
    ('SUP-F04','P4','한국은행 공식 요약은2006Q1-2017Q3 구간에서 공급 측 요인의 중요성을 보고한다. 원문 표·세부 식별은 확인하지 않았다.'),
    ('SUP-F05','P5','수도권과 비수도권의 미분양 관련 변수가 다르게 나타난다는 연구 보고를 확인했다. 신규주택 비율은 최근5년 신축 재고 비중이다.'),
    ('SUP-F06','P6','저자 초록은 공급탄력성의 시간 변화와 토지 관련 변수의 유의성을 보고한다. 규제 변수·효과크기는 본문 미확인이다.'),
]
facts=[]
by_id={p['paper_id']:p for p in papers}
for cid,pid,sentence in claims:
    p=by_id[pid]
    facts.append(dict(claim_id=cid,sentence=sentence,source_url=p['url'],source_file='sources.json',evidence_location=p['locators'],reference_date=p['sample'],checked_on=DATE,status='qualified',qualification=p['limits'],affected_scene_ids=[],scene_status='not_assigned',original_paper_id=pid))
for i,statement in enumerate([
    '이주 집중과 대체 공급 부족이 함께 있는 생활권에서 준공 전 인근 임대료 압력이 더 크다.',
    '서울·경기 일부 시장의 가격 반응은 총준공보다 순증/재고와 멸실-입주 공백을 넣을 때 더 잘 설명된다.',
    '비수도권 및 경기 외곽 일부 시장에서 미분양 잔고와 코호트 계약소진이 준공 충격의 지속기간을 구분한다.',
],1):
    facts.append(dict(claim_id=f'SUP-C0{i}',sentence=statement,source_url=None,source_file='../supply_redevelopment_rental.md',evidence_location=f'section3,C{i}',reference_date='planned test:2006+ sales; rentals/data-available subperiods',checked_on=DATE,status='unverified',qualification=['Falsifiable candidate; not tested on episode trades','Literature provides mechanism only, not evidence of Seoul/Gyeonggi cause'],affected_scene_ids=[],scene_status='not_assigned'))
save('facts.json', {'task_id':'RPR-LIT-20261023','claims':facts,'price_effect_comparison_rules':{'P1':'permit-quantity elasticity to price index, not realized price level','P2':'59m2 mean/median, sale and monthly-equivalent rent; no exact coefficient promoted','P3':'Jeonse deposit per m2, Seoul new contracts, pseudo-repeat groups, event-specific conditional coefficients; boundaries and dates in sources.json','all':'No original episode price calculation or factual update performed'}})

save('issue_RPR-LIT-SUPPLY-01.json',dict(issue_id='RPR-LIT-SUPPLY-01',task_id='RPR-LIT-20261023',scene_ids=[],problem='공급량과 이주·전세 연구를 서울·경기의 확정 인과로 결합할 근거가 부족하다.',evidence='P1은 서울/경기 미포함, P2는 단일 사건/환산월세, P3는 실제 동일주택이 아니고 구역 내부 표본 잔존, P4/P6는 본문 미확인.',proposal='C1-C3을 검증 후보로 유지하고 이주/입주 날짜·사업 경계·미분양 코호트를 확보한 뒤 인과 표현을 결정한다.',impact='향후 공급·정비사업·전세·미분양 원인 설명 장면',affected_claim_ids=['SUP-C01','SUP-C02','SUP-C03'],affected_scene_ids=[],next_owner='director/research integration',external_message_sent=False))

# Keep a compact provenance record rather than redistributing full articles.
cache_names=['P1_park2023.txt','P2_seomun2026.txt','P5_son2025.txt','P3_hfr2025_issue.pdf']
receipt_path=ROOT/'fetch_receipt.json'
receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
for item in receipt:
    cache=ROOT/item['file'] if 'file' in item else None
    if cache and cache.exists():
        item['sha256']=hashlib.sha256(cache.read_bytes()).hexdigest()
        item['retained']=False
        item['disposition']='Read for research; temporary full-text cache removed; short excerpt and locators retained in sources.json.'
save('fetch_receipt.json',receipt)
for name in cache_names:
    cache=(ROOT/name).resolve()
    if cache.parent!=ROOT.resolve():
        raise RuntimeError('Cache path is outside task asset directory')
    if cache.is_file():
        cache.unlink()

text=NOTE.read_text(encoding='utf-8')
validation={
    'note_exists':NOTE.is_file(),
    'note_nonempty':len(text)>1000,
    'korean_whitespace_word_count':len(text.split()),
    'top_level_question_sections':len(re.findall(r'^## ',text,re.M)),
    'paper_count':len(papers),
    'deep_main_text_read_ids':['P1','P2','P5'],
    'partial_pdf_read_ids':['P3'],
    'abstract_or_official_summary_only_ids':['P4','P6'],
    'candidate_claim_count':sum(c['status']=='unverified' for c in facts),
    'long_article_text_in_deliverable':False,
    'scientific_conclusions_independently_replicated':False,
    'full_pdf_visual_table_qa':False,
    'shared_files_modified':False,
    'transactions_or_collectors_read_or_run':False,
}
assert validation['korean_whitespace_word_count']<=3000,validation
assert validation['top_level_question_sections']==3,validation
for name in ['sources.json','facts.json','issue_RPR-LIT-SUPPLY-01.json','fetch_receipt.json']:
    json.loads((ROOT/name).read_text(encoding='utf-8'))
save('validation.json',validation)

inputs={}
for rel in ['video-agent-studio/WORKFLOW.md','video-agent-studio/agents/video_research.toml','video-agent-studio/episodes/regional-price-recovery-20261022/brief.json','video-agent-studio/episodes/regional-price-recovery-20261022/state.json']:
    inputs[rel]=dict(sha256_at_handoff=hashlib.sha256((PROJECT/rel).read_bytes()).hexdigest())
handoff=dict(task_id='RPR-LIT-20261023',owner='supply literature researcher',as_of=DATE,status='literature_notes_complete_with_documented_evidence_gaps',
             outputs=[str(NOTE),str(ROOT/'sources.json'),str(ROOT/'facts.json'),str(ROOT/'issue_RPR-LIT-SUPPLY-01.json'),str(ROOT/'validation.json')],
             input_versions=inputs,input_scope='Task packet latest literature-only scope supersedes episode production stage; no script or media work',
             read_episode_stage='full_visual_review_ready_voice_deferred',read_episode_state_updated_at='2026-10-23T07:06:57.501195+00:00',
             validation=validation,affected_claim_ids=[c['claim_id'] for c in facts],affected_scene_ids=[],scene_ids_not_assigned=True,
             unresolved=['P4/P6 full texts and P2/P5 image-table cell verification','Actual relocation/occupancy dates, destinations and project boundaries','Historical zoning/FAR/developable-land series and credible exogeneity','Unsold cohort contracts, cancellation/reclassification and absorption speed','No causal decomposition of Seoul/Gyeonggi prices'],
             next_owner='parent director/research integrator, then writer and visual after empirical checks',
             authorizations_respected=['literature research only','no paid generation','no script/render/TTS','no external messages','no collection restart','no shared-state edits'])
save('handoff.json',handoff)
print(json.dumps(validation,ensure_ascii=False,indent=2))
print('note_sha256='+hashlib.sha256(NOTE.read_bytes()).hexdigest())
