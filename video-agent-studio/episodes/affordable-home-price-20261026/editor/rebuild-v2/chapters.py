"""Chapter transition emitter, called only with parent-locked titles later."""
import html
import json
import shutil
from pathlib import Path
import pipeline as p


def emit_transition(folder, chapter_id, locked_title, allocation):
    folder=p.owned(folder)
    if not locked_title.strip() or '?' in locked_title or '\ufffd' in locked_title:
        raise ValueError('Unusable chapter title')
    image=p.checked_ref({'path':allocation['asset'],'sha256':allocation['sha256']})
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'assets/fonts').mkdir(parents=True)
    shutil.copy2(image,folder/'assets/background.png')
    shutil.copy2(p.ASSETS/'gsap.min.js',folder/'assets/gsap.min.js')
    shutil.copy2(p.ASSETS/'fonts/Pretendard-Bold.woff2',folder/'assets/fonts/Pretendard-Bold.woff2')
    doc='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>
@font-face{font-family:Pretendard;font-weight:700;src:url(assets/fonts/Pretendard-Bold.woff2)}
*{margin:0;box-sizing:border-box}html,body{width:1920px;height:1080px;overflow:hidden}
#root{position:relative;width:100%;height:100%;overflow:hidden;font-family:Pretendard,sans-serif}
img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.shade{position:absolute;inset:0;background:linear-gradient(90deg,#0d263de0 0%,#0d263d90 45%,#0d263d00 85%)}
h1{position:absolute;left:96px;top:444px;width:1560px;font-size:72px;line-height:1.4;font-weight:700;color:#f6f4ef;white-space:nowrap}
</style></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="3"><img src="assets/background.png"><div class="shade"></div><h1 id="chapter-title">'''+html.escape(locked_title)+'''</h1></div>
<script>const tl=gsap.timeline({paused:true});tl.fromTo('#chapter-title',{opacity:0},{opacity:1,duration:.2,ease:'power2.out'},0);window.__timelines=window.__timelines||{};window.__timelines.main=tl;</script></body></html>'''
    (folder/'index.html').write_text(doc,encoding='utf8')
    p.dump(folder/'chapter.json',{'chapter_id':chapter_id,'title':locked_title,'duration_s':3,'read_hold_s':2.8,'asset':p.pin(image),'type':'ai_concept','source_manifest':allocation['asset_manifest'],'actual_location':False,'policy_document_evidence':False,'photo_motion':'none','screen_AI_badge':False,'html_sha256':p.sha(folder/'index.html')})
    return folder/'index.html'


def validate_schedule(allocations):
    paths=[p.source(a['asset']) for a in allocations]
    if len(paths)!=len(set(paths)):
        raise ValueError('Same photo scheduled for more than one chapter')
    required={'bank_limits','transaction_costs'}
    if not required<={a['topic_key'] for a in allocations}:
        raise ValueError('Both new required chapter images must appear exactly once')
    for a in allocations:
        p.checked_ref({'path':a['asset'],'sha256':a['sha256']})
