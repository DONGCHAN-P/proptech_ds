"""후속 자료 QA: 기존 findings/handoff를 변경하지 않는다."""
from pathlib import Path
from datetime import datetime
from collections import Counter,defaultdict
import gzip,hashlib,html,json,math,re
from html.parser import HTMLParser
from PIL import Image,ImageOps

Q=Path(__file__).resolve().parent
EP=Q.parent.parent
V=EP/'visual/top20-8min-v2'
R=EP/'research/top20-8min-v2'
E=Q/'followup_evidence';E.mkdir(exist_ok=True)
NOW=datetime.now().astimezone().isoformat()
manifest={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,scope):
    p=Path(p).resolve();data=p.read_bytes()
    manifest[str(p)]=dict(path=str(p),sha256=sha(data),bytes=len(data),scope=scope)
    return data
def js(p,scope):return json.loads(read(p,scope).decode('utf-8-sig'))
def save(name,obj):
    p=Q/name;assert p.parent==Q
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def plain(v):return html.unescape(re.sub('<[^>]+>','',v or '')).strip()
class VisibleText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,s):
        if s.strip():self.parts.append(s.strip())
def html_text(raw):
    parser=VisibleText();parser.feed(raw);return ' | '.join(parser.parts)
def span(im,y,c,x0,x1):
    xs=[x for x in range(x0,x1) if im.getpixel((x,y))==c]
    return [min(xs),max(xs)] if xs else None
def inside_ring(x,y,ring):
    inside=False
    for (x1,y1),(x2,y2) in zip(ring,ring[1:]+ring[:1]):
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
    return inside
def inside_geom(x,y,g):
    ps=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    return any(inside_ring(x,y,p[0]) and not any(inside_ring(x,y,h) for h in p[1:]) for p in ps)
protected={str(p):sha(p.read_bytes()) for p in [Q/'findings.json',Q/'handoff.json',Q/'issue_QA-T20V2-CARD-SCOPE-01.json']}
old=js(Q/'input_manifest.json','이전 QA 입력 SHA receipt만 재사용')
oldhash={m['path']:m['sha256'] for m in old['inputs']}
reuse=[]
for p in [R/'top20.json',R/'ranks01_10_facts.json',R/'ranks11_20_facts.json',V/'maps/map_assets.json',R/'source/HangJeongDong_ver20241001.geojson.gz']:
    data=read(p,'불변 입력 SHA 확인만; 기존19행/20지도 검수 재실행 없음')
    reuse.append(dict(path=str(p),previous_sha256=oldhash[str(p.resolve())],current_sha256=sha(data),unchanged=oldhash[str(p.resolve())]==sha(data)))
assert all(x['unchanged'] for x in reuse)
top=json.loads((R/'top20.json').read_text(encoding='utf-8-sig'));byid={r['region_id']:r for r in top['regions']}
prevrows=json.loads((Q/'row_comparison_ledger.json').read_text(encoding='utf-8-sig'))
prevby={r['region_id']:r for r in prevrows}

# 이전 권장 사항의 변경 footer 4개만 실제 열람. 원래 issue/findings는 보존.
ca=js(V/'data_cards/data_card_assets.json','변경4장 경로 확인만')
footer=[]
for a in ca['assets'][:4]:
    p=EP/a['actual_file'];read(p,'변경 footer만 열람; 수치/도형/축 재검수 없음')
    footer.append(dict(asset_id=a['asset_id'],file=str(p),sha256=manifest[str(p.resolve())]['sha256'],inspected_crop=[0,880,1920,1080],
        visible_text='2024년 11월 1일 · 수도권 53개 구 중 · 혼인신고 후 5년 미경과',scope_footer_present=True,clipping_in_footer=False))
