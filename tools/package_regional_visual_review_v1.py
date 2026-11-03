"""Prepare a scoped visual-review handoff while keeping the voice hold in force."""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, zipfile

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP/'outputs/production-v1-jun'
DEST = EP/'director/production-v1/delivery'

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()
def rel(path): return path.relative_to(ROOT).as_posix()
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def stamp(t):
    n=round(t*1000); h,n=divmod(n,3600000); m,n=divmod(n,60000); s,n=divmod(n,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{n:03d}'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--technical',required=True); ap.add_argument('--qa',required=True)
    args=ap.parse_args(); tp=(ROOT/args.technical).resolve(); qp=(ROOT/args.qa).resolve()
    tp.relative_to(EP/'director'); qp.relative_to(EP/'qa')
    tech,qa=read(tp),read(qp)
    assert qa['counts']['required_open']==0
    assert tech['video']['sha256'] in json.dumps(qa), 'QA must bind this exact MP4'
    video=ROOT/tech['video']['path']; assert sha(video)==tech['video']['sha256']
    assert tech['full_decode']=='pass' and tech['timing_locked'] is False and tech['narration_generated'] is False
    decision=read(ROOT/'output/video_decisions/decisions/5fe307eed02c.json')
    assert decision['resolution']=='deferred_by_user' and decision['status']!='approved'
    assert not (EP/'narration/production-v1/authorization.json').exists()
    timing=read(OUT/'project/timing_resolved.json')
    assert sha(OUT/'project/timing_resolved.json')==tech['timing_sha256']
    display_path=OUT/'checks/visual-review/captions.json'
    assert sha(display_path)==tech['display_captions_sha256']
    display=read(display_path)
    DEST.mkdir(parents=True,exist_ok=True)
    caps=display['captions']
    srt=DEST/'regional_visual_review_v1_provisional.srt'
    srt.write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"]+5)} --> {stamp(c["end"]+5)}\n{c["text"]}' for i,c in enumerate(caps))+'\n',encoding='utf8')
    assert srt.read_bytes()==(OUT/'previews/full_visual_review_v1.srt').read_bytes(), 'Packaged SRT must match the rendered caption export'
    duration=tech['video']['duration']; minutes,seconds=divmod(round(duration),60)
    memo=DEST/'검토안내.md'
    memo.write_text(
        '# 지역별 가격 회복 — 전체 화면 검토본 v1\n\n'
        f'{minutes}분 {seconds}초 · 1920×1080 · 30fps. 승인 대본 v3의 12장면·39문단을 차트·자막·기존 채널 브랜드·배경음악으로 연결했습니다.\n\n'
        '**사용자 요청에 따라 음성 생성은 보류했습니다.** 영상 길이와 자막 시점은 글자 수에 따른 임시값이며 실제 Jun 발화 정렬이 아닙니다. 마지막 임시 자막 종료 뒤3초 유지 후 기존10초 아웃트로가 시작합니다.\n\n'
        '2006년 이후 보유7개 지역 전체 유효거래6,640,041건의 통계와, 동일 단지·면적 조건을 맞춘 자체 지수를 구별합니다. 여섯 지역의 지수 시작은2006Q1, 세종은2015Q1이며 관측 종점은2026Q2입니다. 새로 수집 중인 지역은 이번 동결 분석에 포함하지 않았습니다.\n\n'
        '검수는 전체 파일 디코드·화면 규격·음향 신호와 실제 인코딩된 장면/경계/최장 자막의 표본 프레임을 대상으로 했습니다. 전체 연속 재생·실제 청취·모바일 재생은 수행하지 않았습니다. 세부 범위와 권장 개선 사항은 동봉 독립 검수에 있습니다.\n\n'
        '공개 전에는 공식 지수와의 교차검증, 실제 음성이 있는 버전의 타이밍·발음·청취 검수가 남습니다. 현재 파일은 화면 흐름을 검토하기 위한 버전이며 게시를 실행하지 않았습니다.\n\n'
        '음악: Thinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0\n\n'
        'https://creativecommons.org/licenses/by/4.0/\n\n'
        'Microsoft Fluent Emoji(MIT) 고지는 동봉 권리 파일에 있습니다. 기존 브랜드 도시 영상은 AI 개념 자산이며 지역 근거 화면과 구별합니다.\n',encoding='utf8')
    scenes=read(EP/'outputs/script-review-v3/scenes_v3.json')['scenes']
    titles={s['scene_id']:s['message'] for s in scenes}
    chapter_lines=['','## 검토용 장면 위치','', '- 00:00 채널 인트로']
    for beat in timing['beats']:
        if beat['beat_id'].endswith('-P1'):
            sec=int(beat['start']+5)
            chapter_lines.append(f'- {sec//60:02d}:{sec%60:02d} {titles[beat["scene_id"]]}')
    sec=int(tech['outro_start']);chapter_lines.append(f'- {sec//60:02d}:{sec%60:02d} 채널 아웃트로')
    with memo.open('a',encoding='utf8') as stream:stream.write('\n'.join(chapter_lines)+'\n')
    files={
        '검토안내.md':memo,'검토자막_임시.srt':srt,
        '대본_v3.md':EP/'outputs/script-review-v3/script_v3.md',
        '화면설계.md':EP/'outputs/script-review-v3/visual_storyboard.md',
        '출처와_설명초안.md':OUT/'출처와_설명초안.md',
        '검수/기술검사.json':tp,'검수/독립검수.json':qp,
        '데이터/chart_data.json':EP/'visual/production-v1/chart_data.json',
        '데이터/산식과범위.md':OUT/'data_contract.md',
        '권리/음악.json':OUT/'reusable_assets/thinking_music.license.json',
        '권리/emoji_LICENSE.md':OUT/'reusable_assets/emoji_LICENSE.md',
    }
    manifest={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'full_visual_review_voice_deferred',
        'video':tech['video'],'subtitle':rel(srt),'qa':rel(qp),'qa_sha256':sha(qp),'required_open':0,
        'voice_generated':False,'timing_locked':False,'paid_generation_calls':0,'upload_authorized':False,
        'technical':rel(tp),'technical_sha256':sha(tp),'review_note':rel(memo),
        'files':{rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files.values()}}
    write(DEST/'delivery_manifest.json',manifest)
    archive=DEST/'지역별회복_화면검토자료_v1.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,p in files.items(): z.write(p,name)
        z.write(DEST/'delivery_manifest.json','검수/패키지목록.json')
    with zipfile.ZipFile(archive) as z: assert z.testzip() is None
    write(DEST/'archive_manifest.json',{'path':rel(archive),'sha256':sha(archive),'bytes':archive.stat().st_size})
    state=read(EP/'state.json');state.update(stage='full_visual_review_ready_voice_deferred',updated_at=manifest['at_utc'],
        budget_status='voice_generation_deferred_by_user',audio_status='existing_bgm_only_narration_user_hold',
        timing_locked=False,production_review_video=rel(video),production_review_qa=rel(qp),production_delivery_manifest=rel(DEST/'delivery_manifest.json'))
    state['production_render'].update(status='complete_for_visual_review',video_sha256=tech['video']['sha256'])
    write(EP/'state.json',state)
    pre=read(EP/'episode_preflight_production_v1.json');pre['status']='full_visual_review_ready_voice_deferred'
    pre['approvals']['budget']['status']='deferred_by_user'
    pre['qa'].update(full_decode='pass',actual_encoded_frames=rel(qp),continuous_playback_performed=False,actual_listening_performed=False,
        required_open_issues='Visual-review scoped required issues closed; actual narration QA and public-release official-index crosscheck remain',
        visual_review_required_open=0,provisional_caption_to_outro_gap_seconds=3)
    pre['qa']['evidence_paths'] += [rel(tp),rel(qp)]
    write(EP/'episode_preflight_production_v1.json',pre)
    shelf=read(ROOT/'config/video_shelf.json');entry=next(e for e in shelf['entries'] if e['name']=='지역별가격회복')
    entry['status']='전체 화면 검토본 v1 · 1080p30 · 기존 BGM · 사용자 요청으로 음성 생성 보류 · 임시 자막 타이밍 · 외부 미게시. 대본보기.html은 이전 v1.'
    entry['files'].update({'검토영상.mp4':rel(video),'검토자막_임시.srt':rel(srt),'검토안내.md':rel(memo),'화면검토자료.zip':rel(archive)})
    write(ROOT/'config/video_shelf.json',shelf)
    print(json.dumps({'status':manifest['status'],'video_bytes':video.stat().st_size,'archive_bytes':archive.stat().st_size,'required_open':0},ensure_ascii=False))

if __name__=='__main__': main()
