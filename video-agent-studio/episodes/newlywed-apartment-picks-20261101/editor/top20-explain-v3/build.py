"""v2 생성기를 계승한 v3 대표 HTML 시안 전용 빌더입니다.
확정 원고·승인·실측 타임록 전에는 본편 소스/음성/렌더를 만들지 않습니다.
python build.py [--script scene_proposals_v6.json] [--timing v3_actual_lock.json]
"""
from pathlib import Path
import argparse,copy,hashlib,html,json,re,shutil,subprocess,sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
from caption_tools import make_cues,find_anchor,set_protected_phrases,split_semantic
from v3_visuals import install_v3,FIT_SCRIPT
H=Path(__file__).resolve().parent; E=H.parents[1]; R=E.parents[2]; M=H/'spec'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,s):
 p=Path(p).resolve()
 if not p.is_relative_to(H):raise ValueError('v3 담당 폴더 밖 쓰기 금지: '+str(p))
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_text(encoding='utf-8')==s:return
 p.write_text(s,encoding='utf-8')
def js(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stage(src,dst):
 if not Path(dst).resolve().is_relative_to(H):raise ValueError('v3 밖 복사 금지')
 Path(dst).parent.mkdir(parents=True,exist_ok=True)
 if Path(dst).exists() and sha(src)==sha(dst):return
 shutil.copy2(src,dst)
def esc(s): return html.escape(str(s))
def txt(s,x,y,w,size=30,weight=400,color=None,cl='',id=None):
 return f'<div {f"id={chr(34)+id+chr(34)}" if id else ""} class="text {cl}" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;font-weight:{weight};{f"color:{color};" if color else ""}">{esc(s)}</div>'
def box(x,y,w,h,c='#e3e8e8',rad=12,cl='',id=None,extra=''):
 return f'<div {f"id={chr(34)+id+chr(34)}" if id else ""} class="shape {cl}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{c};border-radius:{rad}px;{extra}"></div>'
def img(src,x,y,w,h,cl='',id=None):
 return f'<img {f"id={chr(34)+id+chr(34)}" if id else ""} class="photo {cl}" src="{esc(src)}" alt="" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;object-fit:contain">'

ap=argparse.ArgumentParser(description='대표 HTML spec만 생성합니다. 본편 렌더 기능은 없습니다.');ap.add_argument('--timing');ap.add_argument('--scene-data');ap.add_argument('--visual-module',action='append',default=[]);ap.add_argument('--script');ap.add_argument('--scene-id',action='append');ap.add_argument('--corner-cases',action='store_true');a=ap.parse_args()
T=read(a.timing) if a.timing else {'timing_locked':False,'timing_basis':'provisional_v6_sentence_budget_not_actual_audio','audio_file':None,'scenes':[]}
script_path=Path(a.script or E/'writer/top20-explain-v3/scene_proposals_v6.json')
sp=copy.deepcopy(read(script_path))
if sp.get('project_revision')!='top20-explain-v3':raise ValueError('이번 v3 원고만 허용합니다.')
script_md=script_path.with_name('script_v6.md')
if T.get('timing_locked'):
 if not sp.get('narration_ready'):raise ValueError('NOTFINAL 원고의 실제 타임록을 허용하지 않습니다.')
 if T.get('script_sha256')!=sha(script_md):raise ValueError('실제 타임록과 script_v6.md의 SHA가 다릅니다.')
 if 'actual' not in T.get('timing_basis',''):raise ValueError('실제 음성 기반 타임록이 필요합니다.')
selected=set(a.scene_id or ['O002','S006','S007','S019'])
if a.corner_cases:
 cp=read(E/'director/top20-explain-v3/price_panel_data.json')['regions']
 selected.update([max(cp,key=lambda v:v['median_manwon'])['scene_id'],max(cp,key=lambda v:v['representative']['median_manwon'])['scene_id'],max(cp,key=lambda v:len(v['representative']['apt_name']))['scene_id'],next(v['scene_id'] for v in cp if v['region_id']=='R01')])
if len(selected)>8:raise ValueError('승인 전 대표·경계 시안은 최대 8장면입니다. 본편 생성은 별도 작업입니다.')
scenes=[s for s in sp['scenes'] if s['scene_id'] in selected]
if {s['scene_id'] for s in scenes}!=selected:raise ValueError('원고에 없는 scene_id입니다.')
spec_cursor=0
for s in scenes:
 s['start_s']=spec_cursor;s['end_s']=spec_cursor+float(s.get('estimated_duration_s') or 30);spec_cursor=s['end_s']
 for st in s.get('sentences',[]):
  if st.get('display_text') is not None:st['text']=st['display_text']
  if s['scene_id']=='O002' and st.get('text') and '통계청' in st['text']:
   st['draft_source_text']=st['text'];st['text']=st['text'].replace('통계청','국가데이터처');st['display_override_basis']='최신 사용자 기관명 지시; 최종v6 통합 대기'
  if st.get('text') is None:
   st['is_pending']=True
   st['text']={'regional_feature':'특징 설명 확정 대기','region_price':'지역 실거래 중위값 확정 대기','representative_complex':'대표 단지 가격 확정 대기'}.get(st.get('slot_kind'),'자료·가격 조건 확정 대기')
facts=read(E/'research/top20-8min-v2/combined_facts.json'); regions={r['region_id']:r for r in facts['regions']}
photo_manifest=read(E/'visual/top20-8min-v2/photo_assets_v2.json'); photos={p['region_id']:p for p in photo_manifest['assets']}
plan=read(E/'director/top20-8min-v2/scene_asset_plan.json'); binds={s['scene_id']:s for s in plan['scene_assets']}
map_manifest=read(E/'visual/top20-8min-v2/maps/map_assets.json'); maps={m['region_id']:m for m in map_manifest['assets']}
assert scenes and len({s['scene_id'] for s in scenes})==len(scenes),'Scene IDs must be unique'
assert len(regions)==20 and len({p['sha256'] for p in photos.values()})==20
assert all(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',s['scene_id']) for s in scenes),'Unsafe scene ID'
inputs=[script_path,Path(__file__),H/'visuals.py',H/'v3_visuals.py',H/'phase_timing.py',H/'extra_scenes.py',H/'caption_tools.py',H/'caption_backgrounds.py',H/'design.md',E/'research/top20-8min-v2/combined_facts.json',E/'visual/top20-8min-v2/photo_assets_v2.json',E/'visual/top20-8min-v2/maps/map_assets.json',R/'config/channel_style_tokens.json',R/'config/video_style.json',E/'director/top20-explain-v3/requirements.json',E/'director/top20-explain-v3/price_panel_contract.json',H/'photo_bindings.json']
if a.scene_data:inputs.append(Path(a.scene_data))
inputs.extend(Path(v) for v in a.visual_module)
if a.timing:inputs.append(Path(a.timing))
if script_md.exists():inputs.append(script_md)
if any(s['scene_id'] in ['N001','N002'] for s in scenes):inputs.append(E/'research/top20-enhance-v2/verified_facts.json')
word_groups={};readings={}
if T.get('timing_locked'):
 word_paths={str(T['words_file'])} if T.get('words_file') else {str(v.get('words_path') or '') for v in T.get('scenes',[])}
 if not any(word_paths):raise ValueError('Locked input must identify words_file or per-scene words_path; no old-word fallback')
 for word_path in sorted(word_paths-{''}):
  wp=Path(word_path)
  if not wp.is_absolute():wp=R/wp
  if not wp.exists():raise FileNotFoundError(wp)
  inputs.append(wp)
  expected=(T.get('word_file_sha256s') or {}).get(str(wp).replace('\\','/')) or T.get('words_file_sha256')
  if not expected or sha(wp)!=expected:raise ValueError('실제 단어 파일 SHA 연결이 필요합니다: '+str(wp))
  for w in read(wp)['words']:
   group=word_groups.setdefault(w['sentence_id'],[])
   if w not in group:group.append(w)
 rp=Path(T.get('source_timing') or a.timing)
 if not rp.is_absolute():rp=R/rp
 if rp.exists():
  inputs.append(rp)
  for ns in read(rp)['scenes']:
   for st in ns.get('sentences',[]):readings[st['sentence_id']]=st.get('reading_text',st['text'])
inserts=T.get('inserts') or [{'kind':'intro' if 'intro' in v['id'] else 'outro','start_s':v['start_s'],'duration_s':v['duration_s'],'source_file':str(R/v['path']),'sha256':v['sha256']} for v in T.get('brand_visuals',[])]
if T.get('brand_visuals'):T['audio_includes_brand']=True
overrides={s['scene_id']:s for s in T.get('scenes',[])}
for s in scenes:
 ov=overrides.get(s['scene_id'],{})
 s['start_s']=float(ov.get('start_s',s.get('start_s',0)));s['end_s']=float(ov.get('end_s',s.get('end_s',0)));s['duration_s']=s['end_s']-s['start_s']
 assert s['duration_s']>0
 s['anchors']=dict(ov.get('anchors',{}))
 if T.get('timing_locked') and s['scene_id'] not in overrides:raise ValueError('Scene missing from actual lock: '+s['scene_id'])
 # A sentence anchor is local scene time. Caption timing can be provided globally.
 source=s.get('sentences',[]); weights=[max(1,len(t['text'])) for t in source]; n=sum(weights) or 1;pos=0
 s['sentence_times']=[]
 for i,t in enumerate(source):
  st=s['duration_s']*pos/n;pos+=weights[i];en=s['duration_s']*pos/n
  s['sentence_times'].append(dict(t,start_s=st,end_s=en))
 if ov.get('sentence_times'):
  allowed={t['sentence_id'] for t in source}
  s['sentence_times']=[t for t in ov['sentence_times'] if t['sentence_id'] in allowed]
 if word_groups:
  for st in s['sentence_times']:
   if st.get('reading_text'):readings[st['sentence_id']]=st['reading_text']
def anchor(s,key,sent=0):
 if key in s['anchors']: return float(s['anchors'][key])
 ss=s['sentence_times'];return float(ss[min(sent,len(ss)-1)]['start_s'])+.12 if ss else 0
for i,s in enumerate(scenes):
 if i:
  gap=s['start_s']-scenes[i-1]['end_s']
  covered=sum(v['duration_s'] for v in inserts if v['start_s']>=scenes[i-1]['end_s']-.05 and v['start_s']+v['duration_s']<=s['start_s']+.05)
  if not T.get('timing_locked'):assert abs(gap-covered)<.07,'시안 사이 빈 구간 오류'
total=max([scenes[-1]['end_s']]+[v['start_s']+v['duration_s'] for v in inserts])
lastspeech=T.get('last_speech_end_s',T.get('last_spoken_end_s'))
if T.get('timing_locked') and lastspeech is not None:
 assert abs(scenes[-1]['end_s']-lastspeech-3)<.07,'E001 must account for exactly one last-speech +3s hold'
assets=M/'assets';assets.mkdir(parents=True,exist_ok=True)
for weight in ['Regular','Bold']:
 src=R/f'assets/fonts/Pretendard-{weight}.woff2';stage(src,assets/src.name);inputs.append(src)
gsap_src=R/'video-agent-studio/episodes/affordable-home-price-20261026/editor/jun-quality-v2/main/project/assets/gsap.min.js'
stage(gsap_src,assets/'gsap.min.js');inputs.append(gsap_src)
credits=[];asset_records=[];geos={}
NS='{http://www.w3.org/2000/svg}'
def paths_svg(paths,view='105 190 1160 660'):
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+view+'" width="1160" height="660">'+''.join(ET.tostring(p,encoding='unicode').replace('ns0:','').replace(':ns0','') for p in paths)+'</svg>'
base_paths=None
for rid,p in photos.items():
 src=Path(p['absolute_file']); dest=assets/f'{rid}.jpg'
 assert sha(src)==p['sha256'],f'photo input changed: {rid}'
 stage(src,dest);inputs.append(src)
 msrc=E/maps[rid]['vector_file'];inputs.append(msrc);tree=ET.parse(msrc).getroot();g=tree.find(NS+'g'); ps=list(g)
 target=copy.deepcopy(ps[-1]);target.set('fill','#286cda');geos[rid]=target
 if base_paths is None: base_paths=[copy.deepcopy(n) for n in ps[:-1]]
 write(assets/f'{rid}_locator.svg',paths_svg([*base_paths,target]))
 # Source paths contain only straight M/L/Z commands; fit a static viewBox to actual geometry.
 d=target.get('d','');assert not re.search('[CcQqAaSsTtHhVv]',d),'Unsupported geometry command'
 coords=[float(v) for v in re.findall(r'-?\d+(?:\.\d+)?',d)];xs=coords[::2];ys=coords[1::2]
 x0,y0,x1,y1=min(xs),min(ys),max(xs),max(ys);pad=max(x1-x0,y1-y0)*.09
 view=f'{x0-pad:.3f} {y0-pad:.3f} {x1-x0+2*pad:.3f} {y1-y0+2*pad:.3f}'
 focus=copy.deepcopy(target);focus.set('stroke','#173348');focus.set('stroke-width','0.65');focus.set('vector-effect','non-scaling-stroke')
 write(assets/f'{rid}_focus.svg',paths_svg([focus],view))
 credits.append({'region_id':rid,'scene_id':regions[rid]['scene_id'],'actual_place':p['actual_place'],'photo_capture_year':p['photo_capture_year'],'full_attribution':p['license']['attribution_ko'],'license':p['license'],'source':p['source_or_prompt'],'changes':'사진 파일 바이트 동일. 원본 비율 유지 contain 배치. 크롭·색보정·생성 보정 없음.','photo_sha256':sha(dest),'map_attribution':maps[rid]['attribution']})
 asset_records.append({'region_id':rid,'photo':f'assets/{rid}.jpg','photo_sha256':sha(dest),'photo_source_sha256':p['sha256'],'map':f'assets/{rid}_locator.svg','map_source_sha256':sha(msrc),'geometry_preserved':True})
ovps=[]
for rid,target in geos.items():
 target=copy.deepcopy(target);target.set('fill',{'서울':'#286cda','경기':'#a47d32','인천':'#167f86'}[regions[rid]['province']]);ovps.append(target)
write(assets/'top20_overview.svg',paths_svg([*base_paths,*ovps]))
# 대표시안은 무음입니다. 음성 생성·본편 합성은 이 빌더의 기능이 아닙니다.
audio=None
if audio:
 src=Path(audio); assert src.exists()
 if T.get('audio_sha256') and not T.get('audio_mix_file'):assert sha(src)==T['audio_sha256']
 dest=assets/('narration'+src.suffix);stage(src,dest);inputs.append(src);audio='assets/'+dest.name
panels={};price_maps={};photo_bindings=read(H/'photo_bindings.json')['bindings']
price_file=E/'director/top20-explain-v3/price_panel_data.json'
v3_map_file=E/'visual/top20-explain-v3/maps/map_assets.json'
if price_file.exists():
 pd=read(price_file);inputs.append(price_file)
 if pd.get('source_file')!='research/top20-explain-v3/prices/final-api-20261103-v2/map_price_inputs.json':raise ValueError('정상행 보존 final-api-20261103-v2 원팩만 허용합니다.')
 upstream=E/pd['source_file']
 if sha(upstream)!=pd.get('source_sha256'):raise ValueError('확정 v2 가격 원팩 SHA 불일치')
 inputs.append(upstream)
 verification_file=E/'qa/top20-explain-v3/price_panel_verification.json';verification=read(verification_file);inputs.append(verification_file)
 if verification.get('status')!='passed' or verification.get('price_panel_sha256')!=sha(price_file):raise ValueError('독립 가격 검수 SHA 연결 실패')
 rows=pd.get('regions',pd.get('panels',pd.get('data',[])))
 if not isinstance(rows,list):raise ValueError('price_panel_data는 regions/panels/data 배열이 필요합니다.')
 for row in rows:
  row=copy.deepcopy(row);row.setdefault('status','verified' if pd.get('status')=='verified_price_data_for_script_review_not_video_approval' else pd.get('status'))
  if row['region_id'] in panels:raise ValueError('가격 region_id 중복')
  if row.get('status') in ['verified','final','ready']:
   for k in ['median_manwon','n','contract_window','as_of_date','area_range_m2','representative']:
    if row.get(k) is None:raise ValueError('확정가격 필수 조건 누락: '+k)
   if not isinstance(row['n'],int) or row['n']<=0:raise ValueError('지역 n은 실제 양의 거래 건수여야 합니다.')
   if not all(row['contract_window'].get(k) for k in ['start','end']):raise ValueError('계약기간 시작/종료 필수')
   area=row['area_range_m2']
   if not isinstance(area,dict) or not all(k in area for k in ['minimum','maximum','endpoints_inclusive']):raise ValueError('전용면적 범위와 경계 포함 여부 필수')
   rep=row['representative']
   if not all(rep.get(k) is not None for k in ['apt_name','median_manwon','n']):raise ValueError('단지 자체 가격/표본/명칭 필수')
   if not isinstance(rep['n'],int) or rep['n']<=0:raise ValueError('단지 n은 실제 양의 거래 건수여야 합니다.')
  panels[row['region_id']]=row
set_protected_phrases([(v.get('representative') or {}).get('apt_name') for v in panels.values()])
if v3_map_file.exists():
 md=read(v3_map_file);inputs.append(v3_map_file)
 if not price_file.exists() or md.get('source_price_panel_sha256')!=sha(price_file):raise ValueError('지도와 확정가격 SHA 연결 실패')
 for row in md.get('assets',[]):
  row=copy.deepcopy(row);rid=row['region_id'];price_maps[rid]=row
  file=row.get('vector_file') or row.get('file') or row.get('png_file')
  # 핀 없음/검증됨이 명시된 지도만 통합합니다. 편집기는 가짜 핀을 그리지 않습니다.
  rep=(panels.get(rid) or {}).get('representative') or {};marker=row.get('marker') or {}
  pin_allowed=(row.get('marker') is None) or (row.get('marker_status')=='verified_coordinate_inside_region' and marker.get('point_inside_real_region') is True and rep.get('coordinate_status')=='verified' and marker.get('apt_id')==rep.get('apt_id') and marker.get('lat')==rep.get('lat') and marker.get('lng')==rep.get('lng'))
  if row.get('marker') is not None and not pin_allowed:raise ValueError('지도 핀 검증 정보 연결 실패: '+rid)
  if not file or not pin_allowed:continue
  mp=Path(file)
  if not mp.is_absolute():mp=E/mp
  if not mp.exists():raise FileNotFoundError(mp)
  if not row.get('sha256') or sha(mp)!=row['sha256']:raise ValueError('v3 지도 SHA 불일치/누락: '+rid)
  dest=assets/(rid+'_price_map'+mp.suffix);stage(mp,dest);inputs.append(mp)
  row['_staged_file']='../assets/'+dest.name
  asset_records.append({'region_id':rid,'price_map':str(dest.relative_to(M)).replace('\\','/'),'price_map_sha256':sha(dest),'original_map_sha256':sha(mp),'map_bytes_preserved':True,'marker_status':row.get('marker_status')})
js(H/'input_manifest.json',{'task_id':'top20-explain-editor-v3-spec','status':'provisional','inputs':[{'path':str(p).replace('\\','/'),'sha256':sha(p)} for p in inputs],'assets':asset_records,'timing_file':a.timing,'timing_locked':bool(T.get('timing_locked')),'price_data_present':price_file.exists(),'v3_map_manifest_present':v3_map_file.exists(),'approval_source':'director/top20-explain-v3/requirements.json; 이번 사용자 script gate 지시'})
js(H/'credits.json',credits)

CSS='''@font-face{font-family:Pretendard;src:url(assets/Pretendard-Regular.woff2) format("woff2");font-weight:400}@font-face{font-family:Pretendard;src:url(assets/Pretendard-Bold.woff2) format("woff2");font-weight:700}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#f6f4ef}body{font-family:Pretendard,sans-serif;color:#173348}#film{position:relative;width:100%;height:100%;overflow:hidden}.text{position:absolute;line-height:1.24;white-space:normal;word-break:keep-all;overflow-wrap:break-word;letter-spacing:-.018em;font-variant-numeric:tabular-nums}.shape,.photo{position:absolute;display:block}.photo{border-radius:12px}.bar{transform-origin:left center}.source{color:#536873}.caption{position:absolute;left:96px;right:96px;bottom:28px;height:130px;border-radius:13px;background:#fff;display:flex;align-items:center;justify-content:center;padding:12px 35px;text-align:center;font-size:39px;line-height:1.25;font-weight:400;word-break:keep-all}.caption-inner{width:100%;max-width:1610px}.ink{color:#173348}.blue{color:#286cda}'''
CSS+='''.phase,.statement{position:absolute;inset:0;pointer-events:none}.fit{overflow:visible;word-break:keep-all;overflow-wrap:anywhere}.price-value{white-space:nowrap;font-variant-numeric:tabular-nums}.provisional{color:#88631b}.caption{overflow:visible}.caption.fit{position:absolute}.spec-flag{position:absolute;left:1280px;top:34px;width:560px;text-align:right;color:#88631b;font-size:21px}'''
write(M/'style.css',CSS)
def tween(selector,fr,to,at,dur=.45,ease='power2.out'):
 return f'tl.set({json.dumps(selector)},{json.dumps(fr)},0);tl.fromTo({json.dumps(selector)},{json.dumps(fr)},{json.dumps(dict(to,duration=dur,ease=ease,immediateRender=False))},{at:.4f});'
def count(s,id,val,at):
 # Exact final value; reveal only. No unspoken intermediate count values.
 return f'document.getElementById("{id}").textContent="{val:,}";'+tween('#'+id,{'opacity':0},{'opacity':1},at,.25)
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
def region_scene(s):
 rid=s['region_id'];r=regions[rid];p=photos[rid];n=r['count2024'];pid=s['scene_id'];ss='';an=''
 # Photos are unchanged and always contained. The tinted panel is a separate layer.
 ss+=box(80,210,990,556,'#e7e9e4')+img(f'../assets/{rid}.jpg',80,210,990,556)
 year=p['photo_capture_year'] or '연도 미상'
 ss+=txt(p['actual_place'],80,785,1000,29,700)+txt(f'실제 장소 자료사진 · 촬영 {year}',80,826,1000,20,color='#536873')
 ss+=img(f'../assets/{rid}_locator.svg',1120,210,720,410)
 ss+=txt(('2024 옛 서구 · 현재 서해구+검단구 범위' if rid=='R01' else f'{r["province"]} {r["region"]} · 2024 통계구역'),1120,596,720,23,700)
 ss+=txt('거주 신혼부부',1120,645,650,25,color='#536873')
 ss+=txt('0',1120,678,545,86,700,'#286cda',id=f'{pid}-count')+txt('쌍',1705,719,100,30)
 ss+=box(1120,789,650,21,'#dfe4e5',4)+box(1120,789,650*n/16000,21,'#286cda',4,'bar',f'{pid}-bar')
 ss+=txt('0',1120,819,80,18,color='#536873')+txt('8,000',1420,819,120,18,color='#536873')+txt('16,000쌍',1675,819,160,18,color='#536873')
 ss+=txt('동일 척도',1120,855,180,18,color='#536873')
 rank=r['rank'];prev=regions.get(f'R{rank+1:02d}')
 if prev: note=f'{prev["region"]}보다 {n-prev["count2024"]:,}쌍 더 많음'
 else: note='2024 재설치 · 2023 비교값 없음'
 ss+=txt(note,1300,853,540,20,700)
 at=anchor(s,'count',0);an+=count(s,f'{pid}-count',n,at)+tween(f'#{pid}-bar',{'scaleX':0},{'scaleX':1},at,1.6)
 # Spoken comparisons are an adjacent evidence strip, never a map-pin claim.
 if rid in ['R16','R13','R10','R08','R06','R05','R01']:
  k=2 if rid not in ['R01','R10'] else (4 if rid=='R01' else 3)
  at=anchor(s,'change',k);diff=r['change_couples'];pct=r['change_percent_display'];sign='+' if diff>0 else '−';verb='증가' if diff>0 else '감소'
  ss+=box(95,221,690,66,'#fffef9',10,id=f'{pid}-change-bg')
  ss+=txt(f'2023 → 2024   {sign}{abs(diff):,}쌍 · {abs(pct):.1f}% {verb}',116,238,645,25,700,id=f'{pid}-change-text')
  an+=tween(f'#{pid}-change-bg',{'opacity':0},{'opacity':1},at,.25)+tween(f'#{pid}-change-text',{'opacity':0},{'opacity':1},at,.25)
 # Individual authors are kept readable on screen; complete links/conditions in credits.json/md.
 author=re.sub('<[^>]+>','',p['source_or_prompt'].get('author',''))
 ss+=txt('사진: '+author+' · '+p['license']['name'],80,859,990,17,color='#536873')
 return ss,an
def insight1(s):
 ss='';an='';P=s['scene_id'];x0=290;x1=1000
 y=lambda v:700-(v-7600)/300*360
 ss+=txt('같았던 2023년 → 갈라진 2024년',110,230,1000,31,700)
 for v in [7600,7700,7800,7900]:
  ss+=box(235,y(v),850,2,'#dfe4e5',0)+txt(f'{v:,}',110,y(v)-14,110,22,color='#536873')
 ss+=txt('2023',245,742,180,25,700)+txt('2024',930,742,180,25,700)
 ss+=txt('세로축 7,600–7,900쌍 확대',110,800,900,21,color='#536873')
 ss+='<svg style="position:absolute;left:0;top:0;width:1920px;height:880px" viewBox="0 0 1920 880">'
 for rid,col in [('R18','#a47d32'),('R17','#286cda')]:
  r=regions[rid];d=f'M{x0},{y(7797)} L{x1},{y(r["count2024"])}'
  ss+=f'<path id="{P}-{rid}-line" d="{d}" fill="none" stroke="{col}" stroke-width="6" pathLength="1"/><circle cx="{x0}" cy="{y(7797)}" r="10" fill="#173348"/><circle id="{P}-{rid}-dot" cx="{x1}" cy="{y(r["count2024"])}" r="11" fill="{col}"/>'
  an+=tween(f'#{P}-{rid}-line',{'strokeDashoffset':1},{'strokeDashoffset':0},anchor(s,'difference',1),1.6)
  an+=f'document.getElementById("{P}-{rid}-line").style.strokeDasharray="1";'
 ss+='</svg>'
 ss+=txt('7,797쌍',x0-90,y(7797)+28,230,32,700)
 ss+=txt('연수 7,875',x1-60,y(7875)-58,285,29,700,'#286cda')+txt('+78쌍',x1-15,y(7875)+15,220,26,700,'#286cda')
 ss+=txt('기흥 7,686',x1-60,y(7686)+23,285,29,700,'#88631b')+txt('−111쌍',x1-15,y(7686)-48,220,26,700,'#88631b')
 ss+=img('../assets/R18.jpg',1290,230,550,215)+txt('용인시 기흥구 · 구성역 주변',1290,457,550,23,700)
 ss+=img('../assets/R17.jpg',1290,510,550,215)+txt('인천 연수구 · 송도 센트럴파크',1290,737,550,23,700)
 ss+=txt('비교 가능한 19곳',110,844,500,24,700)+txt('증가 6곳  /  감소 13곳',610,837,1100,33,700,'#286cda',id=f'{P}-summary')
 an+=tween(f'#{P}-summary',{'opacity':0},{'opacity':1},anchor(s,'summary',3))
 return ss,an
def insight2(s):
 ss='';an='';P=s['scene_id']
 ss+=txt('전체 수 차이는 59쌍',100,222,1000,37,700)+txt('영통구 8,388쌍  ·  권선구 8,329쌍',100,278,1050,26)
 ss+=txt('초혼',105,370,220,34,700,'#286cda')+txt('재혼',105,615,220,34,700,'#88631b')
 x=470; maxw=990
 for category,y,key,vals,col in [('초혼',370,'first_marriage_couples',[7634,6746],'#286cda'),('재혼',615,'remarried_couples',[733,1563],'#a47d32')]:
  for j,(rid,name) in enumerate([('R12','영통구'),('R13','권선구')]):
   v=regions[rid][key];yy=y+j*94; bid=f'{P}-{rid}-{category}'
   ss+=txt(name,305,yy+5,150,27,700)+box(x,yy,maxw,54,'#e5e8e7',4)+box(x,yy,maxw*v/8000,54,col,4,'bar',bid)
   nid=bid+'-value';ss+=txt('0',x+maxw+25,yy+4,180,31,700,id=nid)+txt('쌍',x+maxw+185,yy+7,60,28)
   an+=tween(f'#{bid}',{'scaleX':0},{'scaleX':1},anchor(s,category,1 if category=='초혼' else 3),1.6)
   an+=count(s,nid,v,anchor(s,category,1 if category=='초혼' else 3))
 ss+=txt('초혼: 영통구가 888쌍 더 많음',100,828,820,28,700,'#286cda')+txt('재혼: 권선구가 830쌍 더 많음',980,828,850,28,700,'#88631b')
 ss+=txt('0',470,789,100,19,color='#536873')+txt('4,000',940,789,130,19,color='#536873')+txt('8,000쌍',1390,789,150,19,color='#536873')
 return ss,an
def overview(s,close=False):
 ss=img('../assets/top20_overview.svg',80,215,1090,620);an=''
 if not close:
  ss+=txt('TOP20에 든 구의 개수',1220,225,600,30,700)
  for i,(name,v,col) in enumerate([('서울',9,'#286cda'),('경기',6,'#a47d32'),('인천',5,'#167f86')]):
   y=300+i*145;ss+=txt(name,1220,y,200,33,700)+txt(f'{v}곳',1600,y-15,230,60,700,col)
   ss+=box(1220,y+69,560,20,'#e2e7e7',4)+box(1220,y+69,560*v/10,20,col,4,'bar',f'{s["scene_id"]}-{name}')
   an+=tween(f'#{s["scene_id"]}-{name}',{'scaleX':0},{'scaleX':1},anchor(s,'province_counts',1)+i*.15,1.6)
  ss+=txt('구의 개수 · 인구 비중과 구별',1220,756,620,23,color='#536873')
 else:
  for i,(label,line) in enumerate([('규모','기준일에 얼마나 많이 사는가'),('변화','1년 전과 얼마나 달라졌는가'),('구성','어떤 부부가 집계됐는가')]):
   y=230+i*154;ss+=txt(label,1230,y,550,38,700,'#286cda')+txt(line,1230,y+58,590,27)
  ss+=txt('직장 위치  ·  예산  ·  집 크기',1230,741,610,29,700)
  ss+=txt('다음 편: 지역별 아파트 후보 비교',1230,802,610,25,700,'#286cda')
 return ss,an
def opening(s):
 ss='';an=''
 if s['scene_id']=='O001':
  for rid,x,y,w,h in [('R17',80,235,1000,425),('R02',80,674,485,184),('R01',585,674,495,184)]:ss+=box(x,y,w,h,'#e7e9e4')+img(f'../assets/{rid}.jpg',x,y,w,h)
  ss+=img('../assets/top20_overview.svg',1120,250,720,410)
  ss+=txt('20위 → 1위',1140,660,690,78,700,'#286cda')+txt('수도권 53개 구 중 스무 곳',1140,776,680,30,700)
 else:
  ss+=img('../assets/top20_overview.svg',80,225,1000,600)
  for i,(a,b) in enumerate([('2024.11.1','당시 통계구역 기준'),('혼인 5년 미경과','혼인관계 유지 · 국내 거주 조건'),('초혼 + 재혼 포함','신혼부부 전체 수 · 단위는 쌍')]):
   y=245+i*200;ss+=txt(a,1190,y,630,43,700,'#286cda')+txt(b,1190,y+72,630,27)
 return ss,an

from visuals import install_visuals
from extra_scenes import load_renderers
visual_context=install_visuals(globals())
visual_context=install_v3(globals(),visual_context,panels,price_maps,photo_bindings)
extra_renderers=load_renderers(visual_context,a.scene_data,a.visual_module)
hosts=[];story=[]
for i,s in enumerate(scenes):
 sid=s['scene_id']; dur=s['duration_s']
 if s['scene_id'] in extra_renderers:body,anim=extra_renderers[s['scene_id']](s,visual_context)
 elif s.get('visual',{}).get('type'):body,anim=extra_renderers['__generic__'](s,visual_context)
 elif s.get('region_id'): body,anim=region_scene(s)
 elif sid=='I001':body,anim=insight1(s)
 elif sid=='I002':body,anim=insight2(s)
 elif sid in ['I003','C001','E001']:body,anim=overview(s,sid!='I003')
 elif sid in ['O001','O002']:body,anim=opening(s)
 else:raise ValueError('No visual renderer/spec for '+sid+'; add to extra_scenes.py or --scene-data')
 # Subcomposition's root id, host id and paused timeline key are identical.
 flag='<div class="spec-flag">편집 대표시안 · provisional · 실측 타이밍 대기</div>'
 content=f'{shell(s)}{body}{source_line(s)}{flag}'
 sub=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template><style>#{sid}{{position:absolute;inset:0;width:100%;height:100%;background:#f6f4ef;overflow:hidden}}</style><div id="{sid}" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{dur}">{content}</div><script>document.fonts.ready.then(()=>{{{FIT_SCRIPT}const tl=gsap.timeline({{paused:true}});{anim}window.__timelines["{sid}"]=tl;}});</script></template></body></html>'''
 write(M/f'scenes/{sid}.html',sub)
 hosts.append(f'<div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="scenes/{sid}.html" data-start="{s["start_s"]}" data-duration="{dur}" data-track-index="1" data-width="1920" data-height="1080"></div>')
 # 독립 HTML: 실제 음성 없는 검토용이며 자막도 임시 문장 예산을 사용합니다.
 preview_cues=[]
 for st in s['sentence_times']:
  if st.get('is_pending'):continue
  for c in make_cues(st,[],maxchars=43):
   preview_cues.append(f'<div id="{sid}-preview-cue-{len(preview_cues)}" class="clip caption fit" data-min-font="24" data-start="{c["start_s"]:.6f}" data-duration="{c["end_s"]-c["start_s"]:.6f}" data-track-index="4">{esc(c["text"])}</div>')
 standalone=content+''.join(preview_cues)
 preview=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><link rel="stylesheet" href="../../style.css"><script src="../../assets/gsap.min.js"></script></head><body><div id="{sid}" style="position:relative;width:100%;height:100%" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{dur}">{standalone.replace("../assets/","../../assets/")}</div><script>window.__timelines=window.__timelines||{{}};document.fonts.ready.then(()=>{{{FIT_SCRIPT}const tl=gsap.timeline({{paused:true}});{anim}window.__timelines["{sid}"]=tl;}});</script></body></html>'
 write(M/f'representatives/{sid}/index.html',preview)
 if s.get('region_id'):
  # 시간 재생기 없이도 바로 가격 레이아웃을 볼 수 있는 독립 정적 HTML입니다.
  price_only=body[body.index(f'<div id="{sid}-price-phase"'):]
  static_content=f'{shell(s)}{price_only}{flag}'
  static=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><link rel="stylesheet" href="../../style.css"><script src="../../assets/gsap.min.js"></script></head><body><div id="{sid}-static-price" style="position:relative;width:100%;height:100%" data-composition-id="{sid}-static-price" data-width="1920" data-height="1080" data-duration="1">{static_content.replace("../assets/","../../assets/")}</div><script>window.__timelines=window.__timelines||{{}};document.fonts.ready.then(()=>{{{FIT_SCRIPT}window.__timelines["{sid}-static-price"]=gsap.timeline({{paused:true}});}});</script></body></html>'
  write(M/f'price_panels/{sid}/index.html',static)
 rule='feature-photo-hold + original-word-price-map-switch'
 story.append(f'## Frame {i+1} — {sid}\nstatus: animated_provisional_timing\nsrc: main/scenes/{sid}.html\nscene_id: {sid}\ntime: {s["start_s"]:.3f}–{s["end_s"]:.3f}\nmotion: {rule}\nbeat: {s["message"] if "message" in s else s.get("title",sid)}\n')
 # Sidecar documents real motion and explicitly excludes audio validation.
 js(M/f'scenes/{sid}.motion.json',{'scene_id':sid,'duration':dur,'timing_basis':T.get('timing_basis'),'entry':'hard cut under persistent channel shell','exit':'hard cut, no clip visibility tween','rules':rule.split(' + '),'anchors':s['anchors'],'audio_verified':False})

def legacy_split_semantic_unused(text,maxchars=43):
 # Keep number+unit and proper names in whole tokens. Avoid arbitrary character cutting.
 chunks=[];cur=''
 tokens=re.findall(r'(?:\d{4}년\s+\d{1,2}월\s+\d{1,2}일|\d+만\s+[\d,]+쌍|(?:여섯|열세|열아홉|스무|열|다섯|두|한|세|네)\s+(?:곳|쌍|개|사람|지역|가지|구|해)[가-힣]*|\S+)',text)
 for tok in tokens:
  if cur and len(cur)+len(tok)+1>maxchars:chunks.append(cur);cur=tok
  else:cur=(cur+' '+tok).strip()
  if tok.endswith(',') and len(cur)>=16:chunks.append(cur);cur=''
 if cur:chunks.append(cur)
 return chunks
caps=[]
for s in scenes:
 ov=overrides.get(s['scene_id'],{})
 if ov.get('captions') and not word_groups:
  allowed={t['sentence_id'] for t in s.get('sentences',[])}
  for c in ov['captions']:
   if c.get('sentence_id') and c['sentence_id'] not in allowed:continue
   caps.append(dict(c,scene_id=s['scene_id']))
  continue
 for st in s['sentence_times']:
  if st.get('is_pending'):continue
  if word_groups:
   for cue in make_cues(st,word_groups.get(st['sentence_id'],[]),readings.get(st['sentence_id'])):
    caps.append(dict(cue,scene_id=s['scene_id'],start_s=s['start_s']+cue['start_s'],end_s=s['start_s']+cue['end_s']))
   continue
  chunks=split_semantic(st['text']);den=sum(len(c) for c in chunks);p=0
  for ch in chunks:
   b=st['start_s']+(st['end_s']-st['start_s'])*p/den;p+=len(ch);e=st['start_s']+(st['end_s']-st['start_s'])*p/den
   caps.append({'scene_id':s['scene_id'],'start_s':s['start_s']+b,'end_s':s['start_s']+e,'text':ch,'sentence_id':st['sentence_id']})
from caption_backgrounds import body_windows,markup
caption_html=markup(body_windows(scenes,max(c['end_s'] for c in caps)),'spec')+''.join(f'<div id="cue-{i}" class="clip caption fit" data-min-font="24" data-start="{c["start_s"]:.5f}" data-duration="{c["end_s"]-c["start_s"]:.5f}" data-track-index="4" data-track-kind="captions">{esc(c["text"])}</div>' for i,c in enumerate(caps))
write(M/'scenes/CAPTIONS.html',f'<template><style>#CAPTIONS{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}</style><div id="CAPTIONS" data-composition-id="CAPTIONS" data-width="1920" data-height="1080" data-duration="{total}">{caption_html}</div><script>window.__timelines["CAPTIONS"]=gsap.timeline({{paused:true}});</script></template>')
caption_host=f'<div id="CAPTIONS" class="clip" data-composition-id="CAPTIONS" data-composition-src="scenes/CAPTIONS.html" data-start="0" data-duration="{total}" data-track-index="4" data-track-kind="captions" data-width="1920" data-height="1080"></div>'
audio_html=f'<audio id="main-narration" class="clip" src="{audio}" data-start="0" data-duration="{total}" data-track-index="3"></audio>' if audio else ''
brand_refs={'assets':[],'status':'대표시안은 브랜드 삽입·음성 합성 없음'}
inserts=[]
for slot in inserts:
 kind=slot.get('kind','intro');key='channel_brand_'+kind+'_clean_v7';ref=next(v for v in brand_refs['assets'] if v['asset_id']==key)
 src=Path(slot['source_file']) if slot.get('source_file') else R/ref['path'];assert sha(src)==ref['sha256'];stage(src,assets/(kind+'.mp4'))
 # A provided master mix already contains embedded brand music; otherwise leave sound on the brand clip.
 sound='muted' if T.get('audio_includes_brand',False) or T.get('audio_mix_file') else 'data-has-audio="true"'
 hosts.append(f'<video id="brand-{kind}" class="clip" src="assets/{kind}.mp4" {sound} data-start="{slot["start_s"]}" data-duration="{slot["duration_s"]}" data-track-index="2" style="position:absolute;inset:0;width:100%;height:100%"></video>')
js(H/'reusable_media.json',brand_refs)
write(M/'index.html',f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><link rel="stylesheet" href="style.css"></head><body><div id="film" data-composition-id="film" data-width="1920" data-height="1080" data-duration="{total}">{"".join(hosts)}{audio_html}{caption_host}</div><script>window.__timelines["film"]=gsap.timeline({{paused:true}});</script></body></html>')
js(M/'caption_mapping.json',{'timing_locked':T.get('timing_locked',False),'basis':'provider_word_boundaries_with_display_reading_mapping' if word_groups else 'external timings' if a.timing else 'proportional sentence estimates; NOT audio aligned','source_script':str(script_path),'source_script_sha256':sha(script_path),'source_markdown_sha256':sha(script_md),'script_revision':'v6','display_text_basis':'최종v6 sentence_id/display_text 원문; cue 결합 검사는 caption_integrity.json','selected_scene_ids':[s['scene_id'] for s in scenes],'removed_sentence_ids':sp.get('removed_sentence_ids',[]),'cues':caps})
js(H/'timeline_resolved.json',{'timing_locked':bool(T.get('timing_locked')),'audio_file':str((M/audio).resolve()) if audio else None,'words_files':sorted(word_paths-{''}) if word_groups else [],'scenes':scenes,'duration_s':total,'source_timing':a.timing})
js(H/'timing.provisional.json',{'timing_locked':False,'audio_file':None,'timing_basis':'script_estimate_not_audio_aligned','scenes':[{'scene_id':s['scene_id'],'start_s':s['start_s'],'end_s':s['end_s'],'anchors':s['anchors'],'sentence_times':s['sentence_times']} for s in scenes]})
js(H/'timing_adapter_schema.json',{'timing_locked':'boolean. True only when director supplies actual audio lock','timing_basis':'actual_audio or provisional_*','audio_file':'absolute local path of full-timeline dry narration (optional for snapshots)','audio_mix_file':'optional completed full-timeline mix, preferred over audio_file','audio_includes_brand':False,'last_speech_end_s':'global last spoken endpoint; E001.end must equal this +3 exactly once','inserts':[{'kind':'intro','start_s':24.0,'duration_s':5.0},{'kind':'outro','start_s':485.0,'duration_s':10.0}],'scenes':[{'scene_id':'S003','start_s':46.0,'end_s':59.0,'anchors':{'count':0.2,'change':6.3},'sentence_times':[{'sentence_id':'S003-01','text':'Exact spoken sentence','start_s':0.0,'end_s':3.0}],'captions':[{'text':'Exact display cue','start_s':46.0,'end_s':49.0}]}],'note':'scene times/captions global seconds; anchors/sentence_times local seconds. Optional brand insert slots cover explicit scene gaps. Pass --timing. Any unique scene IDs; each must be present in script, lock and a visual renderer/spec. Extra scenes use extra_scenes.py or --scene-data.'})
write(H/'STORYBOARD.md',f'# 편집 대표시안 · {len(scenes)}장면 · provisional\n\n입력: {script_path.name}. 본편 아님. 타이밍 잠금: {T.get("timing_locked",False)}. 실제 청취 미실행.\n\n'+'\n'.join(story))

write(H/'credits.md','# 사진·지도 크레딧\n\n사진은 원본 파일을 그대로 복제해 비율 유지 contain 배치했습니다. 촬영연도와 2024 통계기준일을 구별합니다. 지도는 2024 실제 경계 좌표를 유지하고 범위·배치·색만 편집했습니다.\n\n'+'\n\n'.join(f'## {c["region_id"]} · {c["actual_place"]}\n{c["full_attribution"]}\n영상에서의 변경: 원본 비율 유지 배치.\n지도: {c["map_attribution"]}' for c in credits))
js(H/'build_receipt.json',{'task_id':'top20-explain-editor-v3-spec','spec_project':str(M),'status':'provisional_script_timing_wait_verified_price_connected','scene_count':len(scenes),'canvas':[1920,1080],'fps':30,'spec_duration_s':total,'duration_is_actual':False,'audio_connected':False,'timing_locked':bool(T.get('timing_locked')),'scope':'대표 유형 및 최고가격/최장단지명/옛서구 경계시안; 최종 생성 아님','script_file':str(script_path),'script_markdown':str(script_md),'source_timing':a.timing,'layout_families':visual_context['layout_families'],'full_render_started':False,'new_tts_started':False,'generator_sha256':sha(__file__)})
js(H/'anchor_audit.json',visual_context['anchor_audit'])
js(H/'phase_audit.json',visual_context['phase_audit'])
js(H/'price_audit.json',visual_context['price_audit'])
js(H/'photo_audit.json',visual_context['photo_audit'])
js(H/'price_map_credits.json',{'source_manifest':str(v3_map_file),'assets':[{'region_id':v['region_id'],'source_file':v.get('file'),'sha256':v.get('sha256'),'attribution':v.get('attribution'),'changes':'부모 제공 SVG 바이트 동일 복제·비율 유지 contain 배치. 검증 단지 내부 대표점은 출입구/세대 위치를 뜻하지 않습니다.'} for v in price_maps.values()]})
write(H/'credits.md',(H/'credits.md').read_text(encoding='utf-8')+'\n\n## v3 가격지도\n부모 제공20개 SVG를 원본 바이트 그대로 보존해 배치합니다. 투영·핀 검증은 visual manifest와 부모 검수 기록을 연결합니다. 전체 조건은 price_map_credits.json 및 설명란 전달용 크레딧에 유지합니다. 통합 통계 출처 기관명은 최신 지시에 따라 국가데이터처로 표시합니다.\n')
print(json.dumps({'scenes':len(scenes),'photos':len(photos),'duration_s':total,'timing_locked':T.get('timing_locked',False),'audio':bool(audio),'main':str(M)},ensure_ascii=False))
