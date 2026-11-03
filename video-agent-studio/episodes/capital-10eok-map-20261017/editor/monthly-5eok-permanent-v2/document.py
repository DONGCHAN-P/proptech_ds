from pathlib import Path
import json,hashlib
E=Path('video-agent-studio/episodes/capital-10eok-map-20261017');p=E/'editor/monthly-5eok-permanent-v2/build_cache.py';t=p.read_text(encoding='utf8');t=t.replace("static.save(C/'static.png',compress_level=1)","d.rectangle([294,1822,312,1840],fill=G.navy);static.save(C/'static.png',compress_level=1)");p.write_text(t,encoding='utf8')
O=E/'outputs/monthly-5eok-permanent-v2'
(O/'README.md').write_text('''# 월별 5억 영구 소등 쇼츠 v2

2006.01~2026.10, 수도권 전용 83㎡ 이상 85㎡ 미만, 단지별 계약월 실거래 중위값을 사용합니다. 5억원과 정확히 같은 값은 초과가 아닙니다.

최초 관측이 5억원 이하이면 불이 켜집니다. 이후 무거래 달에는 켜짐을 유지하고, 처음 5억원을 초과한 월 첫 프레임부터 영구 소등합니다. 가격이 다시 내려와도 재등장하지 않습니다. 최초 거래부터 초과인 단지는 처음부터 켜지지 않습니다. 첫 관측 전도 표시하지 않습니다.

이는 현재 시세나 매수 가능 가격이 아니라 **누적 임계 초과 관측 이력**을 그린 영상입니다. 차트와 카운터는 **5억 초과 이력이 없는 단지 / 누적 관측 단지**입니다. 무거래 달 가격 보간이나 현재가 추정은 하지 않았습니다.

신규 단지 등장은 짧게 밝아지고, 기존 켜짐 단지는 무거래에 따른 밝기 변화가 없습니다. 초과는 해당 월 시작부터 즉시 꺼집니다. 매 프레임 차트 커서는 진행하지만 수치는 실제 해당 월 누적값이며 보간하지 않습니다. 좌표는 고정입니다.

57초·1080×1920·30fps·1710프레임·무음. 첫 3초 및 끝 4초 정지 유지. 별도 10초 발췌를 제공합니다.

## 범위와 한계

공식 공간정보 연결 8,288단지를 표시하고 미연결 884단지는 제외했습니다. 마지막 2026.10은 부분월이며 최대 계약일은 2026.10.10입니다. 기존 원문 파일별 수집 시점이 혼재하므로 오늘까지 모든 신고를 갱신한 전수자료라는 뜻은 아닙니다. 큰 지도 구도는 앱 우측·하단 UI와 일부 겹칠 수 있습니다. 모든 기기에서 모든 점이 보인다고 보장하지 않습니다.

기존 월별 원문·집계·기존 결과물을 수정하지 않았습니다. 신규 API·유료 생성·음성·음악·업로드·외부 전송은 없습니다. 실제 연속 재생·청취·실기기 재생 검수는 수행하지 않았습니다.

재현: research/monthly-5eok-v1/monthly_arrays.npz의 실월 상태에서 cumulative_observed와 ever_breached를 계산하고, editor/monthly-5eok-permanent-v2/build_cache.py 및 render_motion.py를 순서대로 실행합니다. 최종 기술 정보와 SHA는 technical_receipt.json, 독립 검수는 qa/monthly-5eok-permanent-v2를 참고합니다.
''',encoding='utf8')
print('README_READY')
