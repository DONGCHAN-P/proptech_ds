import json,re,pathlib
root=pathlib.Path(__file__).resolve().parents[1];out=root/'video/out';cut=412/30;duration=634.9333333333333
rows=json.loads((out/'newtown-v11-timing.json').read_text(encoding='utf-8-sig'))
for r in rows:
    if r['start']>=cut-.001:r['start']+=5;r['end']+=5
rows.insert(2,{'key':'channel-intro-v2','start':cut,'end':cut+5,'text':'','kind':'channel_brand','frames':150})
rows.append({'key':'channel-outro-v2','start':duration-10,'end':duration,'text':'','kind':'channel_brand','frames':300})
(out/'newtown-v12-timing.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
def sec(s):
    h,m,z=s.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(z)
def stamp(t):
    t=round(t*1000);return f'{t//3600000:02}:{t//60000%60:02}:{t//1000%60:02},{t%1000:03}'
def shift(m):
    a,b=sec(m[1]),sec(m[2]);return stamp(a+(5 if a>=cut-.001 else 0))+' --> '+stamp(b+(5 if b>cut+.001 else 0))
s=(out/'newtown-v11.srt').read_text(encoding='utf-8-sig')
(out/'newtown-v12.srt').write_text(re.sub(r'(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})',shift,s),encoding='utf-8')
source=(out/'newtown-v11-sources.md').read_text(encoding='utf-8-sig')
source+='\n\n## v12 공통 영상·음악\n\n공통 인트로5초·아웃트로10초: Runway Gen4.5 + imagegen AI 가상 도심, 실제 지역 촬영 아님. 채널명·사운드 로고 별도 편집.\n음악 Data City Ambient v1: 로컬 합성 원본, 외부 음악 샘플 없음. 패드·벨 음색. 기존 Thinking Music은 사용하지 않음.\n'
(out/'newtown-v12-sources.md').write_text(source,encoding='utf-8')
print('Timing, SRT and credits updated')
