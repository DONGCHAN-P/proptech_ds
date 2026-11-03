from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
from PIL import Image

ROOT=Path('C:/projects/realestate_reco')
HERE=Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p): return Path(p).relative_to(ROOT).as_posix()
ledger=read(HERE/'assets.json')
all_assets=ledger['assets']+ledger['optional_assets']
checks=[]
for a in all_assets:
    p=ROOT/a['actual_file']
    with Image.open(p) as im:
        im.load()
        assert list(im.size)==a['dimensions']
        if a['media_kind']=='chapter_still': assert im.size==(1920,1080)
        else: assert im.mode=='RGBA' and im.getchannel('A').getextrema()[0]==0
    assert sha(p)==a['sha256']
    assert not a['screenbadge'] and not a['screen_AI_badge']
    checks.append({'asset_id':a['asset_id'],'path':a['actual_file'],'sha256':a['sha256'],'dimensions':a['dimensions'],'decoded':True})
    if a['media_kind']=='chapter_still':
        a['review_status']='passed_visual_self_review_final_size_contact_and_source_view'
        a['review_evidence']='review/chapter_contact.png; representative CH01/CH06 full-size title proofs'
        a['review_notes']='배경에는 제목·번호 없음. 장마다 다른 완성 사진. 인물·졸라맨·가족정책 없음. 제목 공간 및 재단 확인. 실제 MP4 통합 검수는 편집/QA 담당.'
    else:
        a['review_status']='passed_visual_alpha_composites_ivory_and_navy_at_560px_max'
        a['review_evidence']='review/cutout_alpha_contact.png'
        a['recommended_max_display_width_px']=560
        a['usage_conditions']='560px 이하 보조 조각으로 사용. 동일 집 표식은 항상 같은 크기로, 노트 위 실제 금액·세 입력칸은 별도 편집 레이어. 실제 주택·평형·공식 서류의 근거 아님.'
assert len(set(a['sha256'] for a in ledger['assets']))==7
scenes=[s for a in ledger['assets'] for s in a['scene_ids']]
assert scenes==[f'S{i:02d}' for i in range(1,32)]
ledger['status']='ready_for_editor_integration'
ledger['visual_QA_scope']='제작자 자체 이미지/여백/알파 검수 완료. 독립 영상 QA·오디오 검수는 포함하지 않음.'
save(HERE/'assets.json',ledger)

review={'status':'passed_asset_packet_self_review','performed_at_utc':datetime.now(timezone.utc).isoformat(),
    'task_id':'FULL-JUN-US1-ASSETS',
    'visual_observations':{'source_reuse_candidates_viewed':5,'built_in_generation_edit_outputs_viewed':6,
      'final_chapters_contact_viewed':7,'full_size_title_proofs_viewed':['CH01','CH06'],
      'optional_alpha_composites_viewed':'2assets on ivory and navy, 560px display width',
      'title_space_readability':'navy on light CH01/04/06; white on dark CH02/03/05/07',
      'people_detected':False,'generated_text_numbers_logos_detected_in_final_backgrounds':False,
      'same_complete_photo_in_different_chapters':False,'newborn_family_policy_assets_used':False,
      'framing':'No material new crop from resize. CH01 calculator has intentional source-edge crop, no extra zoom. Generic Korean skyline in CH05/07 is atmosphere only.'},
    'technical_checks':checks,'all_7_chapters_1920x1080':True,'scene_coverage_31':True,
    'review_images':['review/chapter_contact.png','review/representative_CH01_title_proof.png','review/representative_CH06_title_proof.png','review/cutout_alpha_contact.png'],
    'proof_font':'Malgun Gothic for QA overlay only; final editor titles use approved Pretendard. Review proofs are not production backgrounds.',
    'independent_review':False,'actual_audio_listening':False,'continuous_video_playback':False,
    'final_encoded_video_review':False,'required_asset_issues_open':0,
    'next_checks':'편집자가 최종 Pretendard 글자 경계·흰 자막 rail·모든 컷·발화 타이밍을 실제 MP4로 확인하고 독립 QA에 연결.'}
save(HERE/'review/visual_review.json',review)

