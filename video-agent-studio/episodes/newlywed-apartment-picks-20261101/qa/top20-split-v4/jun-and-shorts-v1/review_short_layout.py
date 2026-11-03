"""독립 QA: 원본 프로젝트를 수정하지 않는 로컬 글리프/가격 앵커 검사."""
import hashlib
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[6]
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
Q = Path(__file__).resolve().parent
H = EP / 'editor/top20-split-v4/jun-and-shorts-v1/shorts/native-v1'
D = EP / 'director/top20-split-v4/part1-jun-and-shorts-v1'
IDS = ['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11']


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def flatten(project, target):
    html = (project / 'index.html').read_text(encoding='utf-8-sig')
    def sub(m):
        tag = m.group(0)
        path = re.search(r'data-composition-src="([^"]+)"', tag)[1]
        content = (project / path).read_text(encoding='utf-8-sig')
        return tag[:-6] + re.search(r'<template>(.*?)</template>', content, re.S)[1] + '</div>'
    html = re.sub(r'<div\b[^>]*data-composition-src="[^"]+"[^>]*></div>', sub, html)
    html = html.replace('<head>', f'<head><base href="{project.as_uri()}/"><script>window.__timelines={{}};</script>', 1)
    html = re.sub(r'<audio\b.*?</audio>', '', html, flags=re.S)
    script = '''<script>window.independentSeek=(t)=>{
      for(const host of document.querySelectorAll('[data-composition-src]')){
        const local=t-(+host.dataset.start),duration=+host.dataset.duration;
        host.style.display=(local>=0&&local<duration)?'block':'none';
        const tl=window.__timelines[host.dataset.compositionId];
        if(tl)tl.pause().time(Math.max(0,local),false);
        for(const el of host.querySelectorAll('.clip[data-start]')){
          const start=+el.dataset.start,end=start+(+el.dataset.duration);
          el.style.display=(local>=start&&local<end)?'flex':'none';
        }
      }
    };</script>'''
    target.write_text(html.replace('</body>', script + '</body>'), encoding='utf-8')


MEASURE = r'''() => {
  function visible(e){for(let p=e;p;p=p.parentElement){let s=getComputedStyle(p);
    if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)<.01)return false;}return true;}
  const c=document.createElement('canvas'),ctx=c.getContext('2d'),rows=[];
  for(const e of document.querySelectorAll('[data-critical]')){
    if(!visible(e))continue;
    let s=getComputedStyle(e),range=document.createRange();range.selectNodeContents(e);
    const rects=Array.from(range.getClientRects()).filter(r=>r.width&&r.height).map(r=>[r.left,r.top,r.right,r.bottom]);
    ctx.font=`${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
    let ink=null,node,walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
    while(node=walker.nextNode())for(let i=0;i<node.textContent.length;i++){
      let ch=node.textContent[i];if(!ch.trim())continue;
      let cr=document.createRange();cr.setStart(node,i);cr.setEnd(node,i+1);
      let b=cr.getBoundingClientRect(),m=ctx.measureText(ch),base=b.bottom-m.fontBoundingBoxDescent;
      let a=[b.left-m.actualBoundingBoxLeft,base-m.actualBoundingBoxAscent,b.left+m.actualBoundingBoxRight,base+m.actualBoundingBoxDescent];
      ink=ink?[Math.min(ink[0],a[0]),Math.min(ink[1],a[1]),Math.max(ink[2],a[2]),Math.max(ink[3],a[3])]:a;
    }
    if(!ink)continue;
    const classes=Array.from(e.classList);
    let min=26;
    if(classes.some(x=>['scope','region','promo-title','promo-units','takeaway','cta-primary'].includes(x)))min=56;
    if(classes.some(x=>['price-value','couples','promo-number','promo-hero-word'].includes(x)))min=52;
    if(classes.includes('caption'))min=54;
    rows.push({id:e.id,text:e.textContent,kind:e.dataset.critical,classes,font_px:parseFloat(s.fontSize),minimum_font_px:min,
      font_family:s.fontFamily,font_loaded:document.fonts.check(`${s.fontWeight} ${s.fontSize} Pretendard`),glyph_bbox:ink,range_rects:rects});
  }
  let rail=document.querySelector('.caption-rail');
  return {rows,rail_visible:!!rail&&visible(rail),visible_captions:rows.filter(r=>r.classes.includes('caption')).length,
    visible_ledger_rows:Array.from(document.querySelectorAll('.ledger-row')).filter(visible).length};
}'''


