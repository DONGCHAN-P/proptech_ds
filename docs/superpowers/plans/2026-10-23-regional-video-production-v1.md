# 지역별 회복 영상 production-v1 제작 계획

> **For agentic workers:** Use the project's video-agent-studio role workflow to execute the bounded tasks below. Director owns shared state; other roles have separate write scopes.

**Goal:** 승인된 대본 v3의 2006년 이후 7지역 데이터 설명을 Jun 음성의 1920×1080 영상으로 제작한다.

**Architecture:** 동결 CSV를 재현 가능한 chart_data.json으로 변환한다. 실제 음성 문단별 정렬이 확정되면 12장면·39비트의 HyperFrames 타이밍을 연결하고 로컬 렌더한다. 브랜드5초·마지막 발화3초뒤 아웃트로10초와 기존 BGM을 재사용한다.

**Tech Stack:** Python3.11, Node, HyperFrames, GSAP/SVG, FFmpeg, 승인 후 ElevenLabs Jun with-timestamps.

**Spec:** episode `outputs/script-review-v3/script_v3.md` / `scenes_v3.json`; `outputs/production-v1-jun/data_contract.md`; `config/channel_style_tokens.json`; 제작 기본가이드.

## Constraints

- 대본 SHA `99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664`; 직접 제작 요청은 현재 대본 승인으로 기록한다.
- 유료 합성 전 별도 예산 결정: 본문4,839자, 수정포함5,807포함크레딧, 추가현금0, 자동재시도없음.
- 2006Q1~2026Q2, 세종 매칭2015Q1 시작, 원거래6640041건과 매칭표본 구별.
- 추가 수집 자료는 이 동결된 분석·대본에 합치지 않는다.
- 예산·완성·게시 승인 별도. 기존 원본·초안·QA 보존.

## Tasks and ownership

- [x] Director: 직접 대본 승인·제작 상태 기록, 39개 원문 입력·정확한 문자수 동결, 읽기 전용 계정 확인·예산 제안 작성·요청.
- [ ] Visual: `visual/production-v1`에서 CSV→JSON 변환, 누락·숫자·검열·해시 검증. 이전 독립 수치검사 승계.
- [ ] Editor: `editor/production-v1`, `outputs/production-v1-jun/project`, `previews`, `checks`에서 프레임 설계·모션·3대표 시안 및 전체39비트 템플릿 준비. 실제 음성 전 provisional.
- [ ] Narration: `narration/production-v1`에서 승인·입력 해시·상한을 검증하는 합성기와 실제 길이·정렬 기반 타이밍/의미 단위 자막 빌더 준비.
- [ ] Director: 사용자 예산 승인 확인 후에만 authorization 기록과 합성 실행. 실제 음성에 맞춰 한 번 타임록.
- [ ] Editor: 실제 타이밍 적용·브랜드/BGM 연결·전체 본편 로컬 렌더.
- [ ] QA: 대표·모든 장면 경계·최장 자막·단위·실제 출력 영상/음성 범위 검수. 필수 수정 후 변경 범위 재확인.
- [ ] Director: 사용자 짧은 경로·입력/미디어 해시·전달 자료·텔레그램 납품. 업로드는 별도 승인 전 실행하지 않음.

## Verification focus

- 실제 금액 축과 정규화 지수 축, ㎡당 가격 분위와 총액 분포를 섞지 않는다.
- 미회복 에피소드에 미래 복귀 표식이 없어야 한다.
- 2/3/5건 민감도는 최근2020~2022 기준 고점 요약이며 미확보 시계열을 만들지 않는다.
- 실제 음성 길이·정렬·자막 단위가 일치하고 출처·자막·차트 영역이 분리돼야 한다.
- decode/신호 검사·정적 프레임 검토와 실제 청취·연속 재생의 범위를 나누어 기록한다.

## Environment notes

## Latest user direction — voice deferred

사용자가 예산 질문에 **음성 생성 보류**로 답했다. 유료 음성 생성과 실제 Jun 타임록은 실행하지 않는다. 기존 영상 제작 요청은 이어서 진행하며, 전체 12장면·39문단을 임시 자막 길이와 재사용 브랜드·BGM으로 연결한 **전체 화면 검토본**을 제작한다. 실제 음성 전용 최종 조립기의 타임록 보호는 유지하고 별도 visual-review 경로를 사용한다. 사용자 보류 상태와 예산 결정 ID `5fe307eed02c`를 보존한다.

- [x] 동결 차트 JSON 변환·17,064 검사와 내레이션 오프라인22검사.
- [x] 대표 시안3개 실제 인코딩·수정 인천v3·지수 단위와 회복일 라벨 교정.
- [x] 전체 visual-review 자막113개 숫자·단위 보호 및 로컬1080p30 렌더. 12장면·39문단, 브랜드 포함855.7초.
- [x] 전체 검토본 디코드·규격·음향 신호 검사. 실제169표본·11시트·원해상도20장 독립 검수: 필수0, 권장REC02(여섯 패널 작은 축 눈금) 유지. 연속 재생·실제 청취·모바일 재생은 미수행.
- [x] 음성 보류·임시 길이·검수 범위를 명시한 자료와 짧은 경로 생성. 단일17MB Telegram 업로드는 write timeout으로 수신 여부 미확인(기존 영수증 보존). 720p 검토 사본을 재인코딩 없이4부분으로 분할했고 전체25,671 비디오 프레임 보존·모든 부분 디코드를 확인했다. 실제 분할 전송 결과는 `output/telegram_deliveries/regional_full_visual_review_v1_parts.json`에서 확인한다.

로컬 검토 원본 SHA: `bba7566079f9d452663f2adccaff8d1a5aff66f41fd298d893ab32c240babd89`. 음성 생성·실제 Jun 타임록·최종 게시 단계는 사용자 보류로 진행하지 않았다. 제작 완료 승인을 부여한 기록이 아니며, 공개 본편 기준 `gyosan-v5-jun`은 유지한다.

HyperFrames usage query: unknown/usage_request_failed. Skills refresh initially npm EACCES; authorized retry returned Unknown skill general-video (remote available catalog differs). Installed general-video instructions remain present and were read; refresh failure is recorded rather than represented as successful. Local render tooling and installed workflow are used, with no paid cloud rendering.
