"""Verify the frozen photo files, build the photo ledger and review contact sheet."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_photos import ROOT, PHOTOS, EVIDENCE, plain
from download_photos import SELECTED

EPISODE=ROOT.parents[1]
RESEARCH=EPISODE/'research'/'top20-8min-v2'
PLACES={
1:('청라호수공원','인천광역시 서해구 크리스탈로 131','공식 시설 페이지의 청라호수공원 항공 실사와 소재지. 2024 통계권역은 옛 인천 서구, 현재 사진 소재지는 서해구.'),
2:('석촌호수·롯데월드타워','서울특별시 송파구 잠실동 일대','File 설명·석촌호수/롯데월드타워 분류·카메라 좌표 및 호수와 타워가 함께 보이는 픽셀 대조.'),
3:('삼송로 도시풍경','경기도 고양시 덕양구 삼송로 일대','File 설명 Samsong-ro, Goyang 및 삼송-지축 파일명. 고양시 삼송1동 소개·관내시설의 삼송로/덕양구 표기와 대조. 정밀 카메라 좌표는 없음.'),
4:('마곡 서울식물원 야외','서울특별시 강서구 마곡동로 161 일대','서울식물원 원문 설명·마곡 카메라 좌표와 실제 야외 정원·온실 배경을 대조. 온실 내부 사진 아님.'),
5:('부평역 외관과 역앞 거리','인천광역시 부평구 부평역 일대','File 설명 부평역 역사·Bupyeong Station 분류·카메라 좌표와 역사 전면 실사 대조.'),
6:('테헤란로·영동대로 교차로','서울특별시 강남구 삼성동 일대','File 설명의 Gangnam 교차로·좌표와 도로/업무지구 실사 대조.'),
7:('고덕역 4번출구와 주변 가로','서울특별시 강동구 고덕역 일대','File 설명에 Gangdong-gu와 고덕역 4번출구 명시. 좌표와 출구 표지·주변 가로 실사 대조. 신축 고덕 단지 현황 사진 아님.'),
8:('여의도 스카이라인','서울특별시 영등포구 여의도','원문 설명과 Yeouido 분류·타워군과 한강 원경 대조. 카메라 위치의 구가 아니라 화면에 묘사된 여의도를 설명.'),
9:('판교테크노밸리 겨울 거리','경기도 성남시 분당구 삼평동 판교테크노밸리','File 설명 눈오는 판교4·Pangyo Techno Valley 분류·좌표(37.402017,127.106722)를 판교테크노밸리 공식 소재 권역과 대조. 눈 쌓인 거리·업무빌딩 실사. 2016년 겨울 자료사진이며 2024/2026 현재 모습 아님.'),
10:('문학경기장 외관','인천광역시 미추홀구 문학경기장 일대','File 설명이 미추홀구 문학경기장 외관으로 명시. 카메라 좌표·구장 외관 대조. 인천축구전용경기장 후보는 제외.'),
11:('상계·중계 경계 당현천과 상계백병원 배경','서울특별시 노원구 상계동·중계동 일대','File 설명이 노원구의 당현천과 상계·중계 경계를 명시. 하천·상계백병원 배경 대조. 다른 구의 중랑천 사진 아님.'),
12:('광교 원천호수 수변','경기도 수원시 영통구 광교호수공원 원천호수 구간','광교호수공원 File 설명·수변 픽셀 및 원문 추정 카메라 좌표(37.28223356,127.06447205)를 대조. 정밀 측량 좌표 아님. 배경 모든 건물을 영통구 소재로 단정하지 않음.'),
13:('권선동 수원종합버스터미널 일대 도시풍경','경기도 수원시 권선구 경수대로 270','File의 수원종합버스터미널 설명·전면 가로 실사. 수원시 공식 교통 안내 및 공공와이파이 주소 목록의 권선구 경수대로270(권선동)과 대조. 수원역/팔달구 사진 아님. 호매실로 표기하지 않음.'),
14:('진관동 은평뉴타운','서울특별시 은평구 진관동','File 설명이 Jingwan-dong, Eunpyeong-gu의 Eunpyeong Newtown 경관을 명시. 아파트군 실사 대조. 한옥마을이라고 표기하지 않음.'),
15:('신도림역 1번출구와 주변 가로','서울특별시 구로구 신도림역 일대','File 설명이 Guro-gu, Sindorim Station entrance1을 명시. 출구 표지·주변 건물 대조. 가산동 G밸리 사진 아님.'),
16:('소래습지생태공원 갈대밭·탐방데크','인천광역시 남동구 소래로154번길 77','File 설명의 남동구 주소·좌표를 research2 공식 주소와 대조. 갈대·데크 실사 확인. 시흥 갯골생태공원 아님.'),
17:('송도 센트럴파크 수로·도시풍경','인천광역시 연수구 송도동 센트럴파크','File 설명 2021년10월 송도센트럴파크 전경·분류를 research2 공식 장소와 대조. 수로·송도 건물군 실사 확인.'),
18:('구성역 5번출구 주변 거리','경기도 용인시 기흥구 구성역 일대','File 설명·Guseong Station 분류·좌표(37.299253,127.102981), 5번출구 주변 실제 가로 대조. 동백호수로 표기하지 않음.'),
19:('신내역 3번출구 버스정류장 일대','서울특별시 중랑구 신내역 일대','File 설명 신내역3번출구 버스정류장·좌표(37.61326533,127.10338667)와 실제 출구/버스정류장 대조. 중랑천 타구 사진 아님.'),
20:('부천 상동 도시 가로','경기도 부천시 원미구 상동','File 설명 Street in Sangdong District, Bucheon·좌표(37.5034,126.7516)와 실제 상동 가로 대조. 부천중앙공원/상동호수공원으로 표기하지 않음.'),
}
SUPPLEMENTAL_GEO={
3:[('고양시 삼송1동 소개','https://www.goyang.go.kr/dong/dong01/dong01_4/dong01_4_5/dong01_4_5_tab1.jsp'),('삼송1동 관내시설','https://www.goyang.go.kr/dong/user/bbs/BD_selectBbsList.do?q_bbsCode=1072&q_clCode=7')],
9:[('판교테크노밸리 공식 입주기업 주소','https://www.pangyotechnovalley.org/base/company/list?menuLevel=3&menuNo=39')],
13:[('수원시 공식 관광 교통안내','https://www.suwon.go.kr/webcontent/ckeditor/2022/7/18/59ea7803-2adb-4b2b-982f-4610e1e3e41e.pdf'),('수원시 공공와이파이 장소 주소','https://www.suwon.go.kr/sw-www/sw-share/sw-share02/sw-share02-04/sw-share02-04-01.jsp')],
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return p.relative_to(ROOT).as_posix()
def write_json(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def suggestion_rows(v):
    if isinstance(v,dict):
        if 'image_suggestions' in v: yield v
        else:
            for x in v.values():yield from suggestion_rows(x)
    elif isinstance(v,list):
        for x in v:yield from suggestion_rows(x)

def main(reviewed):
    now=datetime.now(timezone.utc).isoformat()
    ranking_path=RESEARCH/'top20.json'
    ranking=json.loads(ranking_path.read_text(encoding='utf-8-sig'))
    peers={};inputs=[{'path':str(ranking_path.relative_to(EPISODE)).replace('\\','/'),'sha256':sha(ranking_path),'used_scope':'TOP20 지역ID·장면ID·통계기준일'}]
    for name in ['ranks01_10_facts.json','ranks11_20_facts.json']:
        path=RESEARCH/name
        if not path.exists():continue
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        for row in suggestion_rows(data): peers[row['rank']]=row['image_suggestions']
        inputs.append({'path':str(path.relative_to(EPISODE)).replace('\\','/'),'sha256':sha(path),'used_scope':'image_suggestions만 장소·주소·권리 제한 대조; 공식 사진 권리는 승계하지 않음'})
    assets=[];all_files=[]
    for region in ranking['regions']:
        rank=region['rank'];place,address,geo=PLACES[rank]
        if rank==1:
            meta=json.loads((EVIDENCE/'R01_official_metadata.json').read_text(encoding='utf-8'))
            receipt=next(x for x in meta['files'] if x['width']>=1200)
            title=receipt['title'];author=meta['author'];author_html=author
            license='공공누리 제1유형';version=meta['license_version'];license_url=meta['license_url']
            source_page=meta['source_page'];permalink=source_page;original_url=receipt['url'];metadata_snapshot='photos/evidence/R01_official_metadata.json'
            raw_date=meta['date_note'];year=None;coords=[];categories=[];source_desc=place;source_credit=author
            api_dims=None;api_sha1=None;creator_links=[]
        else:
            mp=EVIDENCE/f'R{rank:02d}_selected_commons.json'
            data=json.loads(mp.read_text(encoding='utf-8'));p=data['page'];ii=p['imageinfo'][0];ex=ii['extmetadata'];val=lambda k:plain(ex.get(k,{}).get('value',''))
            receipt=json.loads((EVIDENCE/f'R{rank:02d}_download_receipt.json').read_text(encoding='utf-8'))
            title=p['title'][5:];author=val('Artist');author_html=ex.get('Artist',{}).get('value','')
            if rank==12:author='Jocelyndurrey'
            license=val('LicenseShortName');version='1.0' if license=='CC0' else (re.search(r'\d\.\d',license).group() if re.search(r'\d\.\d',license) else '해당 없음(PD-self 공개 헌납)')
            license_url=val('LicenseUrl') or 'https://commons.wikimedia.org/wiki/Template:PD-self'
            source_page=ii['descriptionurl'];rev=p['revisions'][0]['revid'];permalink=f'https://commons.wikimedia.org/w/index.php?oldid={rev}'
            original_url=ii['url'];metadata_snapshot=relative(mp);raw_date=val('DateTimeOriginal')
            years=re.findall(r'(?:19|20)\d{2}',raw_date);year=int(years[0]) if years else None
            coords=p.get('coordinates',[]);categories=[x['title'] for x in p.get('categories',[])]
            source_desc=val('ImageDescription');source_credit=val('Credit');api_dims=[ii['width'],ii['height']];api_sha1=ii.get('sha1')
            creator_links=re.findall(r'href="([^"]+)"',author_html)
        actual=(ROOT/receipt['path']).resolve()
        assert actual.is_relative_to(PHOTOS.resolve()),actual
        with Image.open(actual) as im:
            im.load();raw_dims=list(im.size);orientation=im.getexif().get(274,1);display=ImageOps.exif_transpose(im);dims=list(display.size)
        assert min(dims)>0 and max(dims)>=1200,(rank,dims)
        digest=sha(actual);assert digest==receipt['sha256'],rank
        original_hash_match=None
        if rank!=1 and receipt.get('original') and api_sha1:
            source_sha1=hashlib.sha1(actual.read_bytes()).hexdigest();original_hash_match=source_sha1==api_sha1
            assert original_hash_match,(rank,'source SHA1 mismatch')
        is_cdn=not receipt.get('original',False)
        changes='Wikimedia CDN의 비율 유지 축소 사본. 로컬 크롭·색보정·합성·생성보정 없음.' if is_cdn else '게시된 파일 바이트 그대로 저장. 로컬 크롭·색보정·합성·생성보정 없음.'
        usage='상업 이용·변형 가능. 작가·제목·출처·라이선스 링크·변형 여부 표시.'
        if 'BY-SA' in license:usage+=' 편집·변형본을 배포할 때 동일 또는 호환 라이선스 조건을 유지하고 최종 영상 결합 방식은 총괄/QA가 검토.'
        elif license in ['CC0','Public domain']:usage='저작권상 상업 이용·변형 가능. 기록용 출처·작가 표기를 보존.'
        elif rank==1:usage='공공누리 제1유형: 출처 표시, 상업 이용 및 변형 가능. 기관이 이용자를 후원·보증하는 것처럼 표시하지 않음.'
        citation=f'사진: {author}, 「{title}」, {license}{" 1.0" if license=="CC0" else ""}. 출처: {source_page} / 이용조건: {license_url} / 변형: {changes}'
        notes=[]
        if 'Category:NoFoP-South Korea' in categories:notes.append('원문에 NoFoP-South Korea 분류가 있음. 사진가의 CC 허락과 별개인 건축물·미술저작물 권리는 최종 사용 구도에서 확인. 원문 De minimis/Incidental 분류도 함께 보존.')
        if rank==1:notes.append('촬영일 미표시. 공사·미개발지 흔적이 보이는 과거 자료사진이므로 2024 또는 2026 현재 전경으로 단정하지 않음. 1600×600 와이드 사진은 비율 유지 패널 사용 권장.')
        if rank==11:notes.append('EXIF 회전 태그가 있는 세로 사진. 저장 픽셀과 표시 방향 해상도를 구분. 16:9 화면에 비율 유지 패널로 배치.')
        if rank==9:notes.append('2016년2월 촬영한 겨울 야경 자료사진. 계절·촬영연도 표시를 유지하며 현재 날씨나 통계 기준시점의 현장 모습으로 제시하지 않음.')
        if rank==19:notes.append('표준 사본 1280×768. 1920×1080 전체 화면 확대/추가 줌을 피하고 지도 옆 사진 패널로 사용 권장.')
        if rank in (7,13,15,19):notes.append('과거 촬영 자료. 역·가로의 2026년 현 상태·운영·공급 완료를 증명하지 않음.')
        peer=peers.get(rank,[])
        geo_peer=[]
        for s in peer:
            geo_peer.append({'place_name':s.get('place_name'),'address':s.get('address'),'source_url':s.get('place_source_url') or s.get('official_photo_candidate_url'),
                'rights_not_inherited':True,'reference_note':'장소·구역 대조 참고. 이 기관 후보 사진의 이용허락을 현재 Commons 사진에 적용하지 않음.'})
        asset={
            'asset_id':f'PHOTO_R{rank:02d}','region_id':region['region_id'],'scene_ids':[region['scene_id']],
            'rank':rank,'statistical_region_2024':f'{region["province"]} {region["region"]}',
            'statistic_reference_date':'2024-11-01','statistic_year':2024,
            'type':'real_place_photo','purpose':'대표 지역·생활권 소개용 실사. 단지 입지 평가·신혼부부 실거주·추천 수익의 증거 아님.',
            'actual_place':place,'address_or_area':address,'photo_capture_year':year,'photo_capture_date_raw':raw_date,
            'source_or_prompt':{'provider':'인천시설공단' if rank==1 else 'Wikimedia Commons','title':title,'author':author,
                'author_html_original':author_html,'author_urls':creator_links,'file_page':source_page,'fixed_revision_url':permalink,
                'original_image_url':original_url,'actual_download_url':receipt.get('download_url',receipt.get('url')),
                'metadata_snapshot':metadata_snapshot,'original_credit':source_credit,'original_description':source_desc},
            'license':{'name':license,'version':version,'license_url':license_url,'copyright_permission_basis':'개별 File 원문의 CC/PD-self 표기' if rank!=1 else '청라호수공원 시설 원문 페이지의 kogl_type01.gif 출처표시 마크',
                'commercial_copyright_use':True,'adaptation_allowed':True,'share_alike':'BY-SA' in license,'usage_conditions_ko':usage,
                'attribution_ko':citation,'changes_notice':changes,'third_party_content_notes':notes},
            'dimensions':{'width':dims[0],'height':dims[1],'stored_pixel_width':raw_dims[0],'stored_pixel_height':raw_dims[1],
                'exif_orientation':orientation,'api_original_dimensions':api_dims,'long_edge_at_least_1200':True},
            'actual_file':relative(actual),'absolute_file':actual.as_posix(),'bytes':actual.stat().st_size,'sha256':digest,
            'download_variant':receipt.get('variant','original'),'is_original_published_file':not is_cdn,'upscaled':False,
            'ai_generated':False,'AI_표기':'해당 없음: 출처가 있는 실제 장소 사진',
            'geography_verification':{'status':'named_place_match_checked','basis':geo,'coordinates_from_source':coords,
                'coordinates_role':'원문 카메라 위치; 촬영 대상의 대표 중심점으로 사용하지 않음','gis_boundary_point_in_polygon_performed':False,
                'research2_place_reference_only':geo_peer,'supplemental_official_sources':[{'title':t,'url':u} for t,u in SUPPLEMENTAL_GEO.get(rank,[])]},
            'inspection':{'decode_passed':True,'hash_verified':True,'original_commons_sha1_match':original_hash_match,
                'pixel_visual_review':reviewed,'review_scope':'대표2장 패널·전체20장 contact sheet 및 최종 교체 판교 원본/청라 게시파일의 실제 픽셀 확인. 불변 사진은 기존 시각 점검 재사용.' if reviewed else '전체 contact sheet 시각 확인 대기',
                'source_license_checked':True,'status':'self_checked_pending_independent_director_QA' if reviewed else 'pending_final_visual_review',
                'independent_qa_performed':False,'notes':notes},
        }
        assets.append(asset);all_files.append(actual)
    # The contact sheet uses only the 20 primary records, never filename glob counts.
    cellw,cellh=420,365
    sheet=Image.new('RGB',(cellw*5,cellh*4+55),'#20252b');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,a in enumerate(assets):
        x=i%5*cellw;y=i//5*cellh
        im=ImageOps.exif_transpose(Image.open(ROOT/a['actual_file'])).convert('RGB');im.thumbnail((404,277))
        sheet.paste(im,(x+(cellw-im.width)//2,y+80+(277-im.height)//2))
        draw.text((x+9,y+7),f'{a["region_id"]}  {a["statistical_region_2024"]}',font=font,fill='white')
        short=a['actual_place'][:22]
        draw.text((x+9,y+31),short,font=font,fill='#dae3ec')
        draw.text((x+9,y+55),f'{a["dimensions"]["width"]}×{a["dimensions"]["height"]} / 촬영 {a["photo_capture_year"] or "미상"}',font=font,fill='#b4c7d6')
    draw.text((12,cellh*4+15),'검수용 축소본 · 통계 2024-11-01 / 촬영일 별도 · AI 없음 · 개별 저작자·이용조건: photo_sources.md',font=font,fill='white')
    contact=PHOTOS/'TOP20_photo_contactsheet.jpg';sheet.save(contact,quality=93)
    supplemental=[]
    selected_set={p.resolve() for p in all_files}
    for p in PHOTOS.glob('R*.jpg'):
        if p.resolve() not in selected_set and re.match(r'^R\d{2}_',p.name):
            candidate_dir=PHOTOS/'candidates';candidate_dir.mkdir(exist_ok=True)
            dst=candidate_dir/p.name
            assert dst.resolve().is_relative_to(PHOTOS.resolve())
            if not dst.exists():p.rename(dst)
    for p in sorted((PHOTOS/'candidates').glob('*.jpg')):
        supplemental.append({'file':relative(p),'status':'non_primary_candidate_or_low_resolution_reference','use_in_video':False,
            'source_evidence_note':'동일 R번호의 photos/evidence 검색/earlier/official_metadata 원문에 후보 출처와 권리 기록. 대표사진20장 수에 포함하지 않음.'})
    manifest={'revision':'top20-8min-v2','owner':'visual/photos','created_utc':now,
        'brief':{'request':'TOP20 각 구의 사용자 지정 실제 장소 사진 최소1장. 상업 이용·변형 가능한 개별 사용권·실물 파일·지역 일치 확인.',
            'photo_count_target':20,'visual_treatment':'원본 비율·색 유지. 숫자·텍스트·AI·지도·분양 조감도 대체 없음. 영상 배치·줌·자막은 이번 범위 밖.',
            'resolution':'장변1200px 이상 우선; 확대하지 않음','time_prefix':'timing lock 미확정; region_id 연결, 시간 접두사 없음',
            'scope':'photos/**, photo_assets.json, photo_sources.md, photo_handoff.json, 사진 수집 스크립트만 수정'},
        'input_versions':inputs,'statistical_reference_date':'2024-11-01','photo_dates_are_separate':True,
        'primary_photo_count':len(assets),'covered_region_count':len(set(a['region_id'] for a in assets)),
        'missing_regions':[],'assets':assets,'contact_sheet':relative(contact),'non_primary_files':supplemental,
        'constraints':['실제 장소 대표 이미지이며 신혼부부의 거주·전입 원인·단지 입지·현재 개발 상태를 증명하지 않음.',
            '사진가의 명시된 재사용 허락을 확인. 화면 속 건축물·상표·인물 등 별도 권리는 개별 주의사항과 최종 사용 구도에서 검토.',
            '독립 검수·실제 영상 재생·음성 청취·업로드는 미실행.'],
        'collection_issues':[{'issue':'Commons 원본 파일 서버 HTTP429','resolution':'Commons 원본6장+기관 게시파일1장 보존; 나머지13장은 서버 안내 표준3840px/1280px CDN 사본으로 확보. 원본과 구분 기록.','unresolved':False},
            {'issue':'일부 Commons 서울식물원 후보의 CC표기와 변형금지 문구 충돌','resolution':'korea.net 후보 제외, 별도 개인촬영 CC BY4.0 실물로 교체.','unresolved':False},
            {'issue':'Pangyo Techno Valley 2.jpg GPS가 서울로 표시','resolution':'해당 후보 미사용. 원문 설명·좌표가 판교와 일치하는 CC BY3.0 겨울 거리 원본으로 교체. 커피컵이 큰 U-Space 사진도 비대표 후보로 분리.','unresolved':False}],
    }
    write_json(ROOT/'photo_assets.json',manifest)
    md=['# TOP20 실제 장소 사진 원장','',f'버전: top20-8min-v2 · 통계 기준일: 2024-11-01 · 대표 사진: {len(assets)}장/20지역','',
        '사진은 지역 소개용이며 신혼부부 실거주·단지 입지·투자 판단의 증거가 아니다. 사진 촬영일과 통계 기준일은 서로 다르다. 공식 장소 후보의 이용조건을 Commons 사진의 사용권으로 승계하지 않았다.','',
        '담당 소유 파일만 작성했다. 지도·데이터카드·공통 state/scenes·research 원본은 수정하지 않았다.','',
        f'미리보기: [{contact.name}]({relative(contact)}) · 기계 판독 원장: [photo_assets.json](photo_assets.json)','',
        '| ID / 장면 | 통계구역 | 실제 장소 | 파일 해상도(표시 방향) | 촬영연도 | 통계기준 | 이용조건 |',
        '|---|---|---|---|---|---|---|']
    for a in assets:
        md.append(f'| {a["region_id"]} / {a["scene_ids"][0]} | {a["statistical_region_2024"]} | {a["actual_place"]} | {a["dimensions"]["width"]}×{a["dimensions"]["height"]} | {a["photo_capture_year"] or "미상"} | 2024-11-01 | {a["license"]["name"]} |')
    md+=['','## 파일별 출처·귀속·장소 확인','']
    for a in assets:
        s=a['source_or_prompt'];lic=a['license'];md += [f'### {a["asset_id"]} — {a["actual_place"]}','',
            f'- 실물: [{a["actual_file"]}]({a["actual_file"]})',f'- 주소/권역: {a["address_or_area"]}',
            f'- 제목: {s["title"]} / 작가: {s["author"]}',f'- 원문: [{s["title"]}]({s["file_page"]})',
            f'- 고정 원문: {s["fixed_revision_url"]}',f'- 원본 URL: {s["original_image_url"]}',
            f'- 실제 저장 URL: {s["actual_download_url"]}',f'- 라이선스: {lic["name"]}, 버전 {lic["version"]} · {lic["license_url"]}',
            f'- 촬영 시점(원문): {a["photo_capture_date_raw"]} / 통계: 2024-11-01',f'- 저장 방식: {a["download_variant"]}, 업스케일 없음',
            f'- 변형 표시: {lic["changes_notice"]}',f'- 사용조건: {lic["usage_conditions_ko"]}',
            f'- 장소 검증: {a["geography_verification"]["basis"]}',f'- 원문 증거: [{s["metadata_snapshot"]}]({s["metadata_snapshot"]})',
            f'- SHA256: `{a["sha256"]}`',f'- 붙여넣을 귀속문: {lic["attribution_ko"]}']
        for n in a['inspection']['notes']:md.append('- 편집 주의: '+n)
        for u in a['geography_verification']['supplemental_official_sources']:md.append(f'- 장소 보강 근거: [{u["title"]}]({u["url"]})')
        md.append('')
    md+=['## 검수 범위와 다음 단계','',
        '전20장 파일 디코드·표시 해상도·SHA256·원문 라이선스·장소명/좌표/설명을 확인했다. 원본 Commons 성공 파일은 원문 SHA1과 대조했다. EXIF 회전 방향을 존중해 contact sheet를 만들었다.',
        '대표 2장과 전체 contact sheet의 실제 픽셀 자체 점검은 '+('완료했다.' if reviewed else '현재 대기 중이다.'),
        '이 자료의 자체 확인은 총괄/독립 QA를 대신하지 않는다. 촬영 방향의 측량·모든 건물의 행정경계 GIS 검사·최종 영상의 재생/청취는 하지 않았다.',
        'R01 청라는 촬영일 미상, 1600×600. R11 노원은 세로 사진. R19 신내는1280×768. 해당 이미지는 지도 옆 패널 등 비율 유지 배치가 적합하다.',
        'CC BY-SA 자료는 해당 변형본의 동일조건 공유를 유지하고 공개본 결합 구도·귀속·건축물 등 별도 권리 표시를 총괄/QA가 확인해야 한다. 각 사진을 해당 기관/작가가 채널을 보증한 자료로 표현하지 않는다.',
        '비대표 후보/저해상도 참고 파일은 photo_assets.json의 non_primary_files로 명시했으며 영상 삽입 대상으로 세지 않았다.','']
    (ROOT/'photo_sources.md').write_text('\n'.join(md),encoding='utf-8')
    handoff={'revision':'top20-8min-v2','owner':'visual/photos','status':'photo_pack_self_checked' if reviewed else 'photo_pack_visual_review_pending',
        'outputs':{'manifest':str((ROOT/'photo_assets.json').relative_to(EPISODE)).replace('\\','/'),
            'sources':str((ROOT/'photo_sources.md').relative_to(EPISODE)).replace('\\','/'),'photos':str(PHOTOS.relative_to(EPISODE)).replace('\\','/'),
            'contactsheet':str(contact.relative_to(EPISODE)).replace('\\','/')},'input_versions':inputs,
        'counts':{'primary_photos':len(assets),'regions':20,'missing':0,'commons_originals':sum(a['is_original_published_file'] for a in assets if a['rank']!=1),
            'official_site_published_files':1,'commons_standard_cdn_copies':sum(not a['is_original_published_file'] for a in assets)},
        'validation':{'all_files_exist':True,'all_decode':True,'all_hashes_match_receipts':True,'all_long_edges_at_least_1200':True,
            'individual_copyright_licenses_checked':True,'named_region_place_matched':True,'visual_self_review':reviewed,'independent_qa':False,
            'maps_or_cards_modified':False,'state_scenes_research_modified':False,'video_rendered':False},
        'affected_scene_ids':[a['scene_ids'][0] for a in assets],
        'unresolved':['R01 촬영일 미상·600px 높이, R11 세로 사진, R19 1280px 사본: 비율 유지 패널 권장.',
            'CC BY-SA 귀속/변형본 조건과 원문에 있는 NoFoP/De-minimis/Incidental 표시를 최종 공개 구도에서 총괄/QA 확인.'],
        'network_blockers':'현재 미확보 지역 없음. Commons 원본429는 서버 권장 표준 크기 CDN으로 대응했고 원본과 구분.',
        'next_owner':'director: 지도/자료안내 통합 및 독립 QA; 편집·렌더는 후속 승인 범위에서 별도',
        'peer_communication':'직접 peer 메시지 도구 없음. 이 photo_handoff.json으로 총괄에게 전달.',
        'summary':'20지역 대표 실사20장 확보. 각 자산에 출처·작가·촬영일·통계2024·라이선스·URL·변형표시·귀속문·실제해상도·해시 기록. Commons원본6장/기관게시파일1장/CDN13장. 지도·카드·공통파일 수정 없음.'}
    write_json(ROOT/'photo_handoff.json',handoff)
    print(json.dumps({'photos':len(assets),'regions':20,'contactsheet':str(contact),'visual_reviewed':reviewed,'total_photo_bytes':sum(a['bytes'] for a in assets)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviewed',action='store_true');args=p.parse_args();main(args.reviewed)
