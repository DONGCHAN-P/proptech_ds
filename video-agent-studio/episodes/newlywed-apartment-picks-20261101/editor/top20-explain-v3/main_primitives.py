"""기존v3의 도형·문자·공통셸·CSS만 계승합니다. 파일IO·추정시간은 없습니다."""
import html,json

def esc(s): return html.escape(str(s))

def txt(s,x,y,w,size=30,weight=400,color=None,cl='',id=None):
 return f'<div {f"id={chr(34)+id+chr(34)}" if id else ""} class="text {cl}" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;font-weight:{weight};{f"color:{color};" if color else ""}">{esc(s)}</div>'

def box(x,y,w,h,c='#e3e8e8',rad=12,cl='',id=None,extra=''):
 return f'<div {f"id={chr(34)+id+chr(34)}" if id else ""} class="shape {cl}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{c};border-radius:{rad}px;{extra}"></div>'

def img(src,x,y,w,h,cl='',id=None):
 return f'<img {f"id={chr(34)+id+chr(34)}" if id else ""} class="photo {cl}" src="{esc(src)}" alt="" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;object-fit:contain">'

CSS='''@font-face{font-family:Pretendard;src:url(assets/Pretendard-Regular.woff2) format("woff2");font-weight:400}@font-face{font-family:Pretendard;src:url(assets/Pretendard-Bold.woff2) format("woff2");font-weight:700}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#f6f4ef}body{font-family:Pretendard,sans-serif;color:#173348}#film{position:relative;width:100%;height:100%;overflow:hidden}.text{position:absolute;line-height:1.24;white-space:normal;word-break:keep-all;overflow-wrap:break-word;letter-spacing:-.018em;font-variant-numeric:tabular-nums}.shape,.photo{position:absolute;display:block}.photo{border-radius:12px}.bar{transform-origin:left center}.source{color:#536873}.caption{position:absolute;left:96px;right:96px;bottom:28px;height:130px;border-radius:13px;background:#fff;display:flex;align-items:center;justify-content:center;padding:12px 35px;text-align:center;font-size:39px;line-height:1.25;font-weight:400;word-break:keep-all}.caption-inner{width:100%;max-width:1610px}.ink{color:#173348}.blue{color:#286cda}'''

CSS+='''.phase,.statement{position:absolute;inset:0;pointer-events:none}.fit{overflow:visible;word-break:keep-all;overflow-wrap:anywhere}.price-value{white-space:nowrap;font-variant-numeric:tabular-nums}.provisional{color:#88631b}.caption{overflow:visible}.caption.fit{position:absolute}.spec-flag{position:absolute;left:1280px;top:34px;width:560px;text-align:right;color:#88631b;font-size:21px}'''

def tween(selector,fr,to,at,dur=.45,ease='power2.out'):
 return f'tl.set({json.dumps(selector)},{json.dumps(fr)},0);tl.fromTo({json.dumps(selector)},{json.dumps(fr)},{json.dumps(dict(to,duration=dur,ease=ease,immediateRender=False))},{at:.4f});'

def shell(s):
 if s['scene_id']=='E001':s=next(v for v in scenes if v['scene_id']=='C001')
 title={'N001':'초혼 기준으로 다시 읽는 TOP20','N002':'부부의 범위가 바꾸는 지역 목록'}.get(s['scene_id'],s['title'])
 if s.get('region_id'):
  r=regions[s['region_id']];region_name='옛 서구' if s['region_id']=='R01' else r['region'];title=f'거주 수 {r["rank"]}위 · {r["province"]} {region_name}'
 scope='2024.11.1 · 같은 수도권 53개 구 · 전체 기준 / 초혼 기준 · 단위: 쌍' if s['scene_id'] in ['N001','N002'] else '2024.11.1 거주 기준 · 신혼부부 전체 · 단위: 쌍'
 return txt('부동산 데이터 | 신혼부부가 사는 곳',80,32,1200,23)+txt(title,80,103,1760,43,700)+(txt(scope,80,158,1760,23,color='#536873') if not s.get('region_id') else '')

def source_line(s):
 # 통계청 출처는 도입 O002 본문에만 설명합니다. 권리 원장은 credits에 유지합니다.
 return ''

def install(context):
 globals().update(context)
 return {name:globals()[name] for name in ['esc', 'txt', 'box', 'img', 'tween', 'shell', 'source_line']}
