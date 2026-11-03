from pathlib import Path
import json
rows=json.loads(Path('video/out/newtown-v9-timing.json').read_text(encoding='utf8'));new=json.loads(Path('video/public/pilot-v10/plan.json').read_text(encoding='utf8'))['segments'];by={s['id']:s for s in new}
for r in rows:
 if r['key'] in by:r['text']=by[r['key']]['text']
Path('video/out/newtown-v10-timing.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
def fmt(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
Path('video/out/newtown-v10.srt').write_text('\n\n'.join(f'{i+1}\n{fmt(r["start"]+.2)} --> {fmt(r["end"]-.1)}\n{r["text"]}' for i,r in enumerate(rows)),encoding='utf8')
Path('docs/광교_동탄_v10_10분_대본.md').write_text('# 광교·동탄 v10 — 분기별 차트 대본\n\n'+ '\n\n'.join(f'## {int(r["start"]//60)}:{int(r["start"]%60):02} {r["title"]}\n\n{r["text"]}' for r in rows),encoding='utf8')
src=Path('video/out/newtown-v9-sources.md').read_text(encoding='utf8');src+='\n\n## v10 분기 차트와 기업 CI\n\n- 주 추세 차트: 각 분기 전체 거래의 중위가격. 월 중위가격의 평균이 아님. 전용83~85㎡, 해제 제외,2026년3분기까지.2026년4분기는 부분 기간이라 추세 비교에서 제외.\n- 거래 없는 분기는 연결하지 않음.1~2건 분기는 빈 점으로 표시하고 연결선에서 제외.3건 기준은 제작 가독성을 위한 표본 표시 규칙이며 통계적 신뢰 구간이 아님.\n- 연간 중위가격 기반 회복 지수는 연간 보조 비교임을 명시. 연간 방법 카드·지역 가격 분포는 기존 기준 유지.\n- 월·분기 표본 비교: video/public/pilot-v10/period-comparison.json. 계산: analysis/v10_periods.py. 표시 금액은 소수 둘째 자리 반올림.\n- 삼성전자 CI: https://www.samsung.com/sec/about-us/brand-identity/logo/\n- 로고 원본: https://images.samsung.com/kdp/aboutsamsung/brand_identity/logo/300_186_1.png\n- 공식 레터마크의 원형·주변 여백을 유지하고 기업 위치 식별 용도로 사용. 로고가 사업장 경계·통근 경로를 뜻하지 않음.\n- 도입22.25억은 파이낸셜뉴스2026.09.06 기사 사례이며 로컬 국평 거래 원자료에서는 해당 건을 확인하지 못함. 차트에 임의 추가하지 않음. 수집 누락·수정 등의 원인은 확정되지 않음.\n'
Path('video/out/newtown-v10-sources.md').write_text(src,encoding='utf8')
