from pathlib import Path
import json
O=Path('analysis/housing_choice_returns');p=O/'tiger_chart.html';archive=O/'tiger_chart_etf_archive.html'
if not archive.exists():archive.write_text(p.read_text(encoding='utf8'),encoding='utf8')
p.write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=chart.html"><a href="chart.html">미국 S&amp;P500 지표 비교 차트 열기</a>',encoding='utf8')
d=json.loads((O/'comparison.json').read_text(encoding='utf8'));assert {x['years'] for x in d['summary']}=={3,5,10,19};assert all(len(v)==2025-int(k)+1 for k,v in d['paths'].items());print('Verified 4 periods and annual paths')
