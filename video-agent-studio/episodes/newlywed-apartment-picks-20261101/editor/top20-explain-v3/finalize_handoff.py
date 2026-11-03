"""검증된 대표시안의 배치 가이드·파일 원장·한글 인계를 작성합니다."""
from pathlib import Path
import hashlib,html,json,sys
from PIL import Image

H=Path(__file__).resolve().parent;E=H.parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,text):
    p=(H/name).resolve()
    assert p.is_relative_to(H),'담당 폴더 밖 쓰기 금지'
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
def save(name,data):write(name,json.dumps(data,ensure_ascii=False,indent=2)+'\n')

inputs=read(H/'input_manifest.json');build=read(H/'build_receipt.json');check=read(H/'evidence/check_receipt.json');bounds=read(H/'evidence/text_bounds.json');caption=read(H/'caption_integrity.json');phases=read(H/'phase_audit.json');timeline=read(H/'timeline_resolved.json');local=read(H/'infrastructure_verification.json')
assert check['status']==bounds['status']==caption['status']==local['status']=='passed'
assert caption['source_script_sha256']=='8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e'
assert caption['source_markdown_sha256']=='4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38'
assert all(sha(v['path'])==v['sha256'] for v in inputs['inputs'])
sample_records=[]
for r in bounds['PNG_samples']:
    p=Path(r['png']);im=Image.open(p);assert im.size==(1920,1080)
    sample_records.append({**r,'path':str(p.relative_to(H)).replace('\\','/'),'sha256':sha(p),'dimensions':list(im.size)})
assert len(sample_records)==13
save('evidence/png_manifest.json',{'status':'passed','source_script_sha256':caption['source_script_sha256'],'source_markdown_sha256':caption['source_markdown_sha256'],'timing_locked':False,'PNG':sample_records,'contactsheet':{'path':'evidence/contactsheet_final_v6.png','sha256':sha(H/'evidence/contactsheet_final_v6.png')}})

cards=[]
for r in sample_records:
    name=Path(r['path']).name;sid=r['scene_id'];label={'intro':'도입·시점 한계','feature':'특징·사진','price':'가격·지도'}[r['phase']]
    cards.append(f'<figure><a href="대표PNG/{html.escape(name)}"><img src="대표PNG/{html.escape(name)}" alt="{sid} {label}"></a><figcaption>{sid} · {label} · 1920×1080</figcaption></figure>')
gallery='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>최종v6 편집 대표시안</title><style>body{margin:24px;background:#f6f4ef;color:#173348;font-family:system-ui,sans-serif}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:20px}figure{margin:0;background:white;padding:10px}img{width:100%;display:block}figcaption{padding:10px}a{color:#286cda}code{overflow-wrap:anywhere}</style><h1>최종 v6 편집 대표시안</h1><p>대본 승인 검토용 · 무음 · 실제 발화 타이밍 없음 · 본편 영상 아님</p><p>기본3유형과 강남 최고가격·기흥 최장단지명·옛서구를 포함합니다. 지역 거래/단지 거래를 별도로 표시합니다.</p><p><a href="contactsheet_final_v6.png">13장 연락시트</a> · <a href="../caption_integrity.json">최종 원고·자막 일치 검사</a> · <a href="../spec/caption_mapping.json">자막 매핑</a> · <a href="../issue_EDITOR_V3_QA_RECHECK.json">QA 재검수 패킷</a></p><p>sceneJSON <code>8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e</code><br>대본MD <code>4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38</code></p><main>'''+''.join(cards)+'</main></html>'
write('evidence/gallery.html',gallery)

phase_map={v['scene_id']:v for v in phases}
table=[]
for s in timeline['scenes']:
    sid=s['scene_id'];p=phase_map.get(sid)
    typ=build['layout_families'].get(sid,'도입');when=f"장면 안 {p['switch_s']:.3f}초(임시)" if p else '도입 자료 설명'
    files=f'{sid}_feature.png / {sid}_price.png' if p else f'{sid}_intro.png'
    table.append(f'| {sid} | {typ} | {files} | {when} | 30초 시안 예산 |')
