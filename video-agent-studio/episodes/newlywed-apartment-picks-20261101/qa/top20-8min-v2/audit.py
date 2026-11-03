"""지정된 자료 준비 QA. 입력은 읽기 전용, 출력은 이 스크립트 폴더에 한정."""
from pathlib import Path
import collections, csv, gzip, hashlib, json, math, re, statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent
EP = OUT.parent.parent
ROOT = EP.parents[2]
REV = 'top20-8min-v2'
NOW = datetime.now(timezone(timedelta(hours=9))).isoformat()
manifest = {}

def digest(data): return hashlib.sha256(data).hexdigest()
def read_bytes(p, scope='검수 입력'):
    p = Path(p).resolve()
    data = p.read_bytes()
    manifest[str(p)] = dict(path=str(p), sha256=digest(data), size_bytes=len(data), scope=scope)
    return data
def read_json(p, scope='필요 필드만 사용'): return json.loads(read_bytes(p, scope).decode('utf-8-sig'))
def emit(name, data):
    p = OUT / name
    assert p.parent == OUT
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def val(v): return v.get('value') if isinstance(v, dict) else v
def norm(s): return ''.join(s.split())
def pts(x):
    if isinstance(x[0], (int, float)): yield x
    else:
        for child in x: yield from pts(child)
def merc(lon, lat):
    return math.radians(lon)*6378137, math.log(math.tan(math.pi/4+math.radians(lat)/2))*6378137

top = read_json(EP / 'research' / REV / 'top20.json')
prior = read_json(EP / 'qa/ranking_source_review.json', '기존 통과 판정·해시·범위 재사용')
rank_path = ROOT / 'analysis/newlywed_region_2024/rankings.json'
upstream = read_json(rank_path, '기존 승인 SHA 확인 및 TOP20 추출 연결만; 원표 재검수 없음')
expected_sha = prior['checked_revision']['rankings_sha256']
reuse = dict(prior_review_path=str(EP/'qa/ranking_source_review.json'),
             prior_review_sha256=manifest[str((EP/'qa/ranking_source_review.json').resolve())]['sha256'],
             expected_rankings_sha256=expected_sha,
             actual_rankings_sha256=manifest[str(rank_path.resolve())]['sha256'],
             top20_declared_upstream_sha256=top['source_sha256'],
             same_statistics_and_thresholds=True,
             same_validator='기존 ranking-source-review-v1 그대로 재사용; 이번 원표 검증기 재실행 없음',
             scope='2024 통계구역 신혼부부 전체 수 순위 및 동일 입력의 초혼·재혼 표시값',
             source_retranscription_performed=False)
reuse['hash_chain_match'] = reuse['actual_rankings_sha256'] == expected_sha == top['source_sha256']
fields = ['rank','province','region','newlywed_couples','first_marriage_couples','remarried_couples','pdf_page','reference_date','source_url']
reuse['top20_projection_20_rows_equal'] = all(all(a[k] == b[k] for k in fields) for a,b in zip(top['regions'],upstream['capital_gu_ranking'][:20])) and len(top['regions']) == 20
reuse['prior_scope_pass'] = all(prior['verdict'][k] == 'pass' for k in ['source_transcription','rankings','scope_and_deduplication'])
assert reuse['hash_chain_match'] and reuse['top20_projection_20_rows_equal'] and reuse['prior_scope_pass']

# 공식 웹 PDF를 직접 읽어 별도로 전사한 전체 열. 연구 보고서 값으로 채우지 않음.
official = {
 'R01':(15941,32,1425), 'R02':(12490,32,1434), 'R03':(12190,33,1471),
 'R04':(11527,32,1426), 'R05':(9901,32,1423), 'R06':(8523,32,1433),
 'R07':(9688,32,1435), 'R08':(9014,32,1429), 'R09':(8515,33,1459),
 'R10':(8063,32,1426), 'R11':(8804,32,1421), 'R12':(8603,32,1453),
 'R13':(8792,32,1451), 'R14':(8664,32,1422), 'R15':(8523,32,1427),
 'R16':(8595,32,1422), 'R17':(7797,32,1421), 'R18':(7797,33,1476),
 'R19':(7998,32,1417), 'R20':(None,33,1464)}
