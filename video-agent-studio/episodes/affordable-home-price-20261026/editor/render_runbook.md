현재 상태: 실행 명령 준비 완료. Main의 정확한 승인 전에는 본편 렌더하지 않는다.

입력은 승인 대본 v2, 실제 음성 v3, 시각 수정 v4다. 10장·45장면·150큐, 합본 1,186.033333초/35,581프레임이다. v3 소스는 `outputs/private-production-v1/source-archive/measured-v3-before-visual-v4/`에 보존했다.

Main은 `editor/main_render_authorization_template.json`의 현재 SHA와 구조를 참고해 실제 승인 파일을 `director/production-v1/`에 작성한다. 템플릿의 `approved:false`는 승인 기록이 아니다. 실제 승인에는 source_qa/audio_qa/edl_review의 경로와 SHA가 필요하다. 소스 필수 두 건과 ASR 델타가 닫히기 전에는 승인하지 않는다.

작업 루트 `C:/projects/realestate_reco`에서 승인 후 실행할 명령:

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/editor/render_pipeline.py --check-gates --authorization director/production-v1/render_authorization_v3_visual_v4.json
tools/python311/python.exe -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/editor/render_pipeline.py --execute --authorization director/production-v1/render_authorization_v3_visual_v4.json
```

`--execute`는 승인·현재 입력 SHA를 검사한 뒤 순서대로 10장을 렌더하고, EDL 합본·전체 AV 디코드·인코딩 프레임 추출까지 실행한다. 장마다 4 workers, 장별 캐시를 사용한다. 동일 입력·출력 SHA의 완료 장만 재사용한다. 다른 버전/불완전 MP4가 있으면 덮어쓰지 않고 중단한다. CLI는 기존 0.8.181이며 업데이트·자동 설치·텔레메트리를 비활성화한다.

합본은 H.264 CRF18/yuv420p/1920×1080/30fps, AAC 192kbps/48kHz/stereo다. 인트로 150프레임·아웃트로 300프레임을 유지하고, 13개 구간의 최종 atrim 뒤에 8ms in/out fade를 적용한다. 이는 예방적 접합 처리이며 청취된 결함을 주장하지 않는다. 기존 편의 AAC 스트림은 복사하지 않는다.

결과 위치:

- MP4: `outputs/private-production-v1/renders/measured-v3-visual-v4-r1/affordable_home_price_private_voice_v3_visual_v4.mp4`
- 실제 기술 영수증: `editor/render_receipt.json` 및 렌더 폴더의 동명 파일. final_file/final_sha256/captions_file/captions_sha256/decode_returncode/ffprobe/duration과 입력 manifest SHA를 포함한다.
- 전체 프레임 증거: `outputs/private-production-v1/encoded_frame_plan.json` 및 렌더 폴더의 `encoded-evidence/`. 준비 시에는 `encoded_frame_plan.prepared.json`만 고정하며 실제 PNG를 만들었다고 기록하지 않는다.
- 16개 중요 원본 크기 PNG manifest: `outputs/private-production-v1/encoded_critical_frames.json`.
- Main 미디어 패킷 도구용 PNG 목록: `editor/encoded_review_image_list.json` (16컷+45장면 개요 PNG, 중복 파일 제외).

프레임 추출만 재개할 경우 동일 MP4 SHA 및 성공한 전체 AV 디코드 영수증을 먼저 확인한다:

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/editor/encoded_evidence.py --extract
```

기술 영수증과 표본 PNG는 실제 청취·연속 시청·최종 미디어 승인·업로드 승인을 대신하지 않는다. 릴리스 패키징과 외부 전송은 Main 담당이다.
