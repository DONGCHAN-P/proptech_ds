"""독립 픽셀 검수 후 호출하는 보고서 기록기. 자동 시각/청취 판정 도구 아님."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

Q = Path(__file__).resolve().parent
EP = Q.parents[2]
ROOT = EP.parents[2]
IDS = ['SHORT01-PROMO','SHORT02-R20-R16','SHORT03-R15-R11']


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--short', choices=IDS, required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--fullres', default='')
    parser.add_argument('--ui', default='1')
    parser.add_argument('--contacts-perceived', action='store_true', required=True)
    args=parser.parse_args()
    sid=args.short
    h=EP/'editor/top20-split-v4/jun-and-shorts-v1/shorts/native-v4'/sid
    m=read(Q/'encoded'/f'{sid}-v4'/'encoded_manifest.json')
    rec=read(h/'render_receipt.json')
    tech=read(h/'technical_check.json')
    actual=sha(Path(m['video']))
    assert actual==m['video_sha256']==rec['video_sha256']==tech['video_sha256']==args.expected_sha
    assert m['status']=='passed' and tech['decode_exit_code']==0 and all(tech['checks'].values())
    assert all(sha(Path(x['file']))==x['sha256'] for x in m['frames'])
    source=read(Q/'note_cleanup_v4_source_review.json')
    assert next(x for x in source['shorts'] if x['short_id']==sid)['passed']
    visibility=read(Q/'caption_visibility_v3_source_review.json')
    assert next(x for x in visibility['shorts'] if x['short_id']==sid)['passed']
    assert m['minimum_audio_correlation']>.999 and m['peak_pcm']<32767
    ffprobe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
    p=subprocess.run([str(ffprobe),'-v','error','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,pix_fmt,sample_rate,channels:format=duration,size','-of','json',m['video']],capture_output=True,creationflags=0x08000000)
    assert p.returncode==0
    probe=json.loads(p.stdout)
    owntech={'asset_id':sid,'revision':'native-v4','video_sha256':actual,'independent_probe':probe,'full_file_hash_verified':True,'all_sample_hashes_verified':True,'editor_technical_check':tech,'actual_listening':False,'actual_hearing':False,'continuous_playback':False}
    save(Q/(sid+'_v4_technical_verification.json'),owntech)
    full=[int(x) for x in args.fullres.split(',') if x]
    ui=[int(x) for x in args.ui.split(',') if x]
    notes=next(x for x in source['shorts'] if x['short_id']==sid)['changed_notes']
    result={'status':'passed_for_local_review','asset_id':sid,'checked_revision':'native-v4','video':m['video'],'video_sha256':actual,
      'required_open_count':0,'critical_open_count':0,'recommended_open_count':1,
      'closed_issue_ids':['JUN-CAPTION-RAIL-01-'+sid,'JUN-CUE-RAIL-02-'+sid,'JUN-SHORT-NOTE-03-'+sid],
      'technical':{'independent_probe':probe,'video_sha256_independently_verified':True,'all_sample_hashes_verified':True,'full_AV_decode':'편집 담당의 실제 전체 디코드 종료0·필수 기술 검사 전항목 통과 근거 확인; 독립 중복 디코드는 하지 않음.','detail_report':sid+'_v4_technical_verification.json'},
      'coverage':{'actual_sampled_frame_count':m['sample_count'],'sampled_frames':m['frames'],'contact_sheets_actually_viewed':m['contacts'],'full_resolution_frame_ids_actually_viewed':full,'UI_mockups_actually_viewed':[m['UI_mockups'][i] for i in ui],'limits':'표본 프레임과 YouTube UI 모사 검사. 실제 단말/전체 연속 재생이 아님.','actual_listening':False,'actual_hearing':False,'continuous_playback':False},
      'visual_checks':{'forbidden_note_suffix':'실제 표본에서 현재 매물 아님/현재 매물 가격 아님 접미 제거 확인. 조회일까지 신고분·출처 조건 유지.','changed_notes':notes,'inactive_caption_rail':'도입·자연 쉼·장면 경계·마지막 유지 표본에서 빈 박스 없음. 활성 큐는 글자와 박스 함께 표시.','held_text_and_sources':'기존 본문/가격/조건/출처 배치와 활성 자막 가독성 유지. 표본에서 새 잘림/충돌 미관찰.','native_numeric_events':'이미 통과한22개 가격/수치 native 앵커 및 동결 가격/표본/기간 근거 재사용.','five_rank_ledger':'순위 쇼츠는5개 행이 첫 상태·전환·CTA까지 유지. 홍보 쇼츠는53개구/20~11위 범위·연수구 대비 확인.','phone_UI':'검토한1080x1920 YouTube 모사에서 핵심 글자 영역 가림 미관찰. 모든 단말/확장 UI 보장은 아님.'},
      'source_review_reuse':{'changed_note_only':'note_cleanup_v4_source_review.json:14곳 접미만 삭제,26px glyph 안전영역 통과,자막/음성락 불변.','changed_caption_group':'caption_visibility_v3_source_review.json:84큐/357시점 글자·박스 visibility 일치. v4 자막그룹 HTML/CSS 동일 확인.','original_layout':'shorts_layout_review.json:4820glyph/22numeric anchors 안전영역·충돌·native 타이밍 통과.','frozen_facts':'shorts_source_integrity_review.json:84큐와70동결 비교항목 일치.','cuts_PCM':'shorts_cut_caption_review.json:31원음클립 exact PCM·이전/다음 발화 guard·숫자단위 보호 통과.','targeted_new_Jun_ASR':'ASR_support_review.json의23문장 표적 전사만 보조근거로 재사용. 새 ASR/TTS 실행 없음.'},
      'audio_evidence':{'native_master_audio_sha256':rec['master_audio_sha256'],'native_sentence_window_count':len(m['audio_windows']),'native_AAC_windows':m['audio_windows'],'minimum_native_AAC_correlation':m['minimum_audio_correlation'],'peak_pcm':m['peak_pcm'],'full_mono_native_master_correlation':tech['audio_integrity']['decoded_pcm_correlation'],'limits':'스트림·PCM·파형·제공자 정렬 검사는 실제 청취나 발음 자연스러움 평가가 아님.'},
      'input_versions':{'lock_sha256':m['lock_sha256'],'source_project':str(h),'source_input_manifest_sha256':rec['input_manifest_sha256'],'voice':'승인 Jun native097, 기존 main 재사용+공유 CTA, 새 음성 생성 없음.'},
      'recommended':[{'issue_id':'JUN-ACTUAL-LISTENING-UNCHECKED','status':'unchecked','note':'실제 청취/연속 재생 미수행. 발음·호흡·BGM 체감과 전체 모션 자연스러움은 로컬 검토 범위.'}],
      'actual_listening':False,'actual_hearing':False,'continuous_playback':False,'scope':'해당 native-v4 쇼츠 로컬 검토 통과. 게시/외부 전송 승인 아님.'}
    path=Q/(sid+'_final_review.json')
    if path.exists():
        old=read(path)
        ver=old.get('checked_revision','').split('-')[-1]
        archive=Q/(sid+'_final_review_'+ver+'.json')
        if not archive.exists():save(archive,old)
    save(path,result)
    save(Q/(sid+'_final_review_v4.json'),result)
    f=read(Q/'findings.json')
    for item in f['findings']:
        if item['issue_id'] in result['closed_issue_ids']:
            item.update(status='closed_actual_native_v4_verified',checked_revision='native-v4 / '+actual)
            item['evidence']=[sid+'_final_review.json',f'encoded/{sid}-v4/encoded_manifest.json']
            item['resolution']='최종 실제 표본에서 금지 접미 제거, 비활성 큐 박스 숨김 및 활성 자막/마지막 유지 상태 보존 확인.'
    f['required_open_count']=sum(x['severity']=='required' and not x['status'].startswith('closed') for x in f['findings'])
    save(Q/'findings.json',f)
    hnd=read(Q/'handoff.json')
    hnd['status']='main_and_reviewed_v4_passed_remaining_short_encoded_QA_pending'
    hnd['required_open_count']=f['required_open_count']
    hnd['validation'][sid+'_final']='native-v4 passed_for_local_review; '+actual+'; 실제'+str(m['sample_count'])+'표본,필수/치명0,권장1'
    for name in [path.name,sid+'_v4_technical_verification.json']:
        pn=Q/name
        if not any(x['path']==str(pn) for x in hnd['outputs']):hnd['outputs'].append({'path':str(pn),'sha256':sha(pn)})
    for x in hnd['outputs']:x['sha256']=sha(Path(x['path']))
    save(Q/'handoff.json',hnd)
    print(json.dumps({k:result[k] for k in ['asset_id','status','video_sha256','required_open_count','critical_open_count','recommended_open_count']},ensure_ascii=False))


if __name__=='__main__':
    main()
