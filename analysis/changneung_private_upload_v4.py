"""창릉 최종본 전용 비공개 업로드. 기존 영상 수정·공개 전환 기능 없음."""
import argparse, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/goyang-changneung-20261015'
OUT = EP / 'outputs/youtube-private-v4'
EXPECTED = '2fe7362fcbe46e45f69f411a5bbf02391c56610a39bf9cbb5aea9105fdf564e0'
CHANNEL = 'UCr_mTC0x_Uobv6MrIsOkrXw'
sys.path.insert(0, str(ROOT / 'tools/youtube_deps'))

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

def relative(p):
    return Path(p).relative_to(ROOT).as_posix()

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    title = '고양 창릉, 기다릴까 기존 생활권을 고를까? S1·S4·S5 교통·분양가·학교 비교'
    description = '''고양 창릉의 집·철도·학교는 같은 날 완성될까요?
실제 계획 지도에서 S1·S4·S5의 위치를 보고, 입주 초기 교통·학교·분양가를 삼송·원흥·도래울·지축의 기존 생활권과 비교합니다. S4를 먼저 검토하는 조건과 S5·S1이 맞는 가구를 구분합니다. 미래 가격 순위를 제시하는 영상은 아닙니다.

자료 확인: 2026.10.16. 분양가는 본청약 공고의 특정 84㎡대·5층 이상 기본형 사례이며, 확장비 외 옵션·세금·금융비용은 별도입니다. 현재 접수 가능한 청약 가격표로 해석하지 마세요.
기존 단지 실거래는 2026년 3분기 계약분·2026.10.16 조회, 83㎡ 이상 85㎡ 미만·5층 이상·해제 제외·중개/직거래 포함 중위값입니다. 소수 표본과 단지별 역 접근을 함께 보세요. 현재 가격 범위는 미래 창릉 예상가격이 아닙니다.
입주·개교·철도는 예정/목표이며 변경될 수 있습니다. 전매제한과 거주의무의 기산은 서로 다릅니다. 자격·접수·배정·거래 조건은 해당 시점의 공고를 확인하세요.

챕터
00:00 창릉을 기다릴까, 기존 생활권을 고를까
00:53 전체 계획과 S1·S4·S5 위치
01:38 일자리와 원흥역 출근길
03:05 기존 교통과 새 철도의 시간차
04:41 본청약 분양가와 현재 대안
06:25 실제 계획도로 보는 학교·상권·공원
07:41 공급과 전매·거주의무
08:49 삼송·원흥·도래울·지축 실거래 비교
10:25 가구별 선택 기준
11:24 S4·S5·S1 조건부 후보 정리

이전 편 | 남양주 왕숙
https://youtu.be/T_GBxTRgRSc
다음 편 | 하남 교산

주요 자료
LH 청약플러스: S5 본청약 공고
https://apply.lh.or.kr/lhapply/lhFile.do?fileid=60606564
S4 정정 모집공고
https://apply.lh.or.kr/lhapply/lhFile.do?fileid=67715855
S1 공식 홈페이지·모집공고: https://gc.lynn.co.kr/
공식 전체도: 국토교통부 고시2025-813호(2025.12.24), 토지이음, 공공누리3유형 원본 전체 제시
https://www.eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=628391
독립 상세지도: LH 내집어디 공개 공간정보(2026.10.16 조회)
https://wherehome.lh.or.kr/lhmap.do?mainTabNo=12
기존 지도: © OpenStreetMap contributors / ODbL
https://www.openstreetmap.org/copyright
실거래: 국토교통부 실거래가 공개시스템 https://rt.molit.go.kr/
철도: 코레일 공개 일산선 시각표(2022.8.1 시행표의 열차 구간 사례)
https://www.korail.com/com/userBoard.do?mode=list&schBcid=ticketTable
버스 연결: LX 경기북부 방문안내 https://lx.or.kr/ngyeonggi/sub04.do

원흥역 자료사진: 안우석, 2015.03.04, CC BY-SA 3.0. 현재 출입구 접근·현장 상태의 증거가 아닙니다.
https://commons.wikimedia.org/wiki/File:Wonheung_Station_20150304_155831.jpg
https://commons.wikimedia.org/wiki/File:Wonheung_Station_20150304_160820.jpg
https://creativecommons.org/licenses/by-sa/3.0/
AI 음성을 사용했습니다. 인트로·아웃트로의 도시는 채널 브랜딩용 AI 개념 이미지이며 실제 창릉 모습이 아닙니다.

#고양창릉 #창릉신도시 #원흥 #삼송 #지축'''
    job = {'revision':'youtube-private-v4', 'privacy':'private', 'channel_id':CHANNEL,
           'video':relative(EP/'outputs/production-v4/changneung_full_v4r2.mp4'), 'sha256':EXPECTED,
           'srt':relative(EP/'outputs/production-v4/changneung_full_v4.srt'),
           'qa':relative(EP/'qa/production-v4/final_review.json'), 'title':title, 'description':description,
           'tags':['고양창릉','창릉신도시','S1','S4','S5','원흥','삼송','지축','분양가','학교','GTX-A'],
           'category_id':'27', 'thumbnail':None, 'thumbnail_note':'창릉 전용 확정 썸네일 없음; 타지역 썸네일 미사용, YouTube 기본 썸네일',
           'captions_note':'본문 번인 자막 유지. 별도 SRT는 로컬 보존; 기존 OAuth 범위에서 captions.insert 호출하지 않음.',
           'receipt':relative(OUT/'upload_receipt.json')}
    assert len(title)<=100 and len(description.encode('utf-8'))<=5000
    save(OUT/'upload_job.json', job)
    (OUT/'description.txt').write_text(description, encoding='utf-8')
    print(json.dumps({'job':relative(OUT/'upload_job.json'),'job_sha256':sha(OUT/'upload_job.json'),
                      'title':title,'description_utf8_bytes':len(description.encode()),'privacy':'private'},ensure_ascii=False))

