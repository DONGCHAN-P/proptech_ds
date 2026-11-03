$ErrorActionPreference='Stop'
$ep='C:/projects/realestate_reco/video-agent-studio/episodes/goyang-changneung-20261015'
$source=Get-Content -Encoding UTF8 "$ep/visual/production-v1/build_previews.ps1" -Raw
Invoke-Expression ($source.Substring(0,$source.IndexOf("Base '전체")))
foreach($name in @('S030_calendar_review','S050_comparison_review')) { $archive="$out/${name}_internal-v1.png";if(!(Test-Path $archive)){Copy-Item "$out/$name.png" $archive} }
function Bold($t,$x,$y,$s=28,$c='#173348'){$font=[Drawing.Font]::new('Malgun Gothic',$s,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel);$b=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($c));$g.DrawString($t,$font,$b,[single]$x,[single]$y);$font.Dispose();$b.Dispose()}
Base '입주와 학교·철도 목표를 같은 달력에' 'S030 · production-v2 반영 / 내부 설계판 · 대본·최종 타이밍 미확정'
$pen=[Drawing.Pen]::new([Drawing.ColorTranslator]::FromHtml('#cbd3d7'),2)
$left=500;$step=240
for($y=2027;$y -le 2032;$y++){$x=$left+($y-2027)*$step;Bold "$y" ($x-30) 220 27;$g.DrawLine($pen,$x,270,$x,820)}
function At($year,$month){return $left+($year-2027+($month-1)/12)*$step}
$lanes=@(@('S5 입주 예정',2028,1,310,'2028.01'),@('S1 입주 예정',2029,5,395,'2029.05'),@('S4 입주 예정',2030,3,480,'2030.03'),@('S4 6유·6초 개교 목표',2030,3,565,'2030.03'),@('고양은평선 개통 목표',2031,12,745,'2031.12'))
foreach($a in $lanes){Bold $a[0] 80 $a[3] 27;$px=At $a[1] $a[2];Box ($px-5) ($a[3]+8) 10 30 '#286cda';$tx=$px+18;if($tx -gt 1500){$tx=$px-150};Txt $a[4] $tx $a[3] 27 $blue}
Bold 'GTX-A 창릉역 목표' 80 655 27;Box (At 2030 1) 650 240 50 '#d6e5fc';Bold '2030년 · 월 미정' ((At 2030 1)+8) 660 24 $blue
Txt 'S5 5유·5초: 과거 공고 2028.03 목표 · 최신 확인 미완료 / S1 7유·7초: 미정' 80 835 23 '#637580'
Txt '출처: production-v2/calendar.json · 2026.10.16 확인 / 계획 시점이며 개교·개통 보장 아님' 80 875 21 '#637580';$pen.Dispose();Save 'S030_calendar_review.png'
Base '인근 기존 단지의 실제 거래 중위값' 'S050 · 2026년 3분기 계약 / 83≤전용<85㎡ · 5층 이상 · 해제 제외'
$data=Get-Content -Encoding UTF8 "$ep/research/prices-v2/comparisons.json" -Raw | ConvertFrom-Json
$main=@($data.comparisons | Where-Object { !$_.small_sample_warning })
for($i=0;$i -lt $main.Count;$i++){$r=$main[$i];$yy=220+$i*117;Box 80 $yy 1760 101;Bold $r.name 110 ($yy+18) 31;Txt ($r.region+' · 기존 아파트 매매') 110 ($yy+62) 21 '#637580';$w=[single](500*$r.median_eok/12);Box 810 ($yy+30) $w 36 '#286cda';Bold ($r.median_eok.ToString('0.00')+'억') 1350 ($yy+20) 35;Bold ('n = '+$r.n) 1640 ($yy+25) 32}
$r=@($data.comparisons | Where-Object {$_.small_sample_warning})[0];Box 80 820 1760 73 '#e9ecec';Bold ('소수 표본 참고  '+$r.name+'  '+$r.median_eok.ToString('0.00')+'억  /  n = '+$r.n) 110 835 27;Txt '순위 단정 유보' 1560 845 22 '#637580'
Txt '국토교통부 RTMS 원거래 · 2026.10.16 재조회 · 중위값 · 공고 분양가와 별도 · 호가 아님' 80 185 21 '#637580';Save 'S050_comparison_review.png'
