"""Versioned full render, gated by measured source/carve/independent-preview receipts.

Default: write concrete commands only. --execute --qa-receipt <file> runs already-authorized work.
--stop-after-chapter N renders only the approved prefix and never assembles the episode.
No TTS, generation API, upload, user-data changes, or speed fitting.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2];OUT=EP/'outputs/private-production-v2'
DEST=OUT/'renders/measured-v6'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,r):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def path_of(name):
    p=Path(name)
    return p if p.is_absolute() else ROOT/p if (ROOT/p).exists() else EP/p


def preflight(plan,qa_path):
    if plan['status']!='measured_audio_units':raise ValueError('Measured build required')
    qa=read(qa_path)
    status=str(qa.get('status','')).lower()
    if not ('pass' in status or '통과' in status) or any(s in status for s in ['pending','미통과','실패']):
        raise ValueError('Independent preview QA has not passed: '+status)
    if qa.get('approved') is False or qa.get('open_issue_ids') or qa.get('required_open_issues',0) or qa.get('required_issues'):raise ValueError('Independent preview issues remain open or approval denied')
    qa_sha=qa.get('script_sha256') or qa.get('checked_sha256') or qa.get('input_revisions',{}).get('script_sha256')
    if qa_sha!=plan['script_sha256']:raise ValueError('Independent preview QA script SHA mismatch')
    for pin in qa.get('current_HTML_pins',[]):
        folder=OUT/f'ch{pin["chapter"]:02d}'
        if sha(folder/'index.html')!=pin['html_sha256'] or sha(folder/'timing.json')!=pin['timing_sha256']:
            raise ValueError('Independent v6 preview source pin is stale')
    for key,file in [('CLI',HERE/'checks/summary.json'),('BBox',OUT/'preview/bbox_report.json'),('mix',HERE/'mix_receipt.json')]:
        expected=qa.get('receipt_SHA256',{}).get(key)
        if expected and expected!=sha(file):raise ValueError('Independent v6 preview receipt pin is stale: '+key)
    audio_path=EP/'qa/private-production-v1/audio_v6_delta_handoff.json'
    audio=read(audio_path)
    if audio.get('approved') is not True or audio.get('required_issues') or audio.get('checked_sha256')!=plan['script_sha256']:
        raise ValueError('Current v6 two-paragraph audio QA must pass')
    mix=read(HERE/'mix_receipt.json')
    if mix['status']!='canonical_carve_pass' or mix['script_sha256']!=plan['script_sha256']:raise ValueError('Current canonical carve receipt required')
    cli=read(HERE/'checks/summary.json');bbox=read(OUT/'preview/bbox_report.json')
    static=read(HERE/'static_checks.json')
    if static['status']!='pass' or static['script_sha256']!=plan['script_sha256']:raise ValueError('Current static source validation must pass')
    if cli['status']!='pass' or bbox['status']!='sampled_bbox_pass':raise ValueError('Current CLI/BBox checks must pass')
    if any(r['clipped_tweens'] for r in bbox['motion_windows']):raise ValueError('Tween timing exceeds actual scene windows')
    if not all(r['backward_seek_pixel_identical'] for r in bbox['seek_safe_checks']):raise ValueError('Seek-safe check failed')
    for key,file in [('CLI_summary_sha256',HERE/'checks/summary.json'),('BBox_report_sha256',OUT/'preview/bbox_report.json'),('mix_receipt_sha256',HERE/'mix_receipt.json')]:
        expected=qa.get('input_revisions',{}).get(key)
        if expected and expected!=sha(file):raise ValueError('Independent preview QA receipt is stale: '+key)
    for ch in plan['chapters']:
        file=OUT/ch['project']/'index.html'
        evidence=[mix['chapters'],cli['chapters'],bbox['checked_chapters']]
        if qa.get('current_source_checks'):evidence.append(qa['current_source_checks'])
        for rows in evidence:
            row=next(r for r in rows if r['chapter']==ch['chapter'])
            if sha(file)!=row['html_sha256']:raise ValueError('Stale source receipt: '+str(file))
    edl=read(EP/'director/two-episode-production-v1/edl_review_v6.json')
    if edl['status']!='passed_source_timing_and_subtitle_plan' or edl['edl_sha256']!=sha(OUT/'assembly_edl.json') or edl['subtitles_sha256']!=sha(OUT/'captions_measured.srt'):
        raise ValueError('Global EDL/SRT source review is stale')
    return {'independent_qa_sha256':sha(qa_path),'audio_delta_qa_sha256':sha(audio_path),'mix_receipt_sha256':sha(HERE/'mix_receipt.json'),'cli_receipt_sha256':sha(HERE/'checks/summary.json'),'bbox_receipt_sha256':sha(OUT/'preview/bbox_report.json'),'edl_review_sha256':sha(EP/'director/two-episode-production-v1/edl_review_v6.json')}


def probe(file,ffprobe,expected):
    cmd=[str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(file)]
    info=json.loads(subprocess.check_output(cmd))
    video=[s for s in info['streams'] if s['codec_type']=='video'];audio=[s for s in info['streams'] if s['codec_type']=='audio']
    if len(video)!=1 or not audio:raise ValueError('Expected one video and an audio stream: '+str(file))
    v=video[0]
    if (v['width'],v['height'],v['r_frame_rate'])!=(1920,1080,'30/1'):raise ValueError('Encoded canvas/fps mismatch')
    if abs(float(info['format']['duration'])-expected)>.06:raise ValueError('Encoded duration differs from measured timeline')
    return info


def assembly_command(plan,edl,ffmpeg):
    # Feed each chapter once and split chapter 1 at the tested hook boundary in one final encode.
    inputs=[DEST/'ch01.mp4',path_of(plan['brand_assembly']['clean_intro']['path'])]
    chapter_index={1:0}
    for c in plan['chapters'][1:]:chapter_index[c['chapter']]=len(inputs);inputs.append(DEST/f'ch{c["chapter"]:02d}.mp4')
    outro_index=len(inputs);inputs.append(path_of(plan['brand_assembly']['clean_outro']['path']))
    filters=['[0:v]split=2[c1vpre][c1vpost]','[0:a]asplit=2[c1apre][c1apost]'];labels=[]
    for i,seg in enumerate(edl['segments']):
        if seg['id']=='opening_hook':vi,ai='c1vpre','c1apre'
        elif seg['id']=='chapter_1_after_hook':vi,ai='c1vpost','c1apost'
        else:
            index=1 if seg['id']=='clean_brand_intro' else outro_index if seg['id']=='clean_brand_outro' else chapter_index[seg['chapter']]
            vi,ai=f'{index}:v',f'{index}:a'
        a,b=seg['source_start_s'],seg['source_end_s'];duration=b-a
        filters.append(f'[{vi}]trim=start={a}:end={b},setpts=PTS-STARTPTS,fps=30,setsar=1,format=yuv420p[v{i}]')
        filters.append(f'[{ai}]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=whole_dur={duration},atrim=duration={duration},afade=t=in:st=0:d=0.008,afade=t=out:st={duration-.008}:d=0.008[a{i}]')
        labels.append(f'[v{i}][a{i}]')
    filters.append(''.join(labels)+f'concat=n={len(labels)}:v=1:a=1[vout][aout]')
    script=DEST/'assembly.ffscript';script.parent.mkdir(parents=True,exist_ok=True);script.write_text(';\n'.join(filters),encoding='utf8')
    final=DEST/'housing_choice_private_v2_injoon_v6.mp4'
    argv=[str(ffmpeg),'-v','warning','-nostdin']
    for file in inputs:argv+=['-i',str(file)]
    argv+=['-filter_complex_script',str(script),'-map','[vout]','-map','[aout]','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-n',str(final)]
    return argv,final


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--qa-receipt');parser.add_argument('--stop-after-chapter',type=int,choices=range(1,11));args=parser.parse_args()
    plan=read(OUT/'render_plan.json');edl=read(OUT/'assembly_edl.json');media=read(EP/'director/two-episode-production-v1/media_assets.json')
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json');ffmpeg=ROOT/provision['binary'];ffprobe=ROOT/media['ffprobe']
    if sha(ffmpeg)!=provision['binary_sha256']:raise ValueError('FFmpeg lock mismatch')
    cli=shutil.which('hyperframes.cmd')
    if not cli or subprocess.check_output([cli,'--version'],text=True).strip()!='0.8.181':raise ValueError('Pinned installed CLI 0.8.181 required')
    DEST.mkdir(parents=True,exist_ok=True)
    commands=[{'chapter':c['chapter'],'cwd':str(OUT/c['project']),'argv':[cli,'render','.', '--fps','30','--quality','delivery','--workers','4','--browser-gpu','--output',str(DEST/f'ch{c["chapter"]:02d}.mp4'),'--frames-cache-dir',str(DEST/'frames-cache'/f'ch{c["chapter"]:02d}')]} for c in plan['chapters']]
    assembly,final=assembly_command(plan,edl,ffmpeg)
    specification={'status':'commands_prepared','pipeline_sha256':sha(Path(__file__)),'script_sha256':plan['script_sha256'],'timing':'measured_audio_units','measured_body_seconds':sum(c['total_seconds'] for c in plan['chapters']),'final_edl_seconds':edl['total_seconds'],'chapter_commands':commands,'assembly_command':assembly,'final_file':str(final),'execute_authorization':'already given by user; measured CLI/BBox, independent preview QA and canonical carve gates apply','stop_after_chapter':args.stop_after_chapter,'assembly_enabled':args.stop_after_chapter is None,'new_tts_or_speed_change':False}
    dump(HERE/'render_commands.json',specification)
    if not args.execute:print(json.dumps({'status':'commands_prepared','path':str(HERE/'render_commands.json'),'final_seconds':edl['total_seconds']}));return 0
    if not args.qa_receipt:raise ValueError('Independent preview QA receipt path required')
    gates=preflight(plan,path_of(args.qa_receipt));plan['full_render_allowed']=args.stop_after_chapter is None;plan['render_gate_receipts']=gates;plan['render_execution_scope']={'stop_after_chapter':args.stop_after_chapter,'assembly_enabled':args.stop_after_chapter is None};dump(OUT/'render_plan.json',plan)
    env=os.environ.copy();env['PATH']=str(ffmpeg.parent)+os.pathsep+str(ffprobe.parent)+os.pathsep+env['PATH'];env['DO_NOT_TRACK']='1'
    env['TEMP']=str(DEST/'tmp');env['TMP']=str(DEST/'tmp');(DEST/'tmp').mkdir(exist_ok=True)
    result={'status':'rendering','gate_receipts':gates,'commands_sha256':sha(HERE/'render_commands.json'),'stop_after_chapter':args.stop_after_chapter,'assembly_enabled':args.stop_after_chapter is None,'chapters':[],'full_listening':False,'continuous_playback':False}
    for row,ch in zip(commands,plan['chapters']):
        if args.stop_after_chapter is not None and ch['chapter']>args.stop_after_chapter:break
        target=DEST/f'ch{ch["chapter"]:02d}.mp4';record=DEST/f'ch{ch["chapter"]:02d}.receipt.json';html_sha=sha(OUT/ch['project']/'index.html')
        if record.exists() and target.exists():
            old=read(record)
            if old['html_sha256']==html_sha and old['output_sha256']==sha(target):result['chapters'].append(old);print(f'reused completed chapter {ch["chapter"]}',flush=True);continue
        if target.exists():raise ValueError('Unverified pre-existing render target; preserve and use a new version path')
        print('render chapter '+str(ch['chapter'])+' / 10',flush=True)
        with (DEST/f'ch{ch["chapter"]:02d}.render.log').open('w',encoding='utf8') as log:
            completed=subprocess.run(row['argv'],cwd=row['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT)
        if completed.returncode:
            result.update(status='render_failed',failed_chapter=ch['chapter'],returncode=completed.returncode);dump(HERE/'render_receipt.json',result);raise RuntimeError('Chapter render failed; log preserved')
        info=probe(target,ffprobe,ch['total_seconds'])
        receipt={'chapter':ch['chapter'],'html_sha256':html_sha,'output_sha256':sha(target),'file':str(target),'ffprobe':info,'argv':row['argv']};dump(record,receipt);result['chapters'].append(receipt)
        dump(HERE/'render_receipt.json',result);print('verified chapter '+str(ch['chapter']),flush=True)
    if args.stop_after_chapter is not None:
        result.update(status='approved_chapter_batch_rendered_waiting_audio_value_review',stopped_before_chapter=args.stop_after_chapter+1,final_assembled=False)
        dump(HERE/'render_receipt.json',result);print(json.dumps({'status':result['status'],'completed_chapters':[c['chapter'] for c in result['chapters']],'stopped_before_chapter':result['stopped_before_chapter']}),flush=True);return 0
    if final.exists():raise ValueError('Final output exists; do not overwrite a versioned render')
    print('assembling tested hook + 5s brand + full chapters + 10s outro',flush=True)
    with (DEST/'assembly.log').open('w',encoding='utf8') as log:joined=subprocess.run(assembly,env=env,stdout=log,stderr=subprocess.STDOUT)
    if joined.returncode:result.update(status='assembly_failed');dump(HERE/'render_receipt.json',result);raise RuntimeError('Assembly failed; see log')
    info=probe(final,ffprobe,edl['total_seconds'])
    decode=[str(ffmpeg),'-v','error','-i',str(final),'-map','0:v:0','-map','0:a:0','-f','null','-']
    decoded=subprocess.run(decode,env=env,capture_output=True,text=True,encoding='utf8',errors='replace');(DEST/'decode.log').write_text(decoded.stderr,encoding='utf8')
    if decoded.returncode or decoded.stderr.strip():raise ValueError('Final decode reported errors')
    result.update(status='rendered_technical_pass_full_media_review_pending',final_file=str(final),final_sha256=sha(final),ffprobe=info,decode_argv=decode,decode_returncode=decoded.returncode,
                  captions_file=str(OUT/'captions_measured.srt'),captions_sha256=sha(OUT/'captions_measured.srt'),actual_listening=False,continuous_playback=False)
    dump(HERE/'render_receipt.json',result);print(json.dumps({'status':result['status'],'file':str(final),'seconds':info['format']['duration'],'sha256':result['final_sha256']}));return 0


if __name__=='__main__':sys.exit(main())
