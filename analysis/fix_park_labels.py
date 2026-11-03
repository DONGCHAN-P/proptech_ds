from pathlib import Path
p=Path('video/src/ContinuationV6.tsx')
s=p.read_text(encoding='utf8').replace('x="290" y="435"','x="430" y="425"').replace('x="640" y="205"','x="745" y="485"').replace('x="835" y="485"','x="745" y="485"')
s=s.replace('(p[0]-127.044)/.036*1020','157+(p[0]-127.044)/.036*706')
s=s.replace('같은 면적으로 비교하기</div></div></div>','같은 면적으로 비교하기</div><div style={{fontSize:28,color:\'#777\',marginTop:30}}>다음 조사 후보 · 왕숙 / 교산 / 창릉</div></div></div>')
p.write_text(s,encoding='utf8')