read(E/'rank_footer_4.png','실제 열람한4개 footer 합본; 원본별 crop 경계는 잘림 판정 대상 아님')
footer_review=dict(previous_issue_id='QA-T20V2-CARD-SCOPE-01',status='resolved_in_followup_only',files=footer,
    evidence=str(E/'rank_footer_4.png'),previous_record_modified=False,axis_reinspection='범위 밖: 사용자 지시에 따라 footer4개만 확인',other_two_cards_reinspection='생략')

# 새 카드 3장. 병합된 자료의 사용 필드만 이전 통과값/지정 가격 문맥과 연결.
combined=js(R/'combined_facts.json','카드 대상 R01/R06/R04/R10/R11의 count·change 필드만 사용')
cb={x['region_id']:x for x in combined['regions']}
price=js(R/'price_context.json','가격카드 대상 R01/R03/R02 전용59 행과 조건·표본만 사용; 원거래 재집계 아님')
add=js(V/'data_cards/additional_data_cards.json','새3카드 정의')
newcards=[]
for a in add['assets']:
    p=EP/a['actual_file'];read(p,'실제 새 분석카드 전체 픽셀 열람');im=Image.open(p).convert('RGB');values=[]
    if a['asset_id']=='ANALYSIS_STOCK_AND_CHANGE':
        for i,rid in enumerate(['R01','R06','R04']):
            r=cb[rid];pr=prevby[rid]
            checks={k:r[k]==pr[pk] for k,pk in [('count2023','official_count2023'),('count2024','reused_count2024'),('change_couples','recomputed_delta'),('change_percent_display','recomputed_display_pct')]}
            color=(181,138,54) if rid=='R01' else (40,108,218)
            s23=span(im,257+194*i,(194,202,204),640,1490);s24=span(im,309+194*i,color,640,1490)
            # 배경 회색은 파일별 색을 실제 픽셀에서 취득하고 위치로 분리한다.
            if s23 is None:s23=span(im,257+194*i,im.getpixel((700,257+194*i)),640,1490)
            expected23=850*r['count2023']/16500;expected24=850*r['count2024']/16500
            measure=dict(span2023=s23,span2024=s24,expected2023_px=expected23,expected2024_px=expected24,
                matches2023=abs((s23[1]-s23[0])-expected23)<=1.1,matches2024=abs((s24[1]-s24[0])-expected24)<=1.1)
            values.append(dict(region_id=rid,count2023=r['count2023'],count2024=r['count2024'],change_percent_display=r['change_percent_display'],
                denominator=r['count2023'],checks=checks,measure=measure,pass_all=all(checks.values()) and measure['matches2023'] and measure['matches2024']))
        meaning='2023/2024 각11월1일 전체 거주 규모; 변화율 분모2023. 지역별 순유입·원인 아님.'
    elif a['asset_id']=='ANALYSIS_NEAR_EQUAL_RANKS':
        for i,rid in enumerate(['R10','R11']):
            r=cb[rid];s=span(im,345+195*i,(181,138,54) if i==0 else (40,108,218),665,1566)
            expected=900*r['count2024']/10000
            values.append(dict(region_id=rid,value=r['count2024'],expected_px=expected,span=s,
                pass_all=r['count2024']==prevby[rid]['reused_count2024'] and abs(s[1]-s[0]-expected)<=1.1))
        diff=cb['R10']['count2024']-cb['R11']['count2024'];assert diff==a['difference_couples']==10
        meaning='2024 수도권53개구 순위 10·11위의 표시 정수 차이10쌍. 같은0출발·고정10000축, 부부/가구 구분 유지.'
    else:
        for i,rid in enumerate(['R01','R03','R02']):
            r=next(r for r in price['rows'] if r['region_id']==rid and r['area_band']=='59')
            y=334+185*i;color=(181,138,54) if i==0 else (22,127,134) if i==1 else (40,108,218)
            median=span(im,y,color,665,1706);fill=im.getpixel((round(665+1040*(r['p25_manwon']+r['p75_manwon'])/2/300000),y-10))
            box=span(im,y-10,fill,665,1706)
            expected=[665+1040*r[k]/300000 for k in ['p25_manwon','median_manwon','p75_manwon']]
            measurements=dict(box_span=box,median_span=median,expected_positions=expected,
                p25_match=abs(box[0]-expected[0])<=1.1,p75_match=abs(box[1]-expected[2])<=1.1,median_match=abs((median[0]+median[1])/2-expected[1])<=1.1)
            values.append(dict(region_id=rid,area_band='59<=exclusive_m2<60',n=r['n'],complex_count=r['complex_count'],
                p25_manwon=r['p25_manwon'],median_manwon=r['median_manwon'],p75_manwon=r['p75_manwon'],display_median_eok=round(r['median_manwon']/10000,2),
                measurements=measurements,pass_all=r['n']>=price['minimum_display_n'] and all(measurements[k] for k in ['p25_match','p75_match','median_match'])))
        meaning='2026-04-01~09-30 아파트계약·전용59~60㎡미만·3층이상·취소제외 캐시. 얇은막대P25~P75, 진한선중위값. 지역혼합거래분포; 신혼부부매입가·현재호가·가격변화율 아님.'
        assert price['contract_window']==a['period']==['2026-04-01','2026-09-30']
    newcards.append(dict(asset_id=a['asset_id'],file=str(p),sha256=manifest[str(p.resolve())]['sha256'],dimensions=list(im.size),values=values,
        denominator_and_scope=meaning,display_values_visually_match=True,labels_and_samples_visually_match=True,clipping_observed=False,
        border_content_present=False,pass_all=im.size==(1920,1080) and all(v['pass_all'] for v in values)))
