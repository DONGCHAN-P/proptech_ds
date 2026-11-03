"""Record verified final delivery and the exact limited producer review scope."""
import hashlib,json,os,shutil
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
OUT=EP/'outputs/private-production-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
render=read(HERE/'render_receipt.json');plan=read(OUT/'render_plan.json');edl=read(OUT/'assembly_edl.json');frames=read(OUT/'encoded_frame_plan.json')
video=Path(render['final_file'])
assert render['status']=='rendered_technical_pass_full_media_review_pending' and sha(video)==render['final_sha256']
assert render['decode_returncode']==0 and frames['final_sha256']==render['final_sha256']
unique={r['file']:r['sha256'] for r in frames['samples']}
for rel,expected in unique.items():
    p=OUT/rel
    assert sha(p)==expected
    with Image.open(p) as image:assert image.size==(1920,1080)
viewed=['00024.png','00075.png','00088.png','00163.png','00169.png','00172.png']
review={'status':'sampled_producer_visual_pass_independent_media_QA_pending','final_sha256':sha(video),
        'contact_sheets_actually_viewed':frames['contact_sheets'],'overview_scene_count':50,
        'full_resolution_final_frames_actually_viewed':viewed,'observations':['Regional 7 sample ranges remain visible.','Both v6 terminology cues and chapter 5 title match the approved wording.','Housing-life cutout is used in its dedicated scene, distinct from the following teaser.','The sampled end hold has no caption box; next-episode graphic remains.','No new clipping observed in these samples.'],
        'all_175_frames_visually_reviewed':False,'continuous_playback':False,'actual_listening':False,'final_media_approved':False}
dump(HERE/'producer_frame_review.json',review)
outro=next(s['global_start_s'] for s in edl['segments'] if s['id']=='clean_brand_outro')
plan.update(full_rendered=True,final_mp4=str(video.relative_to(EP)).replace('\\','/'),final_sha256=sha(video),render_receipt='editor/private-production-v2/render_receipt.json',encoded_frame_plan='encoded_frame_plan.json',
            pending=['independent final encoded-media QA, listening/continuous review and main release approval'])
plan['brand_assembly']['actual_outro_global_start_s']=outro
dump(OUT/'render_plan.json',plan)
index=OUT/'index.html';text=index.read_text(encoding='utf8')
text=text.replace('전체 렌더·음성 청취·연속 재생 전입니다.','전체 렌더·decode 완료. 실제 청취·연속 재생·최종 미디어 검수는 별도입니다.')
text=text.replace('</ol>','</ol><p><a href="renders/measured-v6/housing_choice_private_v2_injoon_v6.mp4">실측 v6 본편 검토 파일</a> · <a href="encoded_frame_plan.json">50장면·경계 프레임 패킷</a></p>')
index.write_text(text,encoding='utf8')
shutil.copy2(EP/'editor/private-production-v1/music_credit.txt',HERE/'music_credit.txt')
dump(HERE/'audio_design.json',{'script_sha256':plan['script_sha256'],'actual_body_seconds':sum(c['total_seconds'] for c in plan['chapters']),
     'canonical_voiceover_carve':'mix_receipt.json; spectral peaking, gain and speech-following envelopes; core 0.8.181 read-only from v1 audio-deps',
     'music_clock':'chapter 5/6 measured duration deltas carried forward into chapter 7-10 BGM content offsets',
     'assembly_joins':'8ms preventive fade in/out after final atrim; duration/EDL preserved; assembly_audio_recipe.json',
     'rights':'director/two-episode-production-v1/media_assets.json; music_credit.txt','actual_encode_and_full_decode':'pass',
     'actual_listening':False,'continuous_playback':False,'quality_approval':'independent final media review pending','new_installations':0})
def stamp(t):
    m,s=divmod(t,60);h,m=divmod(int(m),60)
    return f'{h:02d}:{m:02d}:{s:06.3f}'
lines=['# 실측 v6 배치 가이드','',f'배포 대상: `{video.relative_to(EP).as_posix()}`. 1920×1080·30fps·H.264/AAC 48kHz stereo, {float(render["ffprobe"]["format"]["duration"]):.6f}초. 전체 decode 통과. v1 원본과 렌더는 보존했다.','',
       '클린 브랜드는 훅 뒤 5초와 마지막 10초다. `assembly_edl.json`의 같은 분할·전역 오프셋을 영상·음성·342큐 SRT에 적용했다. 각 접합에는 길이를 바꾸지 않는 예방적 8ms in/out fade를 적용했다.','',
       '| 장 | 본편 기준 시작 | 장 길이 | 파일/추천 구간 |','|---|---|---|---|']
