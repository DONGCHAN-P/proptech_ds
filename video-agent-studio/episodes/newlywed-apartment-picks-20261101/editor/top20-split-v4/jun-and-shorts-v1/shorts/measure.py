"""Measure source text at every caption and price boundary, independently of HF audits.

The flattened HTML is QA-only: delivery is rendered from index.html by HyperFrames.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as b


MEASURE = r"""() => {
 const result=[];const canvas=document.createElement('canvas');const ctx=canvas.getContext('2d');
 for(const e of document.querySelectorAll('[data-critical]')){
  let vis=true;for(let a=e;a;a=a.parentElement){const s=getComputedStyle(a);if(s.display==='none'||s.visibility==='hidden'||parseFloat(s.opacity)<.01){vis=false;break}}
  if(!vis)continue;const s=getComputedStyle(e);ctx.font=`${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
  const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let node,bb=null;
  while(node=walker.nextNode())for(let i=0;i<node.textContent.length;i++){
   const char=node.textContent[i];if(!char.trim())continue;let r=document.createRange();r.setStart(node,i);r.setEnd(node,i+1);
   const rect=r.getBoundingClientRect();const m=ctx.measureText(char);
   const baseline=rect.bottom-m.fontBoundingBoxDescent;
   const box=[rect.left-m.actualBoundingBoxLeft,baseline-m.actualBoundingBoxAscent,rect.left+m.actualBoundingBoxRight,baseline+m.actualBoundingBoxDescent];
   bb=bb?[Math.min(bb[0],box[0]),Math.min(bb[1],box[1]),Math.max(bb[2],box[2]),Math.max(bb[3],box[3])]:box;
  }
  if(bb)result.push({id:e.id,kind:e.dataset.critical,text:e.textContent,font_px:parseFloat(s.fontSize),bbox:bb,container:[e.getBoundingClientRect().left,e.getBoundingClientRect().top,e.getBoundingClientRect().right,e.getBoundingClientRect().bottom]});
 }return result;
}"""


def flatten(project):
    text = (project/'index.html').read_text(encoding='utf-8')
    def sub(m):
        tag = m.group(0)
        file = re.search(r'data-composition-src="([^"]+)"', tag).group(1)
        inner = (project/file).read_text(encoding='utf-8')
        payload = re.search(r'<template>(.*)</template>', inner, re.S).group(1)
        return tag[:-6] + payload + '</div>'
    text = re.sub(r'<div\b[^>]*data-composition-src="[^"]+"[^>]*></div>', sub, text)
    text = text.replace('<script src=', '<script>window.__timelines={};</script><script src=', 1)
    text = re.sub(r'<audio\b.*?</audio>', '', text, flags=re.S)
    js = r"""<script>
window.qaSeek=(t)=>{
 for(const host of document.querySelectorAll('[data-composition-src]')){
  const a=+host.dataset.start,d=+host.dataset.duration,local=t-a;
  host.style.display=t>=a&&t<a+d?'block':'none';
  const tl=window.__timelines[host.dataset.compositionId];if(tl)tl.pause().time(Math.max(0,local),false);
  for(const clip of host.querySelectorAll('.clip[data-start]')){
   const c=+clip.dataset.start,cd=+clip.dataset.duration;
   clip.style.display=local>=c&&local<c+cd?'flex':'none';
  }
 }
};
</script>"""
    text = text.replace('</body>',js+'</body>')
    text = text.replace('<head>', f'<head><base href="{project.as_uri()}/">',1)
    dest = project/'measurement/qa_flattened.html'
    b.write(dest,text)
    return dest


def measure(project, browser):
    manifest=b.read(project/'input_manifest.json')
    lock=b.read(b.D/'shorts'/manifest['short_id']/'locked_timing.json')
    anchors=b.read(project/'price_anchor_audit.json')
    source=flatten(project)
    page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
    page.goto(source.as_uri(),wait_until='load')
    page.evaluate('document.fonts.ready')
    page.wait_for_function('Object.keys(window.__timelines).length>2')
    times={0.1, lock['total_s']-.1}
    for c in lock['captions']:
        times.add((c['start_s']+c['end_s'])/2)
    for a in anchors:
        times.update([a['target_s']-.001,a['target_s']+.001,a['target_s']+.45])
    elements=[];overlaps=[]
    for t in sorted(times):
        page.evaluate('(t)=>qaSeek(t)',t)
        rows=page.evaluate(MEASURE)
        for r in rows:r['time_s']=t
        elements.extend(rows)
        for i,x in enumerate(rows):
            for y in rows[i+1:]:
                a,c=x['bbox'],y['bbox']
                if min(a[2],c[2])-max(a[0],c[0])>1 and min(a[3],c[3])-max(a[1],c[1])>1:
                    overlaps.append({'time_s':t,'a':x['id'],'b':y['id'],'bbox_a':a,'bbox_b':c})
    bounds={'profile':'youtube_portrait_full_frame_v2','safe_rect':[140,260,840,1360],
            'measurement':'Chromium DOM character Range boxes plus Canvas actual glyph metrics; shipped local Pretendard; native 1080x1920 viewport',
            'sample_count':len(times),'elements':elements,'overlaps':overlaps}
    b.save(project/'glyph_bounds.json',bounds)
    cmd=[str(b.ROOT/'tools/python311/python.exe'),'-X','utf8',str(b.ROOT/'analysis/validate_vertical_layout.py'),str(project/'glyph_bounds.json'),'--profile','youtube_portrait_full_frame_v2','--report',str(project/'safe_area_report.json')]
    proc=subprocess.run(cmd,cwd=b.ROOT,capture_output=True,creationflags=b.NO_WINDOW)
    pricechecks=[]
    for a in anchors:
        cid=next(s['composition_id']for s in b.read(project/'storyboard.json')['scenes']if s['scene_id']==a['scene_id'])
        selector=f'#{cid}-value{a["row"]}'
        states=[]
        for t in [a['target_s']-.001,a['target_s']+.001]:
            page.evaluate('(t)=>qaSeek(t)',t)
            states.append(float(page.locator(selector).evaluate('(e)=>getComputedStyle(e).opacity')))
        pricechecks.append({**a,'opacity_before':states[0],'opacity_after':states[1],'passed':states[0]==0 and states[1]==1})
    b.save(project/'price_boundary_checks.json',pricechecks)
    proofs=[]
    for s in b.read(project/'storyboard.json')['scenes']:
        aa=[a['target_s']for a in anchors if a['scene_id']==s['scene_id']]
        t=max(aa)+.5 if aa else (s['start_s']+s['end_s'])/2
        page.evaluate('(t)=>qaSeek(t)',t)
        dest=project/'source_proofs'/f'{s["composition_id"]}.png'
        b.owned(dest).parent.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(dest))
        proofs.append({'time_s':t,'frame':str(dest),'sha256':b.sha(dest),'scope':'source DOM proof, not decoded MP4'})
    b.save(project/'source_proofs.json',proofs)
    passed=proc.returncode==0 and not overlaps and all(a['passed']for a in pricechecks)
    result={'short_id':manifest['short_id'],'passed':passed,'safe_area_passed':proc.returncode==0,'overlaps':len(overlaps),'measured_elements':len(elements),'sample_count':len(times),'native_price_boundary_checks':len(pricechecks),'all_price_boundary_checks_passed':all(a['passed']for a in pricechecks),'browser':browser.version,'actual_listening':False,'continuous_playback':False}
    b.save(project/'source_measurement_receipt.json',result)
    page.close()
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--version',default='native-v1');p.add_argument('--short',choices=b.IDS);a=p.parse_args()
    with sync_playwright()as pw:
        chrome=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
        browser=pw.chromium.launch(headless=True,executable_path=str(chrome),args=['--allow-file-access-from-files'])
        results=[measure(b.HERE/a.version/sid,browser)for sid in ([a.short]if a.short else b.IDS)]
        browser.close()
    print(json.dumps(results,ensure_ascii=False))
    raise SystemExit(not all(r['passed']for r in results))
