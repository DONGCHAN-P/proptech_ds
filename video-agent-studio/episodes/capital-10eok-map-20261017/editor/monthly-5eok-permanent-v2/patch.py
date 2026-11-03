from pathlib import Path
p=Path('video-agent-studio/episodes/capital-10eok-map-20261017/editor/monthly-5eok-permanent-v2/build_cache.py')
t=p.read_text(encoding='utf8')
for a,b in [('수도권, 5억으로 어디까지?','5억 넘으면, 다시 켜지지 않습니다'),('84㎡급 · 월중위값 · 연결 8,288 / 제외 884','84㎡급 · 월중위값 초과 이력 · 연결 8,288 / 제외 884'),('5억 이하 비율','초과 이력 없는 단지 비율'),('5억 이하 / 당월 관측 단지','초과 이력 없음 / 누적 관측'),('연결 표본 · 해당 월 거래 기준','무거래 유지 · 첫 5억 초과부터 영구 소등'),("'5억 이하',90","'초과 이력 없음',90"),("'당월 미거래',320","'무거래 유지',370"),('초과 숨김','초과 영구 소등')]:t=t.replace(a,b)
# Each transition begins with current breaches already removed; only newly observed points fade in.
needle="if mi%50==0:print('MAP_CACHE '+str(mi)+'/250',flush=True)"
add="""imfrom=G.base.copy();fd=ImageDraw.Draw(imfrom)
 for i in np.flatnonzero((status[max(0,mi-1)]==0)&(status[mi]==0)):
  x,y=xy[i];rad=2.3;fd.ellipse([(x-rad)*S,(y-rad)*S,(x+rad)*S,(y+rad)*S],fill=G.orange)
 imfrom.paste(label_overlay,(0,0),label_overlay);imfrom.resize((G.W,G.H),Image.Resampling.LANCZOS).save(C/f'from_{mi:03d}.png',compress_level=1)
 """
t=t.replace(needle,add+needle)
p.write_text(t,encoding='utf8')
