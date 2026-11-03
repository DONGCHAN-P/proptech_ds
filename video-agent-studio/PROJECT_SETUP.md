# realestate_reco 설치 상태

2026-10-13 로컬 압축 해제 패키지를 복사하여 적용했다. 원본 폴더는 보존했다.

- 운영 루트: `C:/projects/realestate_reco/video-agent-studio`
- 역할 정의: `C:/projects/realestate_reco/.codex/agents`의 TOML 7개
- 프로젝트 연결: 루트 `AGENTS.md`
- 원본 패키지의 START_HERE / CHECKS / WORKFLOW에 적힌 설치 차단 상태는 이전 작업방의 기록이다. 이 프로젝트에서는 파일 배치에 성공했다.
- 네이티브 에이전트 목록 노출과 재시작 후 자동 로딩은 아직 검증하지 않았다. 현재 대화에서는 TOML 지침을 작업 메시지로 전달해 사용할 수 있다.
- `.codex/agents` 설정을 사용할 때는 studio_root를 위 운영 루트로 명시한다. TOML의 상대 경로 추론에 맡기지 않는다.
- 설치 과정에 새 음성·이미지·영상 생성 API는 호출하지 않았다.

다음 요청 예: “이 제작팀으로 스타일 시안을 검토해줘. 아직 본편에는 적용하지 말고 visual과 qa의 의견을 정리해줘.”
