"""Maximum 2 jobs × 2 workers. No paid or external services."""
import sys,subprocess,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline_ui as r
u=r.u
def one(sid):
    p=u.H/sid;r.gate();r.p.render(p);r.p.verify(p)
    return sid
def finalize():
    products=[]
    lines=['# 배치 가이드 · Shorts UI v2','', '배포 파일은 아래 정확한 MP4 3개다. 원생 1080×1920·30fps이며 실제 새 Jun master·lock을 그대로 사용한다. 로컬 검토용이며 게시/관련 영상 버튼 연결 완료를 뜻하지 않는다.','']
    for sid in u.IDS:
        p=u.H/sid;receipt=u.b.read(p/'render_receipt.json');tech=u.b.read(p/'technical_check.json');manifest=u.b.read(p/'input_manifest.json');sb=u.b.read(p/'storyboard.json')
        assert tech['status']=='technical_checks_passed'
        product=dict(short_id=sid,video=receipt['video'],sha256=receipt['video_sha256'],bytes=receipt['video_bytes'],duration_s=tech['duration_s'],project=str(p),lock_sha256=manifest['lock_sha256'],master_audio_sha256=manifest['master_audio_sha256'],technical_check=str(p/'technical_check.json'),proofs=str(p/'encoded_proofs.json'))
        products.append(product)
        lines += [f'## {sid}', '',f'- 실제 배포 파일: `{Path(receipt["video"]).name}`',f'- 길이: {tech["duration_s"]:.6f}초',f'- 편집 프로젝트: `{p}`',f'- 배포 원본: `{receipt["video"]}`','', '| 추천 시간 | 길이 | 장면·레이어·전환 | 자료 유형 |','|---|---:|---|---|']
        for s in sb['scenes']:
            label={'hook':'질문·거주 수 순위 범위', 'region':f'{s.get("region_id")} 사진/큰 지역명 → native 가격 2행/비례막대', 'cta':'다른 순위 범위·본편 안내, 마지막 발화 뒤 정보 유지'}[s['kind']]
            lines += [f'| {s["start_s"]:.3f}초 | {s["end_s"]-s["start_s"]:.3f}초 | {label}; 사진 교체 0.35초, 숫자·출처 별도 고정 레이어 | 실제 지역 정지사진 + native HTML/GSAP 데이터 |']
        lines += ['', '자막은 단일 트랙 54px 흰 박스로 활성 큐 동안만 표시한다. 출처·표본 26px, 금액 88px, 지역명 144px. 막대는 기존 bar_fraction을 사용하며 해당 native 금액/단지 수 발화 앵커에서 0.35초로 완성된 뒤 유지한다. R16은 77개 단지의 가격 구간 분포이며, 동별 거래 중위값과 구분한다.','']
    lines += ['## 재현 및 검수 범위','', '`tools/python311/python.exe -X utf8 <editor-task-root>/build_ui.py` → `proof_ui.py` → `pipeline_ui.py check` → `deliver_ui.py` 순서다. 실제 렌더 argv는 각 프로젝트 render_receipt.json에 보존한다. 대표 QA 통과 증거가 없으면 렌더 스크립트는 중단한다.','', '실제 MP4 ffprobe·전체 A/V decode·마스터 PCM 상관 대조와 대표/경계 프레임을 확인한다. 전체 글리프 실측은 원본 DOM에 대한 검사이며 독립 QA의 실제 MP4 판단과 구분한다. 실제 청취·연속 재생은 미수행이다.']
    u.write(u.H/'placement_guide.md','\n'.join(lines)+'\n')
    u.save(u.H/'delivery_manifest.json',dict(task_id='shorts-ui-v2-20261104',products=products,paid_calls=0,new_audio_calls=0,actual_listening=False,continuous_playback=False))
    u.save(u.H/'handoff.json',dict(status='three_native_mp4s_technically_verified_independent_final_QA_pending',deliverables=products,placement_guide=str(u.H/'placement_guide.md'),input_version='director/top20-split-v4/shorts-ui-v2-20261104 new actual Jun locks',changed_files_root=str(u.H),output_root=str(u.b.OUT),validation='source all-character glyph/cue/native-price/bar checks + HF checks + encoded full A/V decode/master correlation',unresolved=['independent final MP4 QA','actual listening and continuous playback unperformed'],affected_scenes=u.IDS,next_owner='director + independent QA',paid_calls=0,actual_listening=False,continuous_playback=False))
    print(json.dumps({'status':'three_mp4s_ready_for_independent_final_QA','manifest':str(u.H/'delivery_manifest.json')},ensure_ascii=False),flush=True)
if __name__=='__main__':
    r.gate()
    with ThreadPoolExecutor(max_workers=2)as pool:
        jobs=[pool.submit(one,sid)for sid in [u.IDS[0],u.IDS[2]]]
        for j in jobs:j.result()
    one(u.IDS[1]);finalize()
