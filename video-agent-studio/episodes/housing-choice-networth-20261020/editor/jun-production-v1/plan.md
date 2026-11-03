# Jun 교체 편집

수정 범위는 editor/jun-production-v1, outputs/jun-production-v1이다. 최종 대본 SHA·206개 의미 단위·줄바꿈·caption-v7 화면을 보존한다. 실제 Jun 정렬 이전에는 `build.py --prepare`만 실행한다.

1. narration/jun-production-v1의 formal handoff·final_timing·PCM·문자 정렬을 해시와 함께 수신한다.
2. 원문 문자 위치 → 기존 발음 대응표 → 실제 Jun character alignment로 장면 및 모션 앵커를 계산한다. 자막은 206개 그대로 새 start/end를 적용한다. 이전 HTML은 수정하지 않는다.
3. 새 음성으로 canonical carve/ducking을 계산하고 현재 source·전체 자막 시점/글자 경계·모션 경계·seek·CLI 0.8.181을 검사한다.
4. 기존 5초 인트로·10초 아웃트로와 음악을 사용해 새 장들을 렌더한다. Jun 음성 속도는 변경하지 않는다. 마지막 실제 발화 +3초(30fps 상향 정렬)에 아웃트로를 배치한다.
5. 새 MP4의 스펙·전체 AV decode·신호를 측정하고 모든 장면·접합 경계·최장 자막의 실제 프레임을 추출한다. 검수 패킷·SRT·EDL·scene starts·metadata chapters·placement guide·handoff를 전달한다.

독립 Codex/Claude exact-final 검수와 업로드/기존 비공개 삭제는 총괄 담당이다. 실제 청취·연속 재생은 이 런타임에서 하지 못하며 통과로 기록하지 않는다.
