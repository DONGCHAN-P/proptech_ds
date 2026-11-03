# 음성 없는 전체 검토본

현재 세션1596, 소유 PowerShell PID24020에서 본문을 렌더 중이다. 같은 렌더를 중복 실행하거나 프로젝트/자막/폰트/차트 입력을 바꾸지 않는다. 로그는 `outputs/production-v1-jun/checks/visual-review/render_body.log`, 종료 코드는 같은 폴더 `render_exit.json`에 기록된다. 실제 Jun용 index.html과 실제 타임록 guard는 유지했다.

현재 직접 실행 명령(project cwd):

```powershell
npx.cmd --offline --no-install hyperframes@0.8.181 render --composition visual-review.html --output ../previews/full_visual_review_body_v1.mp4 --fps 30 --quality looks --workers 2 --experimental-fast-capture=false --strict
```

본문 렌더 종료코드0 및 파일 완성 후, 저장소 루트에서:

```powershell
tools/python311/python.exe -X utf8 video-agent-studio/episodes/regional-price-recovery-20261022/editor/production-v1/assemble_visual_review.py
```

조립은 기존 clean 브랜드150/300프레임과 Thinking Music만 재사용한다. 내레이션은 없다. 본문837.7초, 자막 종료 후 CTA hold3초, 브랜드5초/10초를 합친 예상 전체 길이는855.7초다. 이는 실제 음성 길이가 아니며 `timing_locked:false`, `provisional:true`다. 자막 종료 전역842.7초, 아웃트로 시작845.7초. 흰 자막 박스는 CTA hold에서 숨긴다.

검토본 표시 자막은 승인된39문단에서 별도 정규화했다.113개 큐·최단3.878초·최장74자. 숫자/단위/날짜와 짧은 술어를 보호했으며 원문 span→표시 변환표를 남겼다. `checks/visual-review/captions.json`을 화면 및 SRT의 기준으로 사용한다. 원본 낭독 대본은 변경하지 않았다.

최종 조립 파일은 `previews/full_visual_review_v1.mp4`, 실제 출력 메타데이터는 `full_visual_review_v1_manifest.json`, 전역5초 오프셋 SRT는 `full_visual_review_v1.srt`다. Thinking Music by Kevin MacLeod / incompetech.com / CC BY4.0이며 자세한 크레딧은 `full_visual_review_v1_music_credit.txt`와 최종 manifest에 있다.

향후 새 작업으로 같은 과정을 실행할 때만 `run_local.ps1 -Mode visual-review` 또는 `-Mode silent-review`를 쓴다. 이 모드는 현재 활성 렌더와 기존 출력이 있으면 중복을 막는다. 현재 작업에는 위 조립 명령만 이어서 실행한다. `-Mode body`는 실제 Jun 타임록과 음성 파일 없이는 계속 거절한다.

완성 MP4의 전체 디코드·컷 경계·대표 화면·BGM 청취·검토본 전달 패키지는 총괄이 별도 director 폴더에서 검증한다. 이 문서는 게시·최종영상 승인이나 음성 생성 허가가 아니다.
