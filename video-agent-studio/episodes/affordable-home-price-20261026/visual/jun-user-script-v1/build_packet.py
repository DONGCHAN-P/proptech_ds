from pathlib import Path
import hashlib, json, shutil, subprocess
from datetime import datetime, timezone
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = Path('C:/projects/realestate_reco')
EP = ROOT / 'video-agent-studio/episodes/affordable-home-price-20261026'
HERE = Path(__file__).resolve().parent
OUT = HERE / 'outputs'
OUT.mkdir(exist_ok=True)
ORIG = OUT / 'originals'
ORIG.mkdir(exist_ok=True)
CHECK = HERE / 'review'
CHECK.mkdir(exist_ok=True)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p, obj): Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):
    p = Path(p)
    try: return p.relative_to(ROOT).as_posix()
    except ValueError: return p.as_posix()
def record(p): return {'path':rel(p), 'sha256':sha(p), 'bytes':Path(p).stat().st_size}
calls = {x['id']:x for x in read(HERE/'generation_log.json')['calls']}
planpath = EP/'director/user-recording-v1/scene_plan.json'
plan = read(planpath)
assert len(plan['scenes']) == 31
assert sorted(set(x['chapter'] for x in plan['scenes'])) == list(range(1,8))
chapters = [
    (1,'S01','돈을 모은 다음의 질문','ch1Clean',EP/'visual/hero-budget-v1.png',EP/'visual/hero-budget-v1.json','열쇠·구매 준비 책상으로 현금과 집값 사이의 질문을 연다.'),
    (2,'S04','집값 밖의 비용','ch2Clean',EP/'visual/rebuild-v2/transaction-costs.png',EP/'visual/rebuild-v2/manifest.json','계약 종이·영수증 형태와 열쇠로 거래비용·준비금을 연다.'),
    (3,'S08','대출의 기준',None,EP/'visual/rebuild-v2/bank-limits.png',EP/'visual/rebuild-v2/manifest.json','은행과 주택의 모형으로 은행 심사와 담보 관계를 연다.'),
    (4,'S13','현금 1억과 2억','ch4',None,None,'같은 크기의 두 집·두 저축 수첩으로 공통 조건의 현금 사례 비교를 연다.'),
    (5,'S18','현금 3억부터 5억',None,ROOT/'video-agent-studio/assets/chapter-backgrounds/v1/price.png',ROOT/'video-agent-studio/assets/chapter-backgrounds/v1/manifest.json','주택 모형·열쇠로 한도 안에서 정할 매수 가격대를 연다.'),
    (6,'S22','지역과 월 상환','ch6',None,None,'장보기·가계 수첩·빈 달력으로 월 원리금 이후 남는 생활비를 연다.'),
    (7,'S27','내 예산 정리',None,ROOT/'video-agent-studio/assets/chapter-backgrounds/v1/comparison.png',ROOT/'video-agent-studio/assets/chapter-backgrounds/v1/manifest.json','서로 다른 주거 동네의 분위기로 자기 예산에 맞는 생활·입지 선택을 연다. S28 작성지는 별도 노트 조각과 편집 레이어 사용.'),
]
assets=[]
for num, scene, title, key, reuse, ledger, purpose in chapters:
    src = Path(calls[key]['actual_source_file']) if key else reuse
    assert src.is_file(), src
    original = ORIG / f'{scene}_CH{num:02d}_source.png'
    shutil.copy2(src, original)
    im = Image.open(src).convert('RGB')
    filename = f'{scene}_CH{num:02d}_AI_1920x1080.png'
    dest = OUT/filename
    scaled = ImageOps.fit(im, (1920,1080), method=Image.Resampling.LANCZOS, centering=(.5,.5))
    scaled.save(dest)
    with Image.open(dest) as verify:
        verify.load()
        assert verify.size == (1920,1080)
    a = {
      'asset_id':f'JUS1_CH{num:02d}', 'chapter':num, 'title_overlay':title,
      'scene_ids':[s['scene_id'] for s in plan['scenes'] if s['chapter']==num],
      'chapter_insert_before_scene':scene, 'type':'ai_concept', 'media_kind':'chapter_still',
      'purpose':purpose, 'actual_file':rel(dest), 'absolute_file':dest.as_posix(),
      'dimensions':[1920,1080], 'sha256':sha(dest), 'bytes':dest.stat().st_size,
      'source_or_prompt':calls[key]['prompt'] if key else {'source_file':rel(reuse),'source_ledger':rel(ledger)},
      'provenance':{'mode':'reused_cleaned' if key and 'Clean' in key else ('new_builtin_image' if key else 'reused_existing'),
        'tool':'built-in image_gen' if key else 'existing built-in image_gen asset',
        'source_file':src.as_posix(), 'source_sha256':sha(src), 'source_dimensions':list(im.size),
        'original_workspace_file':rel(original),
        'existing_source':record(reuse) if reuse else None,
        'existing_ledger':record(ledger) if ledger else None,
        'transform':'Pillow LANCZOS fit to 1920x1080; centered aspect trim below one source pixel',
        'upscaled':im.width<1920 or im.height<1080, 'scale_factor':max(1920/im.width,1080/im.height)},
      'actual_place':None, 'actual_location':False, 'AI_label':'ai_concept', 'screenbadge':False,'screen_AI_badge':False,
      'usage_conditions':'이번 편과 재사용 가능한 개념 분위기 자료. 실제 단지·지리·면적·가격·승인·정책·공식 문서의 증거로 사용하지 않음. 제목·금액은 별도 편집 레이어.',
      'title_safe_box_1920':[96,250,820,700], 'title_color':'#173348' if num in (1,4,6) else '#FFFFFF',
      'title_max_lines':2, 'motion':'static preferred; if zoomed clip, classify as still_motion',
      'review_status':'pending_final_size_contact_review',
    }
    if num == 1: a['framing_note']='원래 화면 오른쪽 계산기 일부가 프레임 밖에 있음. 원본 구도를 계승한 의도된 소품 재단이며 열쇠·집 펜던트·제목 공간은 보존. 추가 확대 금지.'
    if num == 7: a['framing_note']='서울을 연상시키는 가상 스카이라인. 실제 서울·특정 단지 이름을 붙이지 않으며 예산/입지 선택의 분위기로만 사용.'
    assets.append(a)

