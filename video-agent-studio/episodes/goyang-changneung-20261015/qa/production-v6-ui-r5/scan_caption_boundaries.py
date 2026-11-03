from pathlib import Path
import json,re,hashlib
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');Q=E/'qa/production-v6-ui-r5';P=E/'outputs/production-v6-ui-r5/project_r5.json';p=json.loads(P.read_text(encoding='utf-8'));segs=json.loads((E/'narration/preview-v6/segments.json').read_text(encoding='utf-8'));by={s['file']:s for s in segs};norm=lambda s:re.sub(r'\s+','',s)
patterns={'date':r'\d{4}년\d{1,2}월(?:\d{1,2}일)?','money':r'(?:\d[\d,]*억)?(?:\d[\d,]*천)?(?:\d[\d,]*만)?\d*[\d,]*원','count':r'\d[\d,]*(?:만\d[\d,]*)?(?:세대|곳|건|분|㎡|호선)','code':r'(?:S[1-6]|GTX-A|DMC|LH|LX|84AH|84A)'}
issues=[];text_mismatch=[]
for unit,s in by.items():
 rows=[x for x in p['intervals'] if x['unit']==unit];alltext=''.join(norm(x['props'].get('caption','')) for x in rows);orig=norm(s['text'])
 if alltext!=orig:text_mismatch.append(unit)
 spans=[]
 for k,pat in patterns.items():spans.extend((m.start(),m.end(),k,m.group()) for m in re.finditer(pat,orig) if m.end()>m.start()+1)
 pos=0
 for a,b in zip(rows,rows[1:]):
  pos+=len(norm(a['props'].get('caption','')))
  for st,en,k,v in spans:
   if st<pos<en:issues.append({'scene_id':a['scene_id'],'unit':unit,'time_s':a['end_frame']/30,'type':k,'protected':v,'before':a['props']['caption'],'after':b['props']['caption']})
r={'project_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'interval_count':len(p['intervals']),'narration_units':len(segs),'text_mismatch_units':text_mismatch,'protected_boundary_issues':issues,'patterns':patterns,'limits':'Text boundaries only; no speech word alignment claim'}
(Q/'caption_boundary_scan.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
