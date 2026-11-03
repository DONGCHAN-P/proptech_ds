# 확인한 범위

- Codex 공식 standalone custom agent TOML 형식의 필수 항목 name, description, developer_instructions를 7개 파일 모두 파싱하여 확인.
- JSON 양식과 기존 작업 예시의 JSON 문법 확인.
- 예시 장면표가 참조하는 기존 본문 이미지 10개 파일 존재 확인.
- 별도 담당의 읽기 전용 모의 검토: 썸네일 배경-only 요청에서 불필요한 리서치/음성/전체 편집 생략, 전사 실패 뒤 ZIP 해제로 범위 축소 시 전사 재시작 금지.
- 검토 후 수정: 총괄 공통 파일 작성권 명확화, 중단 작업 취소 및 요청 무효화 절차, 예시 episode의 reference_only/실행 금지, 썸네일 TH ID, 해상도 조정과 업스케일 기록.
- 현재 작업방의 AGENTS.md에 제작팀 파일을 읽어 역할별 subagent로 위임하는 사용 지침 저장.

확인하지 않은 범위: 네이티브 .codex/agents 자동 등록/목록 노출, 설정 이름만으로 자동 실행, 새 전체 영상 제작에 대한 통합 실행. 이번 요청에서는 유료 이미지·음성 생성이나 기존 영상 재제작을 실행하지 않았습니다.

자동 등록은 현재 권한 정책이 .codex/agents 쓰기를 거절하여 진행하지 못했습니다. 구성 파일을 읽어 작업 메시지로 넘기는 방식과 네이티브 자동 등록을 구분하세요.

공식 형식 근거: https://learn.chatgpt.com/docs/agent-configuration/subagents