def validate(job):
    assert job['privacy']=='private' and job['channel_id']==CHANNEL
    assert job['sha256']==EXPECTED and sha(ROOT/job['video'])==EXPECTED, '최종 영상 해시 불일치'
    qa=read(ROOT/job['qa'])
    assert qa['sha256']==EXPECTED and qa['local_review_ready'] is True
    assert qa['required_open_count']==0 and qa['critical_open_count']==0
    assert len(job['title'])<=100 and len(job['description'].encode())<=5000

def service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    scopes=set(c.scopes or [])
    assert 'https://www.googleapis.com/auth/youtube.upload' in scopes
    assert 'https://www.googleapis.com/auth/youtube.readonly' in scopes
    if c.expired:
        c.refresh(Request())  # 토큰은 메모리에서만 갱신; 공통 설정파일 수정 없음
    return build('youtube','v3',credentials=c,cache_discovery=False),sorted(scopes)

def inspect(y,job,scopes):
    items=y.channels().list(part='snippet,contentDetails',mine=True).execute().get('items',[])
    assert len(items)==1 and items[0]['id']==CHANNEL, '실제 인증 채널 불일치'
    ch=items[0]
    assert ch['snippet'].get('customUrl','').lstrip('@')=='데이터로보는부동산', '채널 핸들 불일치'
    playlist=ch['contentDetails']['relatedPlaylists']['uploads']
    recent=y.playlistItems().list(part='snippet',playlistId=playlist,maxResults=50).execute().get('items',[])
    matches=[{'id':v['snippet']['resourceId']['videoId'],'title':v['snippet']['title']} for v in recent if v['snippet']['title']==job['title']]
    r={'checked_at':datetime.now(timezone.utc).isoformat(),'channel_id':ch['id'],
       'channel_title':ch['snippet']['title'],'channel_handle':ch['snippet'].get('customUrl'),
       'scopes':scopes,'exact_title_matches':matches,'recent_uploads_checked':len(recent),'video_sha256':EXPECTED}
    save(OUT/'account_preflight.json',r)
    print(json.dumps(r,ensure_ascii=False))
    return r

