"""Bind v3 narration paragraphs to their explicit screen states; no rendering."""
from pathlib import Path
import json
import re
import hashlib

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/script-review-v3'
script=(OUT/'script_v3.md').read_text(encoding='utf8')
pattern=r'### (S\d+)\. ([^\n]+)\n\n\*\*낭독\*\*\n\n(.*?)\n\n\*\*화면\*\*\n\n(.*?)(?=\n\n###|\n\n---)'
sections=re.findall(pattern,script,re.S)
assert [s[0] for s in sections]==[f'S{i:03}' for i in range(1,13)]
scenes=[];spoken=[]
story=['# 전체 기간 지역별 영상 v3 — 자료화면 설계','','2006년 이후 전체 거래 통계 → 조건을 맞춘 가격 변화 → 과거와 현재의 회복 경로. 크림 바탕·Pretendard·고정 흰 본문 자막 박스 등 기존 채널 기준을 계승한다. 시간은 실제 음성 이후 확정한다.','']
for sid,title,narration,screen in sections:
    paragraphs=narration.split('\n\n')
    motions=re.findall(r'^- P(\d+): (.+)$',screen,re.M)
    assert [int(p) for p,_ in motions]==list(range(1,len(paragraphs)+1)),sid
    def field(name):
        m=re.search(r'\*\*'+name+r':\*\* (.+)',screen)
        assert m,(sid,name)
        return m[1]
    source,status,alternative=field('근거'),field('준비 상태'),field('대안')
    beats=[{'beat_id':sid+'-P'+p,'narration_text':text,'visual':motion,'source':source,'readiness':status,'alternative':alternative,'start':None,'end':None} for text,(p,motion) in zip(paragraphs,motions)]
    scenes.append({'scene_id':sid,'message':title,'narration_text':narration,'claim_ids':['FULL-HISTORY-'+sid],'material_type':'actual_data_line_chart_and_source','asset_ids':[sid+'-data'],'script_revision':'v3','audio_revision':None,'start':None,'end':None,'timing_basis':'narration_paragraphs_not_voice_locked','status':'script_review_draft','beats':beats})
    spoken.append(narration)
    story += [f'## {sid}. {title}','','| 연결 | 낭독 시작 | 실제 자료·강조 동작 |','|---|---|---|']
    story += [f'| {b["beat_id"]} | {b["narration_text"][:40]}… | {b["visual"]} |' for b in beats]
    story += ['',f'근거: {source}',f'준비: {status}',f'대안: {alternative}','']
(OUT/'visual_storyboard.md').write_text('\n'.join(story)+'\n',encoding='utf8')
(OUT/'narration_v3.txt').write_text('\n\n'.join(spoken)+'\n',encoding='utf8')
obj={'episode_id':EP.name,'script_revision':'v3','timing_locked':False,'scenes':scenes}
(OUT/'scenes_v3.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(EP/'scenes.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
checks={'script_sha256':hashlib.sha256(script.encode()).hexdigest(),'scene_count':len(scenes),'paragraph_count':sum(len(s['beats']) for s in scenes),'spoken_hangul_syllables':len(re.findall('[가-힣]','\n'.join(spoken))),'all_paragraphs_have_explicit_visual_source_status_alternative':True,'voice_timing_locked':False,'actual_audio_listening':False,'continuous_video_playback':False}
(OUT/'structure_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(checks,ensure_ascii=False))
