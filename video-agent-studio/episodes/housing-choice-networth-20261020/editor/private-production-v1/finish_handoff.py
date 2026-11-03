"""Prepare review sheet, placement notes and scoped handoff; no render or API calls."""
import hashlib
import json
import os
import sys
from pathlib import Path
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];OUT=EP/'outputs/private-production-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clock(t):return f'{int(t)//60:02d}:{t%60:05.2f}'


def main():
    # Legacy PowerShell redirection produced one UTF16 file; all owned JSON receipts are now UTF8.
    converted=[]
    if (HERE/'encoding_receipt.json').exists():converted=read(HERE/'encoding_receipt.json')['converted_legacy_utf16']
    for folder in [HERE,OUT]:
        files=[]
        if folder==HERE:files=list(folder.rglob('*.json'))
        else:
            for directory,dirs,names in os.walk(folder):
                dirs[:]=[d for d in dirs if d not in ['audio-deps','ffmpeg-deps','media-bin','node_modules','.hyperframes','renders']]
                files.extend(Path(directory)/n for n in names if n.endswith('.json'))
        for p in files:
            raw=p.read_bytes()
            if raw.startswith((b'\xff\xfe',b'\xfe\xff')):
                obj=json.loads(raw.decode('utf-16'));dump(p,obj);converted.append(str(p.relative_to(EP)).replace('\\','/'))
    plan=read(OUT/'render_plan.json');edl=read(OUT/'assembly_edl.json')
    report=read(OUT/'preview/bbox_report.json');cli=read(HERE/'checks/summary.json')
    image_rows=list(report['snapshots'])
    extra_path=OUT/'preview/review_stills.json'
    if extra_path.exists():
        for row in read(extra_path)['shots']:
            if sha(OUT/f'ch{row["chapter"]:02d}/index.html')!=row['html_sha256']:raise ValueError('Stale settled preview')
            image_rows=[s for s in image_rows if (s['chapter'],s['scene_id'])!=(row['chapter'],row['scene_id'])]
            image_rows.append(row)
    fixes=OUT/'preview_fixes/handoff.json'
    if fixes.exists():
        frames=read(fixes)['frames']
        for issue in ['PVQA-003','PVQA-001','PVQA-002']:
            row=[r for r in frames if r['issue_id']==issue][-1]
            if sha(OUT/f'ch{row["chapter"]:02d}/index.html')!=row['html_sha256']:raise ValueError('Stale fix preview')
            image_rows=[s for s in image_rows if (s['chapter'],s['scene_id'])!=(row['chapter'],row['scene_id'])]
            image_rows.append(row)
    image_rows.sort(key=lambda s:(s['chapter'],s['time_s']))
    dump(OUT/'preview/final_review_selection.json',{'timing_basis':plan['status'],'frames':image_rows})
    sheet=Image.new('RGB',(1920,((len(image_rows)+2)//3)*390),'#e6e7e2');draw=ImageDraw.Draw(sheet)
    for i,s in enumerate(image_rows):
        sheet.paste(Image.open(OUT/s['file']).convert('RGB').resize((640,360)),((i%3)*640,(i//3)*390))
        draw.text(((i%3)*640+10,(i//3)*390+365),s['file'],fill='#173348')
    sheet.save(OUT/'preview/contact_sheet.jpg',quality=94)
    audio=read(HERE/'audio_design.json');smoke=read(HERE/'audio-smoke/receipt.json')
    provision=EP/'director/two-episode-production-v1/ffmpeg_receipt.json'
    full_ffmpeg=read(provision) if provision.exists() else None
    audio['assembly']['script_sha256_target']=plan['script_sha256']
    audio['assembly']['truth_source']='director/two-episode-production-v1/locked_script.json; exact SHA and both review receipt hashes verified in build'
    audio['assembly']['music_source']='director/two-episode-production-v1/media_assets.json; existing_channel_bgm locked SHA and credit'
    audio['assembly']['brand_assets']='same media_assets.json; actual video frame durations 5s intro / 10s outro'
    audio['assembly']['offset_map']='outputs/private-production-v1/assembly_edl.json; shared piecewise offsets for picture, voice and captions'
    audio['canonical_recipe']['argv_template'] += ['--core',str(OUT/'audio-deps').replace('\\','/')] if '--core' not in audio['canonical_recipe']['argv_template'] else []
    audio['dependencies']['core']='outputs/private-production-v1/audio-deps; installed 0.8.181; canonical loadCore executed, exports carve/fx'
    audio['dependencies']['dependency_probe']='core load passed; Remotion ffmpeg f32le pipe smoke failed: requested output format not known'
    audio['dependencies']['ffmpeg']='required: full-feature FFmpeg with f32le muxer and pcm_f32le; current Remotion binary cannot serve canonical raw float pipe'
    audio['status']='planned_only_blocked_on_measured_voice_and_f32le_decoder'
    audio['smoke_receipt']='editor/private-production-v1/audio-smoke/receipt.json'
    audio['blocking_issue']='editor/private-production-v1/issue_AUDIO_F32LE.json'
    if full_ffmpeg and full_ffmpeg.get('status')=='f32le_decode_pass':
        binary=EP.parents[2]/full_ffmpeg['binary']
        if sha(binary)!=full_ffmpeg['binary_sha256']:raise ValueError('Provisioned FFmpeg binary SHA mismatch')
        audio['status']='planned_only_formal_measured_handoff_pending'
        audio['dependencies']['ffmpeg']=full_ffmpeg['binary']+'; prepend containing directory to process PATH only'
        audio['dependencies']['dependency_probe']='canonical core 0.8.181 load passed; director BGM/voice f32le pipe receipt passed'
        audio['provision_receipt']='director/two-episode-production-v1/ffmpeg_receipt.json'
        audio['provision_receipt_sha256']=sha(provision)
        audio['blocking_issue']=None
        issue=read(HERE/'issue_AUDIO_F32LE.json');issue['done']=True
        issue['resolution']={'receipt':audio['provision_receipt'],'receipt_sha256':sha(provision),'binary_sha256':full_ffmpeg['binary_sha256'],'smoke_owner':'director','global_install':False}
        dump(HERE/'issue_AUDIO_F32LE.json',issue)
    mix_file=HERE/'mix_receipt.json'
    if mix_file.exists() and read(mix_file)['status']=='canonical_carve_pass':
        audio['status']='canonical_carve_attributes_applied_actual_encoded_mix_and_listening_pending'
        audio['carve_applied']=True;audio['carve_receipt']='editor/private-production-v1/mix_receipt.json'
        audio['audio_generated']=True;audio['voice_generation_owner']='narration; editor made no TTS call'
    dump(HERE/'audio_design.json',audio)
    (HERE/'music_credit.txt').write_text(plan['brand_assembly']['existing_music']['license']['credit']+'\n'+plan['brand_assembly']['existing_music']['license']['license_url']+'\n',encoding='utf8')
    rows=[]
    for ch in plan['chapters']:
        for s in ch['scenes']:
            if s['scene_id'] not in ['s2g','s2p','s8h','s8l','s9d','s10invest','s10stable','s10life','s10hold','s10next']:continue
            offsets=[o for o in edl['offset_map'] if o['chapter']==ch['chapter'] and o['local_start_s']<=s['start_s']<o['local_end_s']]
            offset=offsets[0]['global_offset_s']
            rows.append(f'| {ch["chapter"]}/{s["scene_id"]} | {clock(s["start_s"]+offset)} | {s["end_s"]-s["start_s"]:.2f}초 | {ch["project"]}/index.html | {s["material_type"]} |')
    timing_note='본문은 실측 음성 전 estimated_placeholder이며 추천 시간은 변경됩니다.' if plan['status']=='estimated_placeholder' else '본문은 정식 final_timing.json의 실측 341큐에 연결되어 있습니다. 음성 속도와 발화 내용은 유지합니다.'
    audio_note='BGM canonical carve는 믹스 전입니다.' if not audio.get('carve_applied') else '고정 BGM에 canonical carve를 적용했습니다. 실제 인코딩 믹스와 청취는 후속 검수입니다.'
    notes=f'''# 배치 가이드 · 실측 편집 v1

대본 기준: `{plan['script_path']}` / SHA `{plan['script_sha256']}`. 진실의 기준은 `director/two-episode-production-v1/locked_script.json`이다. {timing_note} 현재 프로젝트 합계 {plan['estimated_total_seconds_without_brand']:.2f}초, 브랜드 5초·10초 포함 EDL {edl['total_seconds']:.2f}초.

실제 검증 파일은 `outputs/private-production-v1/ch01/index.html` … `ch10/index.html`, `preview/contact_sheet.jpg`와 같은 폴더의 1920×1080 PNG다. 대표 모음에 고른 PNG는 {len(image_rows)}장이다. 루트 `index.html`은 장별 검토 진입점이며 최종 본편이 아니다. 새 MP4는 생성하지 않았다.

| 장/장면 | 전체시각({plan['status']}) | 길이 | 실제 장별 프로젝트 | 자료 유형 |
|---|---|---|---|---|
{chr(10).join(rows)}

각 장면의 제목·자료·출처·자막은 서로 분리된 레이어다. 그림과 그래프는 GSAP paused timeline의 opacity/transform/stroke로 표시하고 컷 경계는 clip 수명으로 처리한다. 본문 흰 자막 박스는 큐 사이에도 유지하며, 장 표지·클린 브랜드·마지막 발화 뒤 3초 CTA에는 숨긴다. 새 지도 줌이나 보행 캐릭터는 넣지 않았다.

`s2g`는 2006Q1부터 2026Q2까지의 실거래 연결지수 전체 경로와 2016Q2–2026Q2 가이드·양끝점을 표시한다. 세종은 2015Q1 시작이다. 연평균 수치는 facts.json의 해당 기간과 연결했다. `s8h`는 집값만 0/2/4/6%로 바꾸고 투자·대출·계약 조건은 고정한다. `s8l`의 5%는 첫해 비용 반영 전 자기자금 대비 평가액 변화다.

`s10life`의 `ch10/assets/housing-stability-v1.png`는 RGBA 생활 공간 그림으로 이 장면에서 한 번만 사용한다. 실제 단지·면적·가격을 뒷받침하는 자료로 쓰지 않는다. 생성/권리/SHA 기록은 `assets_manifest.json`에 있다. 장 표지는 각 장 자체 도식 조각을 사용하며 공통 price 사진을 반복하지 않는다.

클린 인트로는 첫 문단 발화 뒤 프레임 경계에 넣는다. `assembly_edl.json`의 분할·offset_map을 영상·음성·자막에 공통 적용한다. 실제 브랜드 영상은 150/300프레임이며 AAC 컨테이너 끝 길이로 본문을 밀지 않는다. `captions_estimated.srt`는 검증용 잠정 자막이다. 실측 빌드에서 `captions_measured.srt`로 전환한다.

BGM은 고정된 Thinking Music을 쓰며 설명란 credit은 `editor/private-production-v1/music_credit.txt`를 그대로 전달한다. {audio_note} canonical voiceover carve 설계는 `audio_design.json`에 있다. 기존 Remotion FFmpeg 제약은 총괄이 제공한 media-bin/ffmpeg.exe로 해결했다. 프로세스 PATH만 변경하며 전역 설치는 하지 않는다.

재현: 프로젝트 루트에서 `tools/python311/python.exe -X utf8 video-agent-studio/episodes/housing-choice-networth-20261020/editor/private-production-v1/build.py`. 실제 final_timing.json 준비 뒤 같은 명령에 `--require-measured`를 붙인다. 체크는 `run_cli_checks.py`, 글자/패널 경계·역방향 seek는 `node .../validate_preview.cjs`, 대표 시간은 `snapshot_times.json`이다. 렌더 명령은 render_plan.json의 참조용 명령이며 아직 실행하지 않는다.

검수 범위: headless Chrome 표본 DOM·글자 Range BBox·SVG stroke 경계·큐 사이 박스 연속성·역방향 seek 픽셀 동일성. CLI는 대표 시각의 lint/runtime/layout/contrast 검사다. 이 결과는 독립 QA, 실측 음성 정렬, 실제 인코딩 프레임, 전체 decode, 연속 재생 또는 청취 완료를 뜻하지 않는다. 본문 음성·BGM 혼합·최종 MP4·업로드는 수행 전이다.
'''
    (HERE/'placement_guide.md').write_text(notes,encoding='utf8')
    dump(HERE/'encoding_receipt.json',{'format':'UTF-8 without BOM','converted_legacy_utf16':sorted(set(converted)),'scope':'owned JSON only; audio-deps and other roles untouched'})
    dump(HERE/'diagnostics_status.json',{'current':'static_checks.json, checks/summary.json, outputs/private-production-v1/preview/bbox_report.json','resolved_early_diagnostics':['build_failures.json (now empty)','cli_check_ch02.json (initial runtime failure, historical)','preview/browser_failure.json (historical; latest sampled report passed)'],'open':[] if audio['blocking_issue'] is None else ['issue_AUDIO_F32LE.json']})
    dump(HERE/'handoff.json',{'role':'editor','status':'source_ready_measured_timing_and_independent_QA_pending','script_sha256':plan['script_sha256'],
      'inputs':{'truth':'director/two-episode-production-v1/locked_script.json','manifest':'outputs/private-production-v1/input_manifest.json','timing':plan['status']},
      'artifacts':['editor/private-production-v1/build.py','outputs/private-production-v1/index.html','outputs/private-production-v1/render_plan.json','outputs/private-production-v1/assembly_edl.json','outputs/private-production-v1/preview/contact_sheet.jpg','editor/private-production-v1/placement_guide.md','editor/private-production-v1/audio_design.json'],
      'validation':{'chapters':10,'scenes':50,'cli':'checks/summary.json','bbox':'outputs/private-production-v1/preview/bbox_report.json','source_static':'static_checks.json','full_resolution_PNGs':len(image_rows),'full_render':False,'actual_listening':False,'continuous_playback':False},
      'changed_from_v4':['ch09/s9d deposit return risk','ch10/s10invest base rank and conditional extra performance'],
      'open':['independent preview recheck of PVQA-001/002/003','full render and encoded media review'],
      'next_owner':'QA changed preview recheck → editor render_pipeline.py --execute; user authorization valid, no reconfirmation'})
    print(json.dumps({'handoff':str(HERE/'handoff.json'),'pngs':len(image_rows),'cli':cli['status'],'bbox':report['status'],'encoding':'UTF-8','timing':plan['status']},ensure_ascii=False))


if __name__=='__main__':main()
