from pathlib import Path
root=Path(__file__).resolve().parents[4]
for p in [root/'video/src/NamyangjuV3.tsx']:
 s=p.read_text(encoding='utf-8')
 old="sub:['남양주시 발표','허가 단계','준공 목표 · 운영 미확인']"
 new="sub:['건축허가 받은 달','2026.6 발표로 확인','준공 목표 · 운영 미확인']"
 assert old in s
 p.write_text(s.replace(old,new),encoding='utf-8')
print('permit month distinguished from announcement month')