write('placement_guide.md','''# v3 대표시안 배치 가이드

이 폴더의 실제 전달물은 PNG13개와 HTML 시안입니다. MP4 배포 파일은 없습니다. 최종 v6 문장은 고정했지만 script 승인·음성·실제 단어 타이밍은 아직 없습니다. 총210초는 선택한7장면을 장면당30초로 배치한 검토용 시간이며 본편 길이나 실제 낭독 길이가 아닙니다.

## 현재 파일

- 연락시트: `evidence/contactsheet_final_v6.png`
- 전체 PNG 열람: `evidence/gallery.html`
- 원본 크기 PNG: `evidence/대표PNG/` · 1920×1080 ·13개
- 독립 정적 가격 HTML: `spec/price_panels/<scene_id>/index.html`
- 개별2단계 HTML: `spec/representatives/<scene_id>/index.html`
- 묶음 HyperFrames 프로젝트: `spec/index.html`
- 최종 원고·자막 연결: `spec/caption_mapping.json`, `caption_integrity.json`

| 장면 | 구도 | 실제 PNG 파일명 | 추천 전환 위치 | 시안 길이 |
|---|---|---|---|---|
'''+ '\n'.join(table)+'''

## 실제 음성 이후 적용

사진은 특징·랜드마크 낭독이 끝날 때까지 유지합니다. 특징 마지막 단어 종료와 가격 첫 단어 시작을 실제 원발화 메타데이터로 검사하고, 가격 첫 단어에서 하드 컷합니다. 표의 임시초를 실제 편집 타이밍으로 승계하지 않습니다. 지역 가격 숫자와 단지 가격 숫자는 각각의 실제 숫자 발화 앵커를 사용합니다.

사진·특징 카드, 가격 지도·카드, 고정 흰 자막, 통합 크레딧은 별도 레이어입니다. 줌은 사용하지 않았습니다. 지도SVG는 원본800×600 바이트와 비율을 유지합니다. 단지 위치 점은 검증좌표·단지ID·geometry 내부점이 일치한 부모 지도만 사용합니다. 이 점은 출입구나 개별 세대 위치가 아닙니다.

가격 화면 내내 계약기간·전용면적·취소 제외·지역 거래 건수·단지 거래 건수를 표시합니다. 지역과 단지 중위값을 혼동하지 않도록 별도 카드에 배치했습니다. 사진·지도 전체 이용조건은 `credits.md`, `credits.json`, `price_map_credits.json`으로 설명란에 전달합니다.

기본3유형 사진은 현재 최종 원고의 해당 장소 설명과 연결했습니다. 경계 사례의 특징 단계에 ‘사진 확정 대기’가 있으면 그 장면은 가격 레이아웃 검사 대상으로만 사용한 것입니다.20지역 최종 사진 연결이나 본편 납품 통과를 뜻하지 않습니다.
''')

write('README.md','''# TOP20 지역 설명 v3 편집 인프라

최종 v6와 정상행 보존 `final-api-20261103-v2` 가격을 연결한 대본 승인 검토용 대표시안입니다. 본편 음성·MP4·업로드를 만들지 않았습니다.

`evidence/gallery.html` 또는 `evidence/contactsheet_final_v6.png`부터 확인합니다. QA LockE에게 전달할 패킷은 `issue_EDITOR_V3_QA_RECHECK.json`입니다. QA의 REQ001은 편집 담당이 직접 닫지 않았습니다.

## 재현 명령

프로젝트 루트 `C:/projects/realestate_reco`의 PowerShell에서 실행합니다.

```powershell
$task = 'video-agent-studio/episodes/newlywed-apartment-picks-20261101/editor/top20-explain-v3'
tools/python311/python.exe -X utf8 "$task/build.py" --script "$task/input_snapshot/scene_proposals_v6.json" --corner-cases
tools/python311/python.exe -X utf8 "$task/verify_infrastructure.py"
tools/python311/python.exe -X utf8 "$task/run_checks.py"
```

첫 명령은7장면 HTML만 생성합니다. 두 번째는 입력SHA·문장·자막·가격·지도·전환 로직을 검사합니다. 세 번째는 실제 브라우저 경계 검사와 PNG 캡처만 수행합니다. `--describe false`로 외부 비전분석을 사용하지 않습니다. 버전별 원본 PNG 캡처는 `evidence/snapshots-spec-v*/`에 보존합니다.

## 입력과 보류

`input_snapshot/`은 지정한 최종 원고 SHA의 바이트 사본입니다. 가격·지도·독립 가격검수는 부모 최신파일과 SHA로 연결하며 v1 가격을 거부합니다. 실제 음성 타이밍은 없습니다. 추정 시간을 잠그거나 TTS·본편 렌더로 확장하지 않습니다. 소스/자산 입력은 `input_manifest.json`, 검사 범위는 `handoff.json`, 배치는 `placement_guide.md`에 있습니다.

기존v2 생성기6개 파일 중 필요한 부분만 계승했습니다. 기존v2의 영상·프로젝트·대본·음성 및 공유state를 수정하거나 삭제하지 않았습니다. HyperFrames 사용량은 외부 계정 조회를 하지 않아 미확인입니다. 로컬 CLI 0.8.181을 사용했습니다.
''')

