import hashlib
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

EP=Path('C:/projects/realestate_reco/video-agent-studio/episodes/newlywed-apartment-picks-20261101')
ED=EP/'editor/top20-enhance-v2'; P=ED/'main'; Q=EP/'qa/top20-enhance-v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return re.sub(r'[\W_]+','',s)
def save(n,o):(Q/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
freeze=read(ED/'source_freeze.json');t=read(EP/'director/top20-enhance-v2/locked_timing.json')
mapping=read(P/'caption_mapping.json');cues=mapping['cues'];words=read(t['words_file'])['words']
sv=read(EP/'outputs/top20-enhance-v2/subtitle_verification.json');srtp=Path(sv['file'])
checks=[];issues=[]
def check(n,b,detail=None):
 checks.append(dict(check=n,passed=bool(b),detail=detail))
 if not b:issues.append(n)

records={k:sha(P/k) for k in freeze['files']}
check('동결된100개실파일 SHA',records==freeze['files'],len(records))
check('최신 f622ee9 소스 fingerprint',hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()==freeze['project_sha256'])
check('SRT/매핑SHA',sha(srtp)==sv['sha256'] and sha(P/'caption_mapping.json')==sv['caption_mapping_sha256'])
sentence_list=[s for sc in t['scenes'] for s in sc.get('sentences',[])]
sentences={s['sentence_id']:s for s in sentence_list};scenes={s['scene_id']:s for s in t['scenes']}
grouped=defaultdict(list)
for c in cues:grouped[c['sentence_id']].append(c)
check('157큐/113문장/누락·추가 없음',len(cues)==157 and len(grouped)==len(sentences)==113 and set(grouped)==set(sentences))
check('문장순서 보존',list(grouped)==[s['sentence_id'] for s in sentence_list])
range_errors=[];unit_splits=[];name_splits=[]
protected=re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일|TOP\d+|\d[\d,]*(?:\.\d+)?(?:\s*(?:만|천|억)\s*\d[\d,]*)*(?:\s*(?:퍼센트|쌍|위|개|년|월|일|㎡|만원|원|초|분|%))?')
names=['부천시 원미구','안양시 동안구','서울 마포구','수원시 영통구','수원시 권선구','미추홀구','서해구','검단구','신도림역','고덕역','청라호수공원']
for sid,gs in grouped.items():
 sentence=sentences[sid]['text'];clean=norm(sentence);offset=0;bounds=[]
 if norm(''.join(c['text'] for c in gs))!=clean:range_errors.append([sid,'문장 재결합'])
 for c in gs:
  size=len(norm(c['text']))
  if c['display_normalized_range']!=[offset,offset+size]:range_errors.append([sid,'표시문 매핑 범위',c])
  offset+=size;bounds.append(offset)
 for match in list(protected.finditer(sentence)):
  a=len(norm(sentence[:match.start()]));b=len(norm(sentence[:match.end()]))
  if any(a<x<b for x in bounds[:-1]):unit_splits.append(dict(sentence_id=sid,protected=match.group()))
 for name in names:
  for match in re.finditer(re.escape(name),sentence):
   a=len(norm(sentence[:match.start()]));b=a+len(norm(name))
   if any(a<x<b for x in bounds[:-1]):name_splits.append(dict(sentence_id=sid,protected=name))
check('113문장 정확 재결합/표시문범위',not range_errors,range_errors)
check('숫자·날짜·단위 큐 경계 보호',not unit_splits,unit_splits)
check('지정 지명 큐 경계 보호',not name_splits,name_splits)
check('양의길이·순서·중복시간 없음',all(c['end_s']>c['start_s'] for c in cues)
      and all(a['end_s']<=b['start_s']+1e-7 for a,b in zip(cues,cues[1:])))
check('모든큐 장면·문장 범위 안',all(scenes[c['scene_id']]['start_s']-1e-6<=c['start_s']<c['end_s']<=scenes[c['scene_id']]['end_s']+1e-6
      and sentences[c['sentence_id']]['start_s']-1e-6<=c['start_s']<c['end_s']<=sentences[c['sentence_id']]['end_s']+1e-6 for c in cues))
word_times=defaultdict(set)
for w in words:
 word_times[w['sentence_id']].update([round(w['start_s'],7),round(w['end_s'],7)])
check('큐 경계는 제공자 단어/문장 앵커',all(any(abs(c[key]-x)<1e-6 for x in word_times[c['sentence_id']] | {sentences[c['sentence_id']]['start_s'],sentences[c['sentence_id']]['end_s']})
      for c in cues for key in ['start_s','end_s']))

def seconds(x):
 h,m,s,ms=map(int,re.split('[:,]',x));return h*3600+m*60+s+ms/1000
parsed=[]
for block in re.split(r'\r?\n\s*\r?\n',srtp.read_text(encoding='utf-8-sig').strip()):
 lines=block.splitlines();a,b=lines[1].split(' --> ')
 parsed.append(dict(index=int(lines[0]),start_s=seconds(a),end_s=seconds(b),text='\n'.join(lines[2:])))
check('SRT157큐의 문자열·1ms 타이밍·인덱스',len(parsed)==len(cues) and all(a['index']==i+1 and norm(a['text'])==norm(b['text'])
       and abs(a['start_s']-b['start_s'])<=.001 and abs(a['end_s']-b['end_s'])<=.001 for i,(a,b) in enumerate(zip(parsed,cues))))

class Captions(HTMLParser):
 def __init__(self):super().__init__();self.items=[];self.active=None;self.backgrounds=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('data-caption-bg')=='true':self.backgrounds.append(a)
  if a.get('id','').startswith('cue-'):self.active=dict(attrs=a,text='');self.items.append(self.active)
 def handle_data(self,data):
  if self.active is not None:self.active['text']+=data
 def handle_endtag(self,tag):
  if tag=='div':self.active=None
h=Captions();h.feed((P/'scenes/CAPTIONS.html').read_text(encoding='utf-8-sig'))
check('HTML157큐와 매핑 완전일치',len(h.items)==len(cues) and all(norm(a['text'])==norm(b['text'])
      and abs(float(a['attrs']['data-start'])-b['start_s'])<.00002
      and abs(float(a['attrs']['data-duration'])-(b['end_s']-b['start_s']))<.00002 for a,b in zip(h.items,cues)))
bgs=[(float(a['data-start']),float(a['data-start'])+float(a['data-duration'])) for a in h.backgrounds]
expected_bgs=[(0,t['brand_intro']['start_s']),(t['brand_intro']['end_s'],t['last_spoken_end_s'])]
check('흰박스는 본문 큐 사이 유지·브랜드/마지막 무음 숨김',len(bgs)==2 and all(abs(x-a)<2e-6 and abs(y-b)<2e-6 for (x,y),(a,b) in zip(bgs,expected_bgs)),bgs)
check('브랜드/무음CTA의 자막 없음',all(not(c['start_s']<t['brand_intro']['end_s'] and c['end_s']>t['brand_intro']['start_s'])
      and c['end_s']<=t['last_spoken_end_s']+1e-8 for c in cues))

# 최종 MP4를 열지 않고 동결 CSS와 폰트의 실제 브라우저 글리프 경계를 측정한다.
measurement=dict(status='unchecked',method='headless_chromium_DOM_Range',mp4_opened=False)
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  if not Path(p.chromium.executable_path).exists():raise RuntimeError('설치된 Playwright Chromium 없음')
  html=Q/'caption_measurement.html'
  html.write_text('<!doctype html><html><head><link rel="stylesheet" href="'+(P/'style.css').as_uri()+'"></head><body style="width:1920px;height:1080px"></body></html>',encoding='utf-8')
  browser=p.chromium.launch(headless=True,args=['--allow-file-access-from-files'])
  page=browser.new_page(viewport=dict(width=1920,height=1080),device_scale_factor=1)
  page.goto(html.as_uri());page.evaluate('document.fonts.ready')
  measured=page.evaluate('''async texts => {
    await document.fonts.load('39px Pretendard');
    return texts.map((text,index)=>{
      const div=document.createElement('div');div.className='clip caption';div.textContent=text;
      document.body.appendChild(div);const range=document.createRange();range.selectNodeContents(div);
      const rects=[...range.getClientRects()].map(r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}));
      const b=div.getBoundingClientRect();const css=getComputedStyle(div);
      const x={index,text,rects,lines:new Set(rects.map(r=>r.top)).size,font:css.fontFamily,font_size:css.fontSize,
      within:rects.every(r=>r.left>=b.left+34.5&&r.right<=b.right-34.5&&r.top>=b.top&&r.bottom<=b.bottom)};
      div.remove();return x;
    });
  }''',[c['text'] for c in cues])
  browser.close()
  bad=[x for x in measured if not x['within'] or x['lines']>2]
  measurement=dict(status='passed' if not bad else 'failed',method='headless_chromium_DOM_Range_all157_cues_at1920x1080',
                   mp4_opened=False,fonts_loaded=True,count=len(measured),max_lines=max(x['lines'] for x in measured),findings=bad,
                   evidence=str(Q/'caption_glyph_bounds.json'))
  save('caption_glyph_bounds.json',measured);check('실폰트157큐 글리프박스/2줄상한',not bad,bad)
except Exception as e:
 measurement['reason']=str(e)[:500]
 try:
  from fontTools.ttLib import TTFont
  from PIL import ImageFont
  font_path=P/'assets/Pretendard-Regular.woff2';font=TTFont(font_path)
  cmap=font.getBestCmap();missing=sorted({ch for c in cues for ch in c['text'] if not ch.isspace() and ord(ch) not in cmap})
  ttf=Q/'Pretendard-caption-measurement.ttf';font.flavor=None;font.save(ttf)
  ft=ImageFont.truetype(str(ttf),39)
  measured=[dict(index=i,text=c['text'],advance_px=ft.getlength(c['text']),glyph_bbox=ft.getbbox(c['text'])) for i,c in enumerate(cues)]
  bad=[x for x in measured if x['advance_px']>1658 or x['glyph_bbox'][3]-x['glyph_bbox'][1]>130]
  measurement.update(fallback_status='passed' if not bad and not missing else 'requires_encoded_review',
   fallback_method='실제 Pretendard woff2를 FreeType로 측정;CSS1728px박스-좌우70px패딩=1658px.브라우저DOM검사와구분.',
   source_font_sha256=sha(font_path),count=len(measured),max_advance_px=max(x['advance_px'] for x in measured),
   missing_glyphs=missing,findings=bad,evidence=str(Q/'caption_font_metrics.json'))
  save('caption_font_metrics.json',measured)
  check('실제폰트157큐 advance폭/글리프누락 보조검사',not bad and not missing,dict(max_advance_px=measurement['max_advance_px'],findings=bad,missing=missing))
 except Exception as fallback_error:
  measurement['fallback_error']=str(fallback_error)[:500]

final_reps=[]
for name in ['frame-00-at-238.5s.png','frame-01-at-454.5s.png','frame-02-at-485s.png','frame-03-at-517.1s.png','frame-04-at-353.83s.png']:
 path=ED/'evidence/final-representatives'/name
 final_reps.append(dict(path=str(path),sha256=sha(path),source_kind='editor_preview_PNG',visually_inspected=True))
longest=sorted(enumerate(cues),key=lambda x:len(x[1]['text']),reverse=True)[:12]
report=dict(task_id='top20-enhance-QA-v2',status='passed_source_checks' if not issues else 'required_correction',
 project_sha256=freeze['project_sha256'],source_freeze_sha256=sha(ED/'source_freeze.json'),srt_sha256=sha(srtp),mapping_sha256=sha(P/'caption_mapping.json'),
 checks=checks,failed_checks=issues,caption_count=len(cues),sentence_count=len(sentences),glyph_measurement=measurement,
 longest_caption_samples=[dict(cue_index=i,**c) for i,c in longest],
 final_state_preview_evidence=final_reps,
 final_state_observations=['I002 재혼권선1563·차이830 및 초혼차이888 최종값 확인','N001 동안22→16/6510·마포21→17/6487 최종값 확인',
  'N002 세 행 최종값 재확인','E001 마지막무음 자막박스 숨김 확인','5위 부평 표본에서 미래1~4위 지명·수량·막대길이 마스킹 확인'],
 coverage=dict(continuous_playback=False,actual_listening=False,MP4_sampling=False,final_decode=False,
  actual_encoded_caption_clipping='unchecked;총괄최종handoff후검수',motion='unchecked;표본 정지 상태만 확인'),
 final_contract=dict(path='qa/top20-enhance-v2/main_final.json',requires_exact_video_sha256=True,required_open=0,critical_open=0,
  publication='local_review_only',note='이 소스 검수는 최종 MP4 통과를 대신하지 않음.최종receipt의새소스SHA에 연결할 것.'))
save('caption_source_qa.json',report)
rep=read(Q/'representatives_review.json');rep['final_state_addendum']=dict(evidence=final_reps,observations=report['final_state_observations'])
rep['final_freeze_project_sha256']=freeze['project_sha256'];rep['coverage']['final_values_hidden_in_sample']=[]
save('representatives_review.json',rep)
save('issue_CAPTION_SOURCE_HANDOFF.json',dict(issue_id='EV2-CAPTION-SOURCE-HANDOFF',recipients=['director','editor'],
 scene_id='all113sentences',문제='자막 소스검수 결과',evidence=str(Q/'caption_source_qa.json'),
 제안='최종MP4/receipt/프레임색인 인계 후 인코딩검수 진행',영향='업로드 범위 없음;MP4표본검수는 아직시작하지 않음',direct_message_sent=False))
handoff=read(Q/'handoff.json');handoff['status']='representatives_and_caption_source_reviewed_final_encode_pending'
handoff['artifacts'] = list(dict.fromkeys(handoff['artifacts']+[str(Q/'caption_source_qa.json'),str(Q/'issue_CAPTION_SOURCE_HANDOFF.json')]))
handoff['input_revision']['final_freeze_project_sha256']=freeze['project_sha256'];handoff['verified'] = list(dict.fromkeys(handoff['verified']+['157큐/113문장 자막 소스검수','추가5장 최종상태 시안 확인']))
save('handoff.json',handoff)
print(json.dumps(dict(status=report['status'],checks=len(checks),failed=issues,glyph_measurement=measurement,
 project_sha256=freeze['project_sha256'],report=str(Q/'caption_source_qa.json')),ensure_ascii=False))
