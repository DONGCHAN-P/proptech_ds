import pathlib,re
p=pathlib.Path('video/src/changneung-shorts-leader-v1/entry.tsx');s=p.read_text(encoding='utf8').replace("g.name.includes(block)","g.name.includes('('+block+')')").replace("'S5 · 낮은 공고가 / 빠른 입주 예정'","'S5 · 낮은 공고가 / 입주 예정'").replace("n===4||n===5?30:36","36").replace("n===4||n===5?'condition_source':'key_value'","'key_value'").replace("S5 · 낮은 공고가 / 입주 예정","S5 · 낮은 공고가").replace("10.19(월)08시 준비 · 블록 대표좌표\\n지도 © OSM contributors · 위치 비교","10.19(월)08시 준비 · 블록 대표좌표\\n선: 위치 비교 · 실제 노선 아님\\n지도 © OSM · 공고 시점·타입 상이").replace("176,1053,24","176,1044,24").replace("lineHeight:1.2","lineHeight:kind==='condition_source'?1.15:1.2")
p.write_text(s,encoding='utf8')
ed=pathlib.Path('video-agent-studio/episodes/goyang-changneung-20261015/editor/shorts-leader-v1')
for p in (ed/'public').glob('*.svg'):
 s=p.read_text(encoding='utf8');s=re.sub(r'<text\b[^>]*>.*?</text>','',s,flags=re.S);p.write_text(s,encoding='utf8')
