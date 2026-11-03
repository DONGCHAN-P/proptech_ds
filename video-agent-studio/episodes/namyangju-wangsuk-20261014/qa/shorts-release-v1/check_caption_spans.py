import json
from pathlib import Path
p=Path(__file__).resolve().parents[2];q=Path(__file__).parent
src=json.loads((p/'outputs/readability-cta-v15/timed_captions_v15.json').read_text(encoding='utf8'))
manifest=json.loads((p/'outputs/shorts-release-v1/manifest.json').read_text(encoding='utf8'));r=[]
for m in manifest:
 cues=json.loads((p/('outputs/shorts-release-v1/'+m['id']+'_captions.json')).read_text(encoding='utf8'))
 expected=[c for c in src if m['start']<=c['from_frame']<m['end']]
 assert len(expected)==len(cues)
 for c,e in zip(cues,expected):
  assert c['source']==e
  assert c['from_frame']==e['from_frame']-m['start'] and c['to_frame']==e['to_frame']-m['start']
  assert ''.join(c['lines']).replace(' ','')==''.join(e['lines']).replace(' ','')
 assert expected[0]['from_frame']==m['start'] and expected[-1]['to_frame']==m['end']
 r.append({'id':m['id'],'source_cues_exact':True,'cue_count':len(cues),'cut_exact_complete_sentence_cue_boundaries':True,'max_line_chars':max(len(line) for c in cues for line in c['lines']),'actual_listening':False})
(q/'caption_cut_alignment.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(r)
