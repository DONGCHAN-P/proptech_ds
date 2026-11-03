import json,sys,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_ui as u
import measure as m
m.b=u.b
H=u.H
def main():
    index=[]
    with sync_playwright()as pw:
        browser=pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',args=['--allow-file-access-from-files'])
        for sid in u.IDS:
            p=H/sid;lock=u.b.read(u.D/'shorts'/sid/'locked_timing.json');sb=u.b.read(p/'storyboard.json');aa=u.b.read(p/'price_anchor_audit.json')
            src=m.flatten(p);page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
            page.goto(src.as_uri(),wait_until='load');page.evaluate('document.fonts.ready');page.wait_for_function('Object.keys(window.__timelines).length>2')
            region=next(s for s in sb['scenes']if s['kind']=='region')
            firstaa=[a['target_s']for a in aa if a['scene_id']==region['scene_id']]
            longest=max(lock['captions'],key=lambda c:len(c['text']))
            selections=[('first_frame',0),('intro',1.5),('region_arrival',region['start_s']+1.2),('price_complete',max(firstaa)+.6),('long_caption',(longest['start_s']+longest['end_s'])/2),('outro',lock['total_s']-1.6)]
            (p/'source_proofs').mkdir(exist_ok=True)
            for label,t in selections:
                page.evaluate('(t)=>qaSeek(t)',t);dest=p/'source_proofs'/f'{label}.png';page.screenshot(path=str(dest))
                index.append(dict(short_id=sid,kind=label,time_s=t,path=str(dest),sha256=u.b.sha(dest),scope='source DOM; not decoded MP4'))
            # Every caption and each reveal boundary. All critical glyphs, not only containers.
            times={0,1.5,lock['total_s']-.02}
            for c in lock['captions']:times.update([c['start_s']+.001,c['end_s']-.001,(c['start_s']+c['end_s'])/2])
            for a in aa:times.update([a['target_s']-.001,a['target_s']+.001,a['target_s']+.175,a['target_s']+.4])
            for s in sb['scenes']:times.update([s['start_s']+.001,s['start_s']+.36,s['end_s']-.001])
            elements=[];overlaps=[];out=[]
            for t in sorted(times):
                page.evaluate('(t)=>qaSeek(t)',t);rows=page.evaluate(m.MEASURE)
                for r in rows:
                    r['time_s']=t;elements.append(r);x=r['bbox']
                    if x[0]<140 or x[1]<260 or x[2]>840 or x[3]>1360:out.append(r)
                for i,x in enumerate(rows):
                    for y in rows[i+1:]:
                        a,c=x['bbox'],y['bbox']
                        if min(a[2],c[2])-max(a[0],c[0])>1 and min(a[3],c[3])-max(a[1],c[1])>1:overlaps.append(dict(t=t,a=x['id'],b=y['id']))
            u.save(p/'glyph_bounds.json',dict(profile='youtube_portrait_full_frame_v2',safe_rect=[140,260,840,1360],sample_count=len(times),elements=elements,overlaps=overlaps))
            u.save(p/'source_measurement_receipt.json',dict(passed=not out and not overlaps,out_of_bounds_count=len(out),overlap_count=len(overlaps),samples=len(times),elements=len(elements),out_of_bounds=out[:15],overlaps=overlaps[:15],scope='all critical text glyphs at caption, scene, native value boundaries',actual_listening=False,continuous_playback=False))
            checks=[]
            for i,a in enumerate(aa):
                cid=next(s['composition_id']for s in sb['scenes']if s['scene_id']==a['scene_id']);states=[]
                for off in [-.001,0,.175,.35,.6]:
                    page.evaluate('(t)=>qaSeek(t)',a['target_s']+off)
                    state=page.locator(f'#{cid}-row{a["row"]}').evaluate('(e)=>({opacity:+getComputedStyle(e).opacity,barWidth:e.querySelector(".bar").getBoundingClientRect().width,trackWidth:e.querySelector(".bar-track").getBoundingClientRect().width})')
                    states.append(dict(offset_s=off,**state))
                expected=674*a['bar_fraction'];checks.append(dict(**a,expected_bar_px=expected,states=states,passed=states[0]['opacity']==0 and states[1]['opacity']==1 and abs(states[1]['barWidth'])<.1 and abs(states[3]['barWidth']-expected)<.15 and abs(states[4]['barWidth']-expected)<.15))
            u.save(p/'price_boundary_checks.json',dict(passed=all(c['passed']for c in checks),checks=checks))
            captimes={0,lock['total_s']-.02}
            for c in lock['captions']:captimes.update([max(0,c['start_s']-.001),c['start_s']+.001,c['end_s']-.001,min(lock['total_s']-.001,c['end_s']+.001)])
            capchecks=[]
            for t in sorted(captimes):
                page.evaluate('(t)=>qaSeek(t)',t)
                expected=[c['text']for c in lock['captions']if c['start_s']<=t<c['end_s']]
                actual=page.evaluate('''() => Array.from(document.querySelectorAll('.caption-group')).filter(e=>getComputedStyle(e).display!=='none').map(e=>e.querySelector('.caption').textContent)''')
                same=[re.sub(r'\s','',x)for x in expected]==[re.sub(r'\s','',x)for x in actual]
                capchecks.append(dict(time_s=t,expected=expected,actual=actual,passed=same and len(actual)<=1))
            u.save(p/'caption_visibility_boundary_checks.json',dict(passed=all(x['passed']for x in capchecks),font_px=54,rail_shares_exact_cue_parent=True,single_caption_track=True,checks=capchecks))
            # Stress fixture is QA-only and never written into delivery source or claimed as data.
            page.evaluate('(t)=>qaSeek(t)',max(firstaa)+.6)
            cid=region['composition_id']
            page.locator(f'#{cid}-label0').evaluate('(e)=>e.textContent="2000년까지 준공"')
            page.locator(f'#{cid}-sample0').evaluate('(e)=>e.textContent="거래 1,652건 · 15단지"')
            fixture=[x for x in page.evaluate(m.MEASURE)if x['id']in [f'{cid}-label0',f'{cid}-sample0']]
            u.save(p/'long_label_sample_stress.json',dict(scope='QA-only text stress fixture; not real source values; delivery HTML unmodified',glyphs=fixture,passed=len(fixture)==2 and fixture[0]['bbox'][2]<fixture[1]['bbox'][0] and fixture[1]['bbox'][2]<=840))
            print(sid,'bounds',len(out),'overlaps',len(overlaps),flush=True)
            page.close()
        browser.close()
    u.save(H/'representative_proofs.json',index)
    # Full-frame native source captures, with separate UI mock copies.
    for x in index:
        im=Image.open(x['path']).convert('RGB');draw=ImageDraw.Draw(im,'RGBA')
        draw.rectangle([0,0,1080,225],fill=(20,46,66,140));draw.rectangle([872,500,1080,1500],fill=(20,46,66,135));draw.rectangle([0,1410,1080,1920],fill=(20,46,66,150))
        font=ImageFont.truetype(str(H/u.IDS[0]/'assets/Pretendard-Regular.ttf'),30)
        draw.text((32,60),'YouTube UI 모사 · 상단',font=font,fill='white');draw.text((890,780),'좋아요\n\n댓글\n\n공유',font=font,fill='white');draw.text((32,1480),'채널 · 설명 · 관련 영상 · 탐색 UI 모사',font=font,fill='white')
        im.save(str(Path(x['path']).with_name(Path(x['path']).stem+'_ui_mock.jpg')))
    W=6*270;board=Image.new('RGB',(W,3*526),(246,244,239));draw=ImageDraw.Draw(board);font=ImageFont.truetype(str(H/u.IDS[0]/'assets/Pretendard-Regular.ttf'),17)
    for i,x in enumerate(index):
        xx=(i%6)*270;yy=(i//6)*526;im=Image.open(x['path']).convert('RGB').resize((270,480));board.paste(im,(xx,yy));draw.text((xx+5,yy+482),f'{x["short_id"]}\n{x["kind"]} {x["time_s"]:.2f}s',font=font,fill=(20,46,66))
    board.save(H/'representative_contactboard.jpg',quality=94)
    u.save(H/'handoff.json',dict(status='representative_visuals_ready_full_render_held',contactboard=str(H/'representative_contactboard.jpg'),proof_manifest=str(H/'representative_proofs.json'),projects=[str(H/s)for s in u.IDS],input_version='director/shorts-ui-v2-20261104 actual new locks',next='parent+independent QA representative comparison; full render only after visual QA pass',paid_calls=0,actual_listening=False,continuous_playback=False))
if __name__=='__main__':main()
