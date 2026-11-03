from pathlib import Path
p=Path('video/src/ExpandedV8.tsx');s=p.read_text(encoding='utf8')
s=s.replace('<svg width="710" height="110">{Array.from', '<svg width="710" height="110"><text x="5" y="23" fontSize="21" fill="#777">정렬 위치 개념도</text>{Array.from')
p.write_text(s,encoding='utf8')
