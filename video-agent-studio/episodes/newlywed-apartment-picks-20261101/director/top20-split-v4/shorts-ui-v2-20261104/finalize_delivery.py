"""Bind reviewed replacement Shorts; preserve main, budgets and publication state."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

D = Path(__file__).resolve().parent
E = D.parents[2]
R = E.parents[2]
H = E / 'editor/top20-split-v4/shorts-ui-v2-20261104'
Q = E / 'qa/top20-split-v4/shorts-ui-v2-20261104'
O = E / 'outputs/top20-split-v4/shorts-ui-v2-20261104'
sys.path.insert(0, str(R))
from notify.video_decisions import create, write


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p):
    return p.resolve().relative_to(R).as_posix()


def episode_paths(item):
    result = dict(item)
    for key in ['video', 'timing', 'project', 'editor_receipt', 'qa', 'encoded_manifest']:
        result[key] = (R / item[key]).resolve().relative_to(E).as_posix()
    return result


def main():
    assert not (D / 'delivery.json').exists(), 'Preserve an already delivered revision'
    assert read(R / 'output/video_decisions/decisions/5fa686c7d1e9.json')['status'] == 'revision_requested'
    for item in read(D / 'preserved_state_fingerprint.json')['files']:
        assert sha(R / item['path']) == item['sha256'], item['path']
    media = []
    ids = ['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11']
    for sid in ids:
        p = H / sid
        receipt = read(p / 'render_receipt.json')
        video = Path(receipt['video'])
        qa = Q / f'{sid}_final_review.json'
        review = read(qa)
        evidence = Q / 'encoded' / sid / 'encoded_manifest.json'
        proof = read(evidence)
        digest = sha(video)
        assert digest == receipt['video_sha256'] == review['video_sha256'] == proof['video_sha256'], sid
        assert receipt['status'] == 'technical_checks_passed'
        assert review['status'] == 'passed_for_local_review'
        assert review['required_open_count'] == review['critical_open_count'] == 0
        assert proof['status'] == 'passed' and proof['minimum_audio_correlation'] > .97
        timing = D / 'shorts' / sid / 'locked_timing.json'
        lock = read(timing)
        assert sha(Path(lock['master_audio'])) == lock['master_audio_sha256']
        assert lock['voice_regeneration_calls'] == lock['additional_credits'] == 0
        media.append(dict(id=sid, video=rel(video), video_sha256=digest,
                          duration_s=lock['total_s'], timing=rel(timing), project=rel(p),
                          editor_receipt=rel(p / 'render_receipt.json'), qa=rel(qa),
                          encoded_manifest=rel(evidence), bytes=video.stat().st_size))
    main_asset = read(D / 'baseline_release.json')['assets'][0]
    assert sha(R / main_asset['video']) == main_asset['video_sha256']
    write(D / 'release_manifest.json', dict(revision='shorts-ui-v2-20261104',
          unchanged_main=main_asset, assets=media, new_paid_calls=0, additional_credits=0))
    report = dict(status='passed_for_local_review', required_open_count=0, critical_open_count=0,
                  unchanged_main=main_asset, media=media, actual_listening=False, continuous_playback=False,
                  scope='Three exact replacement Shorts: measured source text/anchors and sampled encoded frame/audio-signal review')
    write(D / 'bundle_review_index.json', report)
    notes = O / '검토안내.md'
    text = ['# 쇼츠 구성·UI 개선본', '',
            '본편은 기존 Jun 11분22초 버전을 유지하고 쇼츠 세 편을 교체했습니다.', '',
            '- 홍보용: 질문으로 시작해 연수구 두 생활권의 가격을 비교한 뒤 본편으로 연결합니다. 약22초.',
            '- 20~16위: 첫 질문과 범위 소개 후 원미·중랑·기흥·연수·남동을 보여줍니다. 약76초.',
            '- 15~11위: 첫 질문과 범위 소개 후 구로·은평·권선·영통·노원을 보여줍니다. 약73초.', '',
            '지역명144px·가격88px, 상시 순위표 제거, 실제 사진의 밝은 배치, 발화에 맞춘 비례 막대, 0.35초 사진 전환을 적용했습니다. 자막54px·출처/표본26px은 별도 안전영역에서 검사했습니다.', '',
            '원래 Jun의 완결된 문장만 재편집했습니다. 이번 수정의 새 음성 생성·추가 크레딧·추가 결제는 모두0입니다. 기존 생성의 사용량2208/상한6500 기록은 보존했습니다.', '',
            '실제 MP4의 표본·장면 경계·긴 자막·숫자 최초 표시·끝 발화/유지 화면, 전체 디코드와 오디오 마스터 대조를 검사했습니다. 전 구간 연속 재생과 실제 청취는 수행하지 않았습니다.', '',
            '공식 제작 자료에서 확인한 원칙과 이번 디자인 선택은 조사 보고서에서 구분했습니다. 업로드와 관련 영상 버튼 연결은 후속 게시 단계에서 확인합니다.', '',
            '이 폴더의 UI_전후비교.jpg는 기존·개선 MP4에서 직접 추출한 화면입니다.', '']
    notes.write_text('\n'.join(text), encoding='utf-8')
    research = E / 'research/shorts-ui-v2-20261104/research_packet.md'
    credits = O / '출처와크레딧.md'
    prior = E / 'outputs/top20-split-v4/jun-and-shorts-v1/출처와크레딧.md'
    credits.write_text(prior.read_text(encoding='utf-8') + '\n## 2026-11-04 쇼츠 개선\n\n기존 Jun 문장·기존 라이선스 사진과 음악을 재사용했습니다. 새 유료 생성은 0회입니다. 공식 Shorts 제작 자료와 적용 해석은 ' + str(research) + '에 기록했습니다.\n', encoding='utf-8')
    gate = create(E.name, 'completed', '쇼츠3편의 질문형 인트로·간결한 아웃트로·지역 사진/큰 가격/발화별 비례막대 개선본. 본편 유지. 필수·치명0건의 로컬 표본/자막/타이밍 검토본. 새 유료호출0. 전 구간 청취·연속재생 미실시. 업로드 승인 별도.')
    paths = [R / x['video'] for x in media] + [R / x['qa'] for x in media] + [notes, credits, research, D / 'release_manifest.json']
    gate.update(artifact_revision='top20-split-v4/shorts-ui-v2-20261104',
                main_video_sha256=main_asset['video_sha256'],
                artifacts=[dict(path=rel(p), sha256=sha(p)) for p in paths],
                additional_credits=0, additional_cash_krw=0,
                upload_authorized=False, part2_production_authorized=False)
    write(R / 'output/video_decisions/decisions' / f"{gate['id']}.json", gate)
    write(D / 'completed_decision.json', gate)
    state = read(E / 'state.json')
    assert state['active_video_sha256'] == main_asset['video_sha256']
    state.update(phase='awaiting_shorts_ui_v2_20261104_completed_review',
                 active_shorts_revision='top20-split-v4/shorts-ui-v2-20261104',
                 active_shorts=[episode_paths(x) for x in media],
                 active_qa=str((D / 'bundle_review_index.json').relative_to(E)).replace('\\','/'),
                 active_completion=str((D / 'completed_decision.json').relative_to(E)).replace('\\','/'),
                 pending_decision_id=gate['id'], active_upload_authorized=False,
                 active_publication_status='local_only_not_uploaded',
                 shorts_ui_revision_additional_credits=0, actual_listening_performed=False,
                 continuous_playback_performed=False, updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(completed='pending:' + gate['id'], pre_upload='not_reached_shorts_ui_v2')
    write(E / 'state.json', state)
    cfg = read(R / 'config/video_shelf.json')
    entry = next(x for x in cfg['entries'] if x['name'] == '신혼부부_TOP20_1편')
    by = {x['id']:x for x in media}
    for filename, sid in [('홍보용_쇼츠.mp4',ids[0]),('순위_20-16위_쇼츠.mp4',ids[1]),('순위_15-11위_쇼츠.mp4',ids[2])]:
        entry['files'][filename] = by[sid]['video']
    for filename, sid in [('홍보용_자막.srt',ids[0]),('순위_20-16위_자막.srt',ids[1]),('순위_15-11위_자막.srt',ids[2])]:
        entry['files'][filename] = rel(D / 'shorts' / sid / 'captions.srt')
    entry['files'].update({'쇼츠_구성안.md':rel(D / 'design.md'),'쇼츠_대본.md':rel(D / 'shorts_script.md'),
                          '검토안내.md':rel(notes),'출처.md':rel(credits),'검수결과.json':rel(D / 'bundle_review_index.json'),
                          '쇼츠_조사와개선안.md':rel(research),'UI_전후비교.jpg':rel(O / 'UI_전후비교.jpg')})
    entry.update(status='Jun 본편 유지 · 질문형 인트로/아웃트로·사진·큰 가격 중심 쇼츠3편 개선 · 로컬 검토용',
                 active_local_revision='top20-split-v4/shorts-ui-v2-20261104')
    write(R / 'config/video_shelf.json', cfg)
    write(D / 'delivery.json', dict(status='local_review_ready', assets=media, unchanged_main=main_asset,
          completed_decision_id=gate['id'], new_paid_calls=0, additional_credits=0, additional_cash_krw=0,
          uploads=0, shelf='영상/신혼부부_TOP20_1편', actual_listening=False, continuous_playback=False))
    print(json.dumps(dict(status='local_review_ready', shorts=3, completed_decision=gate['id'], additional_credits=0)))


if __name__ == '__main__':
    main()
