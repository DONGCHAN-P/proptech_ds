from pathlib import Path
p=Path('video/src/PilotV11.tsx');s=p.read_text(encoding='utf8').replace('import {Checklist,Teaser}','import {Checklist,Teaser,OpeningPurpose,Outro}').replace("s.key==='intro-5')return <Teaser/>","s.key==='intro-5')return <OpeningPurpose/>").replace("s.key==='after-9')return <Teaser/>","s.key==='after-9')return <Outro/>");p.write_text(s,encoding='utf8')
p=Path('video/src/QuarterChartsV11.tsx');s=p.read_text(encoding='utf8').replace('y%2===0||y===from||y===2026','(y-from)%2===0');p.write_text(s,encoding='utf8')
