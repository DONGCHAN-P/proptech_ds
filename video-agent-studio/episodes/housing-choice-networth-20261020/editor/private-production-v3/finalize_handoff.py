"""Finalize caption-only delivery after render, full decode and encoded-frame extraction."""
import argparse,hashlib,json,os,shutil
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2];OUT=EP/'outputs/private-production-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
parser=argparse.ArgumentParser();parser.add_argument('--reviewed-scenes',default='');args=parser.parse_args()
r=read(HERE/'render_receipt.json');plan=read(OUT/'render_plan.json');e=read(OUT/'encoded_frame_plan.json');build=read(HERE/'build_receipt.json')
video=Path(r['final_file']);assert r['decode_returncode']==0 and sha(video)==r['final_sha256'] and r['audio_stream_identical_to_v2']
prior=read(EP/'editor/private-production-v2/render_receipt.json')
old_audio=next(s for s in prior['ffprobe']['streams'] if s['codec_type']=='audio');new_audio=next(s for s in r['ffprobe']['streams'] if s['codec_type']=='audio')
audio_keys=['codec_name','sample_rate','channels','channel_layout','start_pts','start_time','time_base','duration_ts','nb_frames']
assert all(old_audio.get(k)==new_audio.get(k) for k in audio_keys),'AAC timing metadata differs from preserved v2'
dump(HERE/'audio_identity_receipt.json',{'status':'encoded_AAC_payload_and_stream_timing_identical','AAC_payload_SHA256':r['audio_stream_SHA256'],'source_MP4_sha256':prior['final_sha256'],'final_MP4_sha256':r['final_sha256'],'stream_metadata':{k:new_audio.get(k) for k in audio_keys},'new_audio_processing':False,'actual_listening':False})
assert e['final_sha256']==r['final_sha256']
files={row['file']:row['sha256'] for row in e['samples']}
for rel,expected in files.items():
    p=OUT/rel;assert sha(p)==expected
    with Image.open(p) as im:assert im.size==(1920,1080)
reviewed=[]
for scene in filter(None,args.reviewed_scenes.split(',')):
    row=next(x for x in e['samples'] if x['scene_id']==scene and x['role']=='representative')
    cue=next(c for c in read(OUT/f'ch{row["chapter"]:02d}/timing.json')['cues'] if c['start_s']<=row['local_frame']/30<c['end_s'])
    reviewed.append({**{k:row[k] for k in ['scene_id','file','sha256','global_time_s']},'cue_id':cue['id'],'cue_text':cue['text']})
dump(HERE/'producer_caption_review.json',{'scope':'actual final encoded changed-cue samples only','frames_actually_viewed':reviewed,'all_changed_cues_visually_reviewed':False,'actual_listening':False,'continuous_playback':False,'independent_final_QA':'pending main/QA'})
plan.update(full_rendered=True,final_mp4=video.relative_to(EP).as_posix(),final_sha256=sha(video),captions_sha256=sha(OUT/'captions_measured.srt'),pending=['main/QA exact-final media review and private-release gate'])
dump(OUT/'render_plan.json',plan)
links=''.join(f'<li><a href="ch{n:02d}/index.html">CH{n:02d}</a></li>' for n in range(1,11))
(OUT/'index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>의미 단위 자막 v7</title><body><h1>자막 v7 검토</h1><p>기존 대본·음성·화면 연출을 보존한 자막 수정본입니다. 최종 미디어 승인은 별도입니다.</p><a href="renders/caption-v7/housing_choice_private_v3_caption_v7.mp4">본편 MP4</a> · <a href="captions_measured.srt">자막 SRT</a> · <a href="encoded_frame_plan.json">실제 프레임 패킷</a><ol>'+links+'</ol></body></html>',encoding='utf8')
shutil.copy2(EP/'editor/private-production-v2/music_credit.txt',HERE/'music_credit.txt')
guide=['# 의미 단위 자막 v7 배치 가이드','',f'실제 파일: `{video.relative_to(EP).as_posix()}`. {float(r["ffprobe"]["format"]["duration"]):.6f}초, 1920×1080·30fps·H.264/AAC 48kHz stereo. 전체 decode 통과.','',
       '추천 배포 파일은 본편 MP4와 `outputs/private-production-v3/captions_measured.srt`다. 206큐의 명시적 1~2줄 자막을 사용하며 Pretendard 40px·줄 높이 50px·흰 박스 1728×124와 출처 분리 레이어를 유지했다.','',
       '자막 외 DOM·GSAP·장면·기존 T 앵커·그림·폰트·오디오 태그·자산은 v2와 같다. 모든 장의 자막 HTML이 변경돼 10장을 재렌더했다. 최종 음성은 v2 완성본의 AAC 스트림을 재인코딩 없이 복사했고 encoded-payload SHA 일치가 확인됐다. 기존 carve·브랜드 접합 fade가 그대로 유지된다.','',
       '50장면의 추천 대표 시간·길이·레이어별 근거는 `render_plan.json`, 브랜드 전환·global offset은 `assembly_edl.json`, 변경 50그룹의 native 자막 구간은 `cue_change_groups.json`에 있다. `encoded_frame_plan.json`은 일반 50장면·경계·기존 시각 QA 타깃의 PNG와 SHA를 연결한다. 추가 자막 타깃 추출은 main/build_caption_v7_review_packet.py 담당이다.','',
       '자료 유형은 기존 data_chart/editorial_diagram/생활 계획 그림을 계승한다. 새로운 지도·줌·이미지·음성은 생성하지 않았다. 실제 청취·연속 재생·독립 최종 미디어 승인은 main/QA 후속이며 업로드는 수행하지 않았다.']
