# 승인 본편 → Jun 화면 연결

담당 범위는 이 폴더와 동일 상대 경로의 `outputs/.../main`뿐이다. 원본·총괄 시간표·마스터 음성은 읽기 전용 입력이다. 음성 생성·정렬·믹싱은 수행하지 않는다.

## 확정 입력 계약

총괄 입력: `director/top20-split-v4/part1-jun-and-shorts-v1/locked_timing.json`.

- `source_video` + `source_video_sha256`: 승인된 a8d777… 원본. 경로 문자열 또는 `{path, sha256}` 지원.
- `master_audio` + `master_audio_sha256`: 총괄의 Jun·브랜드·BGM 전체 마스터.
- `source_old_sentences`, `main_sentences`: 동일 순서·동일 내용의 본편 90문장. 각 문장에 `sentence_id`, `text`, `reading_text`, `start_s`, `end_s`; 새 문장에는 실제 `words` 포함. 쇼츠 CTA 제외.
- `captions`: 실제 Jun 정렬의 의미 단위 `{sentence_id,text,start_s,end_s}`. 문장별 이어 붙인 표시문이 승인 원문과 같아야 한다.
- `brand_intro: {start_s,duration_s:5}`, `brand_outro: {start_s,duration_s:10}`, `last_spoken_end_s`, `total_s`.
- `source_to_target_anchors: [{source_s,target_s,kind,sentence_id?}]`: 시간 순서, 역행 금지. 실제 `(0,0)`과 양쪽 영상의 끝 경계를 포함한다. 같은 source 시각의 두 target 앵커는 포즈 유지로 처리한다. 같은 target의 두 source 앵커는 컷으로 처리한다.
- 사진 10개의 진입 0.52초·퇴장 0.55초, 브랜드 5/10초는 단위 속도로 보존되어야 한다. 총괄의 앵커가 이를 위반하면 렌더 전에 중단한다.

기준 설명의 **자료·화면**은 승인본 39.7~52.5초의 12.8초 구간을 재사용한다. Jun 발화 길이에 따른 새 위치·전체 길이는 총괄 앵커에서만 받는다. 편집 담당이 새 초수를 추정하지 않는다.

## 구현과 재현

실행 위치: 이 폴더. Python: `C:/projects/realestate_reco/tools/python311/python.exe`.

```powershell
& 'C:/projects/realestate_reco/tools/python311/python.exe' -X utf8 conform.py prepare
& 'C:/projects/realestate_reco/tools/python311/python.exe' -X utf8 test_conform.py
# 실제 Jun lock이 전달된 다음
& 'C:/projects/realestate_reco/tools/python311/python.exe' -X utf8 conform.py compile --version jun-v1
& 'C:/projects/realestate_reco/tools/python311/python.exe' -X utf8 conform.py proofs --version jun-v1
# 실제 proof MP4의 표본 프레임을 본 뒤 jun-v1-proofs/proof_review.json 기록
& 'C:/projects/realestate_reco/tools/python311/python.exe' -X utf8 conform.py render --version jun-v1
```

전체 렌더는 동일 lock SHA의 실제 Jun proof 3개와 내부 검토 기록이 없으면 실행되지 않는다. 새 lock에는 새 버전을 사용한다. `proof_review.json`은 `{status:"passed",lock_sha256:"...",inspected_frames:[...],actual_listening:false,continuous_playback:false}` 형식이다. 프레임을 보지 않고 생성하지 않는다.

FFmpeg 디코더가 원본 YUV420 프레임을 한 번 순서대로 읽는다. target 각 프레임은 총괄의 구간별 선형 앵커로 계산한 **직전 원본 프레임**을 사용한다. 1920×1080 크기를 유지하고 크롭·스케일·광학 보간을 사용하지 않는다. 같은 raw 프레임에서 H.264 CRF16의 편집용 무음 화면과 자막·마스터 음성을 포함한 납품 MP4를 각각 한 번 인코딩한다. 실행 명령·프레임 연결표·입력 SHA·실제 probe·decode 로그는 각 프로젝트에 저장한다. 실제 끝 시간이 프레임 경계 사이에 있으면 최대 1프레임만 끝을 올림한다.

기존 자막은 내레이션 본문 전체의 y922~1080을 불투명하게 가려 문장 사이 공백·끝 호흡에도 남지 않게 한다. 브랜드 구간은 가리지 않는다. 사진 출처·지도 범례·정리된 푸터·우상단 OSM 표시는 y922 위에 그대로 남는다. 흰 자막 박스는 내레이션 구간에 계속 유지한다.

HF `index.html`에는 연결된 무음 화면, 불투명 자막 레일, 편집 가능한 본문 텍스트, 별도 마스터 오디오를 기록한다. 최종 FFmpeg는 같은 자막 데이터·폰트·줄바꿈을 ASS로 렌더한다. CSS와 libass의 서로 다른 폰트 크기 기준은 Pretendard의 실제 hhea/em 비율로 보정한다. `captions.ass`의 시각 정밀도는 0.01초, MP4는 30fps다.

## 준비 실증과 검수 범위

`source-smoke-v*`는 **승인본의 기존 실제 시간표를 그대로 쓰는 무음 실증**이다. Jun 새 시간표·새 발음·청취 검수의 증거로 사용하지 않는다. 새 전체 본편으로 배포하지 않는다. `question_brand`, `photo_to_map`, `new_price_focus` 세 MP4와 각 HF 프로젝트·표본 프레임·render_receipt가 있다. v1은 폰트 크기 차이의 보존 근거이고 v2는 폰트 보정 검증본이다.

현재 HyperFrames CLI는 `0.8.181`; 사용량 조회는 `unknown/usage_request_failed`였다. 외부 전송·유료 호출·업로드를 실행하지 않았다. 독립 QA와 실제 청취·연속 재생은 별도 단계다.

## ?? v3 ??

`caption_stage_v3.py`? v1 ?? ??? AAC? ????? ?? ??? ?? ? ????? ????. `test_caption_stage_v3.py`? ?? 20,452? ????? ?? 181? ?? ?? ??? ???? ????? ????. ?? ? `verify_caption_stage_v3.py native`, `verify_caption_stage_v3.py encoded`? ?? ???? HF? ????. ?? v1/v2 ????????MP4? ????.