optional=[]
for key, scene, name, ids, purpose in [
    ('houseCutout','S02','house_cutout',['S02','S08','S13','S14','S15','S17','S20','S30'],'동일 주택 표식. 가격이 달라도 같은 크기·형태로 재사용하며 가격·평형 차이의 증거로 사용하지 않는다.'),
    ('notebookCutout','S28','blank_budget_notebook',['S28','S31'],'빈 예산 작성지 보조. 세 숫자의 칸·라벨은 편집자가 별도 레이어로 추가한다.')]:
    src=Path(calls[key]['actual_source_file'])
    dest=OUT/f'{scene}_{name}_AI.png'
    shutil.copy2(src,dest)
    im=Image.open(dest)
    im.load()
    alpha=im.getchannel('A') if 'A' in im.getbands() else None
    histogram=alpha.histogram() if alpha else []
    total=im.width*im.height
    alpha_info={'extrema':list(alpha.getextrema()) if alpha else None,
        'fully_transparent_fraction':histogram[0]/total if histogram else 0,
        'near_opaque_fraction':sum(histogram[245:])/total if histogram else 0,
        'visible_bbox':list(alpha.getbbox()) if alpha and alpha.getbbox() else None}
    optional.append({'asset_id':'JUS1_'+name.upper(),'scene_ids':ids,'type':'ai_concept','media_kind':'optional_cutout',
      'actual_file':rel(dest),'absolute_file':dest.as_posix(),'sha256':sha(dest),'dimensions':list(im.size),'mode':im.mode,
      'source_or_prompt':calls[key]['prompt'],'purpose':purpose,'actual_place':None,'actual_location':False,'AI_label':'ai_concept',
      'screenbadge':False,'screen_AI_badge':False,'upscaled':False,'alpha':alpha_info,
      'provenance':{'source_file':src.as_posix(),'source_sha256':sha(src),'tool':'built-in image_gen','mode':'new_transparent_asset'},
      'usage_conditions':'선택 에셋. 실제 주택·평형·공식 서류 근거 아님. 알파 합성 검수 후 채택 여부 기록.',
      'review_status':'pending_alpha_composite_review'})

