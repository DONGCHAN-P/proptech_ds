$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$ep='C:/projects/realestate_reco/video-agent-studio/episodes/goyang-changneung-20261015'
$out="$ep/outputs/visual-review-v1"
New-Item -ItemType Directory -Force $out | Out-Null
$ink='#173348'; $blue='#286cda'
function Txt($t,$x,$y,$s=28,$c='#173348') { $font=[Drawing.Font]::new('Malgun Gothic',$s,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel);$brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($c));$g.DrawString($t,$font,$brush,[single]$x,[single]$y);$font.Dispose();$brush.Dispose() }
function Box($x,$y,$w,$h,$c='#ffffff') {$b=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($c));$g.FillRectangle($b,$x,$y,$w,$h);$b.Dispose()}
function Base($title,$sub) {$script:im=[Drawing.Bitmap]::new(1920,1080);$script:g=[Drawing.Graphics]::FromImage($im);$g.SmoothingMode='AntiAlias';$g.Clear([Drawing.ColorTranslator]::FromHtml('#f6f4ef'));Txt '데이터로 보는 부동산 · 고양 창릉 / 내부 구성 확인판' 80 35 24;Txt $title 80 85 48;Txt $sub 80 150 24 '#637580';Box 80 920 1760 108;Txt '본문 흰 자막 박스 · 큐 공백에도 유지' 140 952 32;Txt '브랜드 무발화 구간과 CTA 끝 무음 유지 구간은 예외' 80 1040 19 '#637580'}
function Fit($path,$x,$y,$w,$h){$src=[Drawing.Image]::FromFile($path);$r=[Math]::Min($w/$src.Width,$h/$src.Height);$nw=$src.Width*$r;$nh=$src.Height*$r;$g.DrawImage($src,[single]($x+($w-$nw)/2),[single]($y+($h-$nh)/2),[single]$nw,[single]$nh);$src.Dispose()}
function Save($name){$im.Save("$out/$name",[Drawing.Imaging.ImageFormat]::Png);$g.Dispose();$im.Dispose()}
Base '전체 계획도에서 권역을 읽습니다' 'S010 · 원도면 전체 fit / 신규 좌표·경계·정밀핀을 만들지 않은 확인판'
Box 80 210 330 610 '#e9ecec';Fit "$ep/research/raw/s5_landuse_20250131.jpg" 95 255 300 430;Txt '창릉 전체 locator 자리' 100 220 23;Txt '정합 영역 테두리: 보류' 100 710 22;Txt '최신 전체도 확보 후 연결' 100 750 20 '#637580'
Box 440 210 1040 610;Fit "$ep/research/raw/s5_landuse_20250131.jpg" 460 230 1000 570
Txt '원도면 밖 안내' 1510 230 28;Txt '2025.01.31 공고 첨부' 1510 290 21;Txt '최신 고시 대조 대기' 1510 340 23;Txt '상업 이용조건 미확인' 1510 390 23;Txt '정밀 지리도와 혼합 금지' 1510 450 21;Txt '지도 고정 구도' 1510 530 26 $blue;Txt 'crop / 덧칠 없음' 1510 580 23
Txt '자료: LH S5 공고 첨부 · CN-MAP01 / 연구 확인용, 본편 사용 전 최신성·권리 해결 필요' 80 850 22 '#637580';Save 'S010_whole_locator_review.png'
Base '입주와 철도 이용 시점을 같은 달력에' 'S030 · research-v1 기준의 잠정 시안 / 목표·예정은 현재 운영과 구분'
$pen=[Drawing.Pen]::new([Drawing.ColorTranslator]::FromHtml('#9baab3'),3);$g.DrawLine($pen,140,310,1470,310)
for($y=2027;$y -le 2032;$y++){$x=140+($y-2027)*266;Txt "$y" ($x-35) 250 28;$g.DrawLine($pen,$x,300,$x,840)}
Box 140 380 140 55 '#e5edf9';Txt '착공 목표' 150 390 22;Txt '고양은평선 · 2027.01' 1550 390 22
Box 406 470 70 55 '#d6e5fc';Txt 'S5 입주 예정 · 2028.01' 80 550 25 $blue
Box 938 570 266 60 '#dce6ed';Txt '2030년 목표' 955 584 25;Txt 'GTX-A 창릉역 · 월 미정' 1260 590 23
Box 938 660 133 55 '#e5edf9';Txt '상반기' 944 672 23;Txt 'S3·S4 입주 · 보도상 예정' 1260 675 23
Box 1460 750 20 55 '#286cda';Txt '고양은평선 · 2031.12 목표' 1080 815 25
Txt '미정: 신설 중·고 / 상가·공원 이용 / 기업 확정 입주·일자리' 80 865 23 '#637580';$pen.Dispose();Save 'S030_calendar_review.png'
Base '신축 공고 가격과 인근 기존 단지를 비교' 'S050 · 레이아웃 확인판 / 거래 검증 전 가격·순위·막대 길이 생성 없음'
Box 80 220 620 620 '#e9ecec';Txt '생활권 위치 지도 자리' 120 260 34;Txt '원흥·도래울 / 삼송·지축' 120 330 28;Txt '단지·운영역·거리 검증 후 표시' 120 400 24;Txt '주소만으로 정밀핀 생성 금지' 120 450 24
$rows=@('창릉 S5 공고 기본형','원흥·도래울 기존 단지','삼송 기존 단지','지축 기존 단지');for($i=0;$i -lt 4;$i++){$yy=230+$i*145;Box 750 $yy 1090 125;Txt $rows[$i] 780 ($yy+15) 29;Txt '면적 / 계약기간 / 층 / n / 해제 제외 조건 확인' 780 ($yy+65) 21 '#637580';Txt '— 미확인' 1580 ($yy+28) 30 $blue}
Txt '83≤전용<85㎡ · 동일 완료분기 · 5층 이상 · 해제 제외 · 원거래 중위값과 표본수' 80 850 23 '#637580';Save 'S050_comparison_review.png'
