"""Freeze a bounded review packet: twelve actual encoded PNGs and the two Shorts texts."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=HERE/'shorts_media_input_v2';out.mkdir(exist_ok=True)
assert not (out/'report.json').exists()
items=[];images=[]
for ident in ['funnel','analysis']:
    folder=EP/'outputs/shorts-jun-v2'/ident;render=read(folder/'renders/render_receipt.json')
    manifest=read(folder/'renders/encoded-evidence/manifest.json');timing=read(folder/'timing.json')
    assert render['video_sha256']==manifest['video_sha256']==sha(ROOT/render['video'])
    selected=[]
    for s in manifest['scene_contact_sheets']:selected.append({'path':s['path'],'sha256':s['sha256'],'role':'actual encoded scene contact sheet'})
    for cue in sorted(timing['cues'],key=lambda q:len(q['text']),reverse=True)[:2]:
        row=next(r for r in manifest['actual_encoded_frames'] if any(x['role']=='caption_midpoint' and x['scene']==cue['id'] for x in r['roles']))
        selected.append({'path':row['path'],'sha256':row['sha256'],'role':'full resolution longest caption','time_s':row['time_s'],'cue':cue['text']})
    scene='F05' if ident=='funnel' else 'A07'
    scenes=read(folder/'scenes.json')['scenes'];i=next(i for i,s in enumerate(scenes) if s['id']==scene)
    for sid,role in [(scenes[i-1]['id'],'scene_exit'),(scene,'scene_entry')]:
        row=next(r for r in manifest['actual_encoded_frames'] if any(x['role']==role and x['scene']==sid for x in r['roles']))
        selected.append({'path':row['path'],'sha256':row['sha256'],'role':'actual boundary '+role,'time_s':row['time_s']})
    images.extend(selected)
    signal=(ROOT/manifest['signal_log']).read_text(encoding='utf8');signal=signal[signal.rfind('Summary:'):]
    items.append({'id':ident,'video':render['video'],'video_sha256':render['video_sha256'],'duration_s':render['duration_s'],
        'script':(EP/f'narration/shorts-jun-v1/{ident}/script.txt').read_text(encoding='utf8'),
        'subtitles':render['subtitles'],'subtitles_sha256':render['subtitles_sha256'],'SRT_content':(ROOT/render['subtitles']).read_text(encoding='utf8'),
        'scenes':scenes,'source_bounds':{'checks':len(read(folder/'preview/bbox_report.json')['elements']),'failures':0,'profile':'youtube_portrait_full_frame_v2'},
        'native_audio_alignment':{'source':'existing Jun / same native speed','source_audio_sha256':timing['audio_sha256'],'cue_count':len(timing['cues']),'last_speech_end_s':timing['last_speech_end_s'],'tail_s':timing['tail_after_speech_s'],'new_TTS_calls':0},
        'technical':{'full_AV_decode':True,'width':1080,'height':1920,'fps':30,'actual_encoded_frames_extracted':manifest['sample_count'],'signal_summary':signal},
        'actual_listening':False,'continuous_playback':False})
assert len(images)==12
for row in images:assert sha(ROOT/row['path'])==row['sha256']
packet={'revision':'shorts-jun-v2','scope':'two native portrait Shorts; actual encoded stills, full caption text, native character timing and measured signal only',
    'items':items,'image_manifest':images,'facts':{'base_conditions':'initial wealth250million KRW; same600million KRW home; monthly housing/saving budget3million;10years; house2%/investment6%/loan4%; deposit/rent fixed; all remaining money invested','base_networth_billion_KRW':{'buy':.61,'jeonse':.66,'rent':.69},'house4pct_buy_networth_billion_KRW':.77,'house6pct_buy_networth_billion_KRW':.96,'leverage':'house600million=own equity240million+loan360million; first year2% house-price gain12million=5% of house equity before interest/holding costs','all_numbers':'rounded model results from locked main script v6'},
    'feedback':['different explanatory visuals between two Shorts','show current spoken condition','protect numbers and units in semantic captions','critical text140..840/260..1360','no clipped letters','no process badges or unnecessary negative disclaimers','distinguish house evaluation gain from final net worth'],
    'previous_source_QA_recommendations_fixed':read(EP/'editor/shorts-jun-v2/changes.json'),'excluded':['audio files','credentials','account data','individual transactions','full metadata/description bodies']}
(out/'report.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(out/'image_paths.json').write_text(json.dumps([r['path'] for r in images],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'packet':str((out/'report.json').relative_to(ROOT)),'images':len(images),'video_hashes':[r['video_sha256'] for r in items]}))