editor={'task_id':'FULL-JUN-US1-ASSETS','status':'ready_for_editor_integration','editor':'Newton 01a17db2-40c1-7f73-a24b-236c89fd9d92',
    'chapter_assets':[{'asset_id':a['asset_id'],'before_scene_id':a['chapter_insert_before_scene'],
      'scene_ids':a['scene_ids'],'title':a['title_overlay'],'file':a['absolute_file'],'sha256':a['sha256'],
      'dimensions':a['dimensions'],'title_safe_box_1920':a['title_safe_box_1920'],'title_color':a['title_color'],'screenbadge':False} for a in ledger['assets']],
    'optional_cutouts':[{'asset_id':a['asset_id'],'scene_ids':a['scene_ids'],'file':a['absolute_file'],'sha256':a['sha256'],
      'dimensions':a['dimensions'],'max_display_width_px':560,'purpose':a['purpose']} for a in ledger['optional_assets']],
    'brand_audio_refs':str(HERE/'brand_audio_refs.json'),
    'integration_notes':['outputs/*.png are clean backgrounds. review/*.png include QA overlay text and must not be used as final backgrounds.',
      'CH cards are distinct inserts before S01/S04/S08/S13/S18/S22/S27; 2.5~3s is only a guide, parent actual Jun edit schedule governs.',
      'Keep same-size house marker across price comparisons; photo atmosphere does not replace data bars/receipt/timelines.',
      'CH07 photo opens living/location choice. S28 and final CTA use code-native three budget fields plus optional notebook, not another full-photo reuse.',
      'Titles/numbers in separate Pretendard layers; no AI screen badge. Static preferred; a zoomed still clip must be labeled still_motion.',
      'Use existing clean brand/BGM refs only. Last actual spoken word +3seconds includes existing tail silence. No visual worker audio changes.']}
save(HERE/'editor_asset_packet.json',editor)

issue={'issue_id':'FULL-JUN-US1-ASSETS-READY','task_id':'FULL-JUN-US1-ASSETS','type':'handoff_delivery_fallback',
    'scene_ids':[f'S{i:02d}' for i in range(1,32)],'recipients':['총괄','Newton 01a17db2-40c1-7f73-a24b-236c89fd9d92'],
    'problem':'현재 세션에 에이전트 직접 메시지 도구가 노출되지 않아 편집자 직접 알림 전송을 실행할 수 없음.',
    'evidence':'노출 도구 이름에서 send_input/send_message/spawn_agent 탐색 결과 없음. 사용자 소유 다른 채팅으로 대체하지 않음.',
    'proposal':'총괄이 이 파일 또는 editor_asset_packet.json 경로를 편집자에게 전달.',
    'impact':'제작 에셋은 준비됨. 직접 알림 전달 여부만 미확인.',
    'paths':{'ledger':str(HERE/'assets.json'),'editor_packet':str(HERE/'editor_asset_packet.json'),
      'images':str(HERE/'outputs'),'brand_audio_refs':str(HERE/'brand_audio_refs.json')},
    'sent_to_editor':False,'requires_user_permission':False}
save(HERE/'issue_FULL-JUN-US1-ASSETS-READY.json',issue)

handoff={'task_id':'FULL-JUN-US1-ASSETS','status':'assets_ready','summary':'7개 장별 1920×1080 PNG와 집·빈 예산 노트 투명 PNG 2개 준비. 사진 3개 재사용·2개 무문자 정리·2개 신규. 실제 파일·SHA·크기·용도·출처·프롬프트·AI 내부 기록 완료, 화면 배지 false. 최종 크기 컨택트·CH01/06 대표 구도·여백·두 배경 알파 합성 자체 검수 통과. 브랜드·BGM 승인 해시 3개 일치. 직접 메시지 도구가 없어 편집자 알림은 총괄 전달 필요.',
    'outputs':['assets.json','editor_asset_packet.json','brand_audio_refs.json','review/visual_review.json','outputs/'],
    'input_versions':'production_brief.json input_versions 참조; source DOCX f28deb75e0a271e30e3d29dbe52291ef30e28b0ef0bfc2648ad98bbd652e6a73; scene plan user-recording-guide-v1-r2',
    'validation':'PNG 9개 decode·SHA·크기, 7장 고유성/31장면 연결, 투명 알파, 기존 브랜드/BGM SHA·probe 확인.',
    'unresolved':['직접 알림 도구 없음: issue_FULL-JUN-US1-ASSETS-READY.json을 편집자에게 전달.'],
    'affected_scene_ids':'S01~S31','next_owner':'Newton 01a17db2-40c1-7f73-a24b-236c89fd9d92 / 총괄',
    'limitations':'이미지 자체 검수 범위. 독립 영상 QA·최종 MP4·실제 청취·연속 재생 미수행. 음성/오디오 변경 없음. 외부 유료 API·계정 자료 사용 없음.'}
save(HERE/'handoff.json',handoff)

manifest=[]
for p in sorted(HERE.rglob('*')):
    if p.is_file() and p.name!='packet_files.json':
        manifest.append({'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size})
save(HERE/'packet_files.json',{'task_id':'FULL-JUN-US1-ASSETS','files':manifest})
print(json.dumps({'status':'ready','chapters':len(ledger['assets']),'optional_cutouts':len(ledger['optional_assets']),
    'ledger':rel(HERE/'assets.json'),'handoff':rel(HERE/'handoff.json'),
    'direct_editor_message_sent':False,'required_asset_issues_open':0,'manifest_files':len(manifest)},ensure_ascii=False))