def verify(y,record,receipt):
    for _ in range(6):
        items=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=record['video_id']).execute().get('items',[])
        assert len(items)==1 and items[0]['snippet']['channelId']==CHANNEL, '업로드 후 채널 불일치'
        v=items[0]
        assert v['status']['privacyStatus']=='private', '비공개 상태 확인 실패'
        record.update(verification=v,verified_private=True,verified_at=datetime.now(timezone.utc).isoformat())
        save(receipt,record)
        state=v.get('processingDetails',{}).get('processingStatus')
        print('처리 상태:',state,flush=True)
        if state in ('succeeded','failed','terminated'):
            break
        time.sleep(5)
    print(json.dumps({'url':'https://youtu.be/'+record['video_id'],'privacy':'private','processing':state},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','inspect','upload','verify']);ap.add_argument('--approval-file');args=ap.parse_args()
    if args.action=='prepare':
        prepare();return
    jobpath=OUT/'upload_job.json';job=read(jobpath);validate(job)
    y,scopes=service();pre=inspect(y,job,scopes);receipt=ROOT/job['receipt']
    if args.action=='inspect':return
    if args.action=='verify':
        verify(y,read(receipt),receipt);return
    assert args.approval_file, '총괄 승인 기록 경로 필요'
    gate=read(ROOT/args.approval_file)
    assert gate['gate']=='pre_upload' and gate['status']=='approved' and gate['privacy']=='private'
    assert gate['channel_id']==CHANNEL and gate['video_sha256']==EXPECTED and gate['job_sha256']==sha(jobpath)
    assert gate.get('decision_id'), '승인 결정ID 필요'
    if receipt.exists():
        record=read(receipt)
        assert record.get('video_id') and record['sha256']==EXPECTED, '이전 업로드 상태 불명: 중복 생성 금지, 실제 계정 확인 필요'
        verify(y,record,receipt);return
    assert not pre['exact_title_matches'], '같은 제목 영상 존재: 중복 업로드 금지'
    record={'phase':'upload_started','sha256':EXPECTED,'job_sha256':sha(jobpath),'approval_file':args.approval_file,
            'decision_id':gate['decision_id'],'privacy_requested':'private','started_at':datetime.now(timezone.utc).isoformat()}
    with receipt.open('x',encoding='utf-8') as f:
        json.dump(record,f,ensure_ascii=False,indent=2)
    from googleapiclient.http import MediaFileUpload
    body={'snippet':{'title':job['title'],'description':job['description'],'tags':job['tags'],
                     'categoryId':job['category_id'],'defaultLanguage':'ko','defaultAudioLanguage':'ko'},
          'status':{'privacyStatus':'private','selfDeclaredMadeForKids':False,'containsSyntheticMedia':True}}
    request=y.videos().insert(part='snippet,status',body=body,notifySubscribers=False,
        media_body=MediaFileUpload(str(ROOT/job['video']),mimetype='video/mp4',chunksize=8*1024*1024,resumable=True))
    result=None
    while result is None:
        progress,result=request.next_chunk(num_retries=0)
        if progress:print('업로드',round(progress.progress()*100),'%',flush=True)
    record.update(video_id=result['id'],phase='uploaded',metadata=result)
    save(receipt,record);verify(y,record,receipt)

if __name__=='__main__':
    try:
        main()
    except Exception as ex:
        code=getattr(getattr(ex,'resp',None),'status',None)
        print(json.dumps({'error_type':type(ex).__name__,'http_status':code,
                          'message':str(ex) if isinstance(ex,AssertionError) else '실행 중단; 자격증명·요청 헤더는 출력하지 않음'},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(1)
