from pathlib import Path
import json,math
p=Path(__file__).resolve().parent
ep=p.parents[1]
read=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
r=read(p/'generation_receipt.json');a=read(p/'M010.alignment.json')
t=(ep/'outputs/story-review-v8/M010_cta.txt').read_text(encoding='utf-8')
assert ''.join(a['characters'])==t
parts=['영상이 만족스러웠다면','구독과 좋아요 버튼 한번씩','눌러주시면 감사하겠습니다.','시청해주셔서 대단히 감사합니다.']
cues=[];cursor=0
for text in parts:
 s=t.index(text,cursor);e=s+len(text);cursor=e
 assert t[s:e]==text
 cues.append(dict(cue_id=f'M010-CTA-{len(cues)+1:02}',text=text,lines=[text],char_start=s,char_end=e,start_s=a['character_start_times_seconds'][s],provider_end_s=a['character_end_times_seconds'][e-1],end_s=min(r['pcm_duration_s'],a['character_end_times_seconds'][e-1])))
speech=[i for i,c in enumerate(a['characters']) if c.isalnum()]
last=speech[-1];speech_end=a['character_end_times_seconds'][last]
over=[dict(index=i,character=c,end_s=a['character_end_times_seconds'][i]) for i,c in enumerate(a['characters']) if a['character_end_times_seconds'][i]>r['pcm_duration_s']]
assert all(not x['character'].isalnum() and x['end_s']-r['pcm_duration_s']<=.1 for x in over)
assert speech_end<=r['pcm_duration_s']
out=dict(scene_id='M010',script_revision='script-v8-user-literal-CTA',cues=cues,timing_basis='provider_original_exact_character_alignment',actual_listening=False)
(p/'M010.captions_timed.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
h=dict(status=r['status'],script_revision='script-v8-user-literal-CTA',source_script_sha256=r['source_script_sha256'],scene_id='M010',file='narration/cta-v8/M010.mp3',sha256=r['sha256'],alignment_file='narration/cta-v8/M010.alignment.json',captions_file='narration/cta-v8/M010.captions_timed.json',pcm_duration_s=r['pcm_duration_s'],frames_30fps=math.ceil(r['pcm_duration_s']*30),actual_speech_end_s=speech_end,actual_speech_end_basis='Provider original alignment last alphanumeric spoken character end; not acoustic listening',last_spoken_character=a['characters'][last],pcm_end_policy='Retain complete decoded PCM without trimming; safest outro hold starts after PCM end',outro_hold_s=3,outro_start_relative_to_M010_pcm_basis_s=r['pcm_duration_s']+3,outro_start_relative_to_M010_last_spoken_character_basis_s=speech_end+3,clamped_terminal_characters=over,actual_credits=r['actual_credits'],submitted_characters=59,additional_cash_usd=0,post_requests=1,retries=0,actual_listening=False,unchanged_existing_audio=True,next_role=['director','editor','qa'])
(p/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:h[k] for k in ['pcm_duration_s','frames_30fps','actual_speech_end_s','actual_credits','outro_start_relative_to_M010_pcm_basis_s']}))