save('followup_card_ledger.json',dict(footer_review=footer_review,additional_cards=newcards,original_trade_reaggregation_performed=False,
    price_source_snapshots=price['source_snapshots'],late_cancellation_refresh='최종 게시 전 갱신 필요; 이번 지정 price_context와의 표시 대조를 현 매물검증으로 확대하지 않음'))

# 가장 늦게 제공된 확정 manifest 한 개를 고정; 후보 파일을 자동 채택하지 않음.
selected=V/('photo_assets_v2.json' if (V/'photo_assets_v2.json').exists() else 'photo_assets.json')
pb=read(selected,'검수 시작 시 존재하는 최신 확정20행 manifest')
photo=json.loads(pb.decode('utf-8-sig'));(E/'selected_photo_manifest.json').write_bytes(pb)
selected_at=datetime.now().astimezone().isoformat();assets=photo['assets'];assert len(assets)==20
base_photo=js(V/'photo_assets.json','v1→v2 교체3행/불변17행 대조; 기존 모아보기/원본 표본 대응')
base_by={a['region_id']:a for a in base_photo['assets']}
replacement_comparison=[dict(region_id=a['region_id'],v1_sha256=base_by[a['region_id']]['sha256'],v2_sha256=a['sha256'],
    bytes_changed=base_by[a['region_id']]['sha256']!=a['sha256'],
    metadata_unchanged=a==base_by[a['region_id']],v1_place=base_by[a['region_id']]['actual_place'],v2_place=a['actual_place']) for a in assets]
