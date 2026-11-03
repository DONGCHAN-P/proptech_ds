from pathlib import Path
import json,hashlib,re
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v8-jun'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
p=read(O/'project_v8_jun.json');t=read(O/'technical_v8_jun.json');render=read(O/'render_receipt.json');mapping=read(E/'semantic_alignment.json');guard=read(O/'layout_guard.json');prov=read(E/'input_provenance.json')
groups={}
for x in p['visual_intervals']:
 if x['kind'] not in ['body','chapter']:continue
 key=json.dumps({k:v for k,v in x['props'].items()if k not in ['caption','hideCaption']},sort_keys=True)
 if key not in groups or len(x['props'].get('caption',''))>len(groups[key].get('caption','')):groups[key]=x['props']
checked=[x['props']for x in guard['checks']]
assert all(dict(q,motionFrame=44) in checked for q in groups.values())
assert guard['passed'];assert t['full_av_null_decode'];assert t['sha256']==hashlib.file_digest((O/'changneung_full_v8_jun.mp4').open('rb'),'sha256').hexdigest()
assert len(p['captions'])==213 and len(mapping)==143 and all(x['end_frame']-x['start_frame']>=30 for x in p['captions'])
assert sum(x['kind']=='chapter' for x in p['visual_intervals'])==6
assert not any(x['props'].get('mode')=='note'for x in p['visual_intervals'])
assert len({x['props']['replacementId']for x in p['visual_intervals']if x['props'].get('replacementId')})==13
assert p['outro_start']/30-p['signal_end_s']>=3
for a,b in zip(p['visual_intervals'],p['visual_intervals'][1:]):assert a['end_frame']==b['start_frame']
diff=read(EP/'outputs/production-v8-labels/affected_ranges.json')['caption_diff']
assert all(any(x['after']==c['text']for c in p['captions'])for x in diff)
paths=[O/x for x in ['changneung_full_v8_jun.mp4','changneung_v8_jun.srt','technical_v8_jun.json','rendered_project_v8_jun.json','project_v8_jun.json','scene_proposal.json','captions.json','timing_audit.json','layout_guard.json','evidence_manifest.json']]+[E/'semantic_alignment.json',E/'input_provenance.json']
artifacts=[dict(path=str(x),sha256=hashlib.file_digest(x.open('rb'),'sha256').hexdigest(),bytes=x.stat().st_size)for x in paths]
save(O/'delivery_manifest.json',dict(version='production-v8-jun',artifacts=artifacts,approved_baseline_sha256=prov['baseline_mp4_sha256'],source_script_sha256=p['script_sha256']))
rows=[]
for s in p['scenes']:
 starts=[x['start_frame']for x in p['scenes']if x['start_frame']>s['start_frame']];end=min(starts)if starts else p['outro_start'];rows.append(f"| {s['scene_id']} | {s['start_frame']/30:.3f}초 | {(end-s['start_frame'])/30:.3f}초 | 실제 자료·데이터/도표 |")
guide='# Jun v8 배치 가이드\n\n배포 파일: `changneung_full_v8_jun.mp4`, 자막 `changneung_v8_jun.srt`.\n전체 길이 '+f"{p['duration_frames']/30:.3f}초, 1920×1080, 30fps.\n\n"+'| 장면 | 시작 | 길이 | 자료 유형 |\n|---|---:|---:|---|\n'+'\n'.join(rows)+'\n\n본문은 실제 자료/수치의 동일 스틸과 의미 강조 모션(최대45프레임)을 유지합니다. 자막의 고정 흰 박스와 그 아래 출처는 별도 레이어입니다.\n6개 챕터(각3초)는 AI 개념 이미지 표기를 유지합니다. 인트로5초·아웃트로10초는 깨끗한 기존 브랜드 클립이며 박스 자막이 없습니다. 마지막 발화 기준 '+f"{p['outro_start']/30-p['signal_end_s']:.6f}초 뒤 아웃트로가 시작합니다.\n"+'학교3개 자막은 일반명으로 표시하고 원문 음성은 승인 대본을 유지합니다. 학교 예정지·S1 라벨 슬롯과 원래 필지까지의 리더선은 labels 승인본 그대로입니다.\n외부 업로드·예약은 총괄의 최종 게이트 대상입니다.\n'
(E/'placement_guide.md').write_text(guide,encoding='utf-8')
checks=dict(exact_143_source_sentence_mapping=True,provider_character_alignment=True,old_voice_times_reused=False,caption_count=213,caption_minimum_frames=min(x['end_frame']-x['start_frame']for x in p['captions']),school_display_changes=3,replacement_ids=13,note_count=0,chapter_count=6,all_visual_intervals_contiguous=True,full_av_decode=True,signal_threshold_dbfs=-60,actual_listening=False,continuous_playback=False)
save(E/'editor_self_review.json',checks)
h=dict(role='editor',status='rendered_technical_pass_independent_qa_pending',version='production-v8-jun',final_mp4=str(O/'changneung_full_v8_jun.mp4'),sha256=t['sha256'],duration_s=p['duration_frames']/30,artifacts=artifacts,input_versions=prov['source_inputs'],narration_handoff=str(EP/'narration/jun-v8-final/handoff.json'),validations=checks,preflight='77 distinct variants/widest captions; four contact sheets visually inspected',stills=render,reused_facts=prov['reused_fact_scope'],changed_scenes=[x['scene_id']for x in p['scenes']],next_owner='qa_jun_v8 / root',required_open=['independent exact-artifact QA'],limitations=['Continuous playback and actual listening not performed; pronunciation/naturalness not asserted'],render_commands=[f'tools/python311/python.exe -X utf8 {E}/jobs.py STAGE',f'tools/python311/python.exe -X utf8 analysis/video_task_runner.py {E}/STAGE_job.json'],stages=['timeline','preflight','render','assembly','evidence'])
save(E/'handoff.json',h);print(json.dumps(dict(sha256=t['sha256'],duration=p['duration_frames']/30,packet=str(E/'handoff.json'))))
