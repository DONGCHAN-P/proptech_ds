# Jun production-v1 준비 산출물

작업 `RPR-PROD1-JUN-PREP`. 승인 대본 v3 4,839자·39문단과 Jun `4p6UA7mnodF5q7JFFrnW` / `eleven_v4`를 그대로 사용한다. 이 단계는 로컬 준비만 완료했다. 실제 음성·실측 타임록은 아직 없다.

`generate.mjs`의 기본 실행은 오프라인 입력 검사다. `--execute-approved`가 있을 때만 승인과 로컬 FFmpeg 가용성을 먼저 검사한 뒤 기존 account()의 읽기 전용 계정 확인, 순차 합성으로 진입한다. 비밀 값은 기존 account() 내부에서 읽으며 영수증·로그·핸드오프에 넣지 않는다. 요청 본문은 원문 `text`와 `model_id`만 사용해 기존 with-timestamps 패턴을 유지한다. 발음 치환·추가 태그·속도·말투 설정을 새로 넣지 않는다.

총괄은 **실제 예산 승인 후** `authorization.template.json`을 참고해 같은 폴더에 새 `authorization.json`을 작성한다. 실행 허용·외부 전송·유료 API 허용을 true로 설정하고, 실제 승인된 예산 결정 파일의 SHA256과 발급·만료 시각을 채운다. 유효 기간은 최대 24시간이다. 템플릿은 실행 승인이 아니다. 예산 결정은 생성기의 실행 시점에 직접 읽으며 approved 상태·대상 episode·대본/manifest SHA·5,807 크레딧·추가 결제 0·자동 재시도 false를 모두 확인한다. 기존 .env를 복사하거나 키를 명령줄에 넣지 않는다.

```powershell
# 현재 폴더와 무관하게 실행 가능. 아래 유료 실행은 총괄이 승인 확인 후 수행한다.
& 'C:/Program Files/nodejs/node.exe' 'C:/projects/realestate_reco/video-agent-studio/episodes/regional-price-recovery-20261022/narration/production-v1/generate.mjs' '--execute-approved'
# 39개 complete 영수증·오디오가 모두 있어야 실제 타이밍과 합본을 만든다.
& 'C:/Program Files/nodejs/node.exe' 'C:/projects/realestate_reco/video-agent-studio/episodes/regional-price-recovery-20261022/narration/production-v1/build_timing.mjs'
```

현재 sandbox에서는 기존 Winget FFmpeg 하위 프로세스를 사용할 수 없었다. 사용자 지시에 따라 실제 생성 및 FFmpeg 실측 조합은 총괄이 `require_escalated` 실행으로 검증한다. 별도 설치는 하지 않았다. 다른 기존 FFmpeg를 사용할 때에는 `FFMPEG_PATH` 환경변수에 실행 파일 경로만 지정한다.

생성기는 최초 account()로 목소리·모델의 알려진 요율이 모두 0 초과·1 이하인지 검사한다. 매 문단 직전 구독의 포함 잔액·초과 결제 비활성 상태와 승인 유효성을 재확인한다. 완료분 실제 비용 + 이번 예약 + 남은 원문 예약이 5,807을 넘으면 중단한다. 한 문단 예약은 원문 문자 수이며 응답 character-cost는 그 이하여야 한다. 수정 여유 968 크레딧은 자동 생성·재시도 권한이 아니다.

`receipts/Sxxx-Pn.json`을 독점 생성하고 디스크에 동기화한 뒤 POST를 단 한 번 보낸다. pending/request_started/failed 영수증, 기존 실행 잠금, 영수증 없는 산출물, 해시가 달라진 완료 산출물은 재요청을 차단한다. 자동 재시도·충전·대체 제공자는 없다. 완료분만 원문·생성 코드·설정·예산·파일 해시·실제 디코딩 길이를 다시 확인해 건너뛴다. 비용 헤더 누락·불명·예약 초과, 정렬 불일치·비단조 시간·오디오 범위 초과, 네트워크·권한·로컬 오류는 failed로 남기고 중단한다. 실패 영수증이나 오래된 잠금을 지워 다시 실행하는 복구 기능은 제공하지 않는다. 총괄이 제공자 사용 내역과 산출물을 대조해 별도 결정해야 한다.

문단별 MP3·원본 alignment·normalized alignment·전체 요청 영수증을 보존한다. 두 정렬의 시간은 실제 PCM 길이 안에 있어야 하고 원본 alignment를 연결한 문장은 원문과 정확히 같아야 한다. 성공 영수증은 기술 검사 통과와 청취 미확인을 함께 표시한다.

`build_timing.mjs`는 실제 MP3를 44,100Hz 단채널 16bit PCM으로 디코딩해 문단 길이를 측정한다. 문단 사이 38곳에 각각 0.35초를 넣고 마지막에는 추가 문단 무음을 넣지 않는다. `duration`과 `narration_duration_s`는 해당 오디오 길이이고 `pause_after_s`는 별도다. 합본의 body 길이와 순수 문단 오디오 합계도 나눈다.

`timing_lock.json`의 beat start/end 및 **caption start/end는 본문 전체 기준**이다. 자막에는 local_start/local_end도 함께 남긴다. 인트로 5초는 최종 조립에서 더한다. 장 전환의 소유자는 editor이며 이 본문 타임록과 합본에는 장 전환 1초를 추가하지 않는다. 편집자가 장 전환을 넣으면 오디오·beat·자막 전체에 동일한 시간 변환을 적용해 총괄이 확정해야 한다. 아웃트로 기준은 제공자 마지막 비공백 문자 종료 +3초이며 실제 청취 결과로 주장하지 않는다.

자막은 승인 원문을 그대로 사용한다. 각 큐의 원문 문자 범위, spoken_text, display_text, 명시적 1~2줄과 본문/문단 시간을 기록한다. 숫자+단위·소수·여러 부분으로 된 기간은 묶고 문장·절·단어 경계에서 대략 55자 이하로 나눈다. 현재는 **시간 없는 자동 분할 후보 138개**이며 editor의 의미·가독성 검토가 필요하다. 표기 변환은 이 task의 원문 유지 지시에 따라 identity로 남겼다.

실행 후 산출물은 `timing_lock.json`, `timing_proposals.json`, `caption_mapping.json`, 본문 기준 `body_captions.srt`, 문단 무음을 포함한 `full_narration.wav` / `.mp3`다. 출력이 이미 있고 입력이 바뀌면 덮어쓰지 않는다. 공통 scenes/state/decisions는 수정하지 않는다.

오프라인 검증은 `offline_checks.mjs`로 재현한다. 실제 입력의 사본을 `.offline-tests` 안에 만들며 비밀 파일을 복사하지 않는다. 사본 생성기에는 fetch 차단을 영구 삽입하고 mock의 양성 대조도 확인한다. 사본의 승인 데이터는 사용자 승인이 아니며 검증 완료 시 사본 authorization도 제거한다. `offline_verification.json`은 실패 경로 11개를 포함한 전체 22개 검사 결과를 기록한다. 라이브 합성, 실제 FFmpeg 디코딩/합본, 연속 재생·청취, 독립 QA는 이 검증 범위에 포함되지 않는다.