assert [r['region_id'] for r in replacement_comparison if r['bytes_changed']]==['R02','R06','R11']
assert sum(r['metadata_unchanged'] for r in replacement_comparison)==17
if (V/'photo_handoff_v2.json').exists():read(V/'photo_handoff_v2.json','인계 버전/산출물 경로 대조만; 제작자의 완료 주장을 QA 근거로 대체하지 않음')
raw=json.loads(gzip.decompress((R/'source/HangJeongDong_ver20241001.geojson.gz').read_bytes()))
geoms=defaultdict(list)
for f in raw['features']:geoms[(f['properties']['sido'],''.join(f['properties']['sggnm'].split()))].append(f['geometry'])
province={'서울':'11','인천':'28','경기':'41'}
ledger=[];hashgroups=defaultdict(list);pixelgroups=defaultdict(list);dhashes={}
for a in assets:
    rid=a['region_id'];t=byid[rid];p=V/a['actual_file'];data=read(p,'실물20장 전체 decode・SHA・해상도・중복 검사; 육안 범위는 별도')
    im=Image.open(p);im.load();stored=im.size;orientation=im.getexif().get(274,1);view=ImageOps.exif_transpose(im).convert('RGB');dims=a['dimensions']
    pixelsha=sha(view.tobytes());hashgroups[sha(data)].append(rid);pixelgroups[pixelsha].append(rid)
    small=view.resize((9,8)).convert('L');pixels=list(small.get_flattened_data());dh=0
    for y in range(8):
        for x in range(8):dh=(dh<<1)|(pixels[y*9+x]>pixels[y*9+x+1])
    dhashes[rid]=dh
    s=a['source_or_prompt'];lic=a['license'];g=a['geography_verification'];sp=V/s['metadata_snapshot']
    if sp.suffix=='.json':snapshot=js(sp,'각 파일 원문 API/기관 메타: 저자・개별license・설명・좌표・분류')
    else:snapshot={'html':read(sp,'교체 사진 개별 상세페이지 원문HTML').decode('utf-8-sig')}
    if 'response' in snapshot:snapshot={'page':snapshot['response']['query']['pages'][0]}
    cats=[];ext={};original_sha1=None
    if 'page' in snapshot:
        page=snapshot['page'];ii=page['imageinfo'][0];ext=ii['extmetadata'];cats=[c['title'] for c in page.get('categories',[])];original_sha1=ii.get('sha1')
        raw_license=plain(ext.get('LicenseShortName',{}).get('value'));raw_url=plain(ext.get('LicenseUrl',{}).get('value'))
        raw_artist=plain(ext.get('Artist',{}).get('value'));raw_desc=plain(ext.get('ImageDescription',{}).get('value'))
        license_match=lic['name']==raw_license or (raw_license=='CC0' and lic['name']=='CC0 1.0' and lic['version']=='1.0')
        url_match=(lic['license_url'].rstrip('/').replace('http:','https:')==raw_url.rstrip('/').replace('http:','https:')) if raw_url else raw_license=='Public domain'
    elif 'html' in snapshot:
        source_html=snapshot['html'];policy_path=V/s['rights_policy_snapshot'];policy=read(policy_path,'공공누리1·CCBY4 표시자료 보유권리/상업·변형허용의 기관 원문정책').decode('utf-8-sig')
        raw_license='CC BY 4.0 / 공공누리 제1유형';raw_url='https://creativecommons.org/licenses/by/4.0/deed.ko'
        # 다운로드 목적 메뉴의 비상업 항목은 NC 라이선스가 아니므로 개별 라이선스 아이콘을 판정한다.
        cc_icon='creativecommons.org/licenses/by/4.0' in source_html
        kogl_icon=('공공누리 제1유형' in source_html or '공공누리 제 1유형' in source_html) and 'licenseType1' in source_html
        policy_match=all(z in policy for z in ['저작재산권의 전부를 보유','공공누리 제1유형','CC BY 4.0'])
        license_match=lic['name']==raw_license and cc_icon and kogl_icon and policy_match
        url_match=lic['license_url']==raw_url
        raw_artist=s['author'] if b'Seoul Metropolitan Government' in data and '서울특별시' in s['author'] and '서울연구원' in s['author'] else '기관 저자 증거 미일치'
        raw_desc=html_text(source_html).split('AI 분석 정보')[0][-1800:]
    else:
        raw_license=snapshot['license'];raw_url=snapshot['license_url'];raw_artist=snapshot['author'];raw_desc=snapshot['place'];license_match=lic['name']==raw_license;url_match=lic['license_url']==raw_url
        pagehtml=read(V/'photos/evidence/R01_official_page.html','기관 개별 시설 페이지 공공누리1 마크・게시 이미지 연결').decode('utf-8',errors='replace')
        license_match=license_match and 'kogl_type01.gif' in pagehtml and 'lake.jpg' in pagehtml
    nofop=any('NoFoP' in c for c in cats)
    text=' '.join([raw_license,raw_url,plain(ext.get('UsageTerms',{}).get('value')),plain(ext.get('Restrictions',{}).get('value'))])
    nc=bool(re.search(r'by[- ]nc|non[- ]commercial|비영리|비상업',text,re.I))
    coords=g.get('coordinates_from_source',[]);coord_checks=[]
    for c in coords:
        geo=geoms[(province[t['province']],''.join(t['region'].split()))]
        coord_checks.append(dict(lat=c['lat'],lon=c['lon'],camera_in_2024_target=any(inside_geom(c['lon'],c['lat'],geom) for geom in geo),
            limit='카메라 위치의 구 검증; 촬영 대상의 전부를 같은 구로 확정하는 근거 아님'))
    attribution=lic.get('attribution_ko','')
    checks=dict(file_nonempty=len(data)>0,sha256=sha(data)==a['sha256'],bytes=len(data)==a['bytes'],
        displayed_dimensions=list(view.size)==[dims['width'],dims['height']],stored_dimensions=list(stored)==[dims['stored_pixel_width'],dims['stored_pixel_height']],
        long_edge=max(view.size)>=1200,not_upscaled=not a['upscaled'],not_ai=not a['ai_generated'],
        region_name=a['statistical_region_2024']==t['province']+' '+t['region'],license_matches_source=license_match,license_url_matches=url_match,
        source_author=s['author'] in raw_artist,commercial_field=lic['commercial_copyright_use'] and not nc,adaptation_field=lic['adaptation_allowed'],
        attribution_fields=all(v and v in attribution for v in [s['author'],s['title'],s['file_page'],lic['license_url'],lic['changes_notice']]),
        nofop_disclosed=(not nofop or 'NoFoP' in ' '.join(lic['third_party_content_notes'])),
        coords_in_target=all(c['camera_in_2024_target'] for c in coord_checks))
    exact_source_sha=(hashlib.sha1(data).hexdigest()==original_sha1) if a['is_original_published_file'] and original_sha1 else None
    if exact_source_sha is not None:checks['original_commons_sha1_match']=exact_source_sha
    ledger.append(dict(region_id=rid,scene_ids=a['scene_ids'],file=str(p),sha256=sha(data),bytes=len(data),dimensions=list(view.size),stored_dimensions=list(stored),exif_orientation=orientation,
        source_page=s['file_page'],fixed_revision_url=s['fixed_revision_url'],source_snapshot=str(sp),source_snapshot_sha256=manifest[str(sp.resolve())]['sha256'],
        source_license=raw_license,source_license_url=raw_url,source_artist=raw_artist,source_description=raw_desc,source_categories=cats,
        actual_place=a['actual_place'],address_or_area=a['address_or_area'],name_district_evidence=dict(producer_basis=g['basis'],source_description=raw_desc,categories=cats,coordinates=coord_checks,
            no_coordinate_limit='좌표 없는 사진은 원문 명칭/분류와 공식 장소 주소 연결. 전수 피사체 GIS 확인 아님.' if not coords else None),
        license_attribution=attribution,changes_notice=lic['changes_notice'],share_alike=lic['share_alike'],third_party_content_notes=lic['third_party_content_notes'],
        noncommercial_source_detected=nc,nofop_source_category=nofop,rights_status='conditional_pending_third_party_review' if nofop else 'photo_license_metadata_checked_third_party_rights_not_blanket_cleared',
        photo_capture_year=a.get('photo_capture_year'),checks=checks,pass_metadata_all=all(checks.values())))
