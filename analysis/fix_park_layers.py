from pathlib import Path
p=Path('video/src/ContinuationV6.tsx')
s=p.read_text(encoding='utf8')
s=s.replace("park.elements.filter(e=>e.kind==='water'||e.kind==='park').map", "park.elements.filter(e=>e.kind==='water'||e.kind==='park').sort((a,b)=>Number(a.kind==='water')-Number(b.kind==='water')).map")
p.write_text(s,encoding='utf8')
