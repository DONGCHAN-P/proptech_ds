"""Package measured outputs without promoting technical passes to final media approval."""
import json,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import HERE,EP,ROOT,OUT,read,sha,dump,SCRIPT_SHA
def main():
    r=read(HERE/'render_receipt.json');p=read(OUT/'render_plan.json');e=read(OUT/'encoded_frame_plan.json');s=read(HERE/'signal_receipt.json')
    video=Path(r['final_file']);assert video.is_file() and r['final_sha256']==sha(video)==e['final_sha256']==s['final_sha256']
    assert r['decode_returncode']==0 and r['status']=='rendered_technical_pass_full_media_review_pending'
    for key in ['width','height']:assert next(x for x in r['ffprobe']['streams'] if x['codec_type']=='video')[key]=={'width':1920,'height':1080}[key]
    files={x['file']:x['sha256'] for x in e['samples']}
    for rel,expected in files.items():assert sha(OUT/rel)==expected
    preview=read(OUT/'preview/bbox_report.json');cli=read(HERE/'checks/summary.json');static=read(HERE/'static_checks.json');mix=read(HERE/'mix_receipt.json');edl=read(OUT/'assembly_edl.json')
    assert preview['status']=='sampled_bbox_pass' and cli['status']=='pass' and static['status']=='pass' and mix['status']=='canonical_carve_pass'
    p.update(full_rendered=True,final_mp4=video.relative_to(EP).as_posix(),final_sha256=sha(video),captions_sha256=sha(OUT/'captions_measured.srt'),pending=['main independent exact-final Codex and Claude media reviews','actual listening/continuous playback not performed in this runtime','private upload/old-private deletion performed only by main after gates'])
    dump(OUT/'render_plan.json',p)
    review=read(HERE/'producer_visual_review.json') if (HERE/'producer_visual_review.json').exists() else {'status':'not_viewed','frames_actually_viewed':[],'actual_listening':False,'continuous_playback':False}
    guide=['# Jun 교체본 배치 가이드','',f'실제 배포 영상: `{video.relative_to(EP).as_posix()}`. {float(r["ffprobe"]["format"]["duration"]):.6f}초, 1920×1080·30fps·H.264/AAC 48kHz stereo. SRT: `outputs/jun-production-v1/captions_measured.srt`.','',
        '본문 v6·206개 의미 단위 및 명시적 줄바꿈·기존 시각자료/색/글꼴/도표 값을 보존했다. 원본 문자 위치를 발음 대응표와 새 Jun 문자 정렬로 연결해 장면·모션·자막 시점을 다시 계산했다. 음성 속도는 편집에서 변경하지 않았다. 음악의 spectral carve와 level ducking은 새 Jun PCM으로 재계산했다.','',
        f'클린 인트로: {edl["hook_cut_s"]:.6f}초부터 5초. 훅 자막은 복귀 프레임 전에 종료한다. 마지막 실제 발화 근거 시점: {edl["actual_last_speech_global_s"]:.6f}초, 아웃트로는 {edl["outro_delay_from_last_speech_s"]:.6f}초 뒤 시작해 10초간 유지한다.','',
        '자막은 별도 track9, 흰 박스 track7, 출처 track8, 제목 track2, 그림 track3, 음성 track10, BGM track11을 사용한다. 출처/하단 자막은 배경 모션에 포함하지 않는다. 전환과 브랜드 삽입은 `assembly_edl.json`, 장·장면 추천 시간과 길이는 `scene_starts.json`, 실제 자료 유형과 원본 출처는 각 장 `timing.json`에 있다. 기존 자체 도표·개념 그림·공식 계획 재구성을 사용하며 새 실사/생성 영상으로 소개하지 않는다.','',
        '메타데이터 챕터는 `metadata_chapters.txt`, 실제 발화/PCM 경계와 해시는 `speech_boundaries.json`, 재현 명령은 `editor/jun-production-v1/render_commands.json`, 새 입력 잠금은 `input_manifest.json`에 있다. 장별 render log·receipt 및 전체 AV decode log를 보존했다.','',
        f'검수 증거: {len(files)}개 실제 MP4 PNG, 모든 장면/접합 경계/최장 자막 샘플. 제작 담당이 실제 확인한 범위는 `editor/jun-production-v1/producer_visual_review.json`이다. 소스 DOM 경계 검사와 실제 인코딩 표본 확인을 구분한다.','',
        '기술 decode·신호·소스 검사는 완료됐다. 실제 청취·연속 재생·독립 exact-final Codex/Claude 승인은 별도이며 이 문서로 통과를 선언하지 않는다. 업로드와 기존 비공개 삭제는 수행하지 않았다.','',
        '|장/장면|추천 시작(초)|길이(초)|자료 유형|레이어/전환|','|---|---:|---:|---|---|']
    for ch in p['chapters']:
        for scene in ch['scenes']:
            off=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==ch['chapter'] and o['local_start_s']<=scene['start_s']<o['local_end_s'])
            guide.append(f'|CH{ch["chapter"]:02d}/{scene["scene_id"]}|{scene["start_s"]+off:.3f}|{scene["end_s"]-scene["start_s"]:.3f}|{scene["material_type"]}|그림3/제목2/출처8/자막9, 기존 진입 유지|')
    (HERE/'placement_guide.md').write_text('\n'.join(guide)+'\n',encoding='utf8')
    manifest=read(OUT/'input_manifest.json')
    for file in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs')):manifest['inputs_sha256'][file.relative_to(ROOT).as_posix()]=sha(file)
    dump(OUT/'input_manifest.json',manifest)
    outputs={}
    for directory,dirs,names in os.walk(OUT):
        dirs[:]=[d for d in dirs if d not in ['.hyperframes','node_modules','tmp','frames-cache']]
        for name in names:
            file=Path(directory)/name
            if name not in ['output_manifest.json','delivery_manifest.json']:outputs[file.relative_to(OUT).as_posix()]=sha(file)
    dump(OUT/'output_manifest.json',outputs)
    h={'task_id':'housing-choice-Jun-v1-editor','role':'video_editor','status':'Jun_render_technical_checks_complete_independent_final_QA_pending','input_revisions':{'script_sha256':SCRIPT_SHA,'caption_timing_sha256':p['caption_timing_sha256'],'audio_revision':'jun-production-v1','visuals':'frozen private-production-v3 caption-v7 picture','CLI_pin':'0.8.181'},
       'outputs':[{'path':video.relative_to(ROOT).as_posix(),'sha256':sha(video)},{'path':(OUT/'captions_measured.srt').relative_to(ROOT).as_posix(),'sha256':sha(OUT/'captions_measured.srt')}],
       'final_file':video.relative_to(EP).as_posix(),'final_sha256':sha(video),'SRT_file':(OUT/'captions_measured.srt').relative_to(EP).as_posix(),'SRT_sha256':sha(OUT/'captions_measured.srt'),'duration_s':float(r['ffprobe']['format']['duration']),'caption_cues':206,'resolution':[1920,1080],'fps':30,
       'affected_scene_ids':[x['scene_id'] for ch in p['chapters'] for x in ch['scenes']],
       'checks':[{'check':'source/current caption bounds and longest texts','result':'pass','evidence':'outputs/jun-production-v1/preview/bbox_report.json'},{'check':'pinned CLI','result':cli['status'],'evidence':'editor/jun-production-v1/checks/summary.json'},{'check':'actual MP4 AV decode','result':'pass','evidence':'editor/jun-production-v1/render_receipt.json'},{'check':'encoded signal','result':'measured; human review pending','evidence':'editor/jun-production-v1/signal_receipt.json'},{'check':'actual encoded sampled visuals','result':review['status'],'evidence':'editor/jun-production-v1/producer_visual_review.json'}],
       'encoded_frame_packet':'outputs/jun-production-v1/encoded_frame_plan.json','fullres_frames':len(files),'fresh_Jun_spectral_carve_ducking':True,'speech_boundaries':'outputs/jun-production-v1/speech_boundaries.json','EDL':'outputs/jun-production-v1/assembly_edl.json','scene_starts':'outputs/jun-production-v1/scene_starts.json','metadata_chapters':'outputs/jun-production-v1/metadata_chapters.txt','placement_guide':'editor/jun-production-v1/placement_guide.md',
       'open_issue_ids':['EXACT_FINAL_DUAL_MEDIA_REVIEW'],'actual_listening':False,'continuous_playback':False,'new_paid_calls_by_editor':0,'upload_performed':False,'delete_performed':False,'prior_versions_preserved':True,'next_role':'video_director → independent Codex and Claude exact-hash media QA → authorized private upload/replacement'}
    dump(HERE/'handoff.json',h)
    dump(OUT/'delivery_manifest.json',{'final_mp4_sha256':h['final_sha256'],'SRT_sha256':h['SRT_sha256'],'records_sha256':{f.relative_to(EP).as_posix():sha(f) for f in [HERE/'handoff.json',HERE/'render_receipt.json',HERE/'signal_receipt.json',OUT/'encoded_frame_plan.json',OUT/'input_manifest.json',OUT/'output_manifest.json']}})
    print(json.dumps({'status':h['status'],'duration_s':h['duration_s'],'final_file':h['final_file'],'sha256':h['final_sha256'],'frames':len(files)},ensure_ascii=False))
if __name__=='__main__':main()
