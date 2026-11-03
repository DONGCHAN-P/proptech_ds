"""현재 final-v3 읽기 전용 소스 QA. 변경은 자신의 QA 폴더에만 기록."""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re

Q=Path(__file__).resolve().parent
E=Q.parents[2]
R=E.parents[2]
D=E/'director/top20-split-v4/part1-production-v1'
P=E/'editor/top20-split-v4/part1-production-v1/final-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in s if c.isalnum())
class Node:
    def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def text(self):return ''.join(c.text() if isinstance(c,Node) else c for c in self.children)
    def nodes(self):
        yield self
        for c in self.children:
            if isinstance(c,Node):yield from c.nodes()
class Doc(HTMLParser):
    def __init__(self,t):
        super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.feed(t)
    def handle_starttag(self,t,a):
        n=Node(t,a);self.stack[-1].children.append(n)
        if t not in {'img','link','meta','source','br','hr','input'}:self.stack.append(n)
    def handle_startendtag(self,t,a):self.handle_starttag(t,a)
    def handle_endtag(self,t):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==t:self.stack=self.stack[:i];break
    def handle_data(self,t):self.stack[-1].children.append(t)
def classes(n,c):return c in n.attrs.get('class','').split()
def oneclass(n,c):return next(v for v in n.nodes() if classes(v,c))
def withid(doc,k):return next(v for v in doc.root.nodes() if v.attrs.get('id')==k)
checks=[]
def check(name,result,evidence=None):checks.append(dict(check=name,passed=bool(result),evidence=evidence))
paths=[P/'index.html',P/'style.css',P/'input_manifest.json',P/'anchor_audit.json',P/'price_audit.json',P/'photo_audit.json',P/'storyboard.json']+sorted((P/'scenes').glob('*.html'))
start_hashes={str(p):sha(p) for p in paths}
html=(P/'index.html').read_text(encoding='utf-8')
css=(P/'style.css').read_text(encoding='utf-8')
doc=Doc(html)
lock=read(D/'locked_timing.json');canonical=read(D/'approved_part1_scene_proposals.json')
scenes={s['scene_id']:s for s in lock['scenes']}
original={s['scene_id']:s for s in canonical['scenes']}
subs={k:Doc((P/f'scenes/{k}.html').read_text(encoding='utf-8')) for k in scenes}
check('current_v2_12_subcompositions',len(subs)==12 and [n.attrs.get('data-composition-id') for n in doc.root.nodes() if 'data-composition-src' in n.attrs]==list(scenes))
check('timing_script_hashes',read(P/'input_manifest.json')['timing_sha256']==sha(D/'locked_timing.json') and read(P/'input_manifest.json')['script_sha256']==sha(D/'approved_part1_scene_proposals.json'))
for sid,s in scenes.items():
    h=withid(doc,sid)
    check('scene_timing_'+sid,abs(float(h.attrs['data-start'])-s['start_s'])<1e-8 and abs(float(h.attrs['data-duration'])-s['duration_s'])<1e-8)
    raw=(P/f'scenes/{sid}.html').read_text(encoding='utf-8')
    check('paused_timeline_id_'+sid,'paused:true' in raw and 'window.__timelines["'+sid+'"]' in raw)
cues=[n for n in doc.root.nodes() if classes(n,'caption')]
check('176_caption_text_and_timing_exact',len(cues)==len(lock['captions'])==176 and all(n.text()==c['text'] and abs(float(n.attrs['data-start'])-c['start_s'])<1e-8 and abs(float(n.attrs['data-duration'])-(c['end_s']-c['start_s']))<1e-8 for n,c in zip(cues,lock['captions'])))
check('caption_timing_no_overlap',all(a['end_s']<=b['start_s']+1e-6 for a,b in zip(lock['captions'],lock['captions'][1:])))
check('caption_DOM_stacking_after_scenes',html.index('id="caption-bg-0"')>max(html.index('id="'+sid+'"') for sid in scenes) and html.index('id="cue-0"')>html.index('id="caption-bg-0"'))
check('caption_box_canvas_bounds_source',126+1668<=1920 and 945+104<=1080 and 'n>32' in html and 'document.fonts.ready' in html,dict(rect=[126,945,1668,104],font_range=[32,39],pixel_fit='pending_actual_MP4; source bounds only'))
check('cover_preserves_map_footer_source', 'top:922px' in css and 'top:942px' in css, 'R20_prices.png을 직접 확인: 범례 약850–878px, 원본 지도 크레딧 약899–915px. cover 시작922px. 나머지19개 static map은 동일 레이아웃 SHA 재사용; 현재 MP4 픽셀은 미확인.')

