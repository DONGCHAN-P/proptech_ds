"""무료 로컬 재현: python build.py 후 powershell -File render.ps1."""
import json, pathlib, html
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT.parent.parent/'outputs'/'visual-review-v2'
OUT.mkdir(parents=True,exist_ok=True)
INK='#173348'; BLUE='#286cda'; GRAY='#607580'; BG='#f6f4ef'; GREEN='#177565'; GOLD='#a16817'
pages=[]
def start(name,title,question):
 global ops
 ops=[]
 text('데이터로 보는 부동산  /  고양 창릉',80,38,24,GRAY)
 text(title,80,90,48)
 text(question,80,158,29,GRAY)
 box(80,926,1760,108,'#ffffff')
def box(x,y,w,h,c='#ffffff'): ops.append(dict(kind='box',x=x,y=y,w=w,h=h,color=c))
def text(t,x,y,s=28,c=INK,bold=False): ops.append(dict(kind='text',text=t,x=x,y=y,size=s,color=c,bold=bold))
def line(x,y,x2,y2,c='#bac6ce',width=3,dash=False): ops.append(dict(kind='line',x=x,y=y,x2=x2,y2=y2,color=c,width=width,dash=dash))
def image_fit(path,x,y,w,h): ops.append(dict(kind='image',path=path,x=x,y=y,w=w,h=h,color='#ffffff'))
def finish(name,caption,source):
 text(source,80,870,20,GRAY)
 text(caption,120,956,32)
 text('대표 시안 · 실제 음성/타임록 전 · 2026.10.16 확인 자료 기준',80,1046,18,GRAY)
 pages.append(dict(name=name,ops=ops))

start('M003_transport','새 철도 전에, 어느 거점을 이용할까요?','기존망의 연결 구조와 입주 달력을 나눠 봅니다')
box(80,220,1760,320)
text('현재 이용 가능한 기존망',110,242,30,BLUE,True)
text('연결 개략도 · 지도/축척/최단경로 아님',1210,248,22,GRAY)
for yy,hub,route,dest in [(315,'원흥역','3호선','종로·도심 / 강남 방면'),(395,'새절·DMC','6호선·공항철도','상암 / 마곡·여의도 환승 검토'),(475,'행신·대곡','경의중앙선·서해선','공덕 / 김포공항 연결 검토')]:
 box(110,yy-10,250,58,'#e7effc');text(hub,132,yy,28,BLUE,True)
 line(380,yy+16,630,yy+16,BLUE,5);text(route,410,yy-24,23,GRAY)
 text(dest,675,yy,28)
text('집 → 정류장 → 버스·대기 → 기존 역 → 환승·직장',1110,330,24,GRAY)
text('단지별 현관 출발 총시간은 미확보',1110,385,28,GOLD,True)
text('7728: 서울 지선 / 도래울–새절–신촌',1110,445,23,GRAY)
box(80,565,1760,265)
text('입주 예정',110,620,24,BLUE,True);text('새 철도',110,735,24,GOLD,True)
X=lambda year: 370+(year-2027)*275
for yr in range(2027,2033):
 xx=X(yr);line(xx,605,xx,790,'#d9e1e6',2);text(str(yr),xx-25,575,22,GRAY)
for v,label,yy in [(2028,'S5 2028.01',625),(2029+4/12,'S1 2029.05',660),(2030+2/12,'S4 2030.03',625)]:
 xx=X(v);box(xx-8,yy+6,16,16,BLUE);text(label,xx+15,yy,25,BLUE)
line(X(2030),750,X(2031),750,GOLD,18,True);text('GTX-A 창릉역 2030년 예정',X(2030)-75,790,23,GOLD)
text('고양은평선 2031.12 목표',X(2030)+160,700,23,GOLD)
box(X(2031+11/12)-7,745,14,16,GOLD)
finish('M003_transport','입주일과 새 철도 이용일은 다릅니다. 집에서 기존 역까지의 이동을 먼저 확인하세요.','출처: commute-v3 / LH 2026.09.30 / 공고 입주월. 연도 예정은 월 단위 확정일로 바꾸지 않음')