duplicates=dict(byte_identical=[v for v in hashgroups.values() if len(v)>1],decoded_pixels_identical=[v for v in pixelgroups.values() if len(v)>1],
    perceptual_near_pairs=[dict(a=a,b=b,dhash_distance=(dhashes[a]^dhashes[b]).bit_count()) for i,a in enumerate(dhashes) for b in list(dhashes)[i+1:] if (dhashes[a]^dhashes[b]).bit_count()<=3],
    scope='SHA256/EXIF적용 RGB해시/dHash64. dHash는 유사 후보만 탐지하며 다른 시점의 같은 장소까지 완전 배제하는 검사가 아님.')
save('followup_photo_ledger.json',dict(selected_manifest=str(selected),selected_manifest_sha256=sha(pb),selected_at=selected_at,rows=ledger,duplicates=duplicates,
    v1_v2_comparison=replacement_comparison,unchanged17_reuse='이전 열람 contact sheet/메타와 v2 동일행/실물해시 전수 확인만 재사용. 교체3장만 새 개별시각 검수.'))
failed=[dict(region_id=x['region_id'],failed=[k for k,v in x['checks'].items() if not v]) for x in ledger if not x['pass_metadata_all']]
print(json.dumps(dict(selected=selected.name,card_pass=[(c['asset_id'],c['pass_all']) for c in newcards],metadata_failed=failed,duplicates=duplicates,
    nofop=[r['region_id'] for r in ledger if r['nofop_source_category']]),ensure_ascii=False))

