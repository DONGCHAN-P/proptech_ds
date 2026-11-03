"""Bind actual manually recorded visual coverage and independent measurements to one exact release."""
import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;E=Q.parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(4194304),b''):h.update(x)
 return h.hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def dump(n,d):(Q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 tech=read(Q/'final_technical_checks.json');visual=read(Q/'visual_review.json');source=read(Q/'source_release_review.json');audio=read(Q/'audio_review.json');waveform=read(Q/'encoded_voice_correspondence.json');findings=read(Q/'findings.json')
 assert source['status']=='pass' and audio['approved'] and waveform['status']=='pass'
 video=Path(tech['video']['path']);vh=sha(video);assert vh==tech['video']['sha256']==visual['video_sha256']==waveform['video_sha256']
 assert visual['actually_viewed'] and visual['all50_scene_representatives'] and visual['all50_scene_boundaries'] and visual['all12_assembly_joins'] and visual['all5_maximum_scale_samples'] and visual['all20_longest_caption_samples']
 assert {x['file']['path'] for x in tech['contact_sheets']} <= set(visual['viewed_sheet_paths'])
 for p in visual['viewed_sheet_paths']:assert Path(p).is_file()
 for k in ['SRT','metadata','description','thumbnail','EDL','timing']:assert sha(Path(source[k]['path']))==source[k]['sha256']
 for p in tech['expected_delivery_files']:assert p['exists'] and p['bytes']>0 and Path(p['path']).stat().st_size==p['bytes']
 assert all(p['resolved'] for p in tech['guide_reference_files']) and tech['placement_guide'] is not None
 assert tech['full_AV_decode']['returncode']==0 and not Path(tech['full_AV_decode']['log']['path']).read_text(encoding='utf-8').strip()
 required=[x for x in findings['findings'] if x['severity']=='required' and x['status'] not in ['closed_verified','not_applicable_to_selected_release']]+visual.get('required_issues',[])
 critical=[x for x in findings['findings'] if x['severity']=='critical' and x['status'] not in ['closed_verified','not_applicable_to_selected_release']]+visual.get('critical_issues',[])
 rec=[]
 for f in findings['findings']:
  if f['scene_id']=='TH004':f['status']='not_applicable_to_selected_release'
  elif f['severity']=='recommended':rec.append(f)
 approved=not required and not critical
 v=next(x for x in tech['probe']['streams'] if x['codec_type']=='video');a=next(x for x in tech['probe']['streams'] if x['codec_type']=='audio')
 d=dict(role='video_qa',revision='jun-production-v1-exact-final',approved=approved,status='pass_exact_final_with_recorded_scope' if approved else 'required_corrections_open',approval_scope='정확한 SHA의 새Jun 최종MP4/SRT/메타데이터/설명/선택TH003. 전체AV기술decode·신호·소스206큐 및 명시한 실제인코딩 표본 검수. 실제청취·연속재생·음성자연스러움은 미확인.',checked_at=datetime.now(timezone.utc).isoformat(),required_issues=required,critical_issues=critical,recommended_issues=rec,script_sha256=audio['script_sha256'],video_sha256=vh,subtitles_sha256=source['SRT']['sha256'],metadata_sha256=source['metadata']['sha256'],description_sha256=source['description']['sha256'],thumbnail_sha256=source['thumbnail']['sha256'],narration_timing_sha256=source['timing']['sha256'],body_audio_sha256=audio['audio_sha256'],edl_sha256=source['EDL']['sha256'],burned_in_captions_verified=visual['burned_in_captions_verified'],burned_in_captions_verification_scope='전체206 source/SRT 의미단위·네이티브시각·표시경계와 실제MP4의 장면/경계/최장자막 표본. 전체206큐를 연속재생으로 보았다는 뜻 아님.',artifacts=dict(video=pin(video),script=pin(E/'outputs/script-final-v6/script_v6.md'),subtitles=source['SRT'],metadata=source['metadata'],description=source['description'],thumbnail=source['thumbnail'],EDL=source['EDL'],timing=source['timing'],guide=tech['placement_guide']),video_bytes=video.stat().st_size,duration_s=float(tech['probe']['format']['duration']),resolution=[v['width'],v['height']],fps=30,video_codec=v['codec_name'],audio_codec=a['codec_name'],audio_sample_rate=int(a['sample_rate']),audio_channels=a['channels'],coverage=dict(actual_listening=False,continuous_playback=False,full_video_and_audio_decode=True,technical_decode_covers_entire_final_MP4=True,full_audio_signal_measurement=True,source_text_native_cues_checked=206,source_scene_count=50,all206_encoded_cues_visually_watched=False,all_frames_continuously_watched=False,raw_54paragraph_PCM_verified=True,source_caption_BBox='제작 담당 current source SHA 핀 확인 후 기존 새Jun DOM metrics 재사용; QA가 DOM측정 재실행했다고 주장하지 않음',frozen_visual_financial_inputs_reused_after_SHA_checks=True,financial_model_recalculated=False,actual_ASR_unique_paragraphs=34,actual_ASR_runs=47,ASR_models=['Whisper-small','Whisper-medium','Vosk-small-ko-0.22'],ASR_references_or_hotwords=False,encoded_waveform_correspondence_chapters=10,encoded_waveform_sample_seconds=80,thumbnail_asset_id='TH003',thumbnail_original_and320px_viewed=True,metadata_description_full_text_read=True,expected_delivery_file_count=len(tech['expected_delivery_files']),guide_references_verified=True,ZIP_integrity='not_applicable_no_ZIP_requested',Studio_Checked=False,ContentID_Checked=False,upload_performed=False,delete_performed=False,separate_Claude_final_media_review='별도 총괄 게이트; 이 판정으로 대체하지 않음',**visual['coverage']),technical_evidence=pin(Q/'final_technical_checks.json'),visual_evidence=pin(Q/'visual_review.json'),source_release_evidence=pin(Q/'source_release_review.json'),audio_evidence=pin(Q/'audio_review.json'),encoded_waveform_evidence=pin(Q/'encoded_voice_correspondence.json'),actual_listening=False,continuous_playback=False,write_scope='qa/jun-production-v1 only')
 dump('final_review.json',d);findings.update(checked_revision='jun-production-v1 / '+vh,required_issues=required,critical_issues=critical,pending_checks=['실제청취·연속재생 미확인; 별도 Claude 최종리뷰는 총괄 담당']);dump('findings.json',findings)
 dump('handoff.json',dict(status=d['status'],approved=approved,outputs=[pin(Q/'final_review.json'),pin(Q/'findings.json'),pin(Q/'audio_review.json'),pin(Q/'source_release_review.json'),pin(Q/'visual_review.json'),pin(Q/'final_technical_checks.json'),pin(Q/'encoded_voice_correspondence.json')],input_versions=dict(script_sha256=d['script_sha256'],video_sha256=vh,timing_sha256=d['narration_timing_sha256'],thumbnail_asset_id='TH003'),validation='실제새Jun 최종MP4 전체AVdecode·신호,206큐+50장면소스/SRT,인코딩장면/경계/최대확대/최장문장 표본,10장파형대응,출시파일/가이드 확인.',unresolved=['실제청취·연속재생 미확인','202만원 Whisper/Vosk 인식차 비차단권장 기록 유지','총괄의 별도Claude exact-final 검수'],required_issues=required,critical_issues=critical,affected_scenes=['C01','C02','C03','C04','C05','C06','C07','C08','C09','C10','TH003'],next_owner='video_director',actual_listening=False,continuous_playback=False,upload_performed=False,delete_performed=False))
 print(json.dumps(dict(approved=approved,video_sha256=vh,required_issues=required,critical_issues=critical,duration_s=d['duration_s'],file=str(Q/'final_review.json')),ensure_ascii=False))
if __name__=='__main__':main()