start('M004_price','이 가격은 이미 본청약 공고 가격입니다','기본가 + 발코니 확장과 현재 기존 단지 매매를 구분합니다')
box(80,220,1090,610);box(1200,220,640,610)
text('본청약 · 특정 타입 / 5층~최상층',110,245,29,BLUE,True)
text('블록 / 공고일',110,305,23,GRAY);text('기본가',440,305,23,GRAY);text('확장비',690,305,23,GRAY);text('합계',930,305,23,BLUE)
for i,(b,typ,day,base,ext,total) in enumerate([
 ('S5','84A · 84.64㎡','2025.01.31','7억 6,998만','661.8만','7.766억'),
 ('S1','84A · 84.99㎡','2026.04.30','7억 8,340만','698만','7.904억'),
 ('S4','84AH · 84.90㎡','2026.06.30','8억 6,719만','613.9만','8.733억')]):
 yy=354+i*133;box(100,yy-10,1050,120,'#f0f4f9' if i!=2 else '#e7effc')
 text(b,120,yy,32,BLUE,True);text(typ,190,yy+2,23);text(day,190,yy+43,21,GRAY)
 text(base,440,yy+15,27);text(ext,690,yy+15,27);text(total,930,yy+10,30,BLUE,True)
text('합계: 억원 소수 3자리 반올림 / 옵션·취득세·금융비용 별도',110,770,22,GRAY)
text('현재 대안 · 기존 매매 중위값',1230,245,29,GREEN,True)
for i,(n,v,nn) in enumerate([('도래울센트럴더포레','7.450억','n=11'),('창릉호반써밋','8.375억','n=20'),('지축역센트럴푸르지오','11.275억','n=6')]):
 yy=320+i*125;text(n,1230,yy,25);text(v,1230,yy+38,33,GREEN,True);text(nn,1640,yy+44,23,GRAY)
text('2026Q3 / 83≤전용<85㎡ / 5층 이상',1230,715,21,GRAY)
text('해제 제외 / 2026.10.16 조회',1230,750,21,GRAY)
text('본청약과 현재 대안은 별도 기준',1230,790,23,GOLD,True)
finish('M004_price','현재 대안은 비교 기준입니다. 창릉의 미래 시세나 보장 수익을 뜻하지 않습니다.','출처: price-stage-v3 · 보존 공식 공고 S5/S1/S4 · prices-v2 국토부 실거래 집계 승계(이번 API 재조회 없음)')

start('M005_life','S4는 기존 생활권과 새 학교를 따로 봅니다','지금 있는 시설의 접근 조건과 입주 시점의 준비 상태가 핵심입니다')
box(80,220,310,610,'#e9eef3');text('창릉 본단지 전체도',100,242,25,GRAY)
image_fit('../../research/map-clearance-v1/raw/eum_lots_overall_20251224.jpg',95,290,280,396)
text('설명 대상  S4',110,705,29,BLUE,True)
text('2025.12.24 고시 기준',100,750,20,GRAY)
text('공공누리 3유형 · 변경 없음',100,782,18,GRAY)
text('도면 내 추가 핀·테두리 없음',100,808,18,GRAY)
box(420,220,1420,610)
text('독립 생활 관계도 · 비축척 / 실제 보행경로 아님',460,245,25,GRAY)
box(470,390,350,175,'#edf2ec');text('서측 초등학교 계획',495,415,27,GREEN,True)
text('가칭 6유·6초',495,463,26);text('2030.03 목표 · 변경 가능',495,510,22,GRAY)
box(900,380,320,195,BLUE);text('창릉 S4',950,415,40,'#ffffff',True);text('2030.03 입주 예정',930,485,25,'#ffffff')
line(825,475,895,475,GREEN,5)
line(1285,345,1285,620,'#a8b4bb',22);text('덕양로',1240,650,23,GRAY)
box(1350,380,430,195,'#fff3dc');text('이케아 · 롯데아울렛',1380,410,28,GOLD,True);text('기존 원흥 생활권 접점',1380,465,25);text('도로 건너 이용 관계',1380,515,23,GRAY)
line(1225,475,1345,475,GOLD,4,True)
text('실제 출입구 · 횡단보도 · 보행거리: 미확인',870,705,29,GOLD,True)
text('시설 배치는 사실 관계 설명용이며 도면을 크롭·트레이싱하지 않았습니다',470,775,23,GRAY)
finish('M005_life','학교 용지와 개교 확정은 다릅니다. 도로를 건너는 실제 생활 동선도 확인해야 합니다.','지도: 국토교통부 고시2025-813호(2025.12.24) · 토지이음 · 공공누리3유형 / 생활: LH 2026.07.03 · S4 정정공고')