(HERE/'placement_guide.md').write_text('\n'.join(guide)+'\n',encoding='utf8')
input_manifest=read(OUT/'input_manifest.json')
for p in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs')):input_manifest['inputs_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
for rel in ['qa/private-production-v1/source_v7_pass_receipt.json','director/two-episode-production-v1/edl_review_v7.json']:
    p=EP/rel;input_manifest['inputs_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
dump(OUT/'input_manifest.json',input_manifest)
outputs={}
for directory,dirs,names in os.walk(OUT):
    dirs[:]=[d for d in dirs if d not in ['preview','preview_captions','renders','.hyperframes','node_modules','audio-deps','ffmpeg-deps','media-bin']]
    for name in names:
        p=Path(directory)/name
        if name not in ['input_manifest.json','output_manifest.json','delivery_manifest.json']:outputs[p.relative_to(OUT).as_posix()]=sha(p)
dump(OUT/'output_manifest.json',outputs)
handoff={'role':'editor','status':'caption_v7_render_complete_decode_pass_final_media_QA_pending','script_sha256':plan['script_sha256'],'caption_timing_sha256':plan['caption_timing_sha256'],
         'final_file':video.relative_to(EP).as_posix(),'final_sha256':sha(video),'SRT_file':'outputs/private-production-v3/captions_measured.srt','SRT_sha256':sha(OUT/'captions_measured.srt'),
         'duration_s':float(r['ffprobe']['format']['duration']),'caption_cues':build['cue_count'],'resolution':[1920,1080],'fps':30,'full_decode':'pass','prior_audio_stream_identical':True,'AAC_payload_SHA256':r['audio_stream_SHA256'],
         'visual_audio_reuse_manifest':'editor/private-production-v3/visual_audio_reuse_manifest.json','audio_identity_receipt':'editor/private-production-v3/audio_identity_receipt.json','encoded_frame_packet':'outputs/private-production-v3/encoded_frame_plan.json','source_changed_groups':build['changed_groups'],'additional_encoded_caption_targets_owner':'main/build_caption_v7_review_packet.py','fullres_frames':len(files),
         'prior_versions_preserved':True,'actual_listening':False,'continuous_playback':False,'new_paid_calls':0,'upload_performed':False,'open':['main/QA final exact MP4/SRT approvals'],'next_owner':'main / video_qa for final target-caption frames and private release gate'}
dump(HERE/'handoff.json',handoff)
dump(OUT/'delivery_manifest.json',{'final_mp4':{'file':handoff['final_file'],'sha256':handoff['final_sha256']},'SRT_sha256':handoff['SRT_sha256'],'records_sha256':{p.relative_to(EP).as_posix():sha(p) for p in [HERE/'handoff.json',HERE/'render_receipt.json',OUT/'encoded_frame_plan.json',OUT/'input_manifest.json',OUT/'output_manifest.json']},'tooling_dependency_trees_excluded':True})
print(json.dumps(handoff,ensure_ascii=False))
