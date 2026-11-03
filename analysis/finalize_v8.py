from pathlib import Path
import json
qa=json.loads(Path('video/out/qa-v8/technical.json').read_text(encoding='utf8'))
assert abs(float(qa['streams']['format']['duration'])-600)<.1
p=Path('config/current_video.json');c=json.loads(p.read_text(encoding='utf8'));c.update(version='v8',entry='video/src/PilotV8.tsx',composition='NewtownV8',video='video/out/newtown-v8-10min.mp4',subtitles='video/out/newtown-v8.srt',timing='video/out/newtown-v8-timing.json',report='docs/영상_v8_10분_확장_2026-10-13.md',duration_seconds=600,sources='video/out/newtown-v8-sources.md',script='docs/광교_동탄_v8_10분_대본.md',qa='video/out/qa-v8/technical.json',chart_motion='draw quickly then hold; highlight representative complex in narration')
p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
p=Path('video/package.json');c=json.loads(p.read_text(encoding='utf8'));c['scripts'].update({'studio:v8':'remotion studio src/PilotV8.tsx','render:v8':'remotion render src/PilotV8.tsx NewtownV8 out/newtown-v8-10min.mp4 --codec=h264 --crf=18 --concurrency=4'});p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
p=Path('config/video_style.json');c=json.loads(p.read_text(encoding='utf-8-sig'));c['version']='v8';c['chart_motion']='1.6–2 sec draw then hold; series focus; one dot per transaction';p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
p=Path('docs/영상_제작방향_v2_2026-10-13.md');s=p.read_text(encoding='utf8');s+='\n\n10분 확장판 v8 완료: video/out/newtown-v8-10min.mp4. 대표 단지 장기 이력·가격 분포·사분위·회복 경로·월별 거래량 설명을 추가하고 거래량 점 모션 및 단지별 선 강조를 적용. 최신 갱신 자료와 계약일10.06 기준을 통일. 대본 docs/광교_동탄_v8_10분_대본.md, 기록 docs/영상_v8_10분_확장_2026-10-13.md. QA는 최종 MP4 샘플 프레임과 음성 신호 측정이며 전편 청취 검수와 구분.\n';p.write_text(s,encoding='utf8')
