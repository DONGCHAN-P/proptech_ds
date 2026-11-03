"""Publish local review links and a scoped completed gate, never YouTube."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).resolve().relative_to(R).as_posix()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',required=True);ap.add_argument('--qa',type=Path,required=True);a=ap.parse_args()
    receipt=read(D/f'render_receipt_{a.version}.json');t=read(D/'locked_timing.json');q=read(a.qa)
    authorization=read(D/'production_authorization.json')
    assert sha(R/authorization['script_md'])==authorization['script_md_sha256']
    assert sha(D/'approved_part1_scene_proposals.json')==authorization['scene_json_sha256']==t['source_scene_json_sha256']
    assert receipt['status']=='rendered_full_decode_passed'
    video=Path(receipt['output']);assert sha(video)==receipt['output_sha256']
    assert q['status'] in ['passed','passed_for_local_review','bounded_review_passed']
    assert q['required_open_count']==0 and q['critical_open_count']==0
    assert q['video_sha256']==receipt['output_sha256']
    out=E/'outputs/top20-split-v4/part1';out.mkdir(parents=True,exist_ok=True)
    photos=read(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets']
    photos=[p for p in photos if 11<=int(p['region_id'][1:])<=20]
    lines=['# 1편 20~11위 출처와 이용조건','','## 통계·가격·지도','',
      '- 순위: 국가데이터처 「2024년 신혼부부통계」, 2024-11-01 거주 기준, 수도권 53개 구. https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3',
      '- 거래: 국토교통부 아파트 매매 실거래가 API. 2026-05-01~10-31 계약, 2026-11-03 조회, 전용 83~85㎡, 취소 거래 제외. https://www.data.go.kr/data/15126468/openapi.do',
      '- 지도 점: 위치가 확인된 단지별 거래 중위값. 동별·준공집단 비교는 거래마다 한 표, 지도 분포는 단지마다 한 점.',
      '- 단지 위치: 한국부동산원 공동주택 단지 연계정보(2025). https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1',
      '- 학교: 한국교육시설안전원 학구도안내서비스 공공 위치자료. https://schoolzone.emac.kr/publicData/publicDataList.do',
      '- 역: KRIC 도시철도 역사정보 20260630. https://data.kric.go.kr/rips/M_01_01/detail.do?id=32',
      '- 도로·수계·공원·상업시설: © OpenStreetMap contributors, Open Database License 1.0. https://www.openstreetmap.org/copyright',
      '- 원천 파일·시설 기준일·좌표 연결·지오메트리 검증은 research/top20-split-v4 및 visual/top20-split-v4/atlas-context 기록에 보존했습니다.','',
      '## 사진','']
    for p in sorted(photos,key=lambda p:-p['rank']):
        s=p['source_or_prompt'];lic=p['license']
        lines += [f"### {p['rank']}위 · {p['actual_place']}",'',
          f"- 제목: {s['title']} / 작가: {s['author']}",
          f"- 원문: {s['file_page']}",f"- 이용조건: {lic['name']} · {lic['license_url']}",
          f"- 촬영 정보: {p.get('photo_capture_date_raw','원문 참조')}",
          '- 영상에서는 원본 사진을 비율을 유지해 축소·배치했습니다. 사진별 원본·라이선스·크레딧과 별도 재사용 조건은 photo_assets_v2.json에 보존했습니다.','']
    project=Path(receipt['project']);music=project/'music_credit.json'
    if music.exists():
        credit=read(music);lines += ['## 음악','',credit.get('credit','Thinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0'),'',credit.get('license_url','https://creativecommons.org/licenses/by/4.0/'),'']
    sourcefile=out/'출처_1편.md';sourcefile.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    minutes,seconds=divmod(round(float(receipt['probe']['format']['duration'])),60)
    note=out/'검토안내_1편.md'
    note.write_text('\n'.join(['# 신혼부부 TOP20 · 1편 20~11위','',
      f'무료 InJoon 로컬 검토본 · {minutes}분 {seconds:02d}초 · 1920×1080 · 30fps.','',
      '부천 원미구부터 서울 노원구까지 10개 지역을 다룹니다. 확정 대본 85문장에 실제 음성으로 맞춘 의미 단위 자막 176개를 붙였습니다. 구 전체와 생활권 상세 지도, 가격 구간별 단지 점, 지역별 실제 사진, 동별·준공시기별 가격 비교를 배치했습니다.','',
      '## 검토 기록','',
      '- 실거래·좌표·원고 검수는 해시가 같은 확정 자료의 기존 검증을 계승했습니다.',
      '- 새 음성의 원문·숫자 대응, 제공자 단어 경계, PCM·브랜드 1회 삽입과 마지막 발화 후 3초를 검사했습니다.',
      '- 실제 MP4의 장면별 표본 프레임과 전체 디코드, 로컬 ASR 대조를 기록했습니다.',
      '- 독립 검수: 필수·치명 수정 0건. 권장 개선 1건은 46.5초 부제 전환에서 약 0.2초간 지도 이미지의 기존 제목이 비치는 현상입니다. 다음 화면 수정 때 부제 배경을 고정하는 개선으로 남겼습니다.',
      '- 실제 청취와 전 구간 연속 재생, Claude 외부 검수는 수행하지 않았습니다. 이 파일은 사용자가 확인할 로컬 검토본입니다.','',
      f"- 영상 SHA256: `{receipt['output_sha256']}`",
      f'- 독립 검수: `{rel(a.qa)}`','',
      '2편 대본 확인과 이 새 영상의 업로드는 별도 결정 단계에 남겨두었습니다. 기존 게시본과 통합판 파일을 보존했습니다.','']),encoding='utf-8')
    gatepath=D/f'completed_decision_{a.version}.json'
    artifacts=[video,D/'captions.srt',R/'영상/신혼부부_지역별아파트/2부작_수정안/1편_20-11위_대본_v2.md',note,sourcefile,a.qa]
    if gatepath.exists():gate=read(gatepath)
    else:
        gate=create(E.name,'completed',f'1편 20~11위 무료 InJoon 로컬 검토본 {minutes}분 {seconds:02d}초. 실제 MP4 표본·자막·전사·기술검사 완료, 필수·치명 0건/권장1건(46.5초 부제 전환의 짧은 제목 잔상). 실제 청취·연속 재생·Claude 검수는 미수행. 로컬 결과 확인 단계이며 업로드·유료 생성·2편 승인을 포함하지 않습니다.')
        gate.update(part=1,artifact_revision='top20-split-v4/part1/'+a.version,
                    artifacts=[{'path':rel(p),'sha256':sha(p)}for p in artifacts],
                    upload_authorized=False,external_file_export_authorized=False,paid_generation_authorized=False,cash_cap_krw=0)
        write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(gatepath,gate)
    state=read(E/'state.json');state.update(phase='awaiting_part1_completed_review',active_video=video.relative_to(E).as_posix(),
      active_video_sha256=sha(video),active_render_receipt=(D/f'render_receipt_{a.version}.json').relative_to(E).as_posix(),
      active_source_project=project.relative_to(E).as_posix(),active_qa=a.qa.resolve().relative_to(E).as_posix(),
      active_completion=gatepath.relative_to(E).as_posix(),pending_decision_id=gate['id'],
      active_upload_authorized=False,active_review_folder='영상/신혼부부_TOP20_1편',updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(completed='pending:'+gate['id'],pre_upload='not_reached_part1')
    state['active_parts'][0].update(status='local_review_ready',video=state['active_video'],completed_decision_id=gate['id'])
    write(E/'state.json',state)
    cfg=read(R/'config/video_shelf.json');entry={'name':'신혼부부_TOP20_1편','status':f'20~11위 · {minutes}분{seconds:02d}초 · 무료 InJoon 로컬 검토본 · 업로드 전',
      'workspace':rel(E),'active_local_revision':'top20-split-v4/part1/'+a.version,
      'files':{'영상.mp4':rel(video),'자막.srt':rel(D/'captions.srt'),'대본.md':rel(artifacts[2]),'출처.md':rel(sourcefile),
               '검토안내.md':rel(note),'검수결과.json':rel(a.qa)}}
    cfg['entries']=[e for e in cfg['entries']if e['name']!=entry['name']]+[entry];write(R/'config/video_shelf.json',cfg)
    print(json.dumps({'status':'local_review_pack_ready','completed_decision_id':gate['id'],'shelf':'영상/신혼부부_TOP20_1편','duration_s':t['total_s'],'youtube_uploads':0},ensure_ascii=False))
if __name__=='__main__':main()