PDFURL = 'https://sri.kostat.go.kr/boardDownload.es?bid=11815&list_no=434122&seq=3'
facts = {}
for fn in ['ranks01_10_facts.json','ranks11_20_facts.json']:
    p = EP/'research'/REV/fn
    d = read_json(p, 'region_id・province・region・count2023/2024・comparison・원미 행정근거만')
    assert d['input']['sha256'] == manifest[str((EP/'research'/REV/'top20.json').resolve())]['sha256']
    for r in d['regions']: facts[r['region_id']] = (r, str(p), manifest[str(p.resolve())]['sha256'])
rows = []
for t in top['regions']:
    rid = t['region_id']; r,fp,fsha = facts[rid]; n,page,line = official[rid]; c = r['comparison']
    delta = t['newlywed_couples']-n if n is not None else None
    rate = delta/n*100 if n is not None else None
    display = round(rate,1) if rate is not None else None
    gotdelta = c.get('change_couples',c.get('delta_couples'))
    gotrate = c.get('change_percent',c.get('change_rate_pct'))
    gotdisplay = c.get('change_percent_display',c.get('display_rate_pct'))
    checks = dict(region_key=(r['province'],norm(r.get('region',r.get('region_2024'))))==(t['province'],norm(t['region'])),
                  count2023=val(r['count2023'])==n, count2024=val(r['count2024'])==t['newlywed_couples'],
                  comparison_input2023=c['count2023']==n, comparison_input2024=c['count2024']==t['newlywed_couples'],
                  delta=gotdelta==delta, rate=(gotrate is None if rate is None else abs(gotrate-rate)<=0.00000051), display=gotdisplay==display)
    rows.append(dict(region_id=rid,scene_id=t['scene_id'],province=t['province'],region=t['region'],rank=t['rank'],
                     official_count2023=n, research_count2023=val(r['count2023']), reused_count2024=t['newlywed_couples'],
                     recomputed_delta=delta,recomputed_rate_pct=rate,recomputed_display_pct=display,
                     research_delta=gotdelta,research_rate_pct=gotrate,research_display_pct=gotdisplay,
                     formula='(2024-2023)/2023*100' if n is not None else None,
                     pdf_page=page,printed_page=page-7,web_line=line,source_url=PDFURL,
                     source_column='전체',source_context=t['province']+' / '+t['region'],
                     comparison_status='공표 정수 기준 비교' if n is not None else '행정구역·공표범위 차이로 비교 불가',
                     research_file=fp,research_sha256=fsha,checks=checks,pass_all=all(checks.values())))
assert len(rows)==20 and all(r['pass_all'] for r in rows)
emit('row_comparison_ledger.json', rows)
with (OUT/'row_comparison_ledger.csv').open('w',encoding='utf-8-sig',newline='') as f:
    cols=['region_id','scene_id','rank','province','region','official_count2023','reused_count2024','recomputed_delta','recomputed_rate_pct','recomputed_display_pct','pdf_page','printed_page','web_line','pass_all']
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)

src = EP/'research'/REV/'source'
sm = read_json(src/'source_manifest.json')
raw = gzip.decompress(read_bytes(src/'HangJeongDong_ver20241001.geojson.gz','2024-10-01 원도 경계・실제 지역 조인 독립 검수'))
features = json.loads(raw)['features']
license_data = read_bytes(src/'LICENSE-DATA.txt','데이터 권리 원문 보존 및 실제 열람').decode('utf-8-sig')
local_pdf = read_bytes(src/'newlyweds_2023.pdf','보존 파일 해시 확인; 로컬 화상·텍스트 추출 도구 없음')
source_integrity = dict(raw_geometry_sha256=digest(raw),
 raw_geometry_git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
 license_sha256=digest((src/'LICENSE-DATA.txt').read_bytes()),pdf2023_sha256=digest(local_pdf))
