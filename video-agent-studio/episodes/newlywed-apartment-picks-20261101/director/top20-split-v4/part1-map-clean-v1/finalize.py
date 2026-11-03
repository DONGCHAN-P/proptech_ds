"""Local review delivery; preserve all five gates and existing publication state."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).resolve().relative_to(R).as_posix()
erel=lambda p:Path(p).resolve().relative_to(E).as_posix()
def main():
    a=read(D/'production_authorization.json');assert a['status']=='approved'and a['scope']['cash_cap_krw']==0
    assert sha(R/a['script'])==a['script_sha256']and sha(R/a['baseline_video'])==a['baseline_sha256']
    source_gate=read(D/'script_decision.json');assert source_gate['status']=='approved'
    for item in source_gate['artifacts']:assert sha(R/item['path'])==item['sha256']
    final=read(D/'assembly_v1.json');timing=read(D/'locked_timing.json');pv=read(D/'previews_v1.json')
    qp=E/'qa/top20-split-v4/map-clean-v1/final_review.json';q=read(qp);video=Path(final['video']);digest=sha(video)
    assert final['status']=='assembled_strict_decode_passed'
    assert final['video_sha256']==q['video_sha256']==pv['source_video_sha256']==digest
    assert q['required_open_count']==q['critical_open_count']==0 and q['status']in['passed','passed_for_local_review','bounded_review_passed']
    assert sha(timing['master_audio'])==timing['master_audio_sha256']
    for key in ['intro','changes']:assert sha(pv[key]['path'])==pv[key]['sha256']
    out=video.parent;photos=read(E/'visual/top20-split-v4/photo-transitions-v1/assets_v2.json')
    project=Path(final['source_project']);assert len(photos)==10
    source=out/'출처_지도정리와사진전환.md'
    old_source=E/'outputs/top20-split-v4/intro-rationale-v3/출처_1편_도입수정.md'
    lines=[old_source.read_text(encoding='utf-8'),'','## 지도 하단 정리와 사진 전환 수정본','',
           '지도 거래 기준은 도입 음성과 기준 화면에서 설명합니다. 2026.05~10 계약·전용 83~85㎡·2026.11.03 조회·취소 거래 제외·단지별 거래 중위값입니다.',
           '지도 화면에는 간결한 © OpenStreetMap 표기를 사용하고, 상세 출처·ODbL 정보는 이 문서 및 업로드 설명문 초안에 유지합니다.',
           '© OpenStreetMap contributors · Open Database License 1.0 · https://www.openstreetmap.org/copyright',
           '출처 배치 근거: https://osmfoundation.org/wiki/Licence/Attribution_Guidelines#TV,_film,_or_video_productions','',
           '### 순위 진입에 새로 사용한 사진','',
           '사진은 화면 비율에 맞춰 일부 크롭하고 명암 오버레이와 작은 카메라 이동을 적용했습니다. 촬영연도를 화면에 표시했으며 기존 본문 사진과 구분됩니다.','']
    for p in photos:
        lines += [f"#### {p['rank']}위 {p['region']} · {p['actual_place']}",'',f"- 작가: {p['author']}",
                  f"- 촬영 정보: {p['photo_date']}",f"- 이용조건: {p['license_name']} · {p['license_url']}",
                  f"- 원문: {p['source_url']}",f"- 파일 SHA256: `{p['sha256']}`",'']
    source.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    description=out/'업로드_설명문_초안.txt'
    description.write_text('신혼부부가 많이 사는 수도권 지역 20위부터 11위까지, 아파트 가격과 생활권을 함께 살펴봅니다.\n\n가격: 2026년5~10월 계약, 전용83~85㎡, 2026년11월3일 조회, 취소 거래 제외. 지도는 단지별 거래 중위가격으로 표시했습니다.\n순위: 2024년 신혼부부통계, 2024.11.01 거주 기준, 수도권53개 구.\n\n지도 데이터: © OpenStreetMap contributors · ODbL 1.0\nhttps://www.openstreetmap.org/copyright\n\n사진별 작가·촬영연도·CC 라이선스와 원문 링크:\n'+'\n'.join(f"{p['rank']}위 {p['region']}: {p['author']} · {p['license_name']} · {p['source_url']} · {p['license_url']}"for p in photos)+'\n\nThinking Music by Kevin MacLeod | incompetech.com | CC BY 4.0\nhttps://creativecommons.org/licenses/by/4.0/\n',encoding='utf-8')
    note=out/'검토안내_지도정리와사진전환.md';recommended=q.get('recommended_open_count',0)
    note.write_text('\n'.join(['# 1편 20~11위 · 지도 정리·사진 전환 수정본','',
        '전체 10분15초 · 1920×1080 · 30fps · 무료 InJoon.', '',
        '## 반영 사항','',
        '- 지도 하단의 계약 기간·조회일과 긴 지도 출처 문구를 정리했습니다. 가격 색상 범례·학교·역·상권·단지 점·자막은 유지했습니다.',
        '- 도입 39.7초부터 12.8초 동안 계약 기간·면적·조회일·취소 제외·단지별 중위가격을 새 음성과 모션 화면으로 설명합니다.',
        '- 지도 출처는 오른쪽 위에 © OpenStreetMap으로 간결하게 표시하고 상세 URL·라이선스는 출처 문서와 설명문 초안에 유지했습니다.',
        '- 20~11위의 진입마다 기존 본문과 다른 실제 지역 사진, 큰 순위와 지역명을 보여준 뒤 지도로 이어집니다. 기존 사진으로 설명하는 본문도 그대로 유지했습니다.',
        '- 새 기준 2문장 외의 기존 88문장 음성은 원본 PCM을 재사용했습니다. 전체 90문장·181개 자막입니다.','',
        '## 파일','',
        '- `영상.mp4`: 현재 전체 검토본.',
        '- `수정구간_미리보기.mp4`: 도입 거래 기준 설명과 10개 순위 전환을 모은 미리보기. 각 소개 문장 뒤 여백에서 편집했습니다.',
        '- `인트로_미리보기.mp4`: 도입부터 20위 첫 소개 문장이 끝날 때까지.',
        '- `이전_검토본.mp4`: 직전 도입 수정본.','',
        '## 검수 범위','',
        '- HyperFrames 소스 48개 시각의 런타임·레이아웃 검사에서 오류 0건. 전환 중 프레임을 포함한 실제 MP4 표본은 독립 검수 기록에 있습니다.',
        '- 전체 영상과 두 미리보기의 전체 디코드를 확인했습니다. 본편 18,454프레임, 615.133초.',
        '- 새 문장 앞뒤의 기존 음성 PCM이 원본과 일치함을 검사했습니다. 새 음성의 숫자·원문/표시문 역변환·공급자 단어 경계를 대조했습니다.',
        f'- 독립 검수: 필수·치명 수정 0건, 권장/미확인 {recommended}건. `검수결과.json`에 타임코드와 범위를 기록했습니다.',
        '- 실제 청취·전체 연속 재생·Claude 외부 검수는 수행하지 않았습니다.','',
        f'- 영상 SHA256: `{digest}`',f'- 편집 프로젝트: `{rel(project)}`','',
        '이번 결과는 새 로컬 completed 확인 단계입니다. 기존 게시본·최종 업로드 결정·2편 대본 결정은 별도 상태를 유지합니다. 현금 사용은 0원입니다.','']),encoding='utf-8')
    artifacts=[video,Path(pv['changes']['path']),Path(pv['intro']['path']),R/a['reader_script'],D/'captions.srt',source,description,note,qp]
    gatepath=D/'completed_decision_v1.json'
    if gatepath.exists():gate=read(gatepath);assert gate['video_sha256']==digest
    else:
        gate=create(E.name,'completed','1편 지도 하단 반복 기준을 도입 음성으로 이동하고 20~11위 각 진입에 새 대표 사진 전환을 넣은 로컬 검토본. 전체10분15초. 표본 화면·모든 순위 경계·전체 디코드 및 음성 PCM 검사를 기록했습니다. 실제 청취·연속 재생은 미수행. 최종 업로드는 별도 결정입니다.')
        gate.update(part=1,artifact_revision='top20-split-v4/map-clean-v1',video_sha256=digest,
                    artifacts=[{'path':rel(p),'sha256':sha(p)}for p in artifacts],
                    cash_cap_krw=0,paid_generation_authorized=False,upload_authorized=False,
                    external_file_export_authorized=False,part2_production_authorized=False)
        write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(gatepath,gate)
    s=read(E/'state.json');s.update(phase='awaiting_part1_map_clean_completed_review',active_production_revision='map-clean-v1',
       active_video=erel(video),active_video_sha256=digest,active_audio=erel(timing['master_audio']),active_audio_sha256=timing['master_audio_sha256'],
       active_timing=erel(D/'locked_timing.json'),active_measured_duration_s=timing['total_s'],active_timing_status='actual_audio_locked',
       active_script=erel(R/a['script']),active_script_sha256=a['script_sha256'],active_script_scope='new2criteria + inherited88sentences',
       active_reader_script=a['reader_script'],active_captions=erel(D/'captions.srt'),active_source_project=erel(project),
       active_render_receipt=erel(D/'assembly_v1.json'),active_qa=erel(qp),active_completion=erel(gatepath),pending_decision_id=gate['id'],
       active_publication_status='local_only_not_uploaded',active_upload_authorized=False,
       actual_listening_performed=False,continuous_playback_performed=False,updated_at=datetime.now(timezone.utc).isoformat())
    s['active_approval_status'].update(completed='pending:'+gate['id'],pre_upload='not_reached_part1')
    s['active_parts'][0].update(status='map_clean_v1_local_review_ready',video=erel(video),completed_decision_id=gate['id'])
    write(E/'state.json',s)
    cfg=read(R/'config/video_shelf.json');entry=next(x for x in cfg['entries']if x['name']=='신혼부부_TOP20_1편')
    entry.update(status='20~11위 · 10분15초 · 지도 하단 정리·사진 순위 전환 · 로컬 검토용',active_local_revision='top20-split-v4/map-clean-v1',
       files={'영상.mp4':rel(video),'수정구간_미리보기.mp4':rel(pv['changes']['path']),'인트로_미리보기.mp4':rel(pv['intro']['path']),
              '이전_검토본.mp4':a['baseline_video'],'자막.srt':rel(D/'captions.srt'),'대본.md':a['reader_script'],
              '출처.md':rel(source),'검토안내.md':rel(note),'검수결과.json':rel(qp)})
    write(R/'config/video_shelf.json',cfg)
    receipt={'status':'local_review_ready','video':rel(video),'video_sha256':digest,'duration_s':timing['total_s'],
             'preview':rel(pv['changes']['path']),'shelf':'영상/신혼부부_TOP20_1편','completed_decision_id':gate['id'],'cash_cost_krw':0,'uploads':0}
    write(D/'delivery_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
