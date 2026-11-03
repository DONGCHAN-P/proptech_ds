from pathlib import Path
import re
R=Path(__file__).resolve().parents[5]
p=R/'video/src/namyangju-landuse-v7/FrontVisuals.tsx'
s=p.read_text(encoding='utf-8')
s=re.sub(r'label:"[^"]+",anchor:\[650,1000\]', 'label:industryLabel,anchor:[650,1000]',s)
p.write_text(s,encoding='utf-8')