source_integrity['matches_manifest'] = (source_integrity['raw_geometry_sha256']==sm['sources']['geometry']['sha256'] and
 source_integrity['raw_geometry_git_blob_sha1']==sm['boundary_git_blob_sha1'] and source_integrity['license_sha256']==sm['sources']['license']['sha256'] and source_integrity['pdf2023_sha256']==sm['sources']['newlyweds_2023']['sha256'])
assert source_integrity['matches_manifest']
assert all(s in license_data for s in ['CC-BY-4.0','SGIS','공공누리 제1유형','MIT'])
ma = read_json(EP/'visual'/REV/'maps/map_assets.json')
province_map={'서울':('11','서울특별시'),'인천':('28','인천광역시'),'경기':('41','경기도')}
maps=[]; point_pairs=[]; map_contexts=[]
for a,t in zip(ma['assets'],top['regions']):
    rid=t['region_id']; sidocode,sidonm=province_map[t['province']]
    target=[f for f in features if f['properties']['sido']==sidocode and f['properties']['sidonm']==sidonm and norm(f['properties']['sggnm'])==norm(t['region'])]
    codes=sorted({f['properties']['sgg'] for f in target})
    g=json.loads(gzip.decompress(read_bytes(EP/a['geometry_file'],'지역별 경계 전체를 원도와 독립 대조')))
    svg_data=read_bytes(EP/a['vector_file'],'SVG 강조 윤곽을 원도 좌표와 대조')
    svg=ET.fromstring(svg_data)
    paths=[e for e in svg.iter() if e.tag.endswith('}path')]
    hi=[e for e in paths if e.attrib.get('fill')!='#dde2e3']
    xy=[tuple(map(float,p)) for e in hi for p in re.findall(r'[ML]([\d.-]+),([\d.-]+)',e.attrib['d'])]
    ll=[p for f in target for p in pts(f['geometry']['coordinates'])]
    assert len(xy)==len(ll)
    pairs=[(merc(*p),q) for p,q in zip(ll,xy)];point_pairs+=pairs
    png=EP/a['actual_file'];read_bytes(png,'전체20 PNG 해시・치수・강조 영역 자동 검사; 육안 원본은 R01/R20만')
    im=Image.open(png).convert('RGB')
    bbox=(min(x for x,y in xy),min(y for x,y in xy),max(x for x,y in xy),max(y for x,y in xy))
    checks=dict(region_key=a['region_id']==rid and a['rank']==t['rank'] and a['province']==t['province'] and norm(a['region'])==norm(t['region']),
                exact_capital_province_region_join=len(codes)==1 and codes[0]==a['source_region_code'],
                validation_source_sgg=next(v['source_sgg'] for v in ma['validation'] if v['region_id']==rid)==codes[0],
                all_target_features_exact=g['features']==target, dong_count=len(target)==a['source_dong_count'],
                boundary_version=a['boundary_version']=='2024-10-01'==sm['boundary_version'],reference_date=a['statistical_reference_date']=='2024-11-01',
                no_ai_or_photo=a['type']=='verified_geographic_data_map' and a['actual_place'] and not a['ai_generated'],
                dimensions=im.size==(1920,1080),png_hash=digest(png.read_bytes())==a['sha256'],
                target_not_clipped=bbox[0]>105 and bbox[1]>190 and bbox[2]<1265 and bbox[3]<850,
                attribution=all(s in a['attribution'] for s in ['SGIS','공공누리 제1유형','vuski/admdongkor','CC BY 4.0']) and 'CC BY 4.0' in a['license'])
    if rid=='R20':
        official_wonmi_dongs={'심곡1동','심곡2동','심곡3동','원미1동','원미2동','소사동','역곡1동','역곡2동','춘의동','도당동','약대동','중동','중1동','중2동','중3동','중4동','상동','상1동','상2동','상3동'}
        checks['wonmi_official_20_dongs_match']={f['properties']['adm_nm'].split()[-1] for f in target}==official_wonmi_dongs
    maps.append(dict(region_id=rid,scene_id=t['scene_id'],province=t['province'],region=t['region'],source_sgg=codes,source_dong_count=len(target),
                     raw_admin_dongs=[f['properties']['adm_nm'] for f in target],highlight_bbox=bbox,checks=checks,
                     actual_file=str(png),svg_contains_labels=any(e.tag.endswith('}text') for e in svg.iter()),
                     note='SVG는 지도 레이어 원본; 순위·표시값은 PNG에서 확인'))
    map_contexts.append((target,im,hi,pairs))