ps=["$ErrorActionPreference='Stop'","Add-Type -AssemblyName System.Drawing",f"$out='{OUT.as_posix()}'","$checks=@()"]
for p in pages:
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',f'<rect width="1920" height="1080" fill="{BG}"/>']
 ps += ["$im=[Drawing.Bitmap]::new(1920,1080)","$g=[Drawing.Graphics]::FromImage($im)","$g.SmoothingMode='AntiAlias'","$g.TextRenderingHint='AntiAliasGridFit'",f"$g.Clear([Drawing.ColorTranslator]::FromHtml('{BG}'))"]
 for o in p['ops']:
  c=o['color'];x=o['x'];y=o['y']
  if o['kind']=='box':
   svg.append(f'<rect x="{x}" y="{y}" width="{o["w"]}" height="{o["h"]}" fill="{c}"/>')
   ps += [f"$brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml('{c}'))",f"$g.FillRectangle($brush,[single]{x},[single]{y},[single]{o['w']},[single]{o['h']})","$brush.Dispose()"]
  elif o['kind']=='image':
   svg.append(f'<image x="{x}" y="{y}" width="{o["w"]}" height="{o["h"]}" href="{o["path"]}" preserveAspectRatio="xMidYMid meet"/>')
   path=(ROOT/o['path']).resolve().as_posix()
   ps += [f"$src=[Drawing.Image]::FromFile('{path}')",f"$ratio=[Math]::Min({o['w']}/$src.Width,{o['h']}/$src.Height)","$nw=$src.Width*$ratio;$nh=$src.Height*$ratio",f"$g.DrawImage($src,[single]({x}+({o['w']}-$nw)/2),[single]({y}+({o['h']}-$nh)/2),[single]$nw,[single]$nh)","$src.Dispose()"]
  elif o['kind']=='line':
   dash=' stroke-dasharray="14 10"' if o['dash'] else ''
   svg.append(f'<line x1="{x}" y1="{y}" x2="{o["x2"]}" y2="{o["y2"]}" stroke="{c}" stroke-width="{o["width"]}"{dash}/>')
   ps += [f"$pen=[Drawing.Pen]::new([Drawing.ColorTranslator]::FromHtml('{c}'),{o['width']})"]
   if o['dash']:ps += ["$pen.DashStyle='Dash'"]
   ps += [f"$g.DrawLine($pen,[single]{x},[single]{y},[single]{o['x2']},[single]{o['y2']})","$pen.Dispose()"]
  else:
   s=o['size'];t=o['text'];b='Bold' if o['bold'] else 'Regular';weight='700' if o['bold'] else '400'
   svg.append(f'<text x="{x}" y="{y+s}" fill="{c}" font-family="Malgun Gothic,sans-serif" font-size="{s}" font-weight="{weight}">{html.escape(t)}</text>')
   q=t.replace("'","''")
   ps += [f"$font=[Drawing.Font]::new('Malgun Gothic',{s},[Drawing.FontStyle]::{b},[Drawing.GraphicsUnit]::Pixel)",f"$brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml('{c}'))",f"$g.DrawString('{q}',$font,$brush,[single]{x},[single]{y})",f"$size=$g.MeasureString('{q}',$font)",f"$checks+=@{{scene='{p['name']}';text='{q}';right=({x}+$size.Width);bottom=({y}+$size.Height);ok=(({x}+$size.Width -le 1860) -and ({y}+$size.Height -le 1080))}}","$font.Dispose();$brush.Dispose()"]
 svg.append('</svg>')
 (ROOT/(p['name']+'.svg')).write_text('\n'.join(svg),encoding='utf-8')
 ps += [f"$im.Save(\"$out/{p['name']}.png\",[Drawing.Imaging.ImageFormat]::Png)","$g.Dispose();$im.Dispose()"]
ps += ["$checks | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 \"$out/text_bounds.json\"","$checks | Where-Object { -not $_.ok } | ConvertTo-Json"]
(ROOT/'render.ps1').write_text('\n'.join(ps),encoding='utf-8-sig')
(ROOT/'drawing_data.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>창릉 대표 시안 v2</title><style>body{background:#263645;color:white;font:20px sans-serif}img{width:100%;max-width:1440px;display:block;margin:25px auto}</style>'+''.join(f'<img alt="{p["name"]}" src="../../outputs/visual-review-v2/{p["name"]}.png">' for p in pages),encoding='utf-8')
print('SVG 3개 / 렌더 스크립트 / 재현 데이터 / HTML 저장')
