from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
p=HERE/'src/index.template.html'
s=p.read_text(encoding='utf8').replace('??? ??</label>','철도역 위치</label>').replace('aria-label="?? ??"','aria-label="철도 노선"').replace('?? ?? ??</option>','수록 노선 전체</option>')
s=s.replace('지하철 역·노선: 원자료 준비 중','역 자료 묶음: 2026.06.30 · 행별 시점 다름<br>실제 선로·계획역 및 일부 역 미수록')
s=s.replace('도로·역·개별 학원 위치는 아직 수록하지 않았습니다.','도로·실제 선로·개별 학원 위치는 아직 수록하지 않았습니다.')
s=s.replace('· 학교·학구도: 한국교육시설안전원','· 학교·학구도: 한국교육시설안전원 · 역: 철도산업정보센터')
p.write_text(s,encoding='utf8')