assert len(maps)==20 and all(all(m['checks'].values()) for m in maps)
# 모든 강조 좌표를 함께 사용해 공통 Mercator 변환을 검증한다. 원도 순서와 좌표 수까지 대조.
ax=[p[0][0] for p in point_pairs];ay=[p[0][1] for p in point_pairs];bx=[p[1][0] for p in point_pairs];by=[p[1][1] for p in point_pairs]
def fit(a,b):
    am,bm=statistics.mean(a),statistics.mean(b)
    s=sum((x-am)*(y-bm) for x,y in zip(a,b))/sum((x-am)**2 for x in a)
    return s,bm-s*am
sx,tx=fit(ax,bx);sy,ty=fit(ay,by)
for m,(target,im,hi,pairs) in zip(maps,map_contexts):
    residual=max(max(abs(p[0]*sx+tx-q[0]),abs(p[1]*sy+ty-q[1])) for p,q in pairs)
    predicted=Image.new('L',im.size)
    for f in target:
        polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
        for poly in polys:
            temp=Image.new('L',im.size);draw=ImageDraw.Draw(temp)
            for i,ring in enumerate(poly):
                coords=[merc(*p) for p in ring];draw.polygon([(round(x*sx+tx),round(y*sy+ty)) for x,y in coords],fill=255 if i==0 else 0)
            predicted=ImageChops.lighter(predicted,temp)
    color=tuple(bytes.fromhex(hi[0].attrib['fill'][1:]));actual=Image.new('L',im.size);crop=im.crop((105,190,1265,850));mask=Image.new('L',crop.size)
    mask.putdata([255 if p==color else 0 for p in crop.get_flattened_data()]);actual.paste(mask,(105,190))
    intersection=ImageChops.darker(actual,predicted).histogram()[255];union=ImageChops.lighter(actual,predicted).histogram()[255]
    # SVG 안티앨리어싱/서브픽셀 반올림과 PIL 정수 채움 차이는 2px 경계 띠에서만 허용.
    actual_outside=ImageChops.subtract(actual,predicted.filter(ImageFilter.MaxFilter(5))).histogram()[255]
    predicted_outside=ImageChops.subtract(predicted,actual.filter(ImageFilter.MaxFilter(5))).histogram()[255]
    m['svg_source_point_max_error_px']=residual;m['highlight_raster_iou']=intersection/union
    m['checks']['svg_matches_raw_mercator_shape']=residual<0.07
    m['raster_boundary_tolerance_px']=2
    m['actual_pixels_outside_predicted_boundary_band']=actual_outside
    m['predicted_pixels_outside_actual_boundary_band']=predicted_outside
    m['checks']['png_matches_independent_shape']=actual_outside==0 and predicted_outside==0
    m['pass_all']=all(m['checks'].values())
emit('map_join_ledger.json',maps)
if not all(m['pass_all'] for m in maps):
    print(json.dumps([dict(region_id=m['region_id'],failed=[k for k,v in m['checks'].items() if not v],error=m['svg_source_point_max_error_px'],iou=m['highlight_raster_iou']) for m in maps if not m['pass_all']],ensure_ascii=False))
assert all(m['pass_all'] for m in maps)

# PNG 중앙 스캔라인에서 직사각형 길이를 직접 측정. 안티앨리어싱/모서리는 피한다.
ca=read_json(EP/'visual'/REV/'data_cards/data_card_assets.json')
colors={'서울':(40,108,218),'경기':(22,127,134),'인천':(181,138,54)}
def span(im,y,color,xmin,xmax):
    xs=[x for x in range(xmin,xmax) if im.getpixel((x,y))==color]
    return [min(xs),max(xs)+1] if xs else None
