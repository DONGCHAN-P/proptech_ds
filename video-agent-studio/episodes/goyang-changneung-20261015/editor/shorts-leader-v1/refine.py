import pathlib,json,re
ed=pathlib.Path('video-agent-studio/episodes/goyang-changneung-20261015/editor/shorts-leader-v1');p=ed/'prepare.py';s=p.read_text(encoding='utf8');start=s.index(' text=u[');end=s.index(' total=sum',start)
s=s[:start]+''' text=u['text'];manual={2:['현재 자료로 대장 후보를 먼저 고르라면','저는 S4부터 보겠습니다.'],3:['기존 원흥 생활권의 수요와','만나는 접점이 있고,','1,024세대 규모의','새 단지가 들어서는 후보입니다.'],6:['다만 S4는 비교한 공고가격도','가장 높았습니다.'],9:['그래서 S4는 가격수준을 이끌','후보로 먼저 보는 것이고,','세 후보 중 상승률이 가장 높다는','결론은 아닙니다.'],10:['가격 부담과 도시가 채워지는','여력을 같이 보면','S5가 경쟁 후보입니다.'],11:['공고 사례가 가장 낮고,','세 곳 중 입주 예정이 빨라','먼저 수요를 만날 수 있습니다.'],14:['S1은 관찰 후보로 두겠습니다.'],15:['공고가격은 S5와 가깝고,','이번 현재 경로 조회에서는','상암 쪽 연결이 상대적으로 짧았습니다.']};groups=manual[int(u['unit_id'][-3:])]
'''+s[end:];p.write_text(s,encoding='utf8')
p=pathlib.Path('video/src/changneung-shorts-leader-v1/entry.tsx');s=p.read_text(encoding='utf-8-sig').replace("g.name.includes('공동주택')","g.name.includes(block)").replace('84㎡대','84AH · 84.9㎡').replace('S1 · 현재 상암 연결 관찰','S1 · 현재 상암 연결 관찰');p.write_text(s,encoding='utf8')
print('updated')