inputs=[ROOT/'video-agent-studio/WORKFLOW.md',ROOT/'video-agent-studio/agents/video_director.toml',
    ROOT/'video-agent-studio/guides/영상제작_마스터가이드.md',ROOT/'video-agent-studio/guides/호출_효율_운영.md',
    ROOT/'config/video_call_policy.json',ROOT/'video-agent-studio/templates/episode_preflight.json',
    ROOT/'영상/매매가격계산/영상가이드_직접녹음_v1.md',EP/'brief.json',EP/'state.json',planpath,
    EP/'director/jun-user-script-v1/episode_preflight.json',EP/'director/jun-user-script-v1/PLAN.md',
    EP/'director/jun-user-script-v1/authorization.json',EP/'director/jun-user-script-v1/input_verification.json']
brief={'task_id':'FULL-JUN-US1-ASSETS','scope':'visual/jun-user-script-v1/ only',
    'revision':'jun-user-script-v1','source_doc_sha256':plan['source_sha256'],'scene_plan_revision':plan.get('design_revision'),
    'latest_user_requirements':{'chapters':7,'scenes':31,'style':'natural warm ivory / navy / oak photographic or believable house interior',
      'no_people':True,'no_stickmen':True,'no_generated_text_numbers_logos':True,'titles_separate':True,
      'screenbadge':False,'distinct_complete_photo_per_chapter':True,'requested_resolution':[1920,1080],
      'margin':'low-detail left 42% title area; source framing preserved; no extra zoom',
      'no_paid_external_API_or_account_data':True},
    'ownership':{'parent':'TTS/alignment','editor':'Newton 01a17db2-40c1-7f73-a24b-236c89fd9d92','self':'visual/jun-user-script-v1/'},
    'superseded_inputs':'brief.json historical 10chapter policy sequence is not this 7chapter user DOCX; Jun choice and 7000credit approval belong to parent, not visual spend authority.',
    'excluded_assets':['visual/rebuild-v2/family-policy.png','visual/newborn-home-v1.png'],
    'preflight_applied':{'input_contract':True,'different_image_per_chapter':True,'unvoiced_brand_captions_hidden':'editor responsibility',
       'body_caption_and_source_safe_areas':'editor responsibility','last_spoken_word_plus_3s':'editor responsibility',
       'actual_property_or_map':'not applicable: concept atmosphere only','audio_generation':'out of scope'},
    'input_versions':[record(p) for p in inputs]}
save(HERE/'production_brief.json',brief)

ledger={'schema_version':'1.0','task_id':'FULL-JUN-US1-ASSETS','revision':'jun-user-script-v1-assets-v1',
    'scene_plan':record(planpath),'source_doc_sha256':plan['source_sha256'],'screenbadge':False,
    'timing_locked_by_visual':False,'timing_note':'scene IDs fixed; no timestamp prefixes assigned',
    'assets':assets,'optional_assets':optional,'chapter_count':len(assets),
    'generation':{'built_in_calls':len(calls),'new_scene_photos':2,'clean_reuse_edits':2,'optional_transparent_requests':2,
       'external_paid_API_calls':0,'API_keys_used':False,'audio_generated_or_changed':False},
    'cutout_search':{'searched':'assets/, video/public/, shared chapter-backgrounds/, housing-choice visual/, regional-price visual/',
       'result':'No previously verified text-free photographic house/checklist cutout found in the searched inventories. Unrelated emoji, site maps and the apartment-stages SVG were not substituted for photographic assets.'}}
save(HERE/'assets.json',ledger)

