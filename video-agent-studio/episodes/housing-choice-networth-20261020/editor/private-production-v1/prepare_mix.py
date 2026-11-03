"""Measured-only local BGM placement and canonical voiceover carve. No video render."""
import hashlib
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2];OUT=EP/'outputs/private-production-v1'
CARVE=Path('C:/Users/e2ken/.agents/skills/hyperframes-audio/scripts/carve.mjs')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def put_audio(source,tags):
    root=source.index('<div id="root"')
    depth=0
    for m in re.finditer(r'</?div\b[^>]*>',source[root:]):
        depth+=-1 if m.group().startswith('</') else 1
        if depth==0:return source[:root+m.start()]+tags+source[root+m.start():]
    raise ValueError('Cannot identify composition root end')


class AudioAttrs(HTMLParser):
    def __init__(self):super().__init__();self.rows={}
    def handle_starttag(self,tag,attrs):
        row=dict(attrs)
        if tag=='audio':self.rows[row.get('id')]=row


def main():
    plan=read(OUT/'render_plan.json')
    if plan['status']!='measured_audio_units':raise ValueError('Canonical carve requires actual measured build')
    lock=read(EP/'director/two-episode-production-v1/locked_script.json')
    if lock['script_sha256']!=plan['script_sha256']:raise ValueError('Mix script lock differs from build')
    receipt=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json')
    if receipt['status']!='f32le_decode_pass':raise ValueError('Full FFmpeg smoke receipt not passed')
    ffmpeg=ROOT/receipt['binary']
    if sha(ffmpeg)!=receipt['binary_sha256']:raise ValueError('Full FFmpeg binary hash mismatch')
    core=OUT/'audio-deps'
    if read(core/'node_modules/@hyperframes/core/package.json')['version']!='0.8.181':raise ValueError('Canonical core version mismatch')
    music=ROOT/plan['brand_assembly']['existing_music']['path']
    if sha(music)!=plan['brand_assembly']['existing_music']['sha256']:raise ValueError('Music lock mismatch')
    env=os.environ.copy();env['PATH']=str(ffmpeg.parent)+os.pathsep+env['PATH']
    logs=HERE/'checks/carve';logs.mkdir(parents=True,exist_ok=True)
    report={'status':'running','script_sha256':plan['script_sha256'],'audio_revision':'production-injoon-v5','canonical_script_sha256':sha(CARVE),
            'ffmpeg_sha256':sha(ffmpeg),'ffmpeg_receipt_sha256':sha(EP/'director/two-episode-production-v1/ffmpeg_receipt.json'),
            'core_version':'0.8.181','strength':0.8,'global_install':False,'chapters':[],'actual_listening':False}
    offset=0
    selected=set(map(int,sys.argv[1:])) if sys.argv[1:] else set(range(1,11))
    old_mix=read(HERE/'mix_receipt.json') if selected!=set(range(1,11)) else None
    for ch in plan['chapters']:
        folder=OUT/ch['project'];file=folder/'index.html';timing=read(folder/'timing.json')
        if ch['chapter'] not in selected:
            prior=next(c for c in old_mix['chapters'] if c['chapter']==ch['chapter'])
            if sha(file)!=prior['html_sha256']:raise ValueError('Cannot reuse canonical carve from changed source')
            report['chapters'].append(prior);offset+=ch['total_seconds'];continue
        duration=ch['last_speech_end_s'] if ch['chapter']==10 else ch['total_seconds']
        bed=folder/'assets/music-bed.wav'
        # Loop the locked source locally; continue its content clock across chapter cuts.
        argv=[str(ffmpeg),'-v','error','-y','-stream_loop','-1','-ss',str(round(offset%195.892250,6)),'-i',str(music),'-t',str(duration),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)]
        run=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',errors='replace')
        if run.returncode:raise RuntimeError(run.stderr)
        before=file.read_text(encoding='utf8')
        (logs/f'ch{ch["chapter"]:02d}.before_carve.html.txt').write_text(before,encoding='utf8')
        narration=re.search(r'<audio\b[^>]*id="narration"[^>]*></audio>',before)
        if not narration:raise ValueError('Measured narration tag is missing')
        voice=narration.group().replace('id="narration"','id="narration" data-audio-group="voiceover"')
        source=before[:narration.start()]+before[narration.end():]
        if 'id="music-bed"' in source:raise ValueError('Rebuild measured source before applying carve again')
        tags=voice+f'<audio id="music-bed" class="clip" data-audio-group="music" src="assets/music-bed.wav" data-start="0" data-duration="{duration}" data-track-index="11" data-volume="1"></audio>'
        file.write_text(put_audio(source,tags),encoding='utf8')
        command=['node',str(CARVE),'--comp',str(file),'--bed','music-bed','--voice','narration','--strength','0.8','--core',str(core)]
        r=subprocess.run(command,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
        (logs/f'ch{ch["chapter"]:02d}.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf8')
        if r.returncode:
            report['status']='failed';report['failed_chapter']=ch['chapter'];dump(HERE/'mix_receipt.json',report)
            raise RuntimeError('Canonical carve failed; see '+str(logs/f'ch{ch["chapter"]:02d}.log'))
        parser=AudioAttrs();parser.feed(file.read_text(encoding='utf8'));attrs=parser.rows['music-bed']
        settings=json.loads(attrs['data-fx-carve']);chain=json.loads(attrs['data-fx-chain']);automation=json.loads(attrs['data-automation'])
        ids={n['id'] for n in chain['nodes']}
        if not any(n['type']=='peaking' and n.get('fromCarve') for n in chain['nodes']):raise ValueError('Missing spectral carve')
        if not any(n['type']=='gain' and n.get('fromCarve') for n in chain['nodes']):raise ValueError('Missing canonical level-match stage')
        for lane in automation['lanes']:
            target=lane['target'].split('.')
            if len(target)!=3 or target[0]!='fx' or target[1] not in ids:raise ValueError('Inert or dangling automation target')
            if len(lane['points'])<2:raise ValueError('Speech-following envelope missing')
        if not settings.get('enabled') or not settings.get('sources'):raise ValueError('Carve settings inactive')
        report['chapters'].append({'chapter':ch['chapter'],'html_sha256':sha(file),'voice_sha256':sha(folder/'assets/narration.wav'),
          'bed_sha256':sha(bed),'bed_duration_s':duration,'music_content_offset_s':offset%195.892250,'carve_argv':command,
          'settings':settings,'fx_node_ids':sorted(ids),'automation_lanes':len(automation['lanes']),'full_chain_and_envelopes_in':'index.html'})
        offset+=ch['total_seconds'];print(json.dumps({'carve_chapter':ch['chapter'],'spectral_and_level_envelopes':'pass'}),flush=True)
    report['status']='canonical_carve_pass';dump(HERE/'mix_receipt.json',report)
    plan['prepared_mix_receipt']='editor/private-production-v1/mix_receipt.json';plan['prepared_mix_receipt_sha256']=sha(HERE/'mix_receipt.json')
    dump(OUT/'render_plan.json',plan)
    return 0


if __name__=='__main__':sys.exit(main())
