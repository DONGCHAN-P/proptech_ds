# v15 재현 명령·입력

프로젝트 루트는 `C:/projects/realestate_reco`다. v14 전체 MP4 SHA `ba5bcfdc625f3c15b3f13548f43696e6f7d8b0579c8f8374d46df7d2083966f1`과 `timing_lock_v15.json`을 기준으로 한다. 기존 버전은 수정하지 않는다.

1. `reproduce_issues.py`로 기존 88·165·188·801초 실제 프레임을 추출한다.
2. `render_common_stills.cjs`, `render_school_still.cjs`로 수정된 일자리·철도·학교 소스 프레임을 만든다. `audit_timeline.cjs`는 실제 사용하는 12개 날짜 배열을 불러와 폰트 로드 후 SVG getBBox에 stroke 절반 폭을 더해 1740×95 영역의 잘림을 검사한다.
3. `render_jobs_rail.cjs`는 일자리 2535프레임·철도 3248프레임을 Remotion으로 렌더한다. `finalize_jobs_rail.py`는 원래 구간 AAC와 결합한 실제 부분본을 만든다.
4. `patch_timelines.py`는 기존 지도·자막을 유지하고 시간표 ROI `(80,759,1740,95)`만 정확한 프레임 범위로 교체한다. 남부 통학 23920~24487프레임에는 검수된 직각 안내선 소스의 상단920px만 넣어 원래 하단 자막을 보존한다. 모든 end는 exclusive이며 FFmpeg enable은 end-1까지다. 실제 패치 범위는 `patch_manifest_v15.json`에 있다.
5. `build_cta_project.py`는 승인 CTA 원문 59자·4큐의 제공자 문자 정렬을 읽어 기존301큐를 보존한 전체305큐 SRT·JSON을 생성한다. `render_cta.cjs`는 306프레임 CTA를 렌더한다.
6. `mix_audio_v15.py`는 실제 v14의 0~27353프레임을 디코드한 PCM 43,764,800샘플/채널을 정확히 재사용한다. CTA 음성7.44초 전체와 추가2.76초를 합친 10.2초, 기존 아웃트로10초를 연결한다. 제공자 마지막 발화 문자7.2초부터 아웃트로까지 정확3초다. 실제 청취 판단이 아니다. 총44,734,400샘플/채널, 최종 AAC 재인코딩이다.
7. `assemble_full_v15.py`는 27959프레임으로 조립한다. 선두2407프레임과 기존 가격2890프레임은 과거 중간 산출물과 압축 패킷이 일치하지 않아, 실제로는 v14 캐논의 정확한 구간을 디코드·재인코딩하는 대체 경로를 사용했다. 내용과 시간을 재사용했으며 비디오 바이트 동일을 주장하지 않는다. `technical_full_v15.json`의 두 `original_video_reuse` 값은 모두 false다. 전체 디코드·접합부 PNG·최종 오디오 astats를 생성한다.
8. `prepare_delivery.py`는 원301개 자막과 음성 메타데이터의 정확 보존을 assert하고 최종 MP4/SRT·소스·근거 해시를 고정한다. 독립 QA 후 정확한 완료 결정·ZIP·텔레그램 텍스트는 총괄이 담당한다. 편집자가 중복 완료 알림을 보내지 않는다.

로컬 렌더는 기존 Remotion·Chrome·FFmpeg를 사용한다. 새 유료 이미지·영상 생성과 편집자의 TTS 호출은 없다. 실제 청취·연속 재생은 미확인이다.
