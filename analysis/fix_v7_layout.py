from pathlib import Path
p=Path('video/src/MediaV7.tsx');s=p.read_text(encoding='utf8')
s=s.replace('top:220,left:90,width:1740,height:650','top:265,left:90,width:1740,height:580')
s=s.replace('width:850,height:570','width:850,height:500')
p.write_text(s,encoding='utf8')
