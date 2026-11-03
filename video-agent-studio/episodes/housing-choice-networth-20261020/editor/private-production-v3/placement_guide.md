# 의미 단위 자막 v7 배치 가이드

실제 파일: `outputs/private-production-v3/renders/caption-v7/housing_choice_private_v3_caption_v7.mp4`. 1525.266667초, 1920×1080·30fps·H.264/AAC 48kHz stereo. 전체 decode 통과.

추천 배포 파일은 본편 MP4와 `outputs/private-production-v3/captions_measured.srt`다. 206큐의 명시적 1~2줄 자막을 사용하며 Pretendard 40px·줄 높이 50px·흰 박스 1728×124와 출처 분리 레이어를 유지했다.

자막 외 DOM·GSAP·장면·기존 T 앵커·그림·폰트·오디오 태그·자산은 v2와 같다. 모든 장의 자막 HTML이 변경돼 10장을 재렌더했다. 최종 음성은 v2 완성본의 AAC 스트림을 재인코딩 없이 복사했고 encoded-payload SHA 일치가 확인됐다. 기존 carve·브랜드 접합 fade가 그대로 유지된다.

50장면의 추천 대표 시간·길이·레이어별 근거는 `render_plan.json`, 브랜드 전환·global offset은 `assembly_edl.json`, 변경 50그룹의 native 자막 구간은 `cue_change_groups.json`에 있다. `encoded_frame_plan.json`은 일반 50장면·경계·기존 시각 QA 타깃의 PNG와 SHA를 연결한다. 추가 자막 타깃 추출은 main/build_caption_v7_review_packet.py 담당이다.

자료 유형은 기존 data_chart/editorial_diagram/생활 계획 그림을 계승한다. 새로운 지도·줌·이미지·음성은 생성하지 않았다. 실제 청취·연속 재생·독립 최종 미디어 승인은 main/QA 후속이며 업로드는 수행하지 않았다.
