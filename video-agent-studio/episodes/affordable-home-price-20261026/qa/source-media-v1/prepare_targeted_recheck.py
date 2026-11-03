"""마지막 두 소스 이슈의 좁은 재검수 계약. 다른 담당 파일은 읽기만 한다."""
from pathlib import Path
import datetime
import hashlib
import json
import re

QA=Path(__file__).resolve().parent
EP=QA.parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(n,d):(QA/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


review=read(QA/'source_review_v3.json')
metrics=read(QA/'source_delta_metrics_v3.json')
revision=review['checked_revision']
base=QA/'postcarve-before-targeted-fix'
base.mkdir(exist_ok=True)
rows=[]
for ch in range(1,11):
    p=EP/f'outputs/private-production-v1/ch{ch:02}/index.html'
    expected=revision['source_chapters'][f'ch{ch:02}']
    current=sha(p)
    row=dict(chapter=ch,expected_postcarve_sha256=expected,observed_sha256=current,same_as_reviewed=current==expected)
    if current==expected:
        target=base/f'ch{ch:02}.html'
        if target.exists():assert sha(target)==expected
        else:target.write_bytes(p.read_bytes())
        raw=p.read_text(encoding='utf-8')
        row['preserved_path']=target.as_posix()
        row['css_sha256']=hashlib.sha256(re.search(r'<style>(.*?)</style>',raw,re.S)[1].encode()).hexdigest()
        row['media_and_fonts']=[dict(path=x.as_posix(),sha256=sha(x),bytes=x.stat().st_size) for x in sorted((p.parent/'assets').rglob('*')) if x.is_file()]
    rows.append(row)
timing=read(EP/'narration/production-injoon-v3/final_timing.json')
selected=[]
for chapter in timing['chapters']:
    for cue in chapter['cues']:
        if cue['id'] in ['C07_S031Q002','C07_S031Q003','C09_S040Q003','C09_S040Q004']:
            selected.append(dict(cue_id=cue['id'],scene_id=cue['scene_id'],chapter=chapter['chapter'],start_s=cue['start_s'],end_s=cue['end_s'],mid_s=(cue['start_s']+cue['end_s'])/2))
hook=read(EP/'outputs/private-production-v1/assembly_edl.json')['hook_cut_s']
first=next(c for c in timing['chapters'][0]['cues'] if c['scene_id']=='S002')
plan=dict(status='ready_waiting_Carson_targeted_source_receipt',prepared_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          open_required=['SOURCE-FOCUS-003','SOURCE-BRAND-004'],closed_required_to_retain=['SOURCE-TAX-001','SOURCE-CLIP-002'],
          baseline_revision=revision,baseline_chapters=rows,
          pinned_inputs=[dict(path=p.as_posix(),sha256=sha(p)) for p in [EP/'director/production-v1/locked_script.json',EP/'narration/production-injoon-v3/final_timing.json',EP/'outputs/private-production-v1/assembly_edl.json',EP/'outputs/private-production-v1/captions_measured.srt',EP/'editor/mix_receipt.json']],
          pinned_scene_graphics=review['coverage']['current_graphic_comparison']['details'],
          scope=['변경HTML/10개postcarve해시목록 확인;변경없는장해시재사용','45개정적SVG/공통CSS/폰트/오디오내용이동일한지해시로대조하며45대표재추출안함','CUES150와BEATS의원어시각/표시문불변을메타데이터로확인','실제화면재검수는CH01브랜드경계·S031상품기한큐·S040월액/저축큐와앞뒤연결만'],
          brand=dict(hook_cut_s=hook,source_frame_samples_s=[hook-1/30,hook,hook+1/30,24.446,first['start_s']-.001,first['start_s'],first['start_s']+.001],
                     expected_before='S001',expected_from_cut='S002',cue_start_s=first['start_s'],caption_before_actual_start='빈문자+본문흰박스유지',forbidden='TTS/오디오/EDL시간변경,임의70ms연장,이전훅/큐hold'),
          focus_samples=selected,
          focus_expected={'C07_S031Q002':{'include':['1개월 안에 전입','전입일부터 2년 실거주'],'exclude':['6개월']},
                          'C07_S031Q003':{'include':['6개월 안에 전입·입증서류'],'exclude':['1개월 안에 전입']},
                          'C09_S040Q003':{'include':['227.3만원','285.5만원','170.0만원','213.5만원'],'exclude':['저축']},
                          'C09_S040Q004':{'include':['저축 여유 42.7만원 → 약 15.5만원 부족','저축 여유 100.0만원 → 56.5만원'],'exclude':['227.3만원','285.5만원','170.0만원','213.5만원']}},
          conditional_approval='직접새프레임/강조/경계를확인하고2건닫힌뒤에만source_approved=true, required=[]와실제postcarve10HTML SHA를발급.자동통과없음.',
          other_gates='voiceQA독립대기.실제MP4/청취/연속재생/최종미디어승인은별도.')
write('targeted_recheck_plan.json',plan)
write('targeted_recheck_ready.json',dict(status=plan['status'],source_approved=False,media_approved=False,plan='qa/source-media-v1/targeted_recheck_plan.json',open_required=plan['open_required'],baseline_chapters_preserved=sum(r['same_as_reviewed'] for r in rows),changed_since_last_capture=[r['chapter'] for r in rows if not r['same_as_reviewed']],next_owner='Carson수정판source/CLI/해시receipt전달→QA해당큐·경계만재검수',actual_listening=False,continuous_playback=False))
print(json.dumps(dict(status=plan['status'],preserved=sum(r['same_as_reviewed'] for r in rows),changed_since_capture=[r['chapter'] for r in rows if not r['same_as_reviewed']],cue_samples=len(selected)),ensure_ascii=False))
