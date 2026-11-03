---
workflow: general-video
flow: automation
storyboard: no
message: 신혼부부 거주 TOP20을 실제 장소와 연결하고 규모·변화·구성을 나누어 읽는다.
audience: 수도권에서 두 사람의 집을 비교하는 시청자
destination: YouTube 본편 1920x1080 30fps + Shorts 1080x1920 30fps 2편
duration: 잠정 본편 480초; 실제 음성 타임록 우선
---

현재 제작 입력은 총괄의 v4 표시 대본(원본 v3에서 반복 연결문13개만 제거)과 최종 무료 TTS v3다. 본편 실제470.95505669초, 홍보33.88687075초, 분석41.10036281초다. I002만 수원시 전체 지명을 읽는 명시적 낭독 매핑을 사용하며 수치/표시문은 보존했다. 비공개 업로드는 총괄 담당이다. 편집 소유권은 editor/top20-production-v1과 타임록 후 지정 outputs/main, outputs/shorts뿐이다.

새 유료 API·클라우드 렌더·새 음성 생성 없음. 사진20장은 photo_assets_v2에서 바이트 동일 복제하고 contain으로 배치한다. 지도 PNG 완성판은 영상으로 쓰지 않고 실제 2024 경계 SVG 좌표를 유지해 새 편집 레이어에 배치한다. 사진은 해당 actual_place와 촬영연도로 이름 붙인다.

본편은 O001/O002 → 20~16위 → I001 변화 → 15~11위 → I002 구성 → 10~6위 → I003 분포 → 5~1위 → C001/E001 순서다. 본편 전체를 하나의 문장 카드로 처리하지 않는다. 각 지역에는 서로 다른 실사·고정 지도·공통 0~16000 척도·해당 거주수가 있다. 세 인사이트는 확대 축의 변화선, 초혼/재혼 개별 막대, 시도별 실제 경계 분포로 구별한다.

실제 음성은 director/top20-production-v1/locked_timing.json의0초 원점 WAV를 사용한다. build.py --script <v4 scene proposals> --timing <locked timing> --shorts <director shorts_locked_timing.json>으로 재현한다. 쇼츠는 총괄이 제공한 완결 문장 컷/완성 WAV만 사용하며 새 소스 절단이나 음성 생성을 하지 않는다. 이미 포함된 꼬리 여백을 한 번만 세어 마지막 발화부터 총3초를 둔다.

렌더 요청은 이미 승인되어 있다. 타임록 뒤3개 프로젝트의 check/snapshot을 확인했다. 음악은 기존 Thinking Music 원본을 재사용하고 설치된 canonical hyperframes-audio carve를 새 음성3개에 각각 적용했다. clean v7 브랜드 시청각은 기존 승인 파일과 같은 해시다. 새 음악/효과음/TTS API 호출은 없다.
