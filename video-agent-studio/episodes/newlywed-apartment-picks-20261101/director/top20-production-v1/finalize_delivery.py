"""Publish local entry points only after all three private uploads are verified."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=EP/'outputs/top20-production-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()

def main():
    package=read(OUT/'release_manifest.json');rows=[]
    for item in package['items']:
        receipt=HERE/'uploads'/item['id']/'upload_receipt.json';r=read(receipt)
        v=r['verification'];assert r['sha256']==item['sha256']==sha(ROOT/item['video'])
        assert v['snippet']['channelId']==package['channel_id']
        assert v['status']['privacyStatus']=='private' and not v['status'].get('publishAt')
        assert v['processingDetails']['processingStatus']=='succeeded'
        tracks=r.get('caption_tracks',[])
        assert any(c['id']==r['caption_id'] and c['snippet'].get('status')=='serving' for c in tracks)
        meta=read(ROOT/item['metadata'])
        assert v['snippet']['title']==meta['title']
        # YouTube strips the final newline; preserve every substantive character.
        assert v['snippet']['description'].rstrip('\r\n')==meta['description'].rstrip('\r\n')
        if item['id']=='main':assert r.get('thumbnail_uploaded')
        rows.append({**item,'video_id':r['video_id'],'url':'https://youtu.be/'+r['video_id'] if item['id']=='main' else 'https://youtube.com/shorts/'+r['video_id'],
          'privacy':'private','processing':'succeeded','captions':'Korean serving','title':meta['title'],'upload_receipt':rel(receipt)})
    completed={'status':'three_private_review_uploads_verified','at':datetime.now(timezone(timedelta(hours=9))).isoformat(),
      'episode_id':EP.name,'label':'비공개 검토본','items':rows,'private_verified':True,'all_processing_succeeded':True,
      'all_manual_captions_serving':True,'voice':'free Microsoft Edge InJoonNeural','new_paid_generation':False,'extra_cash_krw':0,
      'independent_encoded_QA':'passed_with_disclosed_limits','actual_listening':False,'continuous_playback':False,
      'Claude_Opus_Max_review':'not_performed_connection_unavailable','public_release':False,'deleted_existing_uploads':False,
      'native_shorts_related_video_applied':False,'full_source_credits_preserved':True}
    save(OUT/'completion.json',completed)
    labels={'main':'본편','promo':'홍보 쇼츠','analysis':'분석 쇼츠'}
    report=['# 신혼부부 수도권 구 TOP20 — 비공개 업로드 결과\n',
      '2024년 수도권 53개 구 중 신혼부부 전체 수 순위. 본편과 두 쇼츠를 비공개로 업로드하고 처리 상태·공개 범위·한국어 자막을 조회해 확인했습니다.\n',
      '| 영상 | 길이 | 비공개 링크 |','|---|---:|---|']
    for r in rows:
        seconds=round(r['duration_s']);duration=f'{seconds//60}분 {seconds%60:02d}초'
        report.append(f'| {labels[r["id"]]} | {duration} | [{r["title"]}]({r["url"]}) |')
    report.extend(['\n## 반영한 내용\n',
      '- 지역별 실제 사진20장과 2024년 지도, 규모·전년 변화·초혼/재혼 구성 비교를 연결했습니다.\n- 무료 한국어 음성과 실제 단어 경계를 사용했습니다. 자막의103개 문장과 쇼츠7개·8개 문장의 표시값·순서를 대조했습니다.\n- 실제 MP4에서 자막 박스 공백·쇼츠 출처 안전영역·마무리 제작용 문구를 수정했습니다. 마지막 발화 후3초를 유지하고 기존 클린 브랜드·음악을 계승했습니다.\n- 사진·지도·음악 출처와 이용조건, 본편10개 챕터, 선택 썸네일과 한국어 SRT를 준비했습니다. 쇼츠 설명에는 새 본편 URL을 연결했습니다.\n',
      '## 검수 범위\n',
      '독립 검수에서 실제 인코딩 프레임·장면 경계·긴 자막·수치/지리·세로 UI·기술 디코드를 확인했습니다. 주요 음성8장면의 로컬 ASR은 수치 대조의 보조 근거입니다. 실제 청취·전체 연속 재생·Claude Opus/max 검수는 수행하지 않았으며, 일부 지명·초혼/재혼의 ASR 표기 차이는 최종 청취 확인 범위로 남겼습니다. 이번 납품은 비공개 검토본이며 공개 최종 승인으로 기록하지 않습니다.\n',
      '## 보존 자료\n',
      f'- [정확한 산출물·업로드 기록]({(OUT/"completion.json").as_posix()})\n- [검수 기록]({(EP/"qa/top20-production-v1/findings.json").as_posix()})\n- [대본 제작 편집본]({(HERE/"script_v4.md").as_posix()})\n',
      '기존 게시 영상과 원본 대본·자료는 보존했습니다. 추가 유료 음성·이미지 생성과 기존 영상 삭제·공개 전환은 실행하지 않았습니다.\n'])
    (OUT/'업로드결과.md').write_text('\n'.join(report),encoding='utf-8')
    state=read(EP/'state.json')
    state.update(phase='three_private_review_uploads_verified',render_created=True,publication_status='private',
      video=rows[0]['video'],video_sha256=rows[0]['sha256'],youtube_url=rows[0]['url'],youtube_video_id=rows[0]['video_id'],
      shorts=[r for r in rows if r['id']!='main'],completion=rel(OUT/'completion.json'),
      actual_video_duration_s=rows[0]['duration_s'],actual_listening_performed=False,continuous_playback_performed=False,
      Claude_review='not_performed_connection_unavailable',updated_at=completed['at'])
    save(EP/'state.json',state)
    pre=read(EP/'episode_preflight.json')
    pre['status']='private_review_delivered_with_disclosed_limits'
    pre['approvals']['completed']={'status':'local_quality_verified_with_limits_for_private_review','artifact_hashes':{r['video']:r['sha256'] for r in rows}}
    pre['approvals']['pre_upload'].update(status='executed_and_private_verified',visibility='private')
    save(EP/'episode_preflight.json',pre)
    shelf=read(ROOT/'config/video_shelf.json');entry=next(x for x in shelf['entries'] if x['name']=='신혼부부_지역별아파트')
    entry['status']='본편7분51초·홍보34초·분석41초 비공개 검토본 업로드 및 자막 확인. 무료TTS·독립검수, 청취/Claude 추가검수 대기'
    entry['files'].update({'영상.mp4':rows[0]['video'],'홍보쇼츠.mp4':next(r['video'] for r in rows if r['id']=='promo'),
      '분석쇼츠.mp4':next(r['video'] for r in rows if r['id']=='analysis'),'자막.srt':rows[0]['subtitles'],
      '홍보쇼츠_자막.srt':next(r['subtitles'] for r in rows if r['id']=='promo'),'분석쇼츠_자막.srt':next(r['subtitles'] for r in rows if r['id']=='analysis'),
      '썸네일.png':rows[0]['thumbnail'],'대본.md':rel(HERE/'script_v4.md'),'업로드결과.md':rel(OUT/'업로드결과.md')})
    save(ROOT/'config/video_shelf.json',shelf)
    print(json.dumps({'status':completed['status'],'items':[(r['id'],r['url']) for r in rows]},ensure_ascii=False))

if __name__=='__main__':main()