findings=[]
for r in ledger:
    if r['nofop_source_category']:
        findings.append(dict(issue_id='QA-MEDIA-NOFOP-'+r['region_id'],scene_id=r['scene_ids'],timecode=None,severity='required',
            문제='선정 사진 원문에 NoFoP-South Korea가 있어 사진가 라이선스와 별개인 제3자 권리 추가검토 상태를 유지해야 함.',
            evidence=dict(source_page=r['source_page'],source_snapshot=r['source_snapshot'],categories=r['source_categories'],file_sha256=r['sha256']),
            수정안='대체 v2가 확정되면 해당 행만 재검수하거나, 실제 본편 구도별 별도 권리검토 근거를 남긴 뒤 사용. 원문 태그/De minimis·Incidental 분류 확인을 모든 권리 해결로 해석하지 않음.',
            owner='visual / director',status='conditional_pending_rights_review',checked_revision=dict(manifest_sha256=sha(pb),photo_sha256=r['sha256']),
            impact='자료팩 메타 확인은 완료할 수 있지만 이 사진의 무조건 본편 채택 승인은 보류.'))
for r in ledger:
    if not r['pass_metadata_all']:
        findings.append(dict(issue_id='QA-MEDIA-METADATA-'+r['region_id'],scene_id=r['scene_ids'],timecode=None,severity='required',문제='사진 실물/원문 메타 검증 불일치',
            evidence=dict(failed=[k for k,v in r['checks'].items() if not v],file=r['file']),수정안='해당 불일치 필드 또는 사진을 담당자가 수정하고 변경행만 재검수.',owner='visual',status='open',
            checked_revision=dict(manifest_sha256=sha(pb),photo_sha256=r['sha256'])))
for c in newcards:
    if not c['pass_all']:
        findings.append(dict(issue_id='QA-MEDIA-CARD-'+c['asset_id'],scene_id=c['asset_id'],timecode=None,severity='required',문제='분석카드 값/비례 측정 불일치',evidence=c,
            수정안='표시값/도형을 지정 입력에 맞춰 수정하고 이 카드만 재검수.',owner='visual',status='open',checked_revision=dict(sha256=c['sha256'])))
