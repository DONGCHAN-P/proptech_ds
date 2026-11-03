# 왕숙 쇼츠 안전영역 보완 v2

기존 쇼츠 v1의 원본 구간, 30fps, 승인 AAC 음성 패킷과 SRT를 재사용한다. 새 유료 생성이나 플랫폼 업로드는 수행하지 않는다.

재현(프로젝트 루트 PowerShell):
```
tools/python311/python.exe -X utf8 video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/shorts-safe-v2/build_safe.py --preview
tools/python311/python.exe -X utf8 video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/shorts-safe-v2/build_safe.py
tools/python311/python.exe -X utf8 video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/shorts-safe-v2/check_delivery.py
```

`config/vertical_video_safe_area.json`의 기본 프로필을 읽으며, 공통 프로필을 바꾸면 경계 조건을 재검사한다. 기본은 x156..816/y448..1160. 완성 영상을 축소하지 않고 제목44px/자막44px/핵심값36~38px/조건24px로 다시 조판했다. 출력은 각 의미 큐에서 정지판을 교체한다. 지도는 기존 자체 도해만 재사용한다. B17 구간은 지리 혼동 방지를 위해 수치 비교판으로 표시한다.

`layout_bounds.json`은 실제 Malgun Gothic 글꼴의 Pillow textbbox와 전체 지도 래스터 경계를 기록한다. 지도 속 작은 보조 라벨은 확대해서 읽히는 보장을 하지 않으며 핵심 대상은 별도 텍스트로 반복한다. 검증은 프레임·메타데이터·디코드·패킷 동일성 범위이며 실제 청취와 연속 재생은 별도 검수다. 모든 기기·접근성 확대·향후 UI·펼친 설명창까지 완전 대응을 보장하지 않는다.


독립 타겟 출력: 공통 JSON에 검증된 타겟 프로필을 추가한 뒤 --profile <프로필명> --output-tag <타겟명>으로 별도 하위 출력 폴더에 생성할 수 있다. 현재 제공 프로필은 cross_platform_conservative 한 개이며 공통 배치로 세 플랫폼을 지원한다. 새 프로필의 실제 경계와 글꼴은 다시 검증해야 한다.
