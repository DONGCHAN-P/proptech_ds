from pathlib import Path
import json,re
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');o=E/'outputs/production-v6-preview';q=E/'qa/production-v6-preview';p=json.loads((o/'project_r2.json').read_text(encoding='utf-8'));s=json.loads((E/'narration/preview-v6/segments.json').read_text(encoding='utf-8'))
norm=lambda t:re.sub(r'\s+','',t)
a=''.join(x['props'].get('caption','') for x in p['intervals']);b=''.join(x['text'] for x in s)
srt=(o/'changneung_v6_preview_r2.srt').read_text(encoding='utf-8-sig');blocks=re.split(r'\n\s*\n',srt.strip());txt=''.join(''.join(x.splitlines()[2:]) for x in blocks)
r={'project_display_equals_segment_display':norm(a)==norm(b),'srt_equals_segment_display':norm(txt)==norm(b),'srt_cue_count':len(blocks),'final_caption_end_frame':max(x['end_frame'] for x in p['intervals'] if x['props'].get('caption')),'no_spoken_SAPI_names_leaked':not any(x in a for x in ['에스 원','에스 포','에스 파이브','디 엠 씨']),'internal_timing':'proportional estimate, not actual word alignment'}
(q/'subtitle_integrity_r2.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
