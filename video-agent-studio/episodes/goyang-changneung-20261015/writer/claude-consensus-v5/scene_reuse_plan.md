# v5 화면 재사용 계획 · 대본 검토용

영상 기준: outputs/production-v5/changneung_full_v5r2.mp4. 기존 음성·영상·자막은 보존한다. 아래는 제작 실행·새 시간표 확정이 아니다.

| 장 | 전달할 새 역할 | 재사용 가능한 기존 실제 자산 | 변경 |
|---|---|---|---|
| M000 | 기존집 대 새집이라는 질문·시리즈 연결 | state_previous, 브랜드 인트로 | 전편 카드 짧게, 장문 예고 압축 |
| M001 | 창릉 전체와 주변 도시의 관계 | state_official_whole, state_plan_overview, state_agenda | 실제 필지와 locator 유지 |
| M002 | 기존 직장까지의 이동 구조 | state_jobs_question/evidence/region/connections, state_train_compare | 숫자보다 실제 위치·이동 단계 강조 |
| M003 | 입주 초기 교통과 향후 철도 | state_current_route, state_bus_evidence, state_rail_calendar, state_road_focus | 동일 화면 정지 반복 대신 발화 대상만 전환 |
| M004 | 3가격과 추가 부담 | state_price_conditions, state_current_price_range | 정확 가격표 보존, 3회 워터폴 대체 |
| M005 | 학교 달력·생활권 연결 | state_school_detail/calendar, state_existing_facilities | S5 두 달·S1 미정·S4 같은 달을 동일 문법으로 비교 |
| M006 | 확인된 입주 부분집계와 거래 구조 | state_supply_calendar, state_restriction_origins, state_disposal_structure | S6 보조 사례, 지역 전체공급으로 표기 금지 |
| M007 | 같은 예산의 실제 기존집 | state_alternative_detail, state_regional_choice | 기존 6단지 가격·표본·실제 위치 유지 |
| M008 | 내 달력에 적용 | state_household_calendar, state_funding_calendar, state_life_preparation | 기존 장 보완·축약. 신규 장이라고 주장하지 않음 |
| M009 | 조건별 후보와 시리즈 회수 | state_candidate_detail, state_conditional_choice, state_next_episode, 기존 아웃트로 | 한 종합판에서 조건·가격 차이 회수 |

자산 이름은 outputs/production-v5의 기존 PNG 기준이며 아직 재렌더/새 MP4 제작은 안 했다. 새 음성이 생성되기 전 과거 타임코드를 v5에 승계하지 않는다. 현재 새 낭독문 전체가 편집돼 기존 음성을 얼마나 재사용할 수 있는지는 문장 정렬 후에만 산정한다.

## 새 지도 자료의 재사용 검토

10월16일 기존 LH 창릉 WFS 733개와 10월18일 지도 작업에서 받은 창릉 733개의 geometry/properties는 일치한다. 동적 feature ID는 비교에서 제외했다. 상세 결과 map_reuse_check.json. 이는 계획 승인일·입주·개교가 최신 확정됐다는 뜻이 아니다.

OSM 철도경로 22개 노선군은 운영 교통의 위치 보조자료다. 계획 GTX-A 창릉역·고양은평선 위치/개통일을 이 자료에서 생성하지 않는다. 웹 지도 화면 자체를 촬영하는 대신 기존 영상 색·글꼴·locator·고정 구도로 필요한 도형을 렌더한다. 실제 OSM 타일 서버를 자동 영상 촬영용으로 대량 조회하지 않는다.

## 아직 남은 확인

- 창릉 및 주변 지역 전체의 연도별 공급량은 미확보. 원고는 확인된 3후보 공고 규모와 S6 보조사례까지만 설명한다.
- 2022년 공개 열차표는 사례로 남기며 2026년 실측 통근시간으로 표시하지 않는다.
- 원고 합의·사용자 대본 승인·새 음성 예산·본편 완료·업로드는 서로 다른 단계다.
