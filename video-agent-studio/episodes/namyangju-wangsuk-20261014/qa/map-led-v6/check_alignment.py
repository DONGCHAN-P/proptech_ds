import pathlib,json,hashlib
p=pathlib.Path(__file__).parent;e=p.parents[1];m=json.loads((e/'narration/alignment_manifest_v2.json').read_text(encoding='utf-8'));caps=json.loads((e/'writer/map-led-v4/captions_semantic_v4.json').read_text(encoding='utf-8'));rows=[]
for ch in m['chapters']:
 sid=ch['scene_id'];txt=(e/'writer/map-led-v4'/caps['chapter_input_meta'][sid]['path']).read_text(encoding='utf-8');a=json.loads((e/ch['alignment_file']).read_text(encoding='utf-8'));a=a.get('alignment',a)
 assert ''.join(a['characters'])==txt
 assert hashlib.sha256((e/ch['file']).read_bytes()).hexdigest()==ch['sha256']
 starts=a['character_start_times_seconds'];ends=a['character_end_times_seconds'];assert len(starts)==len(ends)==len(txt)
 assert all(x<=y for x,y in zip(starts,ends)) and all(x<=y for x,y in zip(starts,starts[1:]))
 overflow=[i for i,t in enumerate(ends) if t>ch['pcm_duration_s']]
 assert all(txt[i] in '.!?。！？ \n' for i in overflow),(sid,overflow)
 assert max(ends)-ch['pcm_duration_s']<=.081
 for cue in caps['chapters'][sid]:assert txt[cue['char_start']:cue['char_end']]==cue['text']
 rows.append({'scene_id':sid,'chars':len(txt),'pcm_duration_s':ch['pcm_duration_s'],'last_character_end_s':max(ends),'punctuation_tail_overflow_s':round(max(ends)-ch['pcm_duration_s'],6),'spoken_character_overflow':0,'audio_sha_pass':True,'raw_alignment_exact_text':True})
r={'revision':'map-led-v6-audio-alignment-source','chapters':rows,'total_chars':sum(x['chars'] for x in rows),'total_pcm_s':sum(x['pcm_duration_s'] for x in rows),'caption_span_count':sum(len(v) for v in caps['chapters'].values()),'actual_listening':False,'continuous_playback':False,'scope':'제공타임스탬프·텍스트·음성해시검증. 실제발음/음성동기청취검증아님; MP3디코드실측은후속.'}
(p/'alignment_source_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(r['total_chars'],r['total_pcm_s'])