for c in plan['chapters']:
    start=next(s['global_start_s'] for s in edl['segments'] if s.get('chapter')==c['chapter'])
    lines.append(f'| {c["chapter"]} | {stamp(start)} | {c["total_seconds"]:.6f}초 | `renders/measured-v6/ch{c["chapter"]:02d}.mp4` 전체 |')
lines += ['', '제목·본문 도식·출처·흰 자막 박스는 분리 레이어다. 장면 수명은 컷으로 전환하며 GSAP paused/seek-safe 연출을 유지했다. 그래프는 data_chart, 나머지 설명은 editorial_diagram이며 ch10/s10life는 생활 계획용 그림이다. 해당 RGBA 그림은 그 한 장면에서 한 번만 사용하고 실제 단지·면적·가격 증거로 표시하지 않았다.','',
          '`encoded_frame_plan.json`에 50장면의 추천 대표 시점·경계 전후·실제 전역 프레임 번호·175 PNG SHA가 있다. 원본 해상도 PNG와 contact sheet 5장은 `renders/measured-v6/encoded-evidence/`에 있다.','',
          '재현은 `render_commands.json`과 `render_pipeline.py`를 따른다. 완성본을 덮어쓰지 않는다. `prefix_reuse_receipt.json`은 ch01~03 입력 및 MP4 불변 증거다. 기술 검사와 표본 프레임 확인 범위는 `render_receipt.json`, `producer_frame_review.json`에 분리했다. 청취·연속 재생·최종 미디어 승인은 main/QA 후속이며 업로드는 수행하지 않았다.']
(HERE/'placement_guide.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
manifest=read(OUT/'input_manifest.json')
for p in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs')):manifest['inputs_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
for rel in ['qa/private-production-v1/source_v6_pass_receipt.json','qa/private-production-v1/audio_v6_delta_handoff.json','director/two-episode-production-v1/edl_review_v6.json']:
    p=EP/rel;manifest['inputs_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
dump(OUT/'input_manifest.json',manifest)
outputs={}
for directory,dirs,names in os.walk(OUT):
    dirs[:]=[d for d in dirs if d not in ['preview','preview_delta','audio-deps','ffmpeg-deps','media-bin','node_modules','.hyperframes','renders']]
    for name in names:
        p=Path(directory)/name
        if name not in ['input_manifest.json','output_manifest.json','delivery_manifest.json']:outputs[p.relative_to(OUT).as_posix()]=sha(p)
dump(OUT/'output_manifest.json',outputs)
handoff={'task_id':'editor-v6-measured-final-production','role':'editor','status':'render_complete_technical_pass_final_media_QA_pending',
         'summary':'v1 보존. ch01~03 불변 증거로 재사용, ch04~10 새 렌더·브랜드 합본·전체 decode 완료. 50장면 대표/경계 등 175개 fullres PNG와 contact 5장 전달. 청취/연속 재생/최종 미디어 승인은 후속.',
         'script_sha256':plan['script_sha256'],'final_mp4':str(video.relative_to(EP)).replace('\\','/'),'final_sha256':sha(video),
         'duration_s':float(render['ffprobe']['format']['duration']),'bytes':video.stat().st_size,
         'validation':{'resolution':[1920,1080],'fps':30,'audio':'AAC 48kHz stereo','full_decode':'pass','source_CLI_BBox_carve_ASR_EDL':'pass','producer_overview_scenes':50,'producer_fullres_final_samples':6,'actual_listening':False,'continuous_playback':False},
         'artifacts':['outputs/private-production-v2/encoded_frame_plan.json','editor/private-production-v2/render_receipt.json','editor/private-production-v2/prefix_reuse_receipt.json','editor/private-production-v2/producer_frame_review.json','editor/private-production-v2/placement_guide.md','outputs/private-production-v2/captions_measured.srt'],
         'open':['main/QA independent encoded-media review and listening/continuous scope','main final release packaging and private-upload decision'],
         'next_owner':'main / video_qa; release-v2 is main-owned','new_paid_calls':0,'upload_performed':False}
dump(HERE/'handoff.json',handoff)
delivery={'final_mp4':{'file':str(video.relative_to(EP)).replace('\\','/'),'sha256':sha(video)},'records_sha256':{p.relative_to(EP).as_posix():sha(p) for p in [HERE/'handoff.json',HERE/'render_receipt.json',HERE/'producer_frame_review.json',OUT/'captions_measured.srt',OUT/'encoded_frame_plan.json',OUT/'input_manifest.json',OUT/'output_manifest.json']},'tooling_dependency_trees_excluded':True}
dump(OUT/'delivery_manifest.json',delivery)
print(json.dumps({'status':handoff['status'],'final_file':handoff['final_mp4'],'sha256':handoff['final_sha256'],'duration_s':handoff['duration_s'],'fullres_PNGs':len(unique),'handoff':str(HERE/'handoff.json')},ensure_ascii=False))
