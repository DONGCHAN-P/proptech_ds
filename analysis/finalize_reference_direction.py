import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
ep = root / 'video-agent-studio/episodes/goyang-changneung-20261015'
out = ep / 'outputs/reference-direction-v1'
ids = ['FSB-esdhikE', 'u3Ncol4Jx5I', 'SbDrzVB47xQ']
evidence = []
for video_id in ids:
    folder = ep / 'visual/reference-analysis' / video_id
    report = folder / 'report.md'
    content = report.read_text(encoding='utf-8')
    assert content and content.count('?') < 20, report
    json.loads((folder / 'evidence.json').read_text(encoding='utf-8-sig'))
    json.loads((folder / 'handoff.json').read_text(encoding='utf-8-sig'))
    evidence.append({'id': video_id, 'report': str(report.relative_to(root)),
                     'sha256': hashlib.sha256(report.read_bytes()).hexdigest()})
state_path = ep / 'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
script = ep / 'writer/script-v1/script_v1.md'
assert hashlib.sha256(script.read_bytes()).hexdigest() == state['source_script_sha256']
state['reference_direction'] = {
    'revision': 'reference-direction-v1',
    'guide': 'guides/레퍼런스_설명과_자료연출.md',
    'episode_plan': 'outputs/reference-direction-v1/창릉_레퍼런스_적용안.md',
    'script_unchanged': True, 'actual_listening': False,
    'sound_effect_reference_analysis': 'unverified; proposals_only',
    'frames_reviewed_by_specialists': 36, 'continuous_playback': False,
}
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
preflight_path = ep / 'preflight.json'
preflight = json.loads(preflight_path.read_text(encoding='utf-8'))
preflight['reference_direction'] = state['reference_direction']
preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
from notify.telegram import send
sent = send('창릉 레퍼런스 분석·가이드 추가: 제공하신 3편의 표본 프레임 총36장과 확보 자막을 확인했습니다. 고정 위치 지도+주제별 근거 교체, 학교·도로·단지의 생활 관계, 후보별 한 줄 결론을 채택했습니다. 제작 기본가이드에 연결하고 outputs/reference-direction-v1/창릉_레퍼런스_적용안.md에 M000~M009 화면 계획과 버스·도로 문단 구성을 추가했습니다. 원영상 효과음·실제 전환속도는 청취/연속재생 미검증이며 효과음은 후보 제안만 기록했습니다. 낭독·승인 해시·예산 상태는 유지했습니다.')
receipt = {'evidence': evidence, 'script_sha256_unchanged': state['source_script_sha256'],
           'telegram_notice_sent': sent, 'scope': state['reference_direction']}
(out / 'manifest.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'reports_verified': len(evidence), 'script_unchanged': True, 'telegram_notice_sent': sent}))