save('input_contract.json',{
 '상태':'최종대본·확정가격·지도 수신; 실제 음성 타이밍 대기',
 '원고':{'scene_json_sha256':caption['source_script_sha256'],'script_md_sha256':caption['source_markdown_sha256'],'문장기준':'sentence_id와 display_text; price_role 또는 regional_price/complex_price 의미 비트'},
 '실제타이밍필수':{'timing_locked':True,'timing_basis':'actual_audio','script_sha256':'수신 원고MD와 일치','words_file':'원발화 단어 파일','words_file_sha256':'단어 파일 실제 SHA','scenes':'scene_id/start_s/end_s/sentence_times; 단어 local_start_s/local_end_s는 장면 내부 초'},
 '가격':'director/top20-explain-v3/price_panel_data.json → final-api-20261103-v2 및 독립QA SHA 연결',
 '지도':'visual/top20-explain-v3/maps/map_assets.json → 가격패널SHA/개별SVG SHA/marker_status/단지ID/lat/lng 내부점 일치',
 '편집규칙':'특징 마지막 단어 종료 <= 가격 첫 단어 시작에서만 사진→지도 전환. 실제 단어 없는 현재는 provisional 시안만 허용.',
 '본편재개조건':'별도 script 승인, 실제 음성·타이밍 전달 및 총괄 통합 지시. 이 빌더에는 MP4 렌더/업로드 기능이 없습니다.'})

origin=[]
for name in ['build.py','visuals.py','caption_tools.py','caption_backgrounds.py','extra_scenes.py','design.md']:
    p=E/'editor/top20-enhance-v2'/name;origin.append({'원본':str(p),'sha256':sha(p),'v3사본':name,'원본에쓰기':False})
save('source_provenance.json',{'상속한v2파일':origin,'이작업쓰기범위':str(H),'v2영상삭제':False,'공유state쓰기':False})
save('environment_manifest.json',{'python':sys.version,'node':'v24.16.0','hyperframes':'0.8.181','브라우저':'HyperFrames browser path로 확인한 headless shell 152.0.7977.30','사용량':'외부 계정 조회 미실행으로 미확인','실행':'로컬HTML검사·PNG만; TTS/MP4/외부업로드없음'})
save('evidence/editor_visual_review.json',{'상태':'직접 확인한 범위에 필수 수정 발견 없음','현재최종PNG_원본크기열람':['O002_intro.png','S006_feature.png','S007_feature.png','S019_feature.png','S017_price.png','S005_price.png','S022_price.png'],'직접확인범위':'기본3유형의 최종문장·자막, 도입기관명·시점한계, 강남최고가격·기흥최장단지명·옛서구와 각 거래건수 분리. 그 밖의6개PNG는 자동생성·크기·배치 검사 범위입니다.','독립QA':'LockE의REQ001재검수 대기; 편집자 자체 확인을 독립 검수로 기록하지 않음','실제음성청취':False,'연속영상재생':False,'MP4검사':'생성하지 않았으므로 해당없음'})