cards=[]
for a in ca['assets']:
    p=EP/a['actual_file'];read_bytes(p,'육안 열람 6/6; PNG 표시값・축・분모・비례・가장자리 확인');im=Image.open(p).convert('RGB');measure=[]
    if 'rank_order' in a:
        for i,rank in enumerate(a['rank_order']):
            t=top['regions'][rank-1];s=span(im,271+116*i,colors[t['province']],665,1536);actual=s[1]-s[0]-1;expected=870*t['newlywed_couples']/16000
            measure.append(dict(rank=rank,value=t['newlywed_couples'],span=s,measured_length_px=actual,expected_length_px=expected,error_px=actual-expected,pass_proportion=abs(actual-expected)<=1.1))
        metric='신혼부부 전체 수(쌍)';denominator='2024 수도권 53개 구 중 TOP20';axis='0~16000쌍; 네 장 공통 0·4·8·12·16천'
    elif a['asset_id']=='TOP20_PROVINCE_COUNTS':
        counts=collections.Counter(t['province'] for t in top['regions'])
        for i,(province,value) in enumerate([('서울',9),('경기',6),('인천',5)]):
            s=span(im,335+174*i,colors[province],420,1412);actual=s[1]-s[0]-1;expected=110*counts[province]
            measure.append(dict(province=province,display_value=value,recomputed_value=counts[province],span=s,measured_length_px=actual,expected_length_px=expected,pass_proportion=abs(actual-expected)<=1.1 and counts[province]==value))
        metric='TOP20 안에 포함된 구의 개수';denominator='20개 구; 부부 수의 시도 점유율 아님';axis='공통 0 출발·동일 높이; 수치 라벨 9·6·5'
    else:
        for i,rank in enumerate([12,1,16]):
            t=top['regions'][rank-1];n=t['newlywed_couples'];first=t['first_marriage_couples'];rem=t['remarried_couples'];unknown=n-first-rem
            s=span(im,340+175*i,(40,108,218),110,1791)
            gold=span(im,340+175*i,(194,154,68),110,1791)
            gray=span(im,340+175*i,(188,198,200),110,1791)
            actual=s[1]-s[0];expected=1680*first/n
            gold_actual=gold[1]-gold[0];gray_actual=gray[1]-gray[0]
            gold_expected=1680*rem/n;gray_expected=1680*unknown/n
            measure.append(dict(region_id=t['region_id'],rank=rank,denominator=n,first=first,remarried=rem,unknown_or_rounding_residual=unknown,
                share_pct=first/n*100,expected_display_pct=round(first/n*100,1),blue_span=s,gold_span=gold,gray_span=gray,
                measured_length_px=actual,expected_length_px=expected,remarried_length_px=gold_actual,remarried_expected_length_px=gold_expected,
                residual_length_px=gray_actual,residual_expected_length_px=gray_expected,
                pixel_tolerance_basis='전체1680px. 정수좌표 양끝 포함 및 인접 구간 덮어쓰기 차이를 포함해 각 구간 2px 이내(0.12%p) 허용.',
                pass_proportion=abs(actual-expected)<=2 and abs(gold_actual-gold_expected)<=2 and abs(gray_actual-gray_expected)<=2))
        metric='초혼·재혼·미상 구성';denominator='각 지역의 전체 신혼부부 수';axis='지역별 고정 폭 1680px=100%; 초혼 비중 91.0·81.0·69.9%'
    cards.append(dict(asset_id=a['asset_id'],actual_file=str(p),dimensions=list(im.size),metric=metric,denominator=denominator,axis=axis,measurements=measure,
        visual_values_match_input=True,visible_clipping=False,visual_inspection='실제 PNG 열람',source_attribution_present=True,pass_all=im.size==(1920,1080) and all(m['pass_proportion'] for m in measure)))
emit('data_card_ledger.json',cards)
if not all(c['pass_all'] for c in cards):
    print(json.dumps([dict(asset_id=c['asset_id'],failed=[m for m in c['measurements'] if not m['pass_proportion']]) for c in cards if not c['pass_all']],ensure_ascii=False))
assert len(cards)==6 and all(c['pass_all'] for c in cards)

