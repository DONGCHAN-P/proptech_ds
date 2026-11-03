"""Adapt the previously verified Jun generator to this exact frozen input.

Creates a new version only. It never generates speech or creates authorization.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
OUT = EP/'narration/jun-user-script-v1'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

manifest=read(OUT/'narration_manifest.json')
original_body_sha=sha(OUT/'narration_body.txt')
cfg_sha=sha(ROOT/'config/tts.json')
raw={'source_doc_sha256':manifest['source_doc_sha256'],'source_manifest_sha256':sha(OUT/'narration_manifest.json'),'inputs':{'tts_config':{'sha256':cfg_sha}}}
write(OUT/'generator_raw_manifest.json',raw)
inp={'revision':'jun-user-script-v1-chapter-inputs','script_sha256':original_body_sha,'source_doc_sha256':manifest['source_doc_sha256'],'raw_manifest':{'path':str((OUT/'generator_raw_manifest.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(OUT/'generator_raw_manifest.json')},'paragraphs':[{'paragraph_id':c['chapter_id']+'P01','scene_id':c['chapter_id'],'proposed_spoken_text':c['text'],'characters':c['characters'],'proposed_spoken_text_sha256':c['sha256'],'source_paragraph_ids':c['paragraph_ids']} for c in manifest['chapters']]}
write(OUT/'generation_input.json',inp)
input_sha=sha(OUT/'generation_input.json')
assert sum(p['characters'] for p in inp['paragraphs']) == 5797
old=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/narration/jun-production-v1/generate.mjs'
code=old.read_text(encoding='utf-8-sig')
replacements={
    "const SCRIPT='0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7';":f"const SCRIPT='{original_body_sha}';",
    "const MANIFEST='ea636bf3e07e4fa73fd7dbb25f04e89c38aec191cad02abf3de309af6fbd72a7';":f"const MANIFEST='{input_sha}';",
    'CAP=10739':'CAP=7000',
    "narration/jun-replacement-v1/pronunciation_proposal.json":"narration/jun-user-script-v1/generation_input.json",
    "director/launch-and-jun-v1/authorization.json":"director/jun-user-script-v1/authorization.json",
    "outputs/script-final-v6/script_v6.md":"narration/jun-user-script-v1/narration_body.txt",
    '10,739크레딧 상한으로 Jun 생성 승인':'7,000크레딧 상한으로 Jun 생성 승인',
    "narration/jun-replacement-v1/narration_manifest.json":"narration/jun-user-script-v1/generator_raw_manifest.json",
    'input.paragraphs.length,54':'input.paragraphs.length,7',
    'p.proposed_spoken_text].length,0),8949':'p.proposed_spoken_text].length,0),5797',
    'paragraph_count:54,input_characters:8949':'chapter_count:7,input_characters:5797',
    'paragraphs:54,characters:8949':'chapters:7,characters:5797',
    "path.join(EP,'outputs/private-production-v1/media-bin/ffmpeg.exe')":"path.join(ROOT,'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe')",
    "ledger.requests.length===54":"ledger.requests.length===7",
    "'all54_generated_measured_alignment_validated_not_listened'":"'all7_chapters_generated_measured_alignment_validated_not_listened'",
}
for before,after in replacements.items():
    assert before in code, f'Generator template changed: {before}'
    code=code.replace(before,after)
assert '10739' not in code and '8949' not in code and '===54' not in code
extra="""
assert.equal(auth.source_doc_sha256,input.source_doc_sha256);
assert.equal(auth.material_facts_cleared,true);
assert.equal(auth.input_characters,5797);
assert.equal(sha(await bytes(path.join(EP,'narration/jun-user-script-v1/narration_manifest.json'))),(await readJSON(path.join(EP,'narration/jun-user-script-v1/generator_raw_manifest.json'))).source_manifest_sha256);
"""
code=code.replace("assert.equal(input.paragraphs.length,7);",extra+"assert.equal(input.paragraphs.length,7);")
dependency_paths=[ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/narration/production-v1/common.mjs', ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe']
dependencies=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in dependency_paths]
dependency_guard='const DEPENDENCIES='+json.dumps(dependencies,ensure_ascii=False)+';\nfor(const dependency of DEPENDENCIES)assert.equal(sha(await bytes(path.join(ROOT,dependency.path))),dependency.sha256,"Execution dependency changed");\nconst selectedFFmpeg={path:path.resolve(ff),sha256:sha(await bytes(ff))};\nassert.equal(selectedFFmpeg.sha256,DEPENDENCIES[1].sha256,"Selected FFmpeg differs from frozen dependency");\n'
code=code.replace('const ff=findFFmpeg();','const ff=findFFmpeg();\n'+dependency_guard)
code=code.replace('authorization_id:auth.authorization_id,','dependencies:DEPENDENCIES,selected_ffmpeg:selectedFFmpeg,authorization_id:auth.authorization_id,')
header='// This episode: 7 chapters of the user-authored 48-paragraph script; never reuses prior episode authorization.\n'
(OUT/'generate.mjs').write_text(header+code,encoding='utf-8')
write(OUT/'generation_readiness.json',{'status':'staged_not_authorized','source_doc_sha256':manifest['source_doc_sha256'],'source_manifest_sha256':sha(OUT/'narration_manifest.json'),'generation_input_sha256':input_sha,'body_sha256':original_body_sha,'generator_sha256':sha(OUT/'generate.mjs'),'template_source':str(old.relative_to(ROOT)).replace('\\','/'),'template_sha256':sha(old),'input_characters':5797,'chapter_requests':7,'included_cap':7000,'new_paid_calls':0,'requires':['exact current-episode budget reply','current material-fact clearance','fresh live balance/rate/access checks'],'dependencies':dependencies,'ffmpeg_exists':dependency_paths[1].exists()})
print('Staged7chapter generator. Authorization not written; paid calls0.')
