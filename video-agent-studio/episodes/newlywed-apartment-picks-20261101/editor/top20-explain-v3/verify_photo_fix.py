"""S005/S017/S022의 사진 연결 변경분만 검사·캡처합니다."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;E=H.parents[1];O=H/'evidence/photo-fix-v1'
rd=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):(O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1'}
targets={'S005':'R18','S017':'R06','S022':'R01'}
baseline=rd(O/'before/source_freeze.json');current_changes=[r['path'] for r in baseline['source_files'] if sha(H/r['path'])!=r['sha256']]
allowed={f'spec/{kind}/{sid}/index.html' for kind in ['representatives'] for sid in targets}|{f'spec/scenes/{sid}.html' for sid in targets}
assert set(current_changes)==allowed,('예상 밖 프로젝트 변경',current_changes)
old_inputs=rd(O/'before/input_manifest.json');old_caption=next(r['sha256'] for r in baseline['source_files'] if r['path']=='spec/caption_mapping.json')
assert sha(H/'spec/caption_mapping.json')==old_caption
photos={v['region_id']:v for v in rd(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets']};binds=rd(H/'photo_bindings.json')['bindings'];credits=rd(H/'credits.json');photo_rows=[]
for sid,rid in targets.items():
    p=photos[rid];b=binds[sid];body=(H/f'spec/scenes/{sid}.html').read_text(encoding='utf-8')
    assert '확정 대기' not in body and '미확인' not in body,sid+' 대기 문구 잔존'
    assert b['asset_id']==p['asset_id'] and b['sha256']==p['sha256']==sha(p['absolute_file'])==sha(H/f'spec/assets/{rid}.jpg')
    feature,price=body.split(f'<div id="{sid}-price-phase"',1)
    assert f'../assets/{rid}.jpg' in feature and f'../assets/{rid}.jpg' not in price
    assert p['actual_place'] in feature and p['license']['name'] in feature
    assert str(p['photo_capture_year']) in feature if p['photo_capture_year'] else '연도 미상' in feature
    c=next(v for v in credits if v['region_id']==rid)
    assert c['full_attribution']==p['license']['attribution_ko'] and c['license']==p['license']
    photo_rows.append({'scene_id':sid,'region_id':rid,'asset_id':p['asset_id'],'source_file':p['absolute_file'],'sha256':p['sha256'],'actual_place':p['actual_place'],'capture_year':p['photo_capture_year'],'license':p['license']['name'],'full_attribution':p['license']['attribution_ko'],'byte_preserved':True,'photo_in_price_phase':False,'pending_text':False})
t=rd(H/'timeline_resolved.json');ph={p['scene_id']:p for p in rd(H/'phase_audit.json')};times=[];shots=[]
for s in t['scenes']:
    sid=s['scene_id']
    if sid not in targets:continue
    statements=[st for st in s['sentence_times'] if st['sentence_id'] not in ph[sid]['price_sentence_ids']][1:];last=statements[-1]
    mid=s['start_s']+(last['start_s']+last['end_s'])/2
    times.extend([s['start_s']+statements[0]['start_s']+.05,mid,s['start_s']+ph[sid]['switch_s']-.04])
    shots.append({'scene_id':sid,'phase':'feature','global_s':mid})
argv=['npx.cmd','--no-install','hyperframes','check',str(H/'spec'),'--at',','.join(f'{v:.6f}' for v in times),'--json','--snapshots','--timeout','20000']
with (O/'check.json').open('wb') as out,(O/'check.stderr.log').open('wb') as err:result=subprocess.run(argv,env=env,stdout=out,stderr=err)
check=rd(O/'check.json');assert result.returncode==0 and check['ok'] and not check['browserSkipped']
snap=['npx.cmd','--no-install','hyperframes','snapshot',str(H/'spec'),'--at',','.join(f"{s['global_s']:.6f}" for s in shots),'--no-end','--describe','false','--output',str(O/'png'),'--timeout','20000']
assert not (O/'png').exists(),'기존 수정 캡처를 덮어쓰지 않습니다.'
with (O/'snapshot.log').open('wb') as out,(O/'snapshot.stderr.log').open('wb') as err:result=subprocess.run(snap,env=env,stdout=out,stderr=err)
assert result.returncode==0
files=sorted((O/'png').glob('frame*.png'));assert len(files)==3
for shot,p in zip(shots,files):
    im=Image.open(p);assert im.size==(1920,1080)
    dest=H/f"evidence/대표PNG/{shot['scene_id']}_feature.png";shutil.copy2(p,dest)
    shot.update(path=str(dest.relative_to(H)).replace('\\','/'),sha256=sha(dest),dimensions=[1920,1080])
# 수정3개 외 기존10개 PNG는 그대로 사용하며 원본 해시는 대조합니다.
old_png=rd(O/'before/evidence/png_manifest.json')['PNG'];unchanged=[]
for p in old_png:
    if p['scene_id'] in targets and p['phase']=='feature':continue
    assert sha(H/p['path'])==p['sha256'];unchanged.append(p['path'])
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20);title=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',27)
def sheet(samples,target,heading):
    columns=3;cw,ch=640,398;im=Image.new('RGB',(columns*cw,86+ch*((len(samples)+columns-1)//columns)),'#f6f4ef');d=ImageDraw.Draw(im);d.text((20,12),heading,font=title,fill='#173348');d.text((20,50),'최종v6 고정 · 무음 · 임시 타이밍 · 본편 렌더 아님',font=font,fill='#536873')
    for i,r in enumerate(samples):
        p=H/r['path'];x=(i%columns)*cw;y=86+(i//columns)*ch;im.paste(Image.open(p).resize((640,360)),(x,y));d.text((x+10,y+365),r['scene_id']+' · '+{'intro':'도입','feature':'특징·지역 자료사진','price':'가격·지도'}[r['phase']],font=font,fill='#173348')
    im.save(target)
sheet(shots,H/'evidence/contactsheet_photo_fix_v1.png','필수수정: 확정 사진3개 연결 완료')
all_samples=rd(H/'evidence/text_bounds.json')['PNG_samples']
combined=[{'path':str(Path(s['png']).relative_to(H)).replace('\\','/'),'scene_id':s['scene_id'],'phase':s['phase']} for s in all_samples]
old_sheet=H/'evidence/contactsheet_final_v6.png';shutil.copy2(old_sheet,O/'before/contactsheet_final_v6.png');sheet(combined,old_sheet,'최종v6 대표시안 · 확정 사진3개 수정 반영')
receipt={'status':'passed','related_issue_id':'QA-V3-REQ-001','scope':'S005/S017/S022 특징 단계 및 연결 이미지3개만 재검증·PNG 캡처','changed_project_files':current_changes,'caption_mapping_unchanged':True,'caption_mapping_sha256':old_caption,'other_png_files_unchanged':unchanged,'photos':photo_rows,'PNG':shots,'browser_samples':times,'layout_findings':check['layout']['totalIssueCount'],'lint_errors':check['lint']['errorCount'],'runtime_errors':check['runtime']['errorCount'],'contrast':check['contrast'],'commands':[argv,snap],'actual_listening_performed':False,'continuous_playback_performed':False,'full_render_started':False,'independent_QA':'재검수 대기; 편집자가 이슈를 직접 닫지 않음'}
save('validation.json',receipt)
print(json.dumps({'상태':'passed','새PNG':3,'배치검사표본':len(times),'배치문제':receipt['layout_findings'],'불변PNG':len(unchanged),'불변자막SHA':old_caption,'결과':str(O/'validation.json')},ensure_ascii=False))
