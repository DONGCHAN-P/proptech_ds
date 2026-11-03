"""Publish local artifact manifests only; never upload or send externally."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_native_v3 as b


def collect(sid):
    project=b.HERE/'native-v3'/sid
    render=b.read(project/'render_receipt.json')
    technical=b.read(project/'technical_check.json')
    if technical['status']!='technical_checks_passed':raise ValueError(f'Technical checks pending: {sid}')
    video=Path(render['video'])
    if b.sha(video)!=render['video_sha256']:raise ValueError('Final MP4 hash differs')
    stem=video.stem
    b.cp(project/'captions.srt',b.OUT/f'{stem}.srt')
    b.cp(project/'credits_manifest.json',b.OUT/f'{stem}.credits.json')
    b.cp(project/'render_receipt.json',b.OUT/f'{stem}.render_receipt.json')
    b.cp(project/'technical_check.json',b.OUT/f'{stem}.technical_check.json')
    credits=b.read(project/'credits_manifest.json')
    desc=[b.read(b.WRITER/b.PLANFILES[sid])['title'],'',
          '신혼부부 거주 수: 2024.11.01, 수도권 53개 구 기준.',
          '아파트 가격: 전용 83~85㎡, 2026.05~10 계약, 2026.11.03 조회·취소 제외. 10월은 조회일까지의 신고분입니다.',
          '과거 거래 표본의 비교이며 현재 매물의 구매 가능 가격이 아닙니다.',
          '20~11위 전체의 자세한 가격과 생활권 비교는 본편에서 이어집니다.',
          '다른 순위 영상·본편 실제 링크는 게시 상태 확인 후 연결합니다.','',
          '사진 출처 및 이용조건(세로 크롭·정지사진 배경 확대 적용):']
    for photo in credits['photos']:
        desc.extend([f'{photo["region_id"]} {photo["actual_place"]} | {photo["author"]} | {photo["license_name"]} | {photo["photo_date"]}',photo['source_url'],photo['license_url']])
    desc.extend(['','음악:',credits['music']['credit'],credits['music']['url'],credits['music']['license_url']])
    b.write(b.OUT/f'{stem}.description.txt','\n'.join(desc)+'\n')
    row={'short_id':sid,'video':str(video),'video_sha256':render['video_sha256'],'video_bytes':video.stat().st_size,
         'duration_s':technical['duration_s'],'resolution':[1080,1920],'fps':30,'master_audio_sha256':render['master_audio_sha256'],
         'project':str(project),'input_manifest':str(project/'input_manifest.json'),'input_manifest_sha256':b.sha(project/'input_manifest.json'),
         'render_receipt':str(project/'render_receipt.json'),'technical_check':str(project/'technical_check.json'),
         'proof_frames':str(project/'encoded_proofs.json'),'end_fix_verification':str(project/'caption_visibility_checks.json'),
         'subtitles':str(b.OUT/f'{stem}.srt'),'credits':str(b.OUT/f'{stem}.credits.json'),
         'actual_listening':False,'continuous_playback':False,'independent_QA':'director/QA to review encoded artifacts'}
    b.save(project/'handoff.json',{'task_id':'3-native-vertical-shorts-Jun-v1','owner':'shorts-editor','status':'rendered_technical_checks_passed_encoded_QA_pending',
           'artifact':row,'input_version':'director actual_Jun_reuse_locked + native-v3 cue-owned background/text visibility caption rail fix',
           'unresolved':['Independent encoded audiovisual QA pending; no actual listening/continuous viewing claimed'],
           'changed_scene_ids':[sid+'-CTA'],'next_owner':'director + independent QA'})
    return row


if __name__=='__main__':
    ids=sys.argv[1:]or b.IDS
    rows=[collect(sid)for sid in ids]
    if ids==b.IDS:
        manifest={'task_id':'3-native-vertical-shorts-Jun-v1','version':'native-v3','status':'three_mp4s_technical_checks_passed_independent_QA_pending',
                  'artifacts':rows,'scope':'Only assigned editor/shorts and outputs/shorts modified',
                  'safe_profile':'youtube_portrait_full_frame_v2','input_data_and_audio_unchanged':True,
                  'paid_or_TTS_or_API_calls':0,'uploads':0,'placement_guide':str(b.HERE/'placement_guide.md'),
                  'actual_listening':False,'continuous_playback':False}
        b.save(b.OUT/'shorts_delivery_manifest.json',manifest)
        b.save(b.HERE/'handoff.json',{'task_id':manifest['task_id'],'status':manifest['status'],'output_manifest':str(b.OUT/'shorts_delivery_manifest.json'),
               'outputs':[r['video']for r in rows],'input_versions':[{'short_id':r['short_id'],'input_manifest_sha256':r['input_manifest_sha256'],'master_audio_sha256':r['master_audio_sha256']}for r in rows],
               'validation':'MP4 probe, full A/V decode, locked master/AAC PCM correlation, encoded proof frames; native-v3 cue-owned background/text visibility source checks. Unchanged geometry/22 anchors/84 cues reused from approved source QA.',
               'unresolved':['Independent encoded QA incl. actual listening/continuous playback remains with director/QA.'],
               'affected_scenes':[s+'-CTA'for s in b.IDS],'next_owner':'director + independent QA'})
    print(json.dumps(rows,ensure_ascii=False),flush=True)
