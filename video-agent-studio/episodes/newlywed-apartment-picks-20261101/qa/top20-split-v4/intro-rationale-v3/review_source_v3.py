"""Bounded source semantic audit of active project-v3; no production writes."""
import csv,hashlib,html.parser,json,pathlib,re
from datetime import datetime,timezone
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];ROOT=E.parents[2]
P=E/'editor/top20-split-v4/intro-rationale-v3/project-v3';D=E/'director/top20-split-v4/part1-intro-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Parser(html.parser.HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.nodes={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);n=dict(tag=tag,attrs=a,text='',children=[])
        if self.stack:self.stack[-1]['children'].append(n)
        if a.get('id'):self.nodes[a['id']]=n
        if tag not in ['meta','link','img','br','hr','input','source']:self.stack.append(n)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):
        for n in self.stack:n['text']+=data
source=(P/'index.html').read_text(encoding='utf-8-sig');p=Parser();p.feed(source)
js=re.findall(r'<script[^>]*>(.*?)</script>',source,re.S)[-1]
with (ROOT/'analysis/newlywed_region_2024/capital_gu_ranking.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
top=read(E/'research/top20-8min-v2/top20.json');legend=read(E/'research/top20-split-v4/prices/legend.json');lock=read(D/'locked_timing.json');manifest=read(P/'input_manifest.json')
checks=[]
def check(name,passed,evidence=None):checks.append(dict(check=name,passed=bool(passed),evidence=evidence))
records=[]
for r in csvrows:
    rank=int(r['rank']);n=p.nodes['record-'+str(rank)]
    texts=[x['text'].strip() for x in n['children'] if x['tag']=='text']
    count=int(re.sub(r'[^0-9]','',texts[1]));name=texts[0]
    valid=(r['region']==name or r['region'].endswith(' '+name)) and count==int(r['newlywed_couples']) and texts[2]==str(rank)+'위'
    records.append(dict(rank=rank,source_region=r['region'],display_region=name,source_count=int(r['newlywed_couples']),display_count=count,match=valid))
check('53_source_records_exact_count_rank_and_region',len(records)==53 and all(r['match'] for r in records),dict(rows=53,source='capital_gu_ranking.csv',display_abbreviations='city prefixes may be omitted; no region reassignment'))
selected=[]
for rank in range(20,10,-1):
    m=re.search(r'<g[^>]*transform="translate\(([-\d.]+),([-\d.]+)\)"><g[^>]*id="record-%s"'%rank,source)
    a=re.search(r"tl.to\('#record-%s',\{x:([-\d.]+),y:([-\d.]+),scale:([\d.]+),transformOrigin:'0 0',duration:([\d.]+).*?\},([\d.]+)\)"%rank,js)
    assert m and a,(rank,m,a)
    x,y=map(float,m.groups());dx,dy,scale,duration,start=map(float,a.groups())
    selected.append(dict(rank=rank,x=x+dx,y=y+dy,scale=scale,finish_s=start+duration))
check('selected_ten_sorted20_to11_two_rows',all(v['x']==160+(i%5)*328 and v['y']==90+(i//5)*220 for i,v in enumerate(selected)),selected)
check('nonselected43_exit_only',all(re.search(r"tl.to\('#record-%s',\{opacity:0,scale:.7,duration:.6"%r['rank'],js) for r in records if not 11<=r['rank']<=20))
check('ten_match_frozen_TOP20',all(any(x['rank']==r['rank'] and x['newlywed_couples']==r['display_count'] and x['region']==r['source_region'] for x in top['regions']) for r in records if 11<=r['rank']<=20))
check('residence_scope_not_affordability_proof','2024.11.01 거주 기준' in source and '신혼부부 거주 수로 지역을 고르고' in source and '신혼부부가 실제로 사는 곳' in source)
check('episode_and_future_order','이번 20~11위 · 다음 10~1위' in source and '예산별 아파트' in p.nodes['roadmap']['text'])
for i,band in enumerate(legend['bands']):
    n=p.nodes['price-band-'+str(i)]
    check('legend_band_'+str(i),n['text'].strip()==band['label'] and any(band['color'].lower() in x['attrs'].get('style','').lower() for x in n['children']))
check('price_reference_conditions','전용83~85㎡ · 2026.05~10 계약 · 2026.11.03 조회 · 10월은 조회일까지 신고분' in source)
check('one_complex_one_dot','집 한 단지 → 지도 점 하나' in source and '한 단지 · 한 점' in source and p.nodes['caption-11']['text']=='색은 그 단지의 거래 중위가격 구간입니다.')
check('bridge_rank_region_count',all(x in p.nodes['bridge-copy']['text'] for x in ['20위','부천 원미구','7,365쌍']))
clips=[n for n in p.nodes.values() if 'data-start' in n['attrs']]
videos=[n for n in clips if n['tag']=='video'];audios=[n for n in clips if n['tag']=='audio']
check('two_visual_videos_muted_one_master_audio',len(videos)==2 and all('muted' in n['attrs'] for n in videos) and len(audios)==1 and audios[0]['attrs']['src']=='assets/master_audio.wav')
check('brand_once_actual_MP4',sum(n['attrs'].get('src')=='assets/brand_intro.mp4' for n in videos)==1 and abs(float(p.nodes['brand-intro']['attrs']['data-start'])-lock['brand_intro']['start_s'])<1e-8)
check('preserved_body_prefix_source_interval',p.nodes['preserved-body-prefix']['attrs']['src']=='assets/original_body.mp4' and abs(float(p.nodes['preserved-body-prefix']['attrs']['data-start'])-48.5)<1e-8 and abs(float(p.nodes['preserved-body-prefix']['attrs']['data-media-start'])-lock['old_body_cut_s'])<1e-8)
captions=sorted([n for k,n in p.nodes.items() if re.fullmatch(r'caption-\d+',k)],key=lambda n:float(n['attrs']['data-start']))
expected=[c for c in lock['captions'] if c['sentence_id'].startswith('P01-INTRO-V3')]
check('13_caption_texts_times_exact',len(captions)==len(expected)==13 and all(n['text']==c['text'] and abs(float(n['attrs']['data-start'])-c['start_s'])<1e-8 and abs(float(n['attrs']['data-duration'])-(c['end_s']-c['start_s']))<1e-8 for n,c in zip(captions,expected)))
asset_rows=[]
for a in manifest['assets']:
    dest=P/a['dest'];h=sha(dest)
    asset_rows.append(dict(dest=a['dest'],actual_sha256=h,expected_sha256=a['sha256'],match=h==a['sha256']))
check('input_asset_hashes',all(a['match'] for a in asset_rows),asset_rows)
check('CSV_input_hash',manifest['data_csv_sha256']==sha(ROOT/'analysis/newlywed_region_2024/capital_gu_ranking.csv'))
check('timing_input_hash',manifest['timing_sha256']==sha(D/'locked_timing.json'))
check('paused_registered_timeline',"gsap.timeline({paused:true})" in js and 'window.__timelines["intro"]=tl' in js)
checkfile=D/'evidence/v2/check.json';hf=read(checkfile)
summary={k:{x:hf[k].get(x) for x in ['ok','errorCount','warningCount','infoCount','enabled','samples','checked','passed'] if x in hf[k]} for k in ['lint','runtime','layout','motion','contrast']}
check('parent_HF_check_active_project_v3',hf['ok'] and hf['runtime']['errorCount']==0 and hf['layout']['errorCount']==0 and hf['contrast']['errorCount']==0 and all('project-v3' in x['sourceFile'] for x in hf['lint']['findings']),summary)
watch=[dict(time_s=x['time'],selector=x['selector'],message=x['message'],held_ms=x.get('heldMs')) for x in hf['layout']['findings']]
plan=[]
def sample(t,reason):plan.append(dict(time_s=round(t,6),reason=reason))
for t,reason in [(0.1,'opening baseline'),(1.6,'kinetic hook readable state'),(2.8,'hook maximum camera scale/rotation'),(7.1,'brand midpoint'),(11.6,'town-price-unit settled'),(18.1,'all53 records settled'),(23.8,'residence criterion and count53'),(28.0,'ten sorted records after all moves and labels'),(31.6,'selected10 hold and caption'),(36.2,'future roadmap'),(41.8,'building converted into single map point and six price bins'),(44.1,'method end and price reference'),(46.4,'Wonmi bridge identity'),(48.3,'bridge reveal final'),(49.0,'preserved body prefix'),(54.566667,'streamcopy handoff before boundary')]:sample(t,reason)
for t in [4.946190476,9.946190476,16.186931217,20.612857143,26.186931217,33.548042328,39.927671958,45.131375661,48.5]:
    sample(t-1/30,'boundary before');sample(t+1/30,'boundary after')
for x in watch:sample(x['time_s'],'HF transient overlap candidate')
sample(27.8,'after transient sorting overlaps')
report=dict(status='passed_bounded_source_QA_pending_encoded_pixels' if all(c['passed'] for c in checks) else 'required_correction',checked_at=datetime.now(timezone.utc).isoformat(),checked_revision='project-v3',active_project=str(P),source_sha256=sha(P/'index.html'),css_sha256=sha(P/'style.css'),checks=checks,failed_checks=[c for c in checks if not c['passed']],actual_source_records=records,parent_HF_check=dict(path=str(checkfile),sha256=sha(checkfile),summary=summary,limitations='parent-produced source/browser check; motion validator disabled; no final MP4 pixels certified'),pixel_watchlist=watch,interpretation='거주 통계는 지역 선정 기준이며 매수 가능성을 입증하지 않음.',coverage=dict(source_semantics=True,source_asset_hashes=True,encoded_MP4_frames=False,continuous_playback=False,actual_listening=False,old_body_ASR_repeated=False),next_owner='director/editor: encoded frames/full MP4 전달; QA: pixel_review_plan.json 적용')
(Q/'source_review_v3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(Q/'pixel_review_plan.json').write_text(json.dumps(dict(project='project-v3',source_sha256=report['source_sha256'],scope='new intro and adjacent body-prefix/streamcopy join only',samples=sorted(plan,key=lambda x:x['time_s']),final_full_MP4_checks=['probe duration/codecs/one audio stream','strict full decode','original encoded body packet/frame equality receipt','audio alignment to master PCM','actual final MP4 SHA256'],coverage_policy='source/browser snapshots distinct from actual encoded frames; actual listening and continuous playback unchecked'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],checks=len(checks),failed=report['failed_checks'],source_sha256=report['source_sha256'],pixel_watchlist=watch,pixel_samples=len(plan)),ensure_ascii=False))
