"""Offline artifact verification and scoped handoff generation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parent
EP=ROOT.parents[2]
OLD=EP/'visual/top20-8min-v2'
TASK='part1-clean-maps-photo-transitions-v1'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def write(name,data):(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')

NOTES={
 20:'16:9 중앙 크롭 확인. 왼쪽의 2번출구·부천종합운동장 표지 보존. 2015년 역 출입구 자료로 표기.',
 19:'16:9 중앙 크롭 확인. 상단 신내역 간판 보존. 2013년 당시 공사 흔적이 있는 역사 사진; 촬영연도 표기.',
 18:'16:9 중앙 크롭 확인. 구성역 표기를 중앙에 보존. 2026-07-05 촬영 당시 역 5번출구 엘리베이터 사진.',
 17:'16:9 중앙 크롭 확인. 수로·교량·고층건물의 관계를 유지. 2015년 송도 경관; 특정 단지 이름 추가 금지.',
 16:'16:9 중앙 크롭 확인. 풍차 3기와 일출 하늘 보존. 실루엣이 의도된 역광 사진; 과도한 확대 피함.',
 15:'16:9 중앙 크롭 확인. 상단 신도림역 간판·역사 외관 보존. 2015년 당시 철도 생활권 자료.',
 14:'16:9 중앙 크롭 확인. 구파발천 하천식생·산책로 근경. 뉴타운 아파트 전경으로 표기하지 않음.',
 13:'16:9 중앙 크롭 확인. 권선구청과 가로·녹지 맥락 보존. 2015년 촬영 당시 지역 행정시설 경관.',
 12:'16:9 중앙 크롭 확인. 광교호수공원 수변·고층 경관의 반영 보존. 2021년 야간 자료; 추가 확대 최소화.',
 11:'16:9 중앙 크롭 확인. 넓은 주거지 맥락 유지. 촬영 당시 노원구 전경이며 원경 모든 건물의 소재 구를 단정하지 않음.',
}

def main():
    rows=read(ROOT/'assets.json');body={a['rank']:a for a in read(OLD/'photo_assets_v2.json')['assets']}
    expected={'rank','region_id','region','actual_place','file','sha256','width','height','author','license_name',
              'license_url','source_url','photo_date','crop_note','distinct_from_existing_body_photo'}
    assert len(rows)==10 and [a['rank'] for a in rows]==list(range(20,10,-1))
    checks=[];credits=[];hashes=set()
    for a in rows:
        r=a['rank'];p=Path(a['file']);receipt=read(ROOT/f'evidence/R{r:02d}_receipt.json')
        assert p.resolve().is_relative_to(ROOT.resolve())
        assert set(a)==expected,(r,set(a)^expected)
        assert digest(p)==a['sha256']==receipt['sha256']
        with Image.open(p) as im:
            im.load();im=ImageOps.exif_transpose(im);assert im.size==(a['width'],a['height'])
        assert a['width']>=1600 and a['height']>=900
        assert a['sha256'] not in hashes;hashes.add(a['sha256'])
        assert a['sha256']!=body[r]['sha256']
        title=receipt['page']['title'].removeprefix('File:')
        assert title!=body[r]['source_or_prompt']['title']
        assert a['distinct_from_existing_body_photo'] is True
        assert all(a[k] for k in ['author','license_name','license_url','source_url','photo_date'])
        assert a['license_name'].startswith(('CC BY ','CC BY-SA ','CC0'))
        a['crop_note']=NOTES[r]
        if r==14:a['actual_place']='진관동 구파발천 산책로·하천 식생'
        ex=receipt['page']['imageinfo'][0]['extmetadata']
        checks.append({'rank':r,'decode':True,'sha256_match':True,'different_source_title_and_hash_from_body':True,
                       'source_evidence':f'evidence/R{r:02d}_receipt.json','source_title':title,
                       'place_evidence_description_html':ex.get('ImageDescription',{}).get('value',''),
                       'source_coordinates':receipt['page'].get('coordinates',[]),
                       'license_and_author_date_from':'원문 imageinfo extmetadata; 로컬 보관본 재사용, 일부 신규 공개 조회',
                       'ai_generated':False,'upscaled':False,'stored_modifications':'게시 원본 또는 공개 CDN 비율 유지 축소본; 로컬 크롭·보정 없음',
                       'pixel_review':'최종 10장 16:9 contact sheet 실제 확인; 독립 QA 아님'})
        credits.append({'rank':r,'region_id':a['region_id'],'title':title,'author':a['author'],
                        'license_name':a['license_name'],'license_url':a['license_url'],'source_url':a['source_url'],
                        'photo_date':a['photo_date'],
                        'credit_line':f"사진: {a['author']} / {title} / {a['license_name']} / {a['source_url']} / {a['license_url']}",
                        'changes_notice_for_video':'16:9 크롭·줌 적용 시 해당 변형을 표시. 정지 사진에 움직임을 적용하면 still_motion으로 기록.',
                        'usage_conditions':'CC0: 출처 기록 유지 권장.' if a['license_name']=='CC0' else
                        '작가·제목·출처·라이선스 링크·변형 여부 표기.'+(' 변형한 사진의 동일·호환 라이선스 조건을 최종 사용에 반영.' if 'BY-SA' in a['license_name'] else '')})
    write('assets.json',rows);write('credits.json',credits)
    assert (ROOT/'contactsheet.jpg').exists()
    with Image.open(ROOT/'contactsheet.jpg') as im:im.load();assert im.size==(1280,2050)
    write('production_brief.json',{'task_id':TASK,'scope':'1편 20위→11위 4초 순위공개 사진→지도 전환용 지역 실사진',
          'ownership':'visual/top20-split-v4/photo-transitions-v1/**','composition':'16:9 중앙 크롭을 제안. 원본 사진 비율·픽셀은 보존.',
          'color':'원본 색상 유지','text':'사진에 신규 텍스트 합성 없음; 크레디트·촬영연도는 편집 담당이 별도 표기',
          'resolution':'10장 전부 폭 1920 이상·높이 960 이상; 납품 에셋 업스케일 없음',
          'margin':'장소를 식별하는 역명·풍차·수변·건물 맥락을 크롭 노트에 따라 보존',
          'priority':'현재 사용자 요구를 이전 스타일보다 우선. 실제 지역 사진·본문과 다른 원본 우선.',
          'ai_generated':False,'paid_or_cloud_generation':False,'external_upload_or_telegram':False})
    write('validation.json',{'task_id':TASK,'verified_utc':datetime.now(timezone.utc).isoformat(),
          'manifest_row_count':10,'schema_exact':True,'all_files_decode':True,'all_sha256_match':True,
          'all_distinct_from_body':True,'all_width_ge_1600_height_ge_900':True,
          'minimum_dimensions':[min(a['width'] for a in rows),min(a['height'] for a in rows)],
          'thumbnail_review_count':10,'visual_review':'최종 연락시트 10장 16:9 크롭 실제 확인',
          'independent_qa':False,'audio_listening':False,'video_playback':False,'assets':checks})
    inputs={name:{'path':(OLD/name).as_posix(),'sha256':digest(OLD/name)} for name in ['photo_assets.json','photo_assets_v2.json']}
    inputs['state_observed']={'revision':'top20-enhance-v2','active_revision':'top20-split-v4','active_part':1,'changed':False}
    write('handoff.json',{'task_id':TASK,'role':'visual','status':'ready_for_parent_review','input_revisions':inputs,
          'outputs':['assets.json','photos','contactsheet.jpg','credits.json','validation.json'],
          'affected_scene_ids':[s for r in range(20,10,-1) for s in body[r]['scene_ids']],
          'scene_id_basis':'기존 photo_assets_v2 장면ID; 새 4초 전환 연결은 R20→R11 region_id로 매칭',
          'checks':{'photos':10,'distinct':10,'fallback_existing_body':0,'decode_hash_dimensions':'pass','thumbs_inspected':10,'AI':False,'upscaled':False,'independent_qa':False},
          'open_issue_ids':[],'notes':['촬영일은 사진 원문의 사실이며 통계 기준일·현재 모습과 분리.',
          '일부 원본 GET 429는 공개 CDN 사본으로 대체; 동일 URL 자동 재시도 없음.',
          '저장된 파일은 무크롭. 연락시트의 중앙 16:9 크롭과 개별 crop_note를 편집에 적용.'],
          'next_role':'director/editor: region_id로 연결 후 크레디트·촬영연도 반영, 최종 전환 프레임 독립 QA'})
    print(json.dumps({'rows':len(rows),'distinct':10,'minimum_dimensions':[1920,960],'hash_decode_schema':'pass',
                      'assets':str(ROOT/'assets.json'),'handoff':str(ROOT/'handoff.json')},ensure_ascii=False))

if __name__=='__main__':main()