def main():
    outdir = Q / 'source_layout'
    outdir.mkdir(exist_ok=True)
    reports = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True, args=['--allow-file-access-from-files'])
        for sid in IDS:
            project = H / sid
            lock = read(D / 'shorts' / sid / 'locked_timing.json')
            anchors = read(project / 'price_anchor_audit.json')
            story = read(project / 'storyboard.json')['scenes']
            target = outdir / f'{sid}.html'
            flatten(project, target)
            page = browser.new_page(viewport={'width':1080, 'height':1920}, device_scale_factor=1)
            page.route(re.compile(r'^https?://'), lambda route: route.abort())
            page.goto(target.as_uri(), wait_until='load')
            page.evaluate('document.fonts.ready')
            page.wait_for_function('Object.keys(window.__timelines).length>2')
            times = {0.1, lock['total_s']-.1, lock['sentences'][-1]['end_s']+.8}
            times.update((c['start_s']+c['end_s'])/2 for c in lock['captions'])
            for scene in story:
                times.update([scene['start_s']+.01, scene['end_s']-.01])
            for anchor in anchors:
                times.update([anchor['target_s']-.001, anchor['target_s']+.001, anchor['target_s']+.4])
            rows, issues, empty_holds, boundary_checks, ledger = [], [], [], [], []
            for t in sorted(times):
                if not 0 <= t < lock['total_s']: continue
                page.evaluate('(t)=>independentSeek(t)', t)
                measured = page.evaluate(MEASURE)
                for row in measured['rows']:
                    row['time_s'] = t
                    rows.append(row)
                    b=row['glyph_bbox']
                    if b[0]<140-.1 or b[1]<260-.1 or b[2]>840+.1 or b[3]>1360+.1:
                        issues.append({'type':'glyph_overflow', **row})
                    if not row['font_loaded'] or row['font_px'] < row['minimum_font_px']:
                        issues.append({'type':'font_failure', **row})
                for i, a in enumerate(measured['rows']):
                    for b in measured['rows'][i+1:]:
                        x,y=a['glyph_bbox'],b['glyph_bbox']
                        if min(x[2],y[2])-max(x[0],y[0])>1 and min(x[3],y[3])-max(x[1],y[1])>1:
                            issues.append({'type':'glyph_collision','time_s':t,'a':a['id'],'b':b['id']})
                if measured['rail_visible'] and not measured['visible_captions'] and (t < lock['sentences'][0]['start_s'] or t > lock['sentences'][-1]['end_s']):
                    empty_holds.append({'time_s':t,'rail_visible':True,'visible_captions':0})
                ledger.append({'time_s':t,'visible_rows':measured['visible_ledger_rows']})
            for anchor in anchors:
                sentence=next(s for s in lock['sentences'] if s['sentence_id']==anchor['sentence_id'])
                native=sentence['display_character_timing']['chunk_local_start_times_seconds'][anchor['display_char_start']]
                expected=sentence['start_s'] + native-sentence['chunk_local_start_s']
                composition=next(s['composition_id'] for s in story if s['scene_id']==anchor['scene_id'])
                selector=f'#{composition}-value{anchor["row"]}'
                values=[]
                for t in [expected-.001, expected+.001, expected+.4]:
                    page.evaluate('(t)=>independentSeek(t)',t)
                    values.append(page.locator(selector).evaluate('(e)=>({text:e.textContent,opacity:Number(getComputedStyle(e).opacity)})'))
                boundary_checks.append({'sentence_id':anchor['sentence_id'],'token':anchor['token'],'expected_native_start_s':expected,'declared_target_s':anchor['target_s'],
                    'states':values,'passed':abs(expected-anchor['target_s'])<1e-7 and values[0]['opacity']==0 and values[1]['opacity']==1 and values[2]['opacity']==1})
            source_files=[project/'index.html', project/'style.css', *sorted((project/'compositions').glob('*.html'))]
            report={'short_id':sid,'source_version':'native-v1','source_sha256':{str(p):sha(p) for p in source_files},
                'lock_sha256':sha(D/'shorts'/sid/'locked_timing.json'),'profile':'youtube_portrait_full_frame_v2','safe_rect':[140,260,840,1360],
                'method':'independent local flattened source; DOM character Range plus Canvas actual ink metrics; real shipped CSS/fonts; HTTP blocked; not encoded-media evidence',
                'sample_times_s':sorted(times),'measured_element_count':len(rows),'glyph_rows':rows,'layout_issues':issues,'price_boundary_checks':boundary_checks,
                'ledger_rows':ledger,'empty_caption_rail_outside_speech':empty_holds,'layout_passed':not issues and all(x['passed'] for x in boundary_checks),
                'actual_listening':False,'actual_hearing':False,'continuous_playback':False}
            save(outdir/f'{sid}_review.json',report)
            reports.append({k:v for k,v in report.items() if k not in ['glyph_rows','source_sha256','ledger_rows','sample_times_s']})
            page.close()
        browser.close()
    summary={'status':'source_layout_checked_pending_encoded_media','shorts':reports,'actual_listening':False,'actual_hearing':False,'continuous_playback':False}
    save(Q/'shorts_layout_review.json',summary)
    print(json.dumps({r['short_id']:{'layout_passed':r['layout_passed'],'elements':r['measured_element_count'],'issues':len(r['layout_issues']),'empty_rail_holds':r['empty_caption_rail_outside_speech']} for r in reports},ensure_ascii=False))


if __name__=='__main__':
    main()
