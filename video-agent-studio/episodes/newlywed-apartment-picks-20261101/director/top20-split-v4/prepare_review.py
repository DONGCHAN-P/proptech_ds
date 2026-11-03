"""Freeze the two new scripts and local-only map review package; no narration or uploads."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
sys.path.insert(0,str(R));from notify.video_decisions import create,write
W=E/'writer/top20-split-v4';V=E/'visual/top20-split-v4';OUT=R/'영상/신혼부부_지역별아파트/2부작_수정안'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def textfile(path,text):
    if path.exists():assert path.read_text(encoding='utf-8')==text,'Preserve an existing review version'
    else:path.write_text(text,encoding='utf-8')
def link(source,target):
    if target.exists():assert os.path.samefile(source,target)
    else:os.link(source,target)
def money(v):
    a,b=divmod(round(v),10000)
    return f'{a}억'+(f'{b:,}만원' if b else '원') if a else f'{b:,}만원'
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    script=read(W/'scene_proposals_v2.json');scenes=script['scenes']
    validate=read(W/'validation_v2.json')
    assert len([s for s in scenes if s.get('region_id') or '-R' in s['scene_id']])==20
    review=read(E/'qa/top20-split-v4/map_data_review.json');assert review['status'] in ['passed','bounded_review_passed_with_recommendations'] and review['counts']['required']==0
    delta=read(E/'qa/top20-split-v4/map_revision_v3_review.json');assert delta['status']=='passed' and delta['required_open_count']==0
    scriptqa=read(E/'qa/top20-split-v4/script_review.json');assert scriptqa['status']=='passed' and scriptqa['required_open_count']==0
    assert scriptqa['checked_revision']['scene_json_sha256']==sha(W/'scene_proposals_v2.json')
    artifacts=[]
    for part,label in [(1,'20-11위'),(2,'10-1위')]:
        selected=[s for s in scenes if s['part']==part]
        assert len(selected)==12
        lines=[f'# 신혼부부 거주 TOP20 · {part}편 {label} · 대본 v2','','2024년 수도권 구 단위 거주 순위와 2026년 5~10월 전용 83~85㎡ 아파트 매매 실거래를 연결합니다.','']
        for scene in selected:
            lines.extend(['## '+scene['title'],''])
            for sentence in scene['sentences']:lines.extend([sentence['text'],''])
        path=OUT/f'{part}편_{label}_대본_v2.md';textfile(path,'\n'.join(lines)+'\n');artifacts.append(path)
        body=path.read_text(encoding='utf-8');cursor=0
        for scene in selected:
            for sentence in scene['sentences']:
                at=body.find(sentence['text'],cursor);assert at>=cursor;cursor=at+len(sentence['text'])
    proof=Path(read(D/'map_proof_receipt_v3.json')['output'])
    target=OUT/'지도_모션시안_30초_무음.mp4';link(proof,target);artifacts.append(target)
    for rid,name in [('R20','20위_원미구'),('R02','2위_송파구'),('R01','1위_옛서구')]:
        path=OUT/f'지도_{name}.png';link(V/'maps'/f'{rid}_prices.png',path);artifacts.append(path)
    link(E/'research/top20-split-v4/prices/complex_prices.csv',OUT/'단지별_가격집계.csv')
    insights=read(E/'research/top20-split-v4/prices/region_insights.json')['regions']
    lines=['# 가격 기준과 지도 설명','','두 편에 동일한 6개 가격 구간을 적용합니다: 5억 미만 / 5~7억 / 7~10억 / 10~15억 / 15~20억 / 20억 이상. 경계 금액은 위 구간에 포함합니다.','','색 점 하나는 위치가 확인된 아파트 단지입니다. 2026년 5월 1일~10월 31일 계약, 11월 3일 조회, 전용 83~85㎡의 단지별 거래 중위값입니다. 해제 표시 거래를 제외하고 정상 복수 거래는 보존했습니다. 10월 신고는 진행 중입니다.','','전체 14,303건·2,304개 관측 단지 중 12,829건·2,094개 단지를 공식 좌표에 연결했습니다. 지역 중위값과 동별 중위값은 거래마다 한 표, 지도 가격 점은 단지마다 하나입니다. 지도에 연결하지 못한 단지의 가격은 CSV 감사 목록에 남겼습니다.','','왼쪽은 구 전체 가격 분포, 오른쪽은 대표 생활권 상세도입니다. 학교는 녹색 네모, 역은 진한 둥근 네모, 주요 상업시설은 갈색 마름모입니다. 실제 도로·공원·수계와 단지 구역 도형을 사용합니다. 인접 시설 이름은 실제 표시 위치와 원자료를 대조합니다.','','|순위|지역|지역 중위값|거래 수|지도 단지/관측 단지|지도에서 가장 많은 가격대|','|---:|---|---:|---:|---:|---|']
    for r in sorted(insights,key=lambda x:-x['rank']):
        band=max(r['mapped_bands'],key=lambda b:b['complex_n'])
        lines.append(f"|{r['rank']}|{r['province']} {r['region']}|{money(r['region_median_manwon'])}|{r['transaction_n']:,}|{r['mapped_complexes']}/{r['observed_complexes']}|{band['label']} {band['complex_n']}단지|")
    lines+=['','## 자료 출처','','- 순위: 국가데이터처 「2024년 신혼부부통계」, 2024-11-01 거주 기준. https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3','- 거래: 국토교통부 아파트 매매 실거래가 API. https://www.data.go.kr/data/15126468/openapi.do','- 단지 위치·구역: 한국부동산원 공동주택 단지 연계정보(2025). https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1','- 학교 위치: 한국교육시설안전원 학구도안내서비스. https://schoolzone.emac.kr/publicData/publicDataList.do','- 역 위치: KRIC 전체 도시철도역사정보 20260630. https://data.kric.go.kr/rips/M_01_01/detail.do?id=32','- 도로·공원·수계·상업시설: © OpenStreetMap contributors, ODbL 1.0. https://www.openstreetmap.org/copyright','','학교 배정·도보시간·전 지역의 완전한 최인접역 판정은 제공하지 않습니다. 상업시설은 지도 원자료의 공간 기록이며 현재 개별 점포 영업 확인은 별도입니다. 자세한 원자료 기준일·쿼리·해시·정합 검증은 작업폴더의 v4 source ledger에 있습니다.','']
    path=OUT/'가격기준과_지도설명.md';textfile(path,'\n'.join(lines));artifacts.append(path)
    rows=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in artifacts]
    gatepath=D/'script_decision.json'
    if gatepath.exists():
        gate=read(gatepath);assert gate['artifacts']==rows
    else:
        gate=create(E.name,'script','신혼부부 TOP20 두 편 수정 대본 v2: 1편20~11위,2편10~1위. 생활권 설명 보강, 2094단지 가격점과 학교·역·상업시설 지도, 공통6가격범례 인트로. 검토폴더 영상/신혼부부_지역별아파트/2부작_수정안. 두 원고와 지도 규칙 확인을 요청하며 무료 InJoon/현금0원 유지. 실제 본편 길이·음성은 미생성, 30초무음지도시안만 렌더됨. 유료생성·외부파일전송·업로드 승인과 별개입니다.')
        gate.update(artifact_revision='top20-split-v4/scripts-v2',artifacts=rows,scene_json_sha256=sha(W/'scene_proposals_v2.json'),scope='two script contents and common map interpretation; permits production only after approval with existing free voice choice',cash_cap_krw=0,paid_generation_authorized=False,external_file_export_authorized=False,upload_authorized=False)
        write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(gatepath,gate)
    textfile(OUT/'검토안내.md','\n'.join(['# TOP20 두 편 수정안','','1편: 20~11위, 2편: 10~1위. 각 지역의 생활권 특징·가격 차이·학교·교통·생활시설을 연결하도록 대본을 보강했습니다.','','- `1편_20-11위_대본_v2.md`, `2편_10-1위_대본_v2.md`: 읽기용 낭독 원고.','- `지도_모션시안_30초_무음.mp4`: 범례 도입과 원미구·송파구·옛 서구의 레이어 전개를 보여주는 30초 시안.','- `지도_*.png`: 실제 1920×1080 지도판.','- `가격기준과_지도설명.md`, `단지별_가격집계.csv`: 집계·공통 범례·자료 출처.','','현재는 새 대본 확인 단계입니다. 두 본편의 음성·최종 길이는 대본 확정 후 무료 InJoon으로 제작하고 실제 음성에 맞춰 편집합니다. 기존 12분17초 검토본과 비공개 게시본은 보존합니다.','','원고·지도 데이터·정지 시안 및 30초 무음 시안의 검수 범위는 v4 QA 기록에 있습니다. 실제 새 음성 청취·두 본편 연속 재생은 아직 수행하지 않았습니다.','','대본 확인 결정 ID: '+gate['id']+' (script). 공개 범위·업로드는 pre_upload 단계에서 따로 확인합니다.','']))
    manifest={'status':'awaiting_two_script_v2_approval','revision':'top20-split-v4','decision_id':gate['id'],'artifacts':rows,'canonical_scene_json':str(W/'scene_proposals_v2.json'),'canonical_sha256':sha(W/'scene_proposals_v2.json'),'paid_calls':0,'cash_cap_krw':0,'new_final_films':0,'new_narration':False,'telegram_files_sent':0,'youtube_uploads':0}
    write(OUT/'검토파일_명세.json',manifest)
    state=read(E/'state.json')
    state['review_baseline_v3']={'revision':'top20-explain-v3','video':'outputs/top20-explain-v3/main/top20_v6_free_v1.mp4','sha256':'80b7cd14b0fa15de21a696796b2a996f0fa47e29ad02ab067ab8ca20448220d1','audio':'narration/top20-explain-v3/narration_with_clean_brand_v6.wav','timing':'director/top20-explain-v3/locked_timing.json','visibility':'local_only'}
    for key in ['active_video','active_video_sha256','active_audio','active_timing','active_captions','active_measured_duration_s','active_render_receipt','active_source_project','active_final_source_check','active_completion','active_qa']:state.pop(key,None)
    state.update(phase='awaiting_two_script_v2_approval',active_revision='top20-split-v4',active_script='writer/top20-split-v4/scene_proposals_v2.json',active_script_sha256=manifest['canonical_sha256'],active_review_folder=OUT.relative_to(R).as_posix(),pending_decision_id=gate['id'],active_source_maps='visual/top20-split-v4/map_assets.json',active_map_proof='outputs/top20-split-v4/map-proof/map_reading_proof_v3.mp4',active_upload_authorized=False,active_timing_status='unlocked_no_new_audio',active_voice_choice='free_InJoon',active_parts=[{'part':1,'ranks':list(range(20,10,-1)),'status':'script_approval_pending'},{'part':2,'ranks':list(range(10,0,-1)),'status':'script_approval_pending'}],updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(script='pending:'+gate['id'],completed='not_reached_two_new_parts',pre_upload='not_reached_two_new_parts')
    write(E/'state.json',state)
    preflight=read(D/'episode_preflight.json');preflight.update(status='two_scripts_and_map_prototypes_checked_awaiting_script_gate',execution_mode='director_local_data_and_maps_with_native_writer_and_independent_QA')
    preflight['approvals']['script'].update(status='pending',decision_id=gate['id']);preflight['approvals']['budget'].update(status='free_only',cash_cap=0)
    write(D/'episode_preflight.json',preflight)
    print(json.dumps({'status':manifest['status'],'script_decision_id':gate['id'],'review_folder':str(OUT),'files':len(list(OUT.iterdir()))},ensure_ascii=False))
if __name__=='__main__':main()