# 실제 열람 파일을 명시. 모아보기 셀은 원본 전체 해상도 검수로 세지 않는다.
montage=next((EP/'visual'/REV/'maps').glob('*.jpg'));read_bytes(montage,'실제 모아보기 열람 1파일・20셀')
read_bytes(EP/'visual'/REV/'maps/지도_출처와_이용조건.md','출처・범위 주석 열람')
coverage=dict(map_geometry_rows_checked=20,map_png_automatic_checks=20,map_contact_sheet_files_viewed=1,map_contact_sheet_cells_viewed=20,
             full_resolution_map_png_files_viewed=2,full_resolution_map_region_ids=['R01','R20'],data_card_png_files_viewed=6,
             actual_still_image_files_viewed=9,map_view_observations_including_repeats=22,unique_map_regions_visually_sampled=20,
             inspected_still_samples_including_montage_cells=28,pdf_text_pages_checked=[32,33],pdf_page_images_actually_viewed=0,
             sampled_mp4_frames_actually_viewed=0,continuous_playback_performed=False,actual_listening_performed=False,media_stream_inspection='unchecked',
             full_video_render_review='unchecked',actual_photo_review='범위 밖・visual 병행 작업을 기다리지 않음',
             note='9개 실제 이미지 파일=모아보기1+지도 원본PNG2+카드6. 28은 셀·원본 중복을 포함한 정지 샘플이며 영상 프레임 수가 아님.')
emit('coverage.json',coverage)
emit('reuse_receipt.json',reuse)
emit('source_evidence.json',dict(checked_at=NOW,official_pdf=dict(url=PDFURL,title='2023년 신혼부부통계 결과',publication_date='2024-12-10',reference_date='2023-11-01',
    table='6. 시군구별 신혼부부 수',pdf_pages=[32,33],printed_pages=[25,26],selected_column='전체',unit='쌍',web_line_range=[1406,1489],
    rows_evidence='row_comparison_ledger.json',method='웹 PDF 추출 텍스트 독립 열람・시도/시/구 문맥과 전체 열 대조',
    page_image_method='로컬 fitz/pypdf/pdfplumber/Poppler 부재. 웹 screenshot 2쪽 단일 묶음 시도: 한 쪽은 참조만, 한 쪽은 Cache miss. 실제 화상 0쪽. 재시도・설치 없음.',
    footnote='부부 거처가 다르면 시군구별 0.5 가중치. 표시 정수는 반올림으로 합계 차이가 날 수 있음. 시점별 전체 수 변화이며 순유입이 아님.',
    local_file=str(src/'newlyweds_2023.pdf'),local_sha256=digest(local_pdf),live_remote_binary_hash_comparison='unchecked'),
    wonmi=dict(url='https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=105833',
      title='행정기관(행정동) 및 관할구역(법정동) 변경내역(2024.1.1. 시행 일부)',web_lines=[825,839,850,859],
      conclusion='2024-01-01 일반구 복원/신설. 2023 PDF33쪽에는 부천시 전체 14976만 존재하고 원미구 행은 없음. 원미구 2023·delta·rate null 유지. 부천 전체 대체/비례배분 금지.',
      exact_20_admin_dongs_verified=[f['properties']['adm_nm'] for f in map_contexts[-1][0]]),
    old_seo=dict(url='https://www.icouncil.go.kr/webzine/webzineno/webzineNoDetail.do?menudetail=52&no_seq=2241',web_lines=[54,58],
      conclusion='인천광역시의회 2026년7·8월 소식에서 2026-07-01 서구→서해구·검단구 개편 확인. R01은 2024 서구 28260 전체이며 현 서해구 단독 수치가 아님.',
      secondary_official_url='https://www.seohae.go.kr/open_content/bbs/bbsMsgDetail.do?bcd=notice&msg_seq=29334',secondary_web_lines=[549,555],
      caveat='2025 안내의 새 서구 표현을 현재 구명 확정 근거로 단독 사용하지 않음. 현 구명은 2026 의회 자료와 연결.'),
    boundary=dict(source_manifest=str(src/'source_manifest.json'),source_url=sm['sources']['geometry']['url'],boundary_version=sm['boundary_version'],
      integrity=source_integrity,capital_scope='sido 11 서울・28 인천・41 경기 + sggnm 공백만 정규화한 정확 일치',
      mercator_fit=dict(scale_x=sx,scale_y=sy,offset_x=tx,offset_y=ty),
      wonmi_no_whole_bucheon_substitution='R20 sgg41192 원미구20동만 포함; 소사구41194・오정구41196 제외; 원도와 모든 feature 정확 일치'),
    rights=dict(local_license_path=str(src/'LICENSE-DATA.txt'),url='https://raw.githubusercontent.com/vuski/admdongkor/master/LICENSE-DATA',
      web_lines=[2,7,11,37],conclusion='경계 데이터 CC BY4.0, 원자료 SGIS 공공누리1유형 출처표시. MIT는 코드용. 원문 스냅샷 존재・manifest해시 일치. metadata/가이드/열람PNG2장 크레딧 확인.',
      publication_note='본편 채택 시 자료팩 출처와 가공표시를 이어받아야 하며 최종 영상 적용 검수는 이번 범위 밖.')))

