# 창릉 v5 배치·재현 안내

주산출물은 `outputs/production-v5/changneung_full_v5r2.mp4`, `changneung_full_v5.srt`, `project_v5.json`입니다. 완성 및 배포 가능 여부는 최종 QA 서명으로 판단합니다. 비공개 v4 업로드는 보존하며 v5 업로드는 승인되지 않았습니다.

1920×1080, 30fps, 24140프레임(13분24.667초). 첫 훅 613프레임 뒤 기존 브랜드 인트로 5초, 마지막 발화 뒤 3초와 아웃트로 10초를 유지합니다. 183개 의미 자막·원문 span과 표시문자열·승인 음성은 v4에서 그대로 계승합니다.

본문은 고정 카메라의 광역 업무지 지도, 실제 단지·학교용지 지도, 열차 시간 막대, 통근 단계 이미지, 공고 금액 분해, 일정축, 조건 비교를 발화에 따라 교차합니다. 152개 provider 문자 이벤트를 실제 프레임으로 연결하며 강조는 다음 관련 대상까지 유지합니다. 지도 줌이나 단발 플래시는 사용하지 않습니다. 제한된 9개 구간에 25프레임씩 실제 선·막대 애니메이션을 넣고 완성 상태를 유지합니다.

지도: LH 공개 WFS 실제 좌표의 독립 색상 시각화, © OpenStreetMap contributors/ODbL, VWorld 대표점. 창릉지구 경계와 GTX-A 창릉역 예정 권역은 서로 다른 형태와 색으로 구분합니다. 호반은 동산동365 주소 대표점이며 출입구·단지경계가 아닙니다. 수색교는 교통시설 안내점이며 확장 공사범위가 아닙니다. 공식 토지이용계획 원본은 전체 비율로 보존합니다. 통근 파노라마는 AI 개념 이미지이고 실제 장소가 아니라는 표기를 지속합니다.

재현(작업 폴더는 저장소 루트):

1. `node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v5/build_project_v5.cjs`
2. `node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v5/render_frames.cjs`
3. `node video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v5/render_hoban_patch.cjs`
4. `tools/python311/python.exe -X utf8 video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v5/assemble_full_v5.py --ffmpeg-bin <승인된 FFmpeg bin> --output-name changneung_full_v5r2.mp4`
5. `tools/python311/python.exe -X utf8 video-agent-studio/episodes/goyang-changneung-20261015/editor/production-v5/freeze_delivery.py`

`rendered_project_v5.json`에는 실제 PNG 경로와 구간 길이가 있습니다. `render_receipt_v5.json`은 기본 전체 출력, `hoban_patch_receipt.json`은 호반 조건문구만의 영향 범위 재출력, `brand_boundary_patch_receipt.json`은 브랜드 직후 763번째 무발화 1프레임을 전편 카드로 맞춘 기록입니다. 캐시 키에 원본 컴포넌트·데이터 SHA를 포함하며 마지막 패치는 명시한 18props만 무효화했습니다. 같은 bundle 폴더를 여러 프로세스가 동시에 다시 만들면 안 됩니다.

일시 캐시: `editor/production-v5/cache/{public,bundle,assembly}`, `outputs/production-v5/frames`. 원본·입력·소스·권리·검수 기록과 구별합니다. 실제 청취 및 전체 연속 재생은 수행하지 않았습니다. 샘플 프레임 열람과 전체 decode 검사 범위만 기록합니다.
