# 매매전월세 Jun 교체와 두 썸네일 제작 계획

사용자 승인: `authorization.json`. 대본 v6와 본편 화면은 유지하며 음성·실제 타이밍과 제목·썸네일을 교체한다. 제작 원본과 과거 승인은 보존한다.

- [x] 음성: 54문단·8,949자 Jun/eleven_v4 생성. 공급자 헤더 합계3,577크레딧·추가결제0·자동 유료 재시도0. body1177.433333초·206큐 문자 정렬·54개 고유 요청ID 검증. formal handoff와 timing_lock 기록.
- [x] 썸네일: outputs/launch-proposal-v2에 비교형TH003·??차트형TH004 두 가지를 생성·1280×720 납품. 독립 원본·320px 가독성 검수. 사용자가 TH003 비교형을 선택해 thumbnail_choice.json에 고정.
- [ ] 편집: outputs/jun-production-v1에 새 실제 음성에 맞춘 의미 단위 자막·모션·5초 인트로·10초 아웃트로·BGM 믹스를 생성한다. 기존 이미지는 불필요하게 재생성하지 않는다. 마지막 발화3초 후 아웃트로를 시작한다.
- [ ] 검수: 변경 음성의 숫자 인식·정렬·음량, 모든 자막·글자 경계, 장면·브랜드 경계와 실제 인코딩 표본을 검사한다. 직접 청취·연속 재생 가능 여부를 구분한다. 독립 Codex와 실제 Claude 최종 리뷰에서 required를 닫는다.
- [ ] 게시: 새 exact-hash MP4·SRT·제목·썸네일·설명 묶음에 현재 권한을 적용해 비공개 업로드한다. 채널·private·일정없음·처리완료·한국어CC serving을 확인한 뒤 기존 비공개 exEGpjcqdF0 한 편만 삭제한다. 다른 영상과 로컬 파일은 보존한다.
- [ ] 납품: 영상/매매전월세 짧은 경로와 제작 상태를 갱신하고 새 링크·실제 크레딧·삭제 영수증·검수 범위를 전달한다.

파일 소유권: 총괄=director/launch-and-jun-v1 및 공통 state/scenes/decisions/config; 음성 담당=narration/jun-production-v1 및 preparation의 후속 핸드오프; 편집 담당=editor/jun-production-v1 및 outputs/jun-production-v1; 독립QA=qa/jun-production-v1. 입력·범위 변경을 필요한 담당에게 전달한다.
