import hashlib
import json
import re
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
OUT = Path(__file__).resolve().parent
SKILL = ROOT / 'skills/realestate-shorts/SKILL.md'
WORKFLOW = ROOT / 'video-agent-studio/WORKFLOW.md'
REF = SKILL.parent / 'references/production.md'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def links(path):
    result = []
    for value in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
        if '://' in value or value.startswith('#'):
            continue
        target = (path.parent / value.split('#')[0]).resolve()
        result.append({'source': str(path.relative_to(ROOT)), 'link': value,
                       'resolved': target.as_posix(), 'exists': target.exists(),
                       'within_workspace': target.is_relative_to(ROOT)})
    return result

text = SKILL.read_text(encoding='utf-8-sig')
front = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
fields = dict(re.findall(r'^([A-Za-z_][\w-]*):\s*(.+)$', front.group(1), re.M)) if front else {}
all_links = links(SKILL) + links(REF)
workflow_links = [x for x in links(WORKFLOW) if 'realestate-shorts' in x['link']]
episode = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
example_paths = [
    episode / 'director/top20-split-v4/shorts-ui-v2-20261104',
    episode / 'editor/top20-split-v4/shorts-ui-v2-20261104',
    episode / 'outputs/top20-split-v4/shorts-ui-v2-20261104',
    episode / 'qa/top20-split-v4/shorts-ui-v2-20261104',
    episode / 'research/shorts-ui-v2-20261104/research_packet.md',
    episode / 'director/top20-split-v4/shorts-ui-v2-20261104/archive_render_source.py',
]
paths = [{'path': p.as_posix(), 'exists': p.exists(), 'within_workspace': p.is_relative_to(ROOT)} for p in example_paths]
checks = {
    'task_id': 'longform-natural-v5-20261104',
    'phase': 'skill_application_only_before_writer_audit',
    'frontmatter': {'valid_simple_key_value_yaml_shape': bool(front) and len(fields) == 2,
                    'name': fields.get('name'), 'description_present': bool(fields.get('description')),
                    'parser_scope': '현재 두 항목의 단순한 비인용 스칼라 형식을 정규식으로 확인. 범용 YAML 파서는 아니다.'},
    'workflow_discovery_links': workflow_links,
    'local_links': all_links,
    'reference_example_paths': paths,
    'input_sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in [SKILL, REF, WORKFLOW, ROOT / 'config/video_language.json', ROOT / 'config/vertical_video_safe_area.json']},
    'budget_scope': {'skill_grants_generation_or_upload': False,
                     'example_budget_inherited': False,
                     'current_execution': 'local_outlines_and_checks_only',
                     'paid_generation': 'not_executed', 'external_api': 'not_executed',
                     'render': 'not_executed', 'upload': 'not_executed'},
    'catalog_discovery': {'listed_in_current_available_skills': False,
                          'local_explicit_and_workflow_discovery': True,
                          'native_auto_registration': 'unchecked'},
}
checks['pass'] = (bool(front) and fields.get('name') == 'realestate-shorts'
                  and bool(fields.get('description')) and len(workflow_links) == 1
                  and all(x['exists'] and x['within_workspace'] for x in all_links + workflow_links + paths))
(OUT / 'skill_structure_checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'pass': checks['pass'], 'links': len(all_links), 'workflow_links': len(workflow_links),
                  'example_paths': len(paths), 'missing': [x for x in all_links + workflow_links + paths if not x['exists']]}, ensure_ascii=False))
