# 시청자 관점 대표 개선 시안

본편에는 적용하지 않았다. 승인 대본·음성·사실값과 기존 r4 MP4를 보존했다.

|시안|실제 파일|향후 검토 위치|배치·자료 유형|
|---|---|---|---|
|가격 기본·S4 추가부담|price_overview.png / price_s4.png|기존 가격 장 약 06:35 부근|큰 억 단위 요약 + 정확 원·타입·확장비 보조행. S4 추가부담은 S5 대비 약 9,700만원. 본청약 공고 사례 도식|
|공급 세 단계|supply_s5.png / supply_s1.png / supply_s4.png|기존 공급 559.37~631.77초|고정 가로 달력, 현재 대상·수량 배지·759→1,253→2,277 누적. S6 430 별도, 주변 전체 공급 아님|
|내 날짜 입력|family_dates.png|기존 가족달력 755.27~815.13초|계약 종료·입학·희망 입주 3카드, YYYY.MM 미입력값, 일시정지 안내. 기존 5개 입주·철도 일정 유지|

공급 모션 `supply_motion_demo_6s.mp4`는 1920×1080 / 30fps / 6초 / 무음 연출 샘플이다. S6→S5→S1→S4 순서이고 본편 발화에 정렬한 클립이 아니다. 실제 납품 자막과 혼동하지 않게 샘플임을 하단 흰 박스에 명시했다.

`compare_mobile_price.png`, `compare_mobile_supply.png`, `compare_mobile_family.png`는 기존 실제 MP4와 새 시안을 각각 512×288로 축소한 비교다. 가격은 전후 강조 상태가 다르므로 화면 상단에 명시했다. 정확 원 단위·세부 조건·보조 달력은 작은 근거층으로 남기고 주 읽기 대상을 크게 만들었다.

카메라 줌·새 사실·임의 개인 날짜·생활비는 추가하지 않았다. 실제 전체 연속 재생·실제 청취·시청자 유지율 측정은 하지 않았다.

재현: `node video-agent-studio/episodes/goyang-changneung-20261015/editor/viewer-review-v1/render.cjs` 다음 `tools/python311/python.exe -X utf8 video-agent-studio/episodes/goyang-changneung-20261015/editor/viewer-review-v1/verify_and_compare.py`.