rec=dict(issue_id='QA-T20V2-CARD-SCOPE-01',scene_id=['S003','S004','S005','S006','S007','S008','S009','S010','S011','S012','S013','S014','S015','S016','S017','S018','S019','S020','S021','S022'],timecode=None,
 severity='recommended',문제='순위 묶음 카드 4장의 제목은 수도권 신혼부부 TOP20이고 각 카드에 53개 구 모집단 제한이 독립적으로 적혀 있지 않음.',
 evidence=dict(files=[c['actual_file'] for c in cards if c['asset_id'].startswith('RANK_GROUP')],observation='공통 하단은 기준일・거주지・5년 미경과만 표시. 모집단 53개 구는 지도 및 별도 시도개수 카드에서 확인 가능.'),
 수정안='본편 채택 시 네 장 제목 또는 공통 각주에 2024 수도권 53개 구 중 TOP20을 추가. 현재 자료 이미지 준비 QA의 권장 보완이며 그림/폰트 채택 승인은 아님.',owner='visual',status='open',
 checked_revision=dict(revision=REV,top20_sha256=manifest[str((EP/'research'/REV/'top20.json').resolve())]['sha256'],png_sha256={c['actual_file']:manifest[str(Path(c['actual_file']).resolve())]['sha256'] for c in cards if c['asset_id'].startswith('RANK_GROUP')}),impact='도표를 단독 재사용할 때 시・군 포함 전체 수도권 순위로 오인할 가능성을 낮춤')
emit('issue_QA-T20V2-CARD-SCOPE-01.json',rec)
scope=dict(stage='자료 이미지 준비 QA',tasks_completed=['2023 전체19행 독립대조・원미null1행 검증・전년증감19행 재계산','지도20개 원도조인・버전・SGIS/CCBY4 출처・지정 시각 표본','data_cards6장 표시값・축・분모・길이비례・잘림 표본'],
    excluded=['지역선택 인과・순유입 해석','최신 가격/매물 검증','리서치 지역 특징 전체 승격','실제사진 전체 QA','디자인 채택・폰트 맞춤제작 완료','MP4 생성・재생・청취・렌더・납품 ZIP 검사'],
    source_full_review_repeated=False,shared_files_modified=False,other_owner_files_modified=False,direct_peer_messaging_available=False,
    route='메시지 도구 없음. 지정 QA 폴더 issue JSON과 handoff 경로를 총괄에 전달.',
    limitations=['PDF32~33쪽은 텍스트대조만; 화상 미확인','지도 원본 PNG 육안 검수2/20; 나머지는 모아보기 셀+전20 자동 경계검사','기준일 이름 대응은 확인했으나 현2026 경계와의 전수 GIS 크로스워크 아님','본편용 문장/내레이션 동기화/줌 후 잘림 검수는 후속 작업'])
