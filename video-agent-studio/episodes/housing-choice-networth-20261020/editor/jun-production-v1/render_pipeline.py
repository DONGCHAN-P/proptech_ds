"""New Jun render; fresh mix. Reuse verified local renderer and assembly implementation.

Default prepares exact commands; --execute runs within existing user render authorization.
All final independent media approvals remain pending main's Codex/Claude dual review.
"""
import importlib.util, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
spec=importlib.util.spec_from_file_location('frozen_renderer',EP/'editor/private-production-v2/render_pipeline.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old.HERE=HERE;old.OUT=EP/'outputs/jun-production-v1';old.DEST=old.OUT/'renders/measured-jun-v1'
original_assembly=old.assembly_command
def assembly(plan,edl,ffmpeg):
    argv,previous=original_assembly(plan,edl,ffmpeg)
    final=old.DEST/'housing_choice_jun_v1.mp4';argv[-1]=str(final)
    return argv,final
old.assembly_command=assembly

def preflight(plan,unused):
    auth_path=EP/'director/launch-and-jun-v1/authorization.json';auth=old.read(auth_path)
    build=old.read(HERE/'build_receipt.json')
    if plan['audio_revision']!='jun-production-v1' or plan['status']!='measured_audio_units':raise ValueError('Actual Jun source required')
    if auth['script_sha256']!=plan['script_sha256'] or auth['additional_cash_usd_cap']!=0:raise ValueError('Authorization/script differs')
    if old.sha(EP/plan['caption_timing_path'])!=plan['caption_timing_sha256']:raise ValueError('Narrator timing changed')
    if old.sha(old.ROOT/build['narrator_handoff'])!=build['narrator_handoff_sha256']:raise ValueError('Narrator handoff changed')
    r=old.read(HERE/'static_checks.json');mix=old.read(HERE/'mix_receipt.json');cli=old.read(HERE/'checks/summary.json');bbox=old.read(old.OUT/'preview/bbox_report.json')
    if r['status']!='pass' or r['caption_timing_sha256']!=plan['caption_timing_sha256']:raise ValueError('Current static source check required')
    if mix['status']!='canonical_carve_pass' or mix['audio_revision']!='jun-production-v1':raise ValueError('Fresh Jun carve required')
    if cli['status']!='pass' or bbox['status']!='sampled_bbox_pass':raise ValueError('Current CLI/BBox checks must pass')
    if any(r['clipped_tweens'] for r in bbox['motion_windows']) or not all(r['backward_seek_pixel_identical'] for r in bbox['seek_safe_checks']):raise ValueError('Motion/seek check failed')
    inputs=old.read(old.OUT/'input_manifest.json')['inputs_sha256']
    for rel,sha in inputs.items():
        if old.sha(old.ROOT/rel)!=sha:raise ValueError('Frozen input changed: '+rel)
    for ch in plan['chapters']:
        file=old.OUT/ch['project']/'index.html'
        for rows in [r['chapters'],mix['chapters'],cli['chapters'],bbox['checked_chapters']]:
            row=next(x for x in rows if x['chapter']==ch['chapter'])
            if row['html_sha256']!=old.sha(file):raise ValueError('Stale current HTML evidence')
    return {p.relative_to(EP).as_posix():old.sha(p) for p in [auth_path,HERE/'static_checks.json',HERE/'mix_receipt.json',HERE/'checks/summary.json',old.OUT/'preview/bbox_report.json']}
old.preflight=preflight

if __name__=='__main__':
    # Old argument is retained for interface compatibility; the new gate validates current evidence above.
    if '--execute' in sys.argv and '--qa-receipt' not in sys.argv:
        sys.argv += ['--qa-receipt',str(HERE/'static_checks.json')]
    result=old.main()
    receipt=HERE/'render_receipt.json'
    if receipt.exists():
        r=old.read(receipt);r.update(audio_revision='jun-production-v1',fresh_Jun_mix=True,independent_final_media_QA='pending main exact MP4 Codex and Claude review',actual_listening=False,continuous_playback=False)
        old.dump(receipt,r)
    sys.exit(result)
