# guide-v3 제한 preview 검수

**required_open_issues: 0 / critical: 0 / recommended: 0**

실제로 확인한 preview 화면에서 필수 결함을 발견하지 않았다. 본 preview QA가 제기하는 전체 렌더 차단 사항은 0건이다. 전체 제작 가이드나 최종 MP4 합격 판정은 아니다. 사용자 시간상한 지시에 따라 추가 탐색 없이 마감한다.

## 실제 확인한 증거

- 최신 contact sheet 1~7을 직접 열어 57개 시점의 축소 표본 화면을 확인했다. 대표 원본 PNG 12개도 직접 열었다. 연속 재생이 아니다.
- timing.json은 162개 의미단위·162개 자막·8개 장이며 잠정 길이 약 729.367초다. 음성은 보류 상태다.
- 챕터 이미지 8개는 실제 파일 SHA256이 모두 다르다. 전환 화면도 각 장의 주제에 맞게 구분돼 있다.
- assets.json의 새 이미지 9개와 각 local_file의 존재를 확인했다. 새 이미지 전체의 해시를 전량 재검증한 것은 아니다.
- 본문 사진 5개는 asset_usage상 각각 한 장에서만 사용된다. 연속한 두 의미단위 동안 사용하는 창이며, 다른 장으로 돌려 쓰지 않는다.

| 사진 | 장 | 사용 창(초) | 길이 | 뒤의 설명 도식 |
|---|---|---|---:|---|
| smallroom | L002 | 97.233~104.333 | 7.10초 | population |
| budget | L003 | 169.000~175.633 | 6.63초 | tenure |
| relocation | L004 | 274.733~283.767 | 9.03초 | timeline |
| supply | L005 | 412.500~419.433 | 6.93초 | gap |
| commute | L006 | 482.933~490.200 | 7.27초 | journey |

모두 최대 12초 이하다. 후단 도식은 contact sheet에서 확인했으며, 사진과 도식 사이 모든 프레임의 연속성을 검사한 것은 아니다.

## 요청한 수정의 확인

- **단면은 L002만:** manifest의 households mode 3개는 L002에만 있다. 79.1초 원본 PNG에서 집 단면과 세 컵을 확인했다.
- **실제 FP59는 L003만:** floorplan mode 8개는 L003에만 있다. 189.617초 원본에서 남양주왕숙 A-1 59A와 LH 공식 분양 평면·분양 계획도·논문 표본단지 아님 표기를 확인했다.
- **작은 월셋집 강조:** 177.967초 원본에서 해당 발화와 작은 공간·임차 칸의 파란 강조가 일치한다.
- **챕터 출처와 chrome:** 챕터 8개 축소 표본에서 본문 상단 chrome이 보이지 않는다. 272.733초·666초 원본에서 흰 글자의 AI 개념 이미지 출처와 실제 장소·통계 증거 아님 표시를 확인했다. 하단 고정 흰 박스는 챕터에서도 유지한다.
- **AI 사진 표기:** 본문 사진 5개 원본에서 AI 개념 이미지·실제 장소 아님 표기가 보인다.
- **R5 두 결과 대조:** U06은 524.567~528.600초, U07은 528.600~531.333초다. 제공 snapshot에 해당 구간이 직접 포함되지 않아 대조 화면은 **unchecked**다. timing의 문구·focus를 확인한 것과 실제 화면을 본 것을 구분한다. 이를 확인된 결함으로 기록하지 않는다.

## 원본 PNG 확인 목록

모두 `outputs/guide-v3/checks/storyboard/` 아래 파일이다.

`frame-06-at-79.1s.png`, `frame-07-at-99.167s.png`, `frame-14-at-170.617s.png`, `frame-15-at-177.967s.png`, `frame-16-at-189.617s.png`, `frame-21-at-272.733s.png`, `frame-22-at-276.833s.png`, `frame-31-at-413.783s.png`, `frame-38-at-484.867s.png`, `frame-41-at-533.35s.png`, `frame-52-at-666s.png`, `frame-55-at-712.583s.png`.

## 한계와 인계

자막·focus의 화면 일치는 표본 검수다. 162개 timing 항목과 작성자 원본의 모든 필드에 대한 새 전량 비교는 하지 않았다. 앞선 `semantic_review.json/md`의 30문단·162개 의미단위 원문 검수는 별도 범위다. 논문·수치 원자료는 재조사하지 않았다.

기존 check receipt는 exit_code 0, ok true, errors 0이며 `composition_file_too_large`, `timeline_track_too_dense` 경고가 있다. snapshot receipt도 exit_code 0이다. 이번 QA가 기술 check를 새로 실행한 것은 아니며, 기술 0 error를 전체 가이드 합격으로 해석하지 않는다. source 기술 문제는 maincheck 담당 범위다.

실제 MP4·연속 재생·실제 청취·음성 sync·각 경계의 모든 프레임·최대 줌은 **unchecked**다. 렌더 후 MP4 QA에서 R5 U06~U07 대조 화면과 경계·가독성을 확인해야 한다. 이는 발견한 결함의 수정 요청이 아니라 미확인 범위의 인계다.

본 preview QA의 필수 수정 대기는 없다. 기존 계획의 전체 렌더로 인계한다. 제작 소스와 공통 상태를 바꾸지 않았으며, 이번 작성 범위는 `qa/guide-v3/preview_review.json/md` 두 파일뿐이다.