media=read(EP/'director/production-v1/media_assets.json')
refs=[]
probe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
for a in media['assets']:
    p=ROOT/a['path']
    info=record(p)
    info.update(asset_id=a['asset_id'],expected_sha256=a['sha256'],matches_existing_approved_hash=sha(p)==a['sha256'],
      license=a['license'],approval_evidence=rel(EP/'director/production-v1/media_assets.json'),
      review_scope='read-only path/hash/probe and existing approval ledger; not newly listened or continuously played')
    assert info['matches_existing_approved_hash']
    result=subprocess.run([str(probe),'-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate,channels','-of','json',str(p)],capture_output=True,text=True,check=True)
    info['probe']=json.loads(result.stdout)
    refs.append(info)
music_license=ROOT/'assets/music/thinking_music.license.json'
save(HERE/'brand_audio_refs.json',{'scope':'read-only identification; no audio changes',
    'assets':refs,'license_reference':record(music_license),'existing_music_credit':read(music_license)['credit'],
    'placement_notes':{'intro':'P008 / S02 question after actual pause; existing 5-second clean intro',
      'outro':'after final actual spoken word +3seconds, including audio tail silence; existing 10-second clean outro',
      'captions':'hide rail only on unvoiced brands and silent CTA hold',
      'audio':'editor to retain licensed BGM, avoid doubling brand embedded soundtrack; listening and mix QA remain unperformed by visual'},
    'new_voice':False,'actual_listening':False,'continuous_playback':False})

fontpath=Path('C:/Windows/Fonts/malgunbd.ttf')
font=ImageFont.truetype(str(fontpath),38)
small=ImageFont.truetype(str(fontpath),22)
def overlay_preview(a):
    im=Image.open(ROOT/a['actual_file']).convert('RGB')
    d=ImageDraw.Draw(im)
    title_font=ImageFont.truetype(str(fontpath),60)
    title=a['title_overlay']
    lines={1:['돈을 모은','다음의 질문'],2:['집값 밖의 비용'],3:['대출의 기준'],4:['현금 1억과 2억'],5:['현금 3억부터 5억'],6:['지역과 월 상환'],7:['내 예산 정리']}[a['chapter']]
    text_color=a['title_color']
    for i,line in enumerate(lines): d.text((110,385+i*83),line,font=title_font,fill=text_color)
    d.text((110,300),f"CH {a['chapter']:02d}",font=font,fill=text_color)
    return im
sheet=Image.new('RGB',(1280,4*410),'#F6F4EF')
d=ImageDraw.Draw(sheet)
for i,a in enumerate(assets):
    im=overlay_preview(a)
    if a['chapter'] in (1,6): im.save(CHECK/f"representative_CH{a['chapter']:02d}_title_proof.png")
    thumb=im.resize((640,360),Image.Resampling.LANCZOS)
    x,y=(i%2)*640,(i//2)*410
    sheet.paste(thumb,(x,y))
    d.text((x+12,y+366),a['asset_id']+' '+a['chapter_insert_before_scene'],font=small,fill='#173348')
sheet.save(CHECK/'chapter_contact.png')
cutout_sheet=Image.new('RGB',(1280,800),'#F6F4EF')
d=ImageDraw.Draw(cutout_sheet)
for i,a in enumerate(optional):
    im=Image.open(ROOT/a['actual_file']).convert('RGBA')
    im.thumbnail((560,310),Image.Resampling.LANCZOS)
    for row,bg in enumerate(('#F6F4EF','#173348')):
        cell=Image.new('RGBA',(640,400),bg)
        cell.alpha_composite(im,((640-im.width)//2,60))
        cutout_sheet.paste(cell.convert('RGB'),(640*i,400*row))
        d.text((640*i+15,400*row+15),a['asset_id'],font=small,fill='#173348' if row==0 else '#FFFFFF')
cutout_sheet.save(CHECK/'cutout_alpha_contact.png')
print(json.dumps({'status':'files_created_pending_visual_review','chapters':len(assets),'optional':len(optional),
    'alpha':[{'id':a['asset_id'],**a['alpha']} for a in optional],
    'contact':rel(CHECK/'chapter_contact.png'),'cutout_contact':rel(CHECK/'cutout_alpha_contact.png')},ensure_ascii=False))
