import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
render=read(EP/'editor/jun-production-v1/render_receipt.json')
edl=read(EP/'outputs/jun-production-v1/assembly_edl.json')
meta=read(EP/'outputs/jun-release-v1/metadata_measured.json')
video=Path(render['final_file']);subs=Path(render['captions_file'])
assert sha(video)==render['final_sha256'] and sha(subs)==render['captions_sha256']
lines=['# 매매 전세 월세 Jun 최종 영상 배치 가이드','',
       '대본 v6와 기존 화면을 유지하고 ElevenLabs Jun 실제 음성에 맞춰 자막·장면·강조 시점을 연결한 렌더본입니다. 비공개 업로드는 별도 검수·게시 절차에서 기록합니다.','',
       f'- 본편: `{rel(video)}`',f'- 본편 SHA256: `{render["final_sha256"]}`',
       f'- 자막: `{rel(subs)}`',f'- 자막 SHA256: `{render["captions_sha256"]}`',
       '- 편집 소스: `outputs/jun-production-v1/ch01`부터 `ch10`의 index.html',
       '- 시간표: `narration/jun-production-v1/final_timing.json`',
       '- 조립 시간표: `outputs/jun-production-v1/assembly_edl.json`',
       '- 실제 프레임: `outputs/jun-production-v1/encoded_frame_plan.json`',
       '- 제목·설명·선택 썸네일: `outputs/jun-release-v1`','',
       '출력은1920×1080·30fps·H.264/AAC이며 실제 길이는1192.433333초입니다. 자막206개는 영상에 포함했고 동일한 SRT를 별도로 제공합니다.','',
       '첫 문단의 실제 발화가 끝난19.5초에5초 브랜드 인트로를 삽입합니다. 본문은 장별 PCM·공급자 문자 정렬을 기준으로 재배치했습니다. 마지막 실제 발화 끝1179.403333초 이후3.03초 유지하고1182.433333초에10초 아웃트로를 시작합니다.','',
       '| 장 | 시작 | 주제 |','|---|---|---|']
for ch in meta['chapters']:lines.append(f"| {ch['chapter']} | {ch['timestamp']} | {ch['title']} |")
lines += ['', '새 음성은 원래의 Jun 속도로 사용하며 이전 InJoon 길이에 맞추지 않았습니다. BGM은 기존 Thinking Music을 새 Jun 음성 기준으로 carve·덕킹해 섞었습니다. 음량 측정은통합-17.2LUFS·true peak-2.0dBFS입니다.','',
          '전체 AV 디코드·실제 인코딩 표본 프레임·전체 자막과 원문 정렬·선택34문단 음성인식·신호 검수 기록을 제공합니다. 실제 청취·연속 재생·Studio Content ID 확인은 수행하지 않았습니다. 독립 검수 범위와 미해결 권고는 `qa/jun-production-v1/final_review.json` 및 `qa/jun-production-v1/findings.json`에 기록합니다.','',
          '기존 본편·음성·원본·승인 기록은 보존합니다. 새 비공개 업로드의 처리·한국어 자막 제공을 확인한 뒤 기존 비공개 exEGpjcqdF0 한 편만 교체 삭제합니다. 다른 비공개 영상과 공개 기준본은 유지합니다.','']
guide=EP/'editor/jun-production-v1/placement_guide.md'
guide.write_text('\n'.join(lines),encoding='utf8')
report={'guide':rel(guide),'guide_sha256':sha(guide),'references_exist':all(p.exists() for p in [video,subs,EP/'narration/jun-production-v1/final_timing.json',EP/'outputs/jun-production-v1/assembly_edl.json',EP/'outputs/jun-production-v1/encoded_frame_plan.json',EP/'outputs/jun-release-v1/thumbnail.png']),
        'video_sha256':sha(video),'subtitles_sha256':sha(subs),'video_changed':False}
assert report['references_exist']
(HERE/'placement_guide_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