asset_checks=[]
manifest=read(P/'input_manifest.json')
for a in manifest['assets']:
    source=Path(a['source']);dest=P/a['dest'] if 'dest' in a else None
    ok=source.is_file() and sha(source)==a['sha256'] and (dest is None or dest.is_file() and sha(dest)==a['sha256'])
    asset_checks.append(dict(source=str(source),dest=str(dest) if dest else None,sha256=a['sha256'],matched=ok))
check('all_staged_assets_source_hash_exact',all(a['matched'] for a in asset_checks),{'count':len(asset_checks)})
photos=read(P/'photo_audit.json');pm={a['region_id']:a for a in read(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets']}
check('10_distinct_photo_files_source_hashes',len(photos)==10 and len({a['source_sha256'] for a in photos})==10 and all(a['source_sha256']==pm[a['region_id']]['sha256'] and a['actual_place']==pm[a['region_id']]['actual_place'] for a in photos))
for a in photos:
    panel=withid(subs[a['scene_id']],a['scene_id']+'-photo')
    source=pm[a['region_id']]
    credit=oneclass(panel,'photo-credit').text()
    check('photo_source_credit_'+a['scene_id'],all(s in credit for s in [source['actual_place'],source['source_or_prompt']['author'],source['license']['name']]) and 'object-fit:contain' in css)

prices=read(P/'price_audit.json');price_evidence=[]
bands=read(E/'research/top20-split-v4/prices/legend.json')['bands']
def resolve(f):
    v=read(R/f['path'])
    for key in f['field'].strip('/').split('/'):v=v[int(key)] if isinstance(v,list) else v[key]
    return v
def money(v):
    a,b=divmod(int(v),10000)
    return (str(a)+'억'+(format(b,',')+'만원' if b else '원')) if a else format(b,',')+'만원'
check('10_source_derived_price_comparisons',len(prices)==10 and {a['scene_id'] for a in prices}==set(scenes)-{'P01-INTRO','P01-OUTRO'})
for a in prices:
    sid=a['scene_id'];resolved_fields=[resolve(f) for f in a['source_fields']];source=[v for v in resolved_fields if isinstance(v,dict)]
    check('price_source_rows_'+sid,source==a['groups'])
    text=next(s['text'] for s in original[sid]['sentences'] if s['sentence_id']==a['sentence_id'])
    pane=withid(subs[sid],sid+'-price')
    for i,g in enumerate(source):
        row=withid(subs[sid],sid+'-price-row'+str(i))
        value=str(g['complex_n'])+'단지' if a['distribution'] else money(g['median_manwon'])
        count='지도 연결 '+str(g['denominator'])+'단지 기준' if a['distribution'] else '거래 '+format(g['transaction_n'],',')+'건 · '+str(g['complex_n'])+'단지'
        label=g.get('dong',g.get('label')).replace('2000년 이전 준공','2000년까지 준공')
        check('price_display_value_label_n_'+sid+'_'+str(i),oneclass(row,'price-name').text()==label and oneclass(row,'price-value').text()==value and oneclass(row,'price-n').text()==count)
        check('price_narration_value_'+sid+'_'+str(i),norm(str(g['complex_n'])+'곳' if a['distribution'] else value) in norm(text))
        maximum=max(g.get('median_manwon',g.get('complex_n')) for g in source)
        style=oneclass(row,'bar-fill').attrs['style'];pct=float(re.search(r'--pct:([\d.]+)%',style).group(1))
        check('price_bar_scale_'+sid+'_'+str(i),abs(pct-100*g.get('median_manwon',g.get('complex_n'))/maximum)<1e-6)
        expected_color=g['color'] if a['distribution'] else next(b['color'] for b in bands if b['min_manwon']<=g['median_manwon'] and (b['max_manwon'] is None or g['median_manwon']<b['max_manwon']))
        check('v3_price_band_color_'+sid+'_'+str(i),('background:'+expected_color) in style)
        price_evidence.append(dict(scene_id=sid,label=label,value=value,n=count,bar_percent=pct,distribution=a['distribution']))
    check('price_period_area_date_'+sid,'전용 83~85㎡ · 2026.05~10 계약 · 11.03 조회'==oneclass(pane,'chart-foot').text())

anchors=read(P/'anchor_audit.json');maps=read(E/'visual/top20-split-v4/map_assets.json')['assets'];meta={(a['region_id'],a['mode']):a for a in maps};anchor_evidence=[]
for a in anchors:
    if a['kind']!='facility':continue
    sid=a['scene_id'];rid=sid[4:];ctx=read(E/f'visual/top20-split-v4/atlas-context/{rid}_context.json')
    candidates=[(f,typ) for typ in ['schools','stations'] for f in ctx[typ] if f['name']==a['text'] and f['xy']==a['source_xy']]
    check('anchor_native_coordinate_'+sid+'_'+str(len(anchor_evidence)),bool(candidates))
    bb=meta[rid,'prices'][a['panel']+'_bounds_5179'];w=1100 if a['panel']=='detail' else 640;ox=760 if a['panel']=='detail' else 60
    sc=min((w-24)/(bb[2]-bb[0]),601/(bb[3]-bb[1]));x,y=a['source_xy'];xy=[ox+w/2+(x-(bb[0]+bb[2])/2)*sc,205+625/2+((bb[1]+bb[3])/2-y)*sc]
    check('anchor_image_projection_'+sid+'_'+str(len(anchor_evidence)),all(abs(u-v)<1e-6 for u,v in zip(xy,a['pixel_xy'])))
    sent=next(v for v in scenes[sid]['sentences'] if v['start_s']-1e-5<=a['global_s']<=v['end_s']+1e-5)
    words=sent['words'];native=any(abs(w['start_s']-a['global_s'])<1e-8 for w in words)
    check('anchor_is_native_word_time_'+sid+'_'+str(len(anchor_evidence)),native)
    station=bool(candidates and candidates[0][1]=='stations');literal=a['text'] if a['text'].endswith('역') else a['text']+'역'
    exact_spans=[]
    if station:
        for m in re.finditer(re.escape(literal),sent['text']):
            before=sent['text'][m.start()-1:m.start()] if m.start() else ''
            after=sent['text'][m.end():]
            if (not before or not re.match('[가-힣A-Za-z0-9]',before)) and (not after or after[0] in ' ,·.과와이가을를에까의은는'):
                exact_spans.append((m.start(),m.end()))
    correct_time=[]
    for start,end in exact_spans:
        w=next((w for w in words if w['source_char_start']<=start<w['source_char_end']),None)
        if w:correct_time.append(w['start_s'])
    anchor_evidence.append(dict(scene_id=sid,name=a['text'],kind='station' if station else 'school',sentence_id=sent['sentence_id'],native_word_timing=native,pixel_xy=a['pixel_xy'],coordinate_and_projection_checked=True,explicit_station_name_spans=exact_spans,expected_exact_name_word_times=correct_time,declared_global_s=a['global_s'],semantic_review_watch=station and not any(abs(t-a['global_s'])<1e-6 for t in correct_time)))

intro=(P/'scenes/P01-INTRO.html').read_text(encoding='utf-8')
check('v2_intro_brand_content_hides_by_source',"tl.set('#P01-INTRO-content',{opacity:0},5.817052)" in intro and "tl.set('#P01-INTRO-content',{opacity:1},10.817052)" in intro)
check('v2_intro_map_header_does_not_stack_by_source',"tl.set('#P01-INTRO-mast',{opacity:0},29.918904)" in intro)
check('v2_legend_opacity_source',intro.count('{opacity:.65}')==6)
check('v3_rank_line_below_title', '.rank-strip{top:140px}' in css)
check('v3_focus_note_covers_baked_glyph', '.focus-note{left:760px;top:150px;width:1100px;height:45px}' in css)
for sid in list(scenes)[1:-1]:
    raw=(P/f'scenes/{sid}.html').read_text(encoding='utf-8')
    check('v2_price_labels_n_not_animated_as_future_row_'+sid,all(("tl.fromTo('#"+sid+'-price-row'+str(i)+"',") not in raw and ("tl.fromTo('#"+sid+'-price-row'+str(i)+"-value',") in raw for i in [0,1]))

brand_nodes=[n for n in doc.root.nodes() if n.tag=='video']
check('brand_two_muted_clips_timing',len(brand_nodes)==2 and all('muted' in n.attrs for n in brand_nodes))
brand_evidence=[]
for n in brand_nodes:
    p=P/n.attrs['src'];header=p.read_bytes()[:12]
    iswave=header[:4]==b'RIFF' and header[8:12]==b'WAVE'
    check('brand_video_container_'+n.attrs['id'],not iswave,dict(path=str(p),sha256=sha(p),is_WAVE_audio=iswave))
    brand_evidence.append(dict(path=str(p),sha256=sha(p),is_WAVE_audio=iswave,muted='muted' in n.attrs))

stable=all(sha(Path(p))==h for p,h in start_hashes.items())
check('source_snapshot_stable_during_QA',stable)
findings=read(Q/'findings.json')
for issue in findings:
    if issue['issue_id'] in ['QA-PART1-SOURCE-001','QA-PART1-SOURCE-002']:
        issue['checked_revision']={'revision':'final-v3','index_sha256':sha(P/'index.html'),'anchor_audit_sha256':sha(P/'anchor_audit.json')}
        if issue['issue_id']=='QA-PART1-SOURCE-001':
            issue['status']='open_required'
            issue['rechecked_latest_version']='final-v3: both WAV headers and SHA unchanged; current actual files inspected'
            issue['current_evidence']=brand_evidence
        else:
            issue['status']='resolved_source_verified_pending_encoded'
            issue['rechecked_latest_version']='final-v3: P01-R20 has only 계남중학교/계남초등학교/신중동 facility anchors. 중동역 extra ring absent from current HTML and audit. Encoded confirmation pending.'
            issue['current_evidence']=[x for x in anchor_evidence if x['scene_id']=='P01-R20']
        (Q/('issue_'+issue['issue_id']+'.json')).write_text(json.dumps(issue,ensure_ascii=False,indent=2),encoding='utf-8')
(Q/'findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
evidence=dict(checks=checks,asset_hash_checks=asset_checks,price_display_evidence=price_evidence,anchor_evidence=anchor_evidence,brand_evidence=brand_evidence)
(Q/'source_review_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(task_id='PART1-provisional-source-independent-QA',generated_at=datetime.now(timezone.utc).isoformat(),project=str(P),checked_revision='final-v3',status='hold_brand_video_correction_before_render',critical_open_count=0,required_open_count=1,required_issues=['QA-PART1-SOURCE-001'],resolved_source_issues=['QA-PART1-SOURCE-002'],checks_total=len(checks),failed_checks=[x for x in checks if not x['passed']],counts=dict(subcompositions=12,captions=176,distinct_region_photos=10,price_comparisons=10,comparison_rows=20,facility_anchor_projection_checks=len(anchor_evidence)),coverage=dict(source_HTML_CSS='read and independently parsed all12 subcompositions plus index/CSS; final-v3 current source pinned',price_data='20 selected rows resolved from frozen source_fields; display labels/value/n/period/area and narration compared; all20 bar colors matched frozen6bands; no price research reaggregation',photos='10 distinct original hashes/actual_place/author/license linked; images not all visually re-viewed',map='unchanged staged map hashes; all27 facility coordinate/projection/native-word-time checks; R20 wrong extra ring removed',static_pixel_scope='R20_prices.png source image directly viewed once; no encoded frame yet',temporal_initial_states='source GSAP and v2/v3 fixes read; runtime state not independently played',caption_stacking='source DOM order and timing checked; encoded pixel fit pending',HF_check='parent reported pass; raw check artifact not yet independently inspected',actual_listening=False,continuous_playback=False,MP4='not_yet_in_scope_await_parent',Claude='not_called',network_calls=0,paid_calls=0),semantic_timing_watchlist=[x for x in anchor_evidence if x['semantic_review_watch']],source_hashes=start_hashes,stable_snapshot=stable,evidence_file=str(Q/'source_review_evidence.json'),evidence_sha256=sha(Q/'source_review_evidence.json'),next_owner='director/editor: replace two brand WAVE files with approved actual MP4 video assets; QA: verify changed assets and resulting actual MP4')
(Q/'provisional_source_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
handoff=read(Q/'handoff.json');handoff['status']=report['status'];handoff['required_open_count']=1;handoff['critical_open_count']=0;handoff['latest_source_revision']='final-v3';handoff['open_issue_ids']=report['required_issues'];handoff['outputs']=list(dict.fromkeys(handoff['outputs']+[str(Q/'provisional_source_review.json'),str(Q/'source_review_evidence.json')]));handoff['next_owner']=report['next_owner'];handoff['output_hashes']={Path(p).name:sha(Path(p)) for p in handoff['outputs']};(Q/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],revision='final-v3',checks=len(checks),failed_checks=report['failed_checks'],required_open_count=1,semantic_anchor_watch_count=sum(a['semantic_review_watch'] for a in anchor_evidence),report=str(Q/'provisional_source_review.json')),ensure_ascii=False))
