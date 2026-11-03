from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET

Q=Path(__file__).resolve().parent;EP=Q.parents[1];OUT=EP/'outputs/private-production-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(Q/'targeted_recheck_plan.json');native=read(EP/'narration/production-injoon-v3/final_timing.json')
before=OUT/'source-archive/measured-v3-before-visual-v4'
checks=[];chapters=[];geometry=[]


def check(name,passed,details=None):
    checks.append(dict(check=name,passed=bool(passed),details=details))
    assert passed,name


def constants(raw):
    m=re.search(r'const SCENES=(.*?);const CUES=(.*?);const BEATS=(.*?);',raw,re.S)
    assert m
    return tuple(json.loads(x) for x in m.groups())


def visual_geometry(section):
    svg=re.search(r'<svg\b.*?</svg>',section,re.S).group()
    root=ET.fromstring(svg);parts=[]
    for e in root.iter():
        tag=e.tag.split('}')[-1]
        if e.attrib.get('class') in ['focus-ring','native-word-focus']:continue
        if tag=='g':
            if 'transform' in e.attrib:parts.append((tag,e.attrib['transform']))
        elif tag not in ['svg']:
            attrs=sorted((k,v) for k,v in e.attrib.items() if k not in ['id','class'])
            parts.append((tag,attrs,(e.text or '').strip()))
    return hashlib.sha256(json.dumps(parts,ensure_ascii=False).encode()).hexdigest()


for item in plan['pinned_inputs']:
    p=Path(item['path'])
    if p.name=='mix_receipt.json':continue
    check('고정입력SHA:'+p.name,sha(p)==item['sha256'])
receipt=read(EP/'editor/measured_build_receipt.json');mix=read(EP/'editor/mix_receipt.json')
for ch in range(1,11):
    p=OUT/f'ch{ch:02}/index.html';bp=before/f'ch{ch:02}/index.html';b=bp.read_text(encoding='utf-8');a=p.read_text(encoding='utf-8')
    expected=plan['baseline_revision']['source_chapters'][f'ch{ch:02}']
    check(f'변경전보존원본CH{ch}',sha(bp)==expected)
    check(f'현재빌드receiptCH{ch}',sha(p)==next(x['html_sha256'] for x in receipt['chapters'] if x['chapter']==ch))
    bstyle=re.search(r'<style>(.*?)</style>',b,re.S)[1];astyle=re.search(r'<style>(.*?)</style>',a,re.S)[1]
    check(f'공통CSS불변CH{ch}',astyle==bstyle)
    old_audio=re.findall(r'<audio\b[^>]*>',b);new_audio=re.findall(r'<audio\b[^>]*>',a)
    check(f'postcarve오디오태그불변CH{ch}',old_audio==new_audio)
    mix_ch=next(x for x in mix['chapters'] if x['chapter']==ch)
    check(f'voiceWAV불변CH{ch}',sha(p.parent/'assets/narration.wav')==mix_ch['voice_sha256'])
    check(f'carvedbedWAV불변CH{ch}',sha(p.parent/'assets/music-bed.wav')==mix_ch['bed_sha256'])
    old_s,old_c,old_b=constants(b);scenes,cues,beats=constants(a)
    check(f'CUES표시문원어시각전체불변CH{ch}',cues==old_c)
    check(f'BEATS원문시각불변CH{ch}',all({k:x[k] for k in ['cue_id','scene_id','text','start_s','end_s','native_start_s','native_end_s']}=={k:y[k] for k in ['cue_id','scene_id','text','start_s','end_s','native_start_s','native_end_s']} for x,y in zip(old_b,beats)) and len(old_b)==len(beats))
    current_native=native['chapters'][ch-1]['cues']
    check(f'현재native큐와동일CH{ch}',all(c['id']==n['id'] and c['start_s']==n['start_s'] and c['end_s']==n['end_s'] for c,n in zip(cues,current_native)) and len(cues)==len(current_native))
    section=lambda raw:dict(re.findall(r'<section id="(S[0-9]+R?)"[^>]*>(.*?)</section>',raw,re.S))
    bs,ss=section(b),section(a)
    for sid in bs:
        same=visual_geometry(bs[sid])==visual_geometry(ss[sid]);geometry.append(dict(scene_id=sid,unchanged_geometry_and_labels=same));check('도형좌표라벨불변:'+sid,same)
    check(f'허용장면외HTML불변CH{ch}',ch in [1,7,9] or a==b)
    check(f'폰트불변CH{ch}',all(sha(f)==sha(bp.parent/'assets/fonts'/f.name) for f in (p.parent/'assets/fonts').glob('*.woff2')))
    chapters.append(dict(chapter=ch,path=p.as_posix(),postcarve_html_sha256=sha(p),before_html_sha256=sha(bp),changed=sha(p)!=sha(bp),scenes=scenes,cues=cues,beats=beats))
check('45정적도형150큐',len(geometry)==45 and sum(len(c['cues']) for c in chapters)==150)
r=dict(status='pass',checks=checks,scene_geometry=geometry,chapters=chapters,script_sha256=native['script_sha256'],timing_sha256=sha(EP/'narration/production-injoon-v3/final_timing.json'),edl_sha256=sha(OUT/'assembly_edl.json'),mix_receipt_sha256=sha(EP/'editor/mix_receipt.json'))
(Q/'targeted_static_v4.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='pass',checks=len(checks),changed_chapters=[c['chapter'] for c in chapters if c['changed']],scene_geometry=len(geometry),cues=sum(len(c['cues']) for c in chapters)),ensure_ascii=False))