for f in findings:save('issue_'+f['issue_id']+'.json',f)
contact=V/photo['contact_sheet'];read(contact,'실제 열람 v2 교체3장 모아보기; 전체20장으로 세지 않음')
read(V/'photos/TOP20_photo_contactsheet.jpg','실제 열람 v1 모아보기20셀')
for rid in ['R01','R09','R11','R19']:
    a=base_by[rid]
    read(V/a['actual_file'],'실제 view_image 원본 열람: '+rid)
coverage=dict(rank_footer_crops_viewed=4,rank_footer_composite_files_viewed=1,additional_cards_viewed=3,
    photo_contact_sheet_files_actually_viewed=2,photo_contact_sheet_cells_actually_viewed=23,
    photo_files_individually_viewed=['v1:R01','v1:R09','v1:R11','v1:R19','v2:R02','v2:R06','v2:R11'],
    individual_photo_files_actually_viewed=7,active_v2_individual_photo_region_ids=['R01','R02','R06','R09','R11','R19'],
    photo_rows_metadata_checked=20,photo_files_decoded=20,
    actual_view_image_file_count=13,source_pixel_100percent_screen_display='도구 표시 크기로 열람; 모든 원본 픽셀을 화면1:1비율로 전수 확인한 것은 아님. R02v2는3840×2880→3669×2752 도구표시 리사이즈.',
    sampled_mp4_frames=0,continuous_playback=False,actual_listening=False,render_review='unchecked',new_photo_candidates_not_selected='미검수',
    note='실제13열람파일=footer합본1+분석카드3+v1모아보기1+v1원본4+v2교체모아보기1+v2원본3. 모아보기23셀은 v1/v2 교체중복을 포함. 현재20장 전부 개별 육안검수를 뜻하지 않음.')
report=dict(task_id='qa-top20-v2-media-followup',revision='top20-8min-v2-media-followup-v1',checked_at=NOW,status='completed_with_use_conditions',
    owner='qa',selected_photo_manifest=str(selected),selected_photo_manifest_sha256=sha(pb),photo_v2_present_when_selected=selected.name=='photo_assets_v2.json',
    prior_qa_reuse=dict(inputs=reuse,previous_19_numeric_rows_reaudited=False,previous_20_maps_reaudited=False,old_records_preserved=True),
    footer_review=footer_review,additional_card_ledger=str(Q/'followup_card_ledger.json'),photo_ledger=str(Q/'followup_photo_ledger.json'),
    verdict=dict(footer4='pass',additional_cards3='pass' if all(c['pass_all'] for c in newcards) else 'required',
        photos_file_metadata='pass' if not failed else 'required',photo_rows=20,noncommercial_photo_rows=sum(r['noncommercial_source_detected'] for r in ledger),
        conditional_nofop_rows=[r['region_id'] for r in ledger if r['nofop_source_category']],
        required_open=len([f for f in findings if f['severity']=='required']),unconditional_final_media_approval=False),
    findings=findings,coverage=coverage,
    sample_observations=dict(R01='1600×600, 공사 흔적이 있는 과거 와이드 전경. 현재/2024 전경 단정 금지·비율유지 패널.',
        R11='v1 세로 당현천·상계백병원 사진. EXIF방향 적용 후2268×4032. 16:9 강제 늘림/무리한크롭 제외.',
        R19='1280×768, 신내역 표지와 정류장 확인. 전체화면 확대·추가줌 제한, 작은 패널 권장.',
        R09='3000×1688 겨울 야간 판교. 2016 자료사진/계절 표시를 유지.'),
    source_evidence=dict(source_snapshot_count=20,live_source_pages_checked=[
        dict(region_id='R01',url='https://www.insiseol.or.kr/park/cheongna/facility/lake.jsp',web_lines=[785,787,833,839],result='시설 주소·공공누리 출처표시 마크'),
        dict(region_id='R02',url='https://commons.wikimedia.org/wiki/File:Lotte_World_morning_view_8.jpg',web_lines=[380,392],result='Incidental views와NoFoP분류'),
        dict(region_id='R06',url='https://commons.wikimedia.org/wiki/File:Teheran-ro_Yeongdong-daero_crossing_6.jpg',web_lines=[334,339],result='NoFoP·De minimis분류'),
        dict(region_id='R11',url='https://commons.wikimedia.org/wiki/File:Danghyeoncheon_and_Inje_University_Sanggye_Paik_Hospital.jpg',web_lines=[278,286],result='Nowon-gu·NoFoP·CCBYSA3분류')],
        scope='v2 최신20행: Commons API17건·인천시설공단1건·서울연구원 개별HTML2건과 기관 저작권 정책을 대조. v1 NoFoP3원문도 별도 확인해 이전 조건부 이력으로 분리. 사진저작권 허락과 화면 속 제3자 권리의 최종 정리는 구분.'),
    replacement_review=dict(changed_region_ids=['R02','R06','R11'],unchanged_rows=17,old_nofop_rows='v1 이력으로 조건부 유지. 현재 선택은 교체3장으로 분리.',
        v2_scope='개별허락·귀속문·실물·장소를 확인한 이번 수변/산책로 구도. 원문에 NoFoP 표시가 없다는 이유만으로 모든 제3자 권리를 해결했다고 판단하지 않음.',
        R02='석촌호수 수면/벚꽃과 주변 건물 원경. 배경 건축물을 주피사체로 확대하는 사용은 미검수.',
        R06='양재천 영동4교 수변길. 2019년12월 촬영·2020사업 저작권 귀속을 구분.',R11='경춘선숲길과 옛 철로. 기관 제공 모자이크 유지; 인물 주피사체 확대/복원 미승인.'),
    out_of_scope=['기존 통계19행 및 지도20개 재검수','대본script_v2/v3 전체 검수','현재 가격/매물 적합성','원거래 전체 재집계','모든 제3자 권리 해소','영상·자막·최대줌 렌더 검수','연속재생·실제음성청취','디자인/폰트채택 완료'])