interface=read(H/'issue_EDITOR_V3_INPUT_INTERFACE.json');interface['status']='대본·가격·지도수신_실제음성타이밍대기';interface['received']={'최종대본SHA':caption['source_script_sha256'],'가격':'정상행보존v2 및 독립검수SHA 연결통과','지도':'20개 검증핀과 원본SVG 연결통과'};save('issue_EDITOR_V3_INPUT_INTERFACE.json',interface)
outputs=['evidence/contactsheet_final_v6.png','evidence/gallery.html','evidence/png_manifest.json','spec/index.html','spec/caption_mapping.json','caption_integrity.json','infrastructure_verification.json','evidence/check_receipt.json','evidence/text_bounds.json','evidence/editor_visual_review.json','input_manifest.json','input_contract.json','placement_guide.md','credits.md','credits.json','price_map_credits.json','issue_EDITOR_V3_QA_RECHECK.json','README.md']
save('handoff.json',{'task_id':'TOP20-explain-v3-editor','role':'editor','status':'대표시안완료_독립QA재검수및script승인대기','input_revisions':{'scene_json_sha256':caption['source_script_sha256'],'script_md_sha256':caption['source_markdown_sha256'],'price_panel_sha256':sha(E/'director/top20-explain-v3/price_panel_data.json'),'map_manifest_sha256':sha(E/'visual/top20-explain-v3/maps/map_assets.json'),'price_source':'final-api-20261103-v2'},'outputs':[{'path':'editor/top20-explain-v3/'+p,'sha256':sha(H/p)} for p in outputs],'affected_scene_ids':build['layout_families'] and [v['scene_id'] for v in timeline['scenes']],'checks':[{'check':'最終原稿SHA·입력·앵커·가격·지도·자막','result':'passed','evidence':'infrastructure_verification.json:34개; caption_integrity.json:41문장/68큐 정확일치'},{'check':'실제브라우저 경계13표본','result':'passed','evidence':'evidence/check_receipt.json:lint/runtime/layout0,contrast67/67'},{'check':'PNG13개1920x1080·대표7개직접열람','result':'passed_in_stated_scope','evidence':'evidence/png_manifest.json; evidence/editor_visual_review.json'},{'check':'독립QA REQ001 재검수','result':'pending','evidence':'issue_EDITOR_V3_QA_RECHECK.json'}],'open_issue_ids':['QA-V3-REQ-001','실제음성및타이밍대기'],'next_role':'QA LockE(01a19d09-266e-7ab1-80d6-d2bdd28a026e) → director의script gate','summary':'지정8bee/4259 최종v6를 고정하고7장면 대표HTML/PNG13개를 재생성했습니다. 가격은 정상행보존v2만 사용하고 지역·단지 가격/거래건수를 분리했습니다. 기본3유형·강남최고가격·기흥최장단지명·옛서구를 포함합니다.41문장/68자막 cue가 최종display_text와 글자·띄어쓰기·수치까지 일치합니다.13개 전환 경계표본의 실제브라우저 배치오류0입니다. PNG7개를 직접 확인했습니다. QA LockE용파일패킷을 남겼으며 직접메시지도구는 없습니다. QA 이슈를 직접 닫지 않았습니다. 전체대본133문장의독립QA는 부모 담당 범위입니다. 본편음성·실제타임록·렌더·업로드를 하지 않았습니다.210초는7장면×30초의 검토용예산이며 실제본편길이가 아닙니다. 기존v2와 공유state는 보존했습니다.','timing_locked':False,'actual_listening_performed':False,'continuous_playback_performed':False,'new_tts_generated':False,'full_render_started':False,'upload_performed':False,'direct_peer_message_sent':False})
handoff=read(H/'handoff.json');handoff['checks'][0]['check']='최종 원고SHA·입력·앵커·가격·지도·자막';save('handoff.json',handoff)
save('source_freeze.json',{'source_files':[{'path':str(p.relative_to(H)).replace('\\','/'),'sha256':sha(p)} for p in sorted((H/'spec').rglob('*')) if p.is_file() and '.hyperframes' not in p.parts],'고정원고':{'scene_json':caption['source_script_sha256'],'MD':caption['source_markdown_sha256']},'상태':'실제음성타이밍없음_대표시안검토용'})
delta_file=H/'evidence/photo-fix-v1/validation.json'
if delta_file.exists():
    delta=read(delta_file);assert delta['status']=='passed'
    review=read(H/'evidence/editor_visual_review.json')
    review['현재최종PNG_원본크기열람']+=['S005_feature.png','S017_feature.png','S022_feature.png']
    review['직접확인범위']+=' 추가로 구성역5번출구·양재천 교체본·청라호수공원 특징 PNG3개를 원본 크기로 확인했습니다. 촬영연도/미상·라이선스·지역 자료사진 캡션과 가격단지 전경으로 사용하지 않는 분리를 확인했습니다.'
    review['그밖의자동검사범위']='현재13개 중 직접열람10개, 불변 가격PNG3개는 기존 자동검사 근거를 재사용합니다.'
    save('evidence/editor_visual_review.json',review)
    guide=(H/'placement_guide.md').read_text(encoding='utf-8')
    guide=guide.replace('경계 사례의 특징 단계에 ‘사진 확정 대기’가 있으면 그 장면은 가격 레이아웃 검사 대상으로만 사용한 것입니다.20지역 최종 사진 연결이나 본편 납품 통과를 뜻하지 않습니다.','경계 사례 S005/S017/S022도 확정된 구성역5번출구·양재천 교체본·청라호수공원 사진을 연결했습니다. 해당3장면의 대기 문구는 없으며 지역 자료사진·촬영연도(미상 포함)·라이선스를 표시합니다. 가격 단지의 전경으로 사용하지 않습니다. 본편 전체 납품 통과를 뜻하지 않습니다.')
    write('placement_guide.md',guide)
    packet=read(H/'issue_EDITOR_V3_QA_RECHECK.json')
    packet['status']='필수사진연결3개수정완료_독립QA최종확인요청'
    packet['scene_ids']=['S005','S017','S022']
    packet['problem']='spec_final_review.json에서 유일하게 남은3특징장면의 실제사진 확정대기 문구를 해소했습니다.'
    packet['evidence']['photo_fix_contactsheet']='editor/top20-explain-v3/evidence/contactsheet_photo_fix_v1.png'
    packet['evidence']['photo_fix_validation']='editor/top20-explain-v3/evidence/photo-fix-v1/validation.json'
    packet['evidence']['photo_fix_browser_check']='editor/top20-explain-v3/evidence/photo-fix-v1/check.json'
    packet['evidence']['photo_binding']='editor/top20-explain-v3/photo_bindings.json'
    packet['changes']=['S005→PHOTO_R18 구성역5번출구(2026·CC0)','S017→PHOTO_R06_ALT01 양재천 교체본(2019·CC BY4.0/공공누리1)','S022→PHOTO_R01 청라호수공원(촬영연도미상·공공누리1)','기존 원본JPEG 바이트·전체귀속문·라이선스 유지. 사진은 특징 단계에만 표시하고 가격단지 전경으로 사용하지 않습니다.']
    packet['proposal']='변경된 특징3장면 HTML과 새PNG3개 및 연결이미지만 최종재검수해 주십시오. 자막매핑과 나머지10개PNG는 SHA불변이므로 기존통과를 재사용합니다.'
    packet['impact']='새 조사·이미지생성·음성·본편렌더·업로드 없음. 문장/가격/지도/타이밍 변경 없음. 편집자는 QA 이슈를 직접 닫지 않았습니다.'
    packet['editor_verification']['photo_delta']={'new_png':3,'browser_samples':9,'layout_findings':0,'unchanged_png':10,'caption_mapping_unchanged':True,'editor_full_resolution_pngs_viewed':['S005_feature.png','S017_feature.png','S022_feature.png']}
    save('issue_EDITOR_V3_QA_RECHECK.json',packet)
    handoff=read(H/'handoff.json');handoff['status']='유일필수사진수정완료_독립QA최종확인대기'
    handoff['affected_scene_ids']=['S005','S017','S022']
    handoff['summary']='유일하게 남은 필수 사진연결3곳을 수정했습니다. S005 구성역5번출구(2026·CC0), S017 양재천 교체본(2019·CC BY4.0/공공누리1), S022 청라호수공원(연도미상·공공누리1)을 확정 manifest의 asset_id/SHA로 연결했습니다. 대기문구가 없으며 지역자료사진 캡션·연도·라이선스와 전체귀속문을 유지합니다. 특징3장면9표본 실제브라우저 배치오류0, 새PNG3개1920x1080 생성 후 모두 원본크기로 직접확인했습니다. 사진은 가격단지 전경으로 사용하지 않습니다. 자막매핑SHA5cdf…와 나머지10개PNG는 불변입니다. 최종8bee/4259·가격·지도·문장·타이밍은 유지합니다. 수정 연락시트와 QA LockE용 파일패킷을 갱신했습니다. 직접 메시지도구는 없으며 QA의 최종이슈판정만 남습니다. 실제음성·본편렌더·업로드는 하지 않았습니다.'
    handoff['checks'].append({'check':'사진3개 수정 범위 재검증','result':'passed','evidence':'evidence/photo-fix-v1/validation.json:9표본오류0·사진원본SHA/라이선스일치·불변자막/PNG10개대조'})
    handoff['checks'][0]['evidence']+='; 해당 로직·문장·가격은 불변으로 기존 근거 재사용'
    handoff['open_issue_ids']=['QA-V3-REQ-001_사진수정독립최종확인대기']
    for name in ['evidence/contactsheet_photo_fix_v1.png','evidence/photo-fix-v1/validation.json','photo_bindings.json']:
        handoff['outputs'].append({'path':'editor/top20-explain-v3/'+name,'sha256':sha(H/name)})
    for record in handoff['outputs']:record['sha256']=sha(E/record['path'])
    save('handoff.json',handoff)
print(json.dumps({'상태':'인계준비완료','연락시트':str(H/'evidence/contactsheet_final_v6.png'),'QA패킷':str(H/'issue_EDITOR_V3_QA_RECHECK.json'),'handoff':str(H/'handoff.json'),'PNG':len(sample_records),'자막문장':caption['sentence_count']},ensure_ascii=False))
