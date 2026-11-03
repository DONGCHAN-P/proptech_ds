import sys,json
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify import telegram
o=root/'output/cleanup-20261015';p=o/'telegram_wrapup.json'
if p.exists():print('Already notified');raise SystemExit
d=json.loads((o/'cleanup_completed.json').read_text(encoding='utf-8'))
e=root/'video-agent-studio/episodes/goyang-changneung-20261015'
assert (e/'outputs/research-brief-v1/창릉_조사브리프.md').is_file()
message=f'''영상 작업 정리 완료

1) 제작 기본가이드 + 피드백 이력 완성
왕숙 대화62항목/광교·동탄 기록28항목을 정리하고 AGENTS·WORKFLOW의 다음 작업 기본값으로 연결했습니다.
{root / 'video-agent-studio/guides/제작_기본가이드.md'}

2) 실제 삭제 {d['deleted_files']:,}개 / {d['deleted_gib']:.2f}GiB, 실패{d['failed_files']}개. 빈 폴더1620개 정리. 최종롱폼2·쇼츠6·재현입력·원본자료·승인기록 보존, 왕숙 업로드4파일 해시 재검증.
{o / '정리_결과.md'}

3) 다음 창릉 공식자료 1차 조사팩
{e / 'outputs/research-brief-v1/창릉_조사브리프.md'}
조사만 진행했으며 새 유료음성·이미지·영상·공개는 시작하지 않았습니다.

4) 공용 HTML 지도 의견: 활용 가치가 높습니다. 수도권 SHP 전량 다운로드보다 창릉 지역팩부터 GPKG/GeoJSON→HTML/영상 공통장면으로 구축하고 왕숙·교산으로 확장하는 안을 권합니다. 출처별 상업이용/변경/저장권리·계획/현황·좌표정합을 먼저 확인해야 합니다.
{root / 'reports/수도권 영상 지도 데이터 검토.md'}'''
assert telegram.send(message,quiet=True)
p.write_text(json.dumps({'sent_at':datetime.now(timezone.utc).isoformat(),'sent':True,'file_sent':False},indent=2),encoding='utf-8')
print('Wrap-up and research artifact paths sent to Telegram')
