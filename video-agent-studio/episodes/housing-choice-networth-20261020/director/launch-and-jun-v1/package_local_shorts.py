"""Expose exact local review files without changing publication or pending permissions."""
import hashlib,json,os,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

assert os.path.samefile(ROOT/'영상/매매전월세/영상.mp4',EP/'outputs/jun-production-v1/renders/measured-jun-v1/housing_choice_jun_v1.mp4')
shelf_path=ROOT/'config/video_shelf.json';shelf=read(shelf_path)
entry=next(x for x in shelf['entries'] if x['name']=='매매전월세')
for alias,source in {
    '쇼츠_유입_검토본.mp4':'outputs/shorts-jun-v2/funnel/renders/housing_choice_funnel_jun_v2.mp4',
    '쇼츠_요약_검토본.mp4':'outputs/shorts-jun-v2/analysis/renders/housing_choice_analysis_jun_v2.mp4',
    '쇼츠_유입.srt':'outputs/shorts-jun-v2/funnel/captions.srt',
    '쇼츠_요약.srt':'outputs/shorts-jun-v2/analysis/captions.srt',
    '쇼츠_로컬검수.json':'qa/shorts-jun-v1/final_review.json',
    '쇼츠_제작안내.md':'editor/shorts-jun-v2/placement_guide.md',
}.items():
    source_path=EP/source;assert source_path.is_file();entry['files'][alias]=source_path.relative_to(ROOT).as_posix()
write(shelf_path,shelf)
state_path=EP/'state.json';state=read(state_path)
state['shorts_jun_v1'].update(status='two_v2_videos_rendered_independent_Codex_pass_Claude_payload_permission_pending',
    editor_sources='outputs/shorts-jun-v2',final_render_executed=True,
    independent_source_review='passed_with_2_recommendations_resolved_in_v2',
    independent_final_review='qa/shorts-jun-v1/final_review.json',source_text_bbox_checks=1271,source_bbox_failures=0,
    final_videos=['outputs/shorts-jun-v2/funnel/renders/housing_choice_funnel_jun_v2.mp4','outputs/shorts-jun-v2/analysis/renders/housing_choice_analysis_jun_v2.mp4'],
    youtube_upload_executed=False,Claude_payload_question_pending=True)
write(state_path,state)

# Windows PowerShell's legacy native-pipe encoding damaged a quote in the local record.
# Preserve that record and restore the actual conversation reply; consent itself is unchanged.
authorization_path=HERE/'claude_payload_authorization.json';authorization=read(authorization_path)
if authorization.get('user_quote')!='이 자료 묶음의 Claude 전송 승인':
    backup=HERE/'claude_payload_authorization.original-encoding.json'
    assert not backup.exists();shutil.copyfile(authorization_path,backup)
    authorization['user_quote']='이 자료 묶음의 Claude 전송 승인'
    authorization['record_encoding_correction']={
        'basis':'Exact explicit user reply to questionItemId call_bc05f69d567e45be9b04c2a4fd7c269b; no new permission inferred.',
        'previous_record':backup.name,'previous_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),
        'scope_or_payload_changed':False}
    write(authorization_path,authorization)
print(json.dumps({'main_alias_same_file':True,'Shorts_review_aliases_added':6,'publication_changed':False,'new_TTS_calls':0}))
