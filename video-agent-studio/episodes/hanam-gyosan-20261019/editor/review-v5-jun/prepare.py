from pathlib import Path
import json
E=Path(__file__).resolve().parent;EP=E.parents[1];OLD=E.parent/'review-v5';O=EP/'outputs/production-v5-jun';O.mkdir(parents=True,exist_ok=True)
s=(OLD/'assemble.py').read_text(encoding='utf8').replace('production-v5','production-v5-jun').replace("tag='v5'","tag='v5_jun'").replace('gyosan_review_v5_free_tts.mp4','gyosan_v5_jun.mp4')
a=s.index("for u in p['audio_units']:");b=s.index("music=pcm(",a)
s=s[:a]+'''for track in p['narration_tracks']:
 chunk=pcm(track['audio_path']);a=track.get('input_sample_start',0);b=track.get('input_sample_end',len(chunk));chunk=chunk[a:b];dst=track.get('start_sample',round(track['start_frame']/30*sr));mix[dst:dst+len(chunk)]+=chunk
'''+s[b:]
s=s.replace("voice='New v4 local free Microsoft Heami rate2 / 263 phrase WAVs'","voice='Approved ElevenLabs Jun / ten full scene WAVs, exact character alignment; no generation by editor'")
s=s.replace("p['audio_units'][-1]['end_frame']","p['narration_end_frame']")
(E/'assemble.py').write_text(s,encoding='utf8')
contract=dict(status='awaiting_final_narration_alignment',baseline_project=str(EP/'outputs/production-v5/rendered_project.json'),baseline_sha256='a13779a6b9dd5da21100d1c5f7db4c3199d8f3eacccb13cdd29f2d36536dbc3a',segments_expected=str(EP/'narration/jun-v5-final/segments.json'),timing_expected=str(EP/'narration/jun-v5-final/timing_proposals.json'),phrase_key='unit_id',alignment_fields=['scene_local_start_s','scene_local_end_s','source_character_start','source_character_end_exclusive'],audio_strategy='Ten full scene WAVs; split M000 PCM once at intro insertion without dropping samples; all other scene clips played intact',visual_strategy='Map261 unit IDs to existing v5 PNG/motion sequences. Re-time each phrase from Jun character alignment. Existing PNG source files preserved and reused without new visual generation.',paid_api_calls_by_editor=0,heami_calls=0,brand_intro_frames=150,brand_outro_frames=300,chapter_frames=90,ending_hold_frames=90)
(E/'preparation.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(status='prepared',paid_api_calls_by_editor=0)))
