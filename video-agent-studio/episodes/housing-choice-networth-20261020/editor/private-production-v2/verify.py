"""Static source/ownership/manifest checks. Does not certify voice or encoded media."""
import hashlib
import json
import re
import sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from alignment import norm,parse_script
EP=HERE.parents[1]; ROOT=EP.parents[2]; OUT=EP/'outputs/private-production-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    plan=read(OUT/'render_plan.json'); manifest=read(OUT/'input_manifest.json')
    failures=[]; total_cues=0; anchors=0
    for rel,expected in manifest['inputs_sha256'].items():
        p=ROOT/rel
        if not p.is_file() or sha(p)!=expected:failures.append('input SHA drift: '+rel)
    script=EP/plan['script_path']; chapters=parse_script(script.read_text(encoding='utf8'))
    for c in plan['chapters']:
        folder=OUT/c['project']; source=(folder/'index.html').read_text(encoding='utf8'); timing=read(folder/'timing.json');audit=read(folder/'anchor_audit.json')
        total_cues+=len(timing['cues']);anchors+=len(audit['anchors'])
        if '{{' in source or re.search(r'<script[^>]+src=["\']https?://',source):failures.append('unresolved placeholder/external script: '+c['project'])
        if 'class="mark no"' in source or 'AI 개념 이미지' in source:failures.append('obsolete badge/warning: '+c['project'])
        if ''.join(norm(q['text']) for q in timing['cues'])!=''.join(map(norm,chapters[c['chapter']]['paragraphs'])):failures.append('script/caption mismatch: '+c['project'])
        if audit['zero_second_fallback'] or any(a['time_s']<.5 for a in audit['anchors']):failures.append('missing-anchor zero fallback: '+c['project'])
        if any(a['review_required'] for a in audit['anchors']):failures.append('unreviewed semantic alignment: '+c['project'])
        if len(set(re.findall(r'\bid="([^"]+)"',source)))!=len(re.findall(r'\bid="([^"]+)"',source)):failures.append('duplicate DOM ids: '+c['project'])
        if not re.search(r'gsap.timeline\(\{\s*paused:\s*true\s*\}\)',source):failures.append('timeline not paused: '+c['project'])
        previous=0
        for q in timing['cues']:
            if not previous<=q['start_s']<q['end_s']<=timing['total_seconds']:failures.append('invalid timing '+q['id'])
            previous=q['end_s']
        for s in timing['scenes']:
            if s['end_s']<=s['start_s']:failures.append('nonpositive scene span '+s['scene_id'])
    for copy,original in [('framework.py','outputs/motion-v1/framework.py'),('chapters.py','outputs/motion-v1/chapters.py'),('intro_build.py','outputs/intro-motion-v1/build.py'),('src/helpers.js','outputs/motion-v1/src/helpers.js'),('src/shell.css','outputs/motion-v1/src/shell.css'),('intro-src/template.html','outputs/intro-motion-v1/src/template.html')]:
        if sha(HERE/'baseline'/copy)!=sha(EP/original):failures.append('baseline source changed from frozen copy: '+original)
    for receipt,rows_key in [(HERE/'checks/summary.json','chapters'),(OUT/'preview/bbox_report.json','checked_chapters')]:
        evidence=read(receipt)
        for row in evidence[rows_key]:
            if sha(OUT/f'ch{row["chapter"]:02d}/index.html')!=row['html_sha256']:failures.append('stale representative evidence: '+str(receipt))
    uses=sum((OUT/f'ch{n:02d}/index.html').read_text(encoding='utf8').count('src="assets/housing-stability-v1.png"') for n in range(1,11))
    if uses!=1:failures.append('housing-stability illustration must appear in exactly one scene')
    from PIL import Image
    image=Image.open(EP/'visual/private-production-v1/housing-stability-v1.png')
    if image.mode!='RGBA' or image.getextrema()[3][0]!=0:failures.append('housing cutout lacks actual RGBA transparency')
    result={'status':'pass' if not failures else 'fail','chapters':len(plan['chapters']),'cues':total_cues,'anchors':anchors,'failures':failures,
            'script_sha256':sha(script),'scope':'local static source, '+plan['status']+' and current representative evidence hashes; no encoded-media or listening claim','full_rendered':False,'actual_listening':False,'continuous_playback':False}
    (HERE/'static_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False));return int(bool(failures))


if __name__=='__main__':sys.exit(main())
