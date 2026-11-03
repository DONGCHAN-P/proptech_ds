"""Package the approved PART1 intro revision for local completed review only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]
sys.path.insert(0, str(R))
from notify.video_decisions import create, write

read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel = lambda p: Path(p).resolve().relative_to(R).as_posix()
erel = lambda p: Path(p).resolve().relative_to(E).as_posix()


def main():
    a = read(D/'production_authorization.json')
    gate = read(R/'output/video_decisions/decisions'/f"{a['decision_id']}.json")
    assert gate['status'] == 'approved' and gate['gate'] == 'script'
    assert a['scope']['part'] == 1 and a['scope']['cash_cap_krw'] == 0
    assert not a['scope']['upload_authorized']
    for row in a['artifacts']:
        assert sha(R/row['path']) == row['sha256'], row['path']
    timing = read(D/'locked_timing.json')
    assembly = read(D/'assembly_v2.json')
    reuse = read(D/'reuse_verification_v2.json')
    qa_path = E/'qa/top20-split-v4/intro-rationale-v3/final_review.json'
    qa = read(qa_path)
    video = Path(assembly['video'])
    video_sha = sha(video)
    assert assembly['status'] == 'assembled_strict_decode_passed'
    assert assembly['video_sha256'] == reuse['video_sha256'] == qa['video_sha256'] == video_sha
    assert reuse['status'] == 'passed' and reuse['non_key_body_video_packets_equal'] > 16000
    assert len(reuse['body_decoded_frame_checks']) == 11
    assert qa['status'] in ['passed', 'passed_for_local_review', 'bounded_review_passed']
    assert qa['required_open_count'] == qa['critical_open_count'] == 0
    old = Path(timing['original_video'])
    assert sha(old) == a['existing_body_sha256'] == timing['original_video_sha256']
    assert sha(timing['master_audio']) == timing['master_audio_sha256']
    assert sha(assembly['prefix']) == assembly['prefix_sha256']
    preview = read(D/'preview_v1.json')
    prefix = Path(preview['preview'])
    assert preview['status'] == 'passed' and preview['source_video_sha256'] == video_sha
    assert sha(prefix) == preview['preview_sha256']
    assert len(timing['intro_sentences']) == 8 and len(timing['captions']) == 177
    assert sum(len(s['sentences']) for s in timing['body_scenes']) == 80
    out = video.parent
    script = R/a['artifacts'][1]['path']
    credits = out/'출처_1편_도입수정.md'
    original_credits = E/'outputs/top20-split-v4/part1/출처_1편.md'
    credit_body = original_credits.read_text(encoding='utf-8')
    credit_body += '\n## 새 도입 화면\n\n'
    credit_body += '- 지역 선택 화면은 위 신혼부부통계의 수도권 53개 구 집계를 사용하며, 20~11위 10개 지역을 같은 레코드에서 추려 이동시켰습니다. 원천은 `analysis/newlywed_region_2024/capital_gu_ranking.csv`입니다.\n'
    credit_body += '- 아파트·도시·지역 탐색·가격 범례는 이번 편을 위해 제작한 SVG 및 타이포그래피입니다. 점의 가격 구간은 기존 본편과 동일합니다.\n'
    credit_body += '- 공개 HyperFrames ui-3d-reveal의 perspective/rotationY/scale/y 동작 구조를 참고했습니다. 참고 코드와 입력 해시는 editor/top20-split-v4/intro-rationale-v3에 보존했습니다.\n'
    if 'Thinking Music' not in credit_body:
        credit_body += '\n## 음악\n\nThinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0\n\nhttps://creativecommons.org/licenses/by/4.0/\n'
    credits.write_text(credit_body, encoding='utf-8')
    recommended = qa.get('recommended_open_count', len(qa.get('recommendations', [])))
    note = out/'검토안내_도입수정.md'
    note.write_text('\n'.join([
        '# 신혼부부 TOP20 · 1편 20~11위 · 도입 수정본', '',
        '전체 10분 02초 · 도입과 본편 연결 미리보기 52.7초 · 1920×1080 · 30fps · 무료 InJoon.', '',
        '## 반영한 방향', '',
        '우리 예산으로 어느 동네부터 찾아볼지 질문하고, 신혼부부가 실제로 매매를 검토할 지역과 아파트를 찾으려는 채널의 취지를 설명합니다. 수도권 53개 구의 신혼부부 거주 데이터를 펼친 뒤 이번 편의 20~11위 10개 지역을 추려 이동시키고, 후속 지역별·예산별 아파트 비교로 연결합니다.', '',
        '아파트 도시의 입체 등장, 지역→가격대→아파트 탐색 과정, 실제 통계 레코드 재배치, 아파트 한 단지→지도 점 하나의 변환과 가격 범례를 제작했습니다. 도입 8문장 음성을 새로 만들고 기존 지역 본문·마무리 80문장과 연결했습니다.', '',
        '## 파일', '',
        '- `인트로_미리보기.mp4`: 새 도입과 첫 지역 소개 문장까지 52.7초. 문장이 끝난 뒤 화면과 소리가 함께 잦아듭니다.',
        '- `영상.mp4`: 지역 설명을 포함한 전체 영상.',
        '- `대본.md` · `자막.srt`: 승인된 도입과 기존 지역 본문, 전체 177개 자막.',
        '- `이전_검토본.mp4`: 수정 전 10분 검토본.', '',
        '## 검수 범위', '',
        '- 최종 MP4 전체 디코드 성공. 총 18,070프레임, 10분 02.333초.',
        '- 실제 MP4에서 추출한 49개 프레임으로 도입 움직임·지역 화면·접합 전후·마지막 화면을 확인했습니다.',
        '- 소스 45개 시각의 런타임·레이아웃·대비 검사에서 오류 0건.',
        '- 본편은 기존 영상을 연결했습니다. 54.633초부터는 기존 인코딩된 프레임을 재사용했으며, 비키프레임 패킷 16,364개와 11개 장면의 디코드 영상이 원본과 일치했습니다.',
        '- 최종 음성 19개 표본 구간을 마스터와 대조해 최소 상관계수 0.99995를 확인했습니다. 신규 도입은 오프라인 전사와 공급자 단어 경계도 대조했습니다.',
        f'- 독립 검수: 필수·치명 수정 0건, 권장 개선 {recommended}건. 세부 내용은 `검수결과.json`에 기록했습니다.',
        '- 실제 청취·전 구간 연속 재생·Claude 외부 검수는 수행하지 않았습니다. “53개 구”는 자동 전사에서 표기가 달라 실제 발음 확인 항목으로 남겼습니다.', '',
        f'- 영상 SHA256: `{video_sha}`',
        f'- 검수 원본: `{rel(qa_path)}`', '',
        '이번 결과는 1편 도입 수정본의 로컬 확인 단계입니다. 2편 대본 결정과 최종 업로드 결정은 각각 보존했습니다.', ''
    ]), encoding='utf-8')
    complete_path = D/'completed_decision_v2.json'
    artifacts = [video, prefix, script, D/'captions.srt', note, credits, qa_path, D/'reuse_verification_v2.json', D/'preview_v1.json']
    if complete_path.exists():
        complete = read(complete_path)
        assert complete['video_sha256'] == video_sha
    else:
        complete = create(E.name, 'completed', '1편 20~11위 도입 수정본: 예산 질문→신혼부부 거주통계 53개 구→이번 10개 지역→후속 예산별 아파트 탐색. 전체10분02초, 미리보기52.7초. 실제 MP4 49개 프레임·전체 디코드·기존 본편 동등성·음성 신호 대조 완료. 실제 청취·연속 재생은 미수행. 로컬 결과 확인 단계.')
        complete.update(part=1, artifact_revision='top20-split-v4/intro-rationale-v3/v2',
                        video_sha256=video_sha,
                        artifacts=[{'path': rel(p), 'sha256': sha(p)} for p in artifacts],
                        upload_authorized=False, paid_generation_authorized=False,
                        external_file_export_authorized=False, part2_production_authorized=False,
                        cash_cap_krw=0)
        write(R/'output/video_decisions/decisions'/f"{complete['id']}.json", complete)
        write(complete_path, complete)
    state = read(E/'state.json')
    state.update(phase='awaiting_part1_intro_completed_review',
                 active_production_revision='intro-rationale-v3/v2',
                 active_video=erel(video), active_video_sha256=video_sha,
                 active_audio=erel(timing['master_audio']), active_audio_sha256=timing['master_audio_sha256'],
                 active_timing=erel(D/'locked_timing.json'), active_timing_status='actual_audio_locked',
                 active_measured_duration_s=timing['total_s'],
                 active_new_intro_audio_generated=True,
                 active_script=erel(R/a['artifacts'][0]['path']),
                 active_script_sha256=a['artifacts'][0]['sha256'],
                 active_script_scope='8 intro sentences + inherited approved 80 body/outro sentences',
                 active_body_script='director/top20-split-v4/part1-production-v1/approved_part1_scene_proposals.json',
                 active_captions=erel(D/'captions.srt'),
                 active_source_project=erel(E/'editor/top20-split-v4/intro-rationale-v3/project-v3'),
                 active_render_receipt=erel(D/'assembly_v2.json'), active_qa=erel(qa_path),
                 active_completion=erel(complete_path), pending_decision_id=complete['id'],
                 production_authorization=erel(D/'production_authorization.json'),
                 active_upload_authorized=False, active_publication_status='local_only_not_uploaded',
                 active_review_folder='영상/신혼부부_TOP20_1편',
                 actual_listening_performed=False, continuous_playback_performed=False,
                 updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(completed='pending:'+complete['id'], pre_upload='not_reached_part1')
    state['active_parts'][0].update(status='intro_v3_local_review_ready', video=erel(video),
                                    completed_decision_id=complete['id'])
    write(E/'state.json', state)
    cfg = read(R/'config/video_shelf.json')
    entry = next(e for e in cfg['entries'] if e['name'] == '신혼부부_TOP20_1편')
    entry.update(status='20~11위 · 10분02초 · 도입 모션 수정본 · 로컬 검토용',
                 active_local_revision='top20-split-v4/intro-rationale-v3/v2',
                 files={'영상.mp4': rel(video), '인트로_미리보기.mp4': rel(prefix),
                        '이전_검토본.mp4': rel(old), '자막.srt': rel(D/'captions.srt'),
                        '대본.md': rel(script), '출처.md': rel(credits),
                        '검토안내.md': rel(note), '검수결과.json': rel(qa_path)})
    write(R/'config/video_shelf.json', cfg)
    receipt = {'status': 'local_review_pack_ready', 'video': rel(video), 'video_sha256': video_sha,
               'duration_s': timing['total_s'], 'preview': rel(prefix),
               'completed_decision_id': complete['id'], 'shelf': '영상/신혼부부_TOP20_1편',
               'cash_cost_krw': 0, 'youtube_uploads': 0,
               'actual_listening': False, 'continuous_playback': False}
    write(D/'delivery_v2.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
