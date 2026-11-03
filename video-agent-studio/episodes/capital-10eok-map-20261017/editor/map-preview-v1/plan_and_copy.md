# 로컬 지도 시안·입력 계약

현재 범위는 실제 데이터 대표 3PNG와 6초 무음 스타일 MP4, 재사용 지도·폰트·렌더러 준비다. 최종 본편, 음성·음악, 외부 업로드/전송은 실행하지 않는다. 대본 gate는 미확정이다.

자료 한계: 보유 master의 계약연도 단지 중위값이며 83≤전용<85㎡. API 월별 page1 잘림으로 일부 거래 누락이 확인되어 전체 단지/거래의 결과나 가격분포 결론으로 해석할 수 없다. 좌표는 candidate_unverified이며 불명/중복 의심 등을 제외한 후보만 내부 시안에 사용했다. 공급자 및 저장·재사용권 검토가 남아 있다. 화면에 '데이터 검증 중 · 시안', '국토부 보유자료·일부누락'을 고정했다.

원본 packet은 변경하지 않았다. 보유자료 전체의 관측/10억이하 통계, 지도에 표시 가능한 후보의 관측/이하 통계, 좌표 제외수를 분리했다. 정확히 10억원은 포함하며 초과는 완전히 숨기고 다시 이하이면 재등장한다. 미거래는 회색, 최초관측 이전은 숨김, 이전 가격의 역채움/carry-forward는 하지 않는다. 총괄 결정에 따라 준공연도를 기준으로 실제 존재 거래를 삭제하지 않는다. 최초 버전에서 빠졌던2006의2단지는복원했고 first_valid_trade_year 이전만 숨긴다.

원본 경계는 assets/geo/sudogwon_sgg.geojson, 77개 시군구. 로컬 파일에는 CRS가 없으며 LICENSE의 ° 설명과 실제 투영좌표가 모순이다. SGIS 출처·공식 UTM-K 설명을 결합한 EPSG5179 추정과 검증된 강남역이 서울(서초구) 면내에 들어오는 검사만 기록한다. 파일별 CRS 인증·정밀 지오코딩으로 표현하지 않는다. 원본 경계/라이선스는 수정하지 않았다. 인천 원거리 도서는 고정 inset, 모든 후보점은 한 번 고정한 main extent 안에 들어온다. 연도마다 줌/extent 변화 없음.

현재 문구 초안:
- 제목: '10억 이하, 수도권 84㎡'
- 규칙: '단지의 한 해 거래 중위값이 10억원을 넘으면 점을 숨깁니다.'
- 재등장: '다시 10억원 이하가 되면 점이 돌아옵니다.'
- 미거래: '회색은 그 해 거래가 없는 단지입니다.'
- 부분연도: '2026년 · 부분연도'. master의 최종 계약일은2026.10.10이나 그 날짜까지 신고가 완결됐다는 뜻은 아니다. 수집일 전수 확인 후 별도 표시해야 한다.

향후 대본/자료/권리 gate 후의 제안(실제 실행하지 않음): 규칙 소개3초 + 2006~2025 각1.6초(32초) + 2026부분연도2.5초 + 규칙/범위 마무리4.5초 = 약42초. 고정 지도에서 연도·숫자·점 상태만 바꾸고 효과음/음성/음악은 별도 승인 범위를 따른다.

재현(저장소 루트):
1. `tools/python311/python.exe -X utf8 <episode>/editor/map-preview-v1/prepare.py`
2. `tools/python311/python.exe -X utf8 <episode>/editor/map-preview-v1/render_preview.py --packet <episode>/research/annual-map-v1/map_packet_v1.json`
3. `tools/python311/python.exe -X utf8 analysis/validate_vertical_layout.py <episode>/outputs/map-preview-v1/layout_bounds.json --report <episode>/outputs/map-preview-v1/layout_validation.json`
4. `tools/python311/python.exe -X utf8 <episode>/editor/map-preview-v1/assemble_preview.py --ffmpeg-bin <기존FFmpeg경로>`

폰트는 기존 Pretendard WOFF2를 기존 Node의 Brotli 기능과 기존 fontTools로 로컬 TTF 변환했다. 새 패키지를 설치하지 않았다. Pillow로 한번 만든 고정 경계 캐시 위에 gray→blue 순서로 실제 점을 합성한다. 세 PNG 렌더 약0.3초; 전체 프레임을 매번 지리 재계산하는 방식이 아니다. UI 모사는 내부 보수적 가정이며 실제 기기/앱 재생 증거가 아니다.

후속안 제안(미구현): 고정 수도권 main과 별개로 좌측 바다 빈 공간에 서울 고정 상세 inset을 두되 복제 점은 통계에 다시 세지 않는다. 서울·인천·수원 안내 앵커를 최소 표기한다. 관측수/이하수 이중 나열 대신 명확한 보유자료 분모의 이하 비율을 사용해 정보량을 줄인다. 현재 데이터·권리 보완 전에는 이 개선안을 본편에 확장하지 않는다.
