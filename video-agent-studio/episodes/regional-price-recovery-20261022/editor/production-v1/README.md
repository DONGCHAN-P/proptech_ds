# 편집 준비본: RPR-PROD1-EDITOR

승인 대본 v3의 12장면·39비트 HyperFrames 프로젝트와 로컬 파이프라인이다. 현재 본문 837.7초는 6자/초로 만든 배치용 추정값이며 실제 음성 길이가 아니다. 전체 본편 렌더·브랜드 조립·업로드는 실행하지 않았다.

프로젝트: `../../outputs/production-v1-jun/project`. 최종 시안 선택은 `placement_guide.md`를 따른다. 인천은 v2를 선택하며 v1은 보존한다. 기존 24초 연결본은 인천 v1을 포함하므로 최신 검수본으로 쓰지 않는다.

## 현재 상태 재현

저장소 루트에서 실행한다. `build.py`는 동결 대본/차트 해시를 검사한다. 무작정 재빌드하면 실제 타임록 대신 추정 타이밍이 되므로 actual 단계에서는 반드시 `--timing-lock`을 준다.

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/build.py
tools/python311/python.exe -X utf8 video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/validate_timeline.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/run_local.ps1 -Mode check
tools/python311/python.exe -X utf8 video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/offline_animation_map.py
```

CLI는 실제 사용한 HyperFrames 0.8.181, Node 24.16.0. `npx.cmd --no-install`을 사용한다. gsap/폰트/데이터는 프로젝트에 로컬 고정했다. 생성물은 `checks/project_manifest.json`과 해시로 연결한다. 갱신/설치/외부 provider는 필요 없다.

## 실제 Jun 음성 도착 후

총괄이 `narration/production-v1/timing_lock.json`을 계약에 맞게 확정한 다음 아래 명령을 실행한다. 승인 SHA와 39개 비트 순서, body 기준 start/end/duration, 실제 파일 존재, caption 범위를 검사한다. 자막 시간은 body 절대 시간이다. `last_spoken_end`를 실제 문자 정렬로 명시하는 것을 권장하며, 생략하면 마지막 자막의 end를 발화 끝으로 사용한다. 분기 경로와 scene_id는 유지되고 자막·모션 길이만 갱신된다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/run_local.ps1 -Mode body -TimingLock C:/projects/realestate_reco/video-agent-studio/episodes/regional-price-recovery-20261022/narration/production-v1/timing_lock.json
```

이 명령은 실제 음성의 stream/duration을 FFprobe로 대조하고, 검사 통과 후 `previews/body_actual_jun_v1.mp4`에 본문을 렌더한다. 실행 전에 자막 숫자·단위 표시 변환과 실제 발음·문장 경계 검수를 마쳐야 한다. 본문 BGM carve/믹스·실제 청취는 후속 통합 담당의 일이다. 음성/음악을 여기서 생성하지 않는다.

승인된 믹스와 실제 발화 끝이 확인되면 다음 명령으로 원본 브랜드의 영상 프레임 150/300개를 연결한다. 컨테이너 5.013/10.005초를 영상 프레임 길이로 오인하지 않는다. 아웃트로는 body 기준 마지막 발화+3초를 올림한 첫 30fps 프레임에서 시작한다. PCM 꼬리가 그 3초를 넘으면 자동 절단하지 않고 실패한다.

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/assemble_final.py --body video-agent-studio/episodes/regional-price-recovery-20261022/outputs/production-v1-jun/previews/body_actual_jun_v1.mp4
```

`assemble_final.py`는 아직 실행하지 않았다. 실제 출력에 대한 stream/decode/모든 컷 경계/마지막 발화+3초/브랜드 무자막/연속 재생·청취 및 독립 QA는 후속 필수 게이트다.

## 도구 제약과 대안

기본 sandbox는 Winget FFmpeg/FFprobe 실행과 HyperFrames 전역 history 쓰기를 막았다. 총괄 및 승인된 로컬 미디어 escalation으로 렌더/검증을 수행했고, history 기록 실패는 `checks`의 별도 증거로 보완했다. 실행 파일을 복사하지 않았다. PowerShell은 native stderr를 Continue로 수집하고 실제 `LASTEXITCODE`만 실패로 판단한다.

general-video 업데이트는 총괄 재시도에서도 `Unknown skill(s): general-video`였다. 설치된 SKILL.md와 core/animation/creative/registry/CLI 문서를 읽고 사용했다. 초기화의 자동 스킬 설치는 중단했다. 사용량 조회는 총괄의 unknown/usage_request_failed 기록을 승계했다. allowance를 추정하지 않았다.

`animation-map.mjs`는 로컬 `@hyperframes/producer`, `@hyperframes/core` 미발견으로 실패했다. npm latest bootstrap은 하지 않고 `offline_animation_map.py`로 실제 작성된 106개 차트 driver의 시작·구간·관측값·hold를 추출했다. 이 지도는 소스 분석이며 연속 재생 검수가 아니다.
