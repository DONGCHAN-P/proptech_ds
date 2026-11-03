# 다산역 주변 배치 보완 · 조각 시안 v2

검토 파일: `outputs/rail-route-proof-v2/namyangju_rail-route-proof_v2.mp4`

80초 조각 중 **40.3~61초**만 보완합니다. 본편 시간으로 **02:14.3~02:35**에 대응합니다. 이전 조각 v1b 및 본편 v3는 보존하며, 본편 연결은 하지 않습니다.

41초부터 다산역 주변의 실제 공개지도 기반 주거·상업·공원 폴리곤과 건물·도로를 바로 보여 줍니다. 실제 좌표와 등록 도형 60개, 건물 394개, 도로 963개를 사용하며 표시한 여섯 대표 시설 이름은 연구 담당이 공식 이름·주소 근거를 연결했습니다. 화면 가독성을 위해 전체 도형에 이름을 모두 붙이지 않습니다.

| 조각 시간 | 강조 |
|---|---|
| 40.3~43.3초 | 주변 배치 전체를 표시하고 다산역 위치 강조 |
| 43.3~48.3초 | 주거 단지 황색 면과 윤곽 강조 |
| 48.3~53.3초 | 상업·쇼핑시설 분홍색 면과 윤곽 강조 |
| 53.3~61초 | 공원·녹지 녹색 면과 윤곽 강조 |

지도에서 경기행복주택, 자이 IVY PLACE, 자연앤푸르지오, 선형공원, 중앙공원, 스페이스원의 실제 위치를 표시합니다. 인출선은 라벨을 읽기 위한 선이며 보행 동선이나 실제 통행 경로를 뜻하지 않습니다. 스페이스원은 다산역 남쪽, 중앙공원은 동쪽에 표시합니다. 도보로 가깝다는 시간·거리 평가는 추가하지 않습니다.

이 지도는 **OSM에 등록된 주변 배치 현황**을 재구성한 것으로, 법정 토지이용계획도가 아닙니다. 무작위 도형이나 허구의 시설을 넣지 않습니다. 개별 단지의 입주 완료, 상가의 현재 영업, 정확한 법적 경계까지 검증한 자료로 표현하지 않습니다. 연구 조회일은 2026-10-15입니다. 원천 자료 및 권리는 `research/dasan-context-v2/context.json`, `facts.json`, `handoff.json`에 있습니다. OSM 기여자 표기는 영상에 고정합니다.

다른 철도·도보·버스 장면, 기존 자막 시간, 원본 음성·BGM WAV는 그대로 사용합니다. 새 TTS·유료 이미지·외부 전송은 없습니다.

재현 명령(프로젝트 루트):

```powershell
tools/python311/python.exe video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/dasan-context-v2/prepare_data.py
tools/python311/python.exe video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/dasan-context-v2/prepare_template.py
node video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/dasan-context-v2/render.cjs
```

실제 MP4 전체 디코딩·스트림과 변경 구간/경계 대표 프레임은 `outputs/rail-route-proof-v2/technical_check.json`에 기록합니다. 실제 청취·연속 재생·문장별 자막 정렬은 미확인입니다.
