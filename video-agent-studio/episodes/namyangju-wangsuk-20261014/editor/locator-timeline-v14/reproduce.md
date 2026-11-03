# v14 재현 순서

작업 루트는 `C:/projects/realestate_reco`다. 기존 버전은 수정하지 않는다. Remotion 의존성은 `video/node_modules`, 렌더 브라우저는 기존 로컬 headless Chrome을 사용한다. 새 API 호출은 이 편집 절차에 없다.

1. `render_price_still.cjs` → `assemble_price.py` → `check_price_audio.py`: M007 원본 15758~18648프레임의 동시 가격 지도.
2. `render_detail.cjs` → `finalize_detail.py` → `check_detail_audio.py`: 8190~15758 상세 위치판·시간표. `source_identity.cjs`는 visual cue hold와 구조 전환 인벤토리다.
3. `render_common.cjs` → `render_outside_corrected.cjs` → `finalize_common.py` → `finalize_outside_corrected.py`: 일자리·교통·외부 비교 시간표. 외부 비교표 A3 타입은 `outside_rows`에 84A1을 적용한다.
4. `assemble_prefix.py`: 기존 선두 2407프레임과 변경 구간을 연결한다. 전체 21636프레임, 오디오는 원본 단일 AAC를 721.2초로 한 번만 자른다.
5. `build_closing_project.py` → `render_closing.cjs`: 승인 v7의 실제 문자 정렬로 M008/M009 자막과 5717프레임 후반을 생성한다. 현재 소스는 요약표의 전매·거주 조건까지 포함한다.
6. `mix_full_audio.py`: 원본 앞부분 PCM 34,617,600샘플을 정확 재사용하고 새 음성·자체 BGM·기존 아웃트로를 연결한다. 최종 44,244,800샘플/채널, AAC 재인코딩.
7. `assemble_full.py`: 21636프레임 prefix + 5717프레임 새 후반 + 300프레임 기존 아웃트로. 총27653프레임. 실제 디코드·경계 추출·astats를 수행한다.
8. 독립 QA의 `qa/locator-timeline-v14/final_review.json`이 확정된 뒤 총괄이 정확 파일의 completed 결정과 ZIP을 만들고 최종 텔레그램 텍스트 알림을 보낸다. editor의 `notify_full.py`는 중복 방지를 위해 이번 최종 알림에는 실행하지 않는다.

부분본 가격·상세·prefix 알림은 각각 receipt 파일로 이미 기록했다. 영상 파일 외부 전송은 없다. 청취·연속 재생은 별도 확인하지 않았다.