emit('review_scope.json',scope)
report=dict(task_id='qa-top20-8min-v2-data-preparation',role='qa',revision=REV,status='completed_with_recommendation',checked_at=NOW,
    verdict=dict(count2023_19_rows='pass',wonmi_null='pass',count2024_prior_hash_reuse='pass',yoy_19_rows='pass',map_20_joins_and_version='pass',
      map_20_geographic_shape_and_png_checks='pass',map_rights_source_snapshot='pass',data_cards_6='pass',critical_open=0,required_open=0,recommended_open=1,
      decision='지정3과제 자료준비 QA 완료. 권장보완1건. 최종 디자인・사진・영상・음성 통과로 확대 금지.'),
    findings=[rec],input_manifest_path=str(OUT/'input_manifest.json'),row_comparison_ledger=str(OUT/'row_comparison_ledger.json'),
    source_evidence=str(OUT/'source_evidence.json'),review_scope=scope,coverage=coverage,reuse_receipt=str(OUT/'reuse_receipt.json'),
    checked_revision=dict(revision=REV,top20_sha256=manifest[str((EP/'research'/REV/'top20.json').resolve())]['sha256'],input_manifest=str(OUT/'input_manifest.json')))
emit('findings.json',report)
outputs=[str(p) for p in OUT.iterdir() if p.is_file() and p.name not in ['handoff.json','input_manifest.json']]
handoff=dict(task_id=report['task_id'],role='qa',status=report['status'],input_revisions=report['checked_revision'],outputs=outputs,
    affected_scene_ids=[t['scene_id'] for t in top['regions']],checks=[dict(check=k,result=v,evidence=str(OUT/'findings.json')) for k,v in report['verdict'].items() if v=='pass'],
    counts=dict(independent_2023_rows=19,null_area_rows=1,reused_2024_rows=20,yoy_rows=19,map_join_rows=20,data_cards=6,actual_image_files_viewed=9,mp4_frames_viewed=0),
    open_issue_ids=[rec['issue_id']],unresolved=['필수 수정 없음','권장: 순위카드4장에 53개 구 범위 독립 표기','PDF 화상・사진・영상/음성 미검수는 scope대로 유지'],
    next_role='director → visual(권장 사항 및 본편 채택 시 출처 승계)',input_manifest=str(OUT/'input_manifest.json'),source_evidence=str(OUT/'source_evidence.json'),
    handoff_summary='2023 공식PDF 텍스트19행·원미null1행 통과, 2024 기존 QA 해시/추출20행 재사용, 증감19행 통과. 지도20개 원도정확조인/2024버전/PNG윤곽 및 CC BY4+SGIS 출처 통과. 모아보기1파일20셀+원본R01/R20+카드6=실제 이미지9파일(정지샘플28,MP4프레임0). 카드6장 축·분모·비례·표시값·잘림 확인. 필수0/권장1(4개 순위카드53개구 범위표기). PDF화상0,실제사진/디자인채택/최신가격/인과/순유입/영상청취재생은 미검수. 소유범위 QA 폴더만 작성.')
emit('handoff.json',handoff)
stability=[]
for p,m in manifest.items():
    current=digest(Path(p).read_bytes());stability.append(dict(path=p,initial_sha256=m['sha256'],final_sha256=current,unchanged=current==m['sha256']))
assert all(s['unchanged'] for s in stability)
emit('input_manifest.json',dict(revision=REV,checked_at=NOW,inputs=list(manifest.values()),stability=stability,all_unchanged=True,validator=dict(path=str(Path(__file__).resolve()),sha256=digest(Path(__file__).read_bytes())),
    evidence_reuse='reuse_receipt.json',read_scope='입력 report의 지정 숫자/증감/행정 근거만 사용. 기타 지역설명/이미지후보/가격은 검수 승격하지 않음.'))
print(json.dumps(dict(status=report['status'],numeric_rows=len(rows),map_rows=len(maps),cards=len(cards),
    map_min_iou=min(m['highlight_raster_iou'] for m in maps),map_max_coordinate_error=max(m['svg_source_point_max_error_px'] for m in maps),
    inputs=len(manifest),all_inputs_unchanged=True,critical=0,required=0,recommended=1,output=str(OUT)),ensure_ascii=False))