save('media_followup.json',report)
save('media_followup_handoff.json',dict(task_id=report['task_id'],role='qa',status=report['status'],input_revisions=dict(photo_manifest=str(selected),sha256=sha(pb)),
    outputs=[str(Q/n) for n in ['media_followup.json','followup_card_ledger.json','followup_photo_ledger.json','media_followup_input_manifest.json']],
    affected_scene_ids=sorted({s for a in assets for s in a['scene_ids']}),checks=report['verdict'],open_issue_ids=[f['issue_id'] for f in findings],
    next_role='director → writer/editor(최신사진 장소·귀속문·사용구도 조건 인계; 본편 반영 후 해당 구도 별도 QA)',
    handoff_summary='footer4개 보완·새분석카드3장 값/분모/표본/잘림/비례 확인. 사진v2 최신20행: 불변17동일행·실물해시·기존시각근거재사용, 교체R02/R06/R11 원문허락·귀속문·실물·구역 확인. v1모아보기20셀+원본4장 및 v2교체모아보기3셀+원본3장 열람. 사진가허락과 모든 제3자권리해결을 구분하고 현 구도/기관모자이크 조건 유지. 기존19행/20지도/대본전체 재검수생략. 실제영상/청취 미수행. 기존findings/핸드오프 보존.'))
for p,h in protected.items():assert sha(Path(p).read_bytes())==h
stability=[dict(path=p,unchanged=sha(Path(p).read_bytes())==d['sha256']) for p,d in manifest.items()]
save('media_followup_input_manifest.json',dict(checked_at=NOW,inputs=list(manifest.values()),stability=stability,protected_prior_records=protected,
    all_inputs_unchanged=all(x['unchanged'] for x in stability),validator_sha256=sha(Path(__file__).read_bytes())))
print(json.dumps(dict(report=str(Q/'media_followup.json'),required=len(findings),protected_prior_unchanged=True,inputs=len(manifest),selected_photo_manifest=str(selected)),ensure_ascii=False))
