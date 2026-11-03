# Literature Video Visuals Implementation Plan

> For agentic workers: use executing-plans for the main implementation and the studio's visual/QA roles for bounded tasks.

**Goal:** 승인한 논문 인용형 대본의 8장면을 담은 로컬 화면 검토용 MP4와 재현 가능한 HyperFrames 프로젝트를 만든다.

**Architecture:** 새 `outputs/literature-visual-v1`에만 화면 프로젝트를 작성한다. 장면별 sub-composition과 하나의 자막 트랙으로 구성하고, 텍스트 기반 임시 시간표는 실제 음성 시간표와 분리한다. 총괄이 데이터·공통 프레임·통합을, visual이 L002–L006 도식 제작을, QA가 실제 출력 프레임 검수를 맡는다.

**Tech Stack:** 로컬 HyperFrames/GSAP, Python 3.11, 기존 Pretendard·브랜드 자산, FFmpeg.

**Spec:** `video-agent-studio/episodes/regional-price-recovery-20261022/outputs/literature-video-v1/영상구성안.md`, `내레이션_초안.md`, `장면표.json`, `인용근거.json`.

## Global Constraints

- 승인 대본 SHA256 `5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b` 유지.
- 사용자 회신 `이 대본으로 화면 제작 진행`은 이 버전의 화면 제작 승인이다. 음성 생성 보류·업로드 미승인은 유지한다.
- 1920×1080, 30fps, 8장면. 기존 원본·대본·MP4 보존. 새 유료 서비스·텔레그램 전송 없음.
- 명목 자체 지수·논문 결과·가상 예시·종합 해석·후속 과제를 화면에서 구분한다.
- source는 자막 아래 별도 영역. 채널의 크림 바탕·Pretendard·번호형 소제목·흰 자막 형식을 유지한다.
- 실제 음성·마지막 발화·연속 재생·청취를 확인했다고 주장하지 않는다.

## Review Focus

- 분기·기간·기준분기와 실제 데이터 곡선이 일치하는가.
- 가상 가구·공급·통근 그림을 실제 지역 관측으로 오인하게 하지 않는가.
- 재건축 이주 공백과 순증 공급을 같은 뜻으로 그리지 않는가.
- 자막/출처/장면 전환에서 잘림·겹침·빈 프레임이 없는가.
- 긴 낭독 중 같은 정지 도표를 반복하지 않고 문장의 설명 대상이 바뀌는가.

## Tasks

- [x] 승인·보존 해시를 기록하고 새 제작 폴더·임시 시간표·자막 매핑·로컬 자산을 준비한다.
- [x] 공통 화면 규격과 프레임을 만들고 L001·L007·L008을 제작한다.
- [x] visual 역할에 L002–L006의 독립 파일 제작을 위임한다. 전체 대화·자격증명은 전달하지 않는다.
- [x] 대표 가구·이주·교통 장면을 실제 픽셀로 확인하고 공통 결함을 고친다.
- [x] HyperFrames check, sub-composition 표본, 숫자·문구·범위 검사를 수행한다.
- [x] 로컬 Studio preview를 열고 임시 타이밍의 화면 검토본을 렌더한다.
- [x] 실제 MP4의 대표·전환 프레임과 전체 디코드를 확인하고 독립 QA의 필수 항목을 닫는다.
- [x] 검토 범위·임시 타이밍·음성 없음·출처·재현 입력을 안내하고 짧은 로컬 경로로 전달한다.

기존 사용자의 계속 진행 지시와 이번 화면 제작 승인에 따라 별도의 실행 방법 승인 없이 진행한다. 정밀 인과 분석이나 새 대본 작성은 범위에 추가하지 않는다.
