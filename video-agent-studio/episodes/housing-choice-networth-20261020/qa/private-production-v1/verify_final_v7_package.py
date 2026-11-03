"""Read exact final v7 artifacts; write technical/package evidence only in QA."""
import hashlib, json, math, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
QA=Path(__file__).resolve().parent
EP=QA.parents[1]
ROOT=EP.parents[2]
SOURCE=EP/'outputs/private-production-v3'
RELEASE=EP/'outputs/private-release-v3'
sys.dont_write_bytecode=True
sys.path.insert(0,str(QA/'asr/deps'))
import av
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def pin(p):return {'path':p.relative_to(EP).as_posix(),'sha256':sha(p)}
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    rp=EP/'editor/private-production-v3/render_receipt.json';receipt=read(rp)
    assert receipt['status']=='rendered_technical_pass_full_media_review_pending' and receipt['decode_returncode']==0
    video=Path(receipt['final_file']);vsha=sha(video)
    assert vsha==receipt['final_sha256']=='28b2623aed5b74478a113ab453825cb809311c7bc46ce5f94b1c90cc009273b8'
    dest=QA/f'encoded-v7/final-{vsha[:12]}';assert not dest.exists(),'Preserve existing exact-artifact evidence'
    dest.mkdir(parents=True)
    timingp=EP/'narration/free-tts-v1/caption-v7/final_timing.json';timing=read(timingp)
    sourcep=QA/'source_v7_pass_receipt.json';source=read(sourcep)
    assert source['approved'] is True and sha(sourcep)==receipt['gate_receipts']['independent_qa_sha256']
    assert sha(timingp)==source['caption_timing_sha256']=='a97d59fbe5d9dccb4b4b936dc8a839c4a02d754479a34bab4220760925bd40f7'
    script=EP/'outputs/script-final-v6/script_v6.md';assert sha(script)==timing['script_sha256']==source['script_sha256']
    for p in source['current_HTML_pins']:
        assert sha(SOURCE/f'ch{p["chapter"]:02d}/index.html')==p['html_sha256']
        assert sha(SOURCE/f'ch{p["chapter"]:02d}/timing.json')==p['timing_sha256']
        rendered=next(c for c in receipt['chapters'] if c['chapter']==p['chapter'])
        assert rendered['html_sha256']==p['html_sha256'] and sha(Path(rendered['file']))==rendered['output_sha256']
    edlp=SOURCE/'assembly_edl.json';edl=read(edlp)
    srt=SOURCE/'captions_measured.srt'
    assert sha(srt)==receipt['captions_sha256']==source['subtitles_sha256']=='23f177b22a24696f4d1889fc70506608de5ce343af463748061db94446d09aaf'
    assert sha(edlp)==source['EDL_sha256']
    blocks=re.split(r'\n\s*\n',srt.read_text(encoding='utf-8-sig').strip());assert len(blocks)==206
    assert sum(len(c['cues']) for c in timing['chapters'])==206
    streams=[]
    with av.open(str(video)) as container:
        duration=container.duration/av.time_base
        for s in container.streams:
            c=s.codec_context;row={'type':s.type,'codec':c.name,'start_s':float(s.start_time*s.time_base),'duration_s':float(s.duration*s.time_base)}
            if s.type=='video':
                row.update(width=c.width,height=c.height,pix_fmt=c.format.name,fps=float(s.average_rate),frames=s.frames)
                assert (c.name,c.width,c.height,c.format.name,float(s.average_rate))==('h264',1920,1080,'yuv420p',30.0)
                assert s.frames==round(edl['total_seconds']*30)==45758
            else:
                assert s.type=='audio' and c.name=='aac' and c.sample_rate==48000 and c.channels==2
                row.update(sample_rate=c.sample_rate,channels=c.channels)
            streams.append(row)
    assert len(streams)==2 and abs(duration-edl['total_seconds'])<.002
    assert abs(streams[0]['duration_s']-streams[1]['duration_s'])<1/30
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json');ffmpeg=ROOT/provision['binary'];assert sha(ffmpeg)==provision['binary_sha256']
    argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-']
    decoded=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace')
    log=dest/'full_AV_decode.log';log.write_text(decoded.stderr,encoding='utf-8');assert decoded.returncode==0 and not decoded.stderr.strip()
    def audiohash(p):
        result=subprocess.run([str(ffmpeg),'-v','error','-nostdin','-i',str(p),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-'],capture_output=True,text=True,encoding='utf-8',errors='replace')
        assert result.returncode==0 and not result.stderr.strip();return result.stdout.strip()
    prior=Path(receipt['audio_stream_copy_from']);assert sha(prior)=='14078d1309cb2e32e766a13d66b9aee278af083a14eb75806a21a2acfae2fc0b'
    new_aac=audiohash(video);old_aac=audiohash(prior)
    assert new_aac==old_aac==receipt['audio_stream_SHA256']=='SHA256=8c4cbc8664ca3ce4d4a34b0de83b2ba0e00ac06b285f0e176af0832bbda91b32'
    expected={'metadata_measured.json':'ae69b6ce964e62ec4e4de853f84220f6e4c2060edca1627e9e8a8bb0ddbfae32','description_measured.md':'69f47cb49aadbc2390d487eb274d971af0927c3e1fcbb093529ce95272053eeb','thumbnail.png':'b3588479af8459405883bfcb1c6cbb257e4bed02243265408a53ba22689a8fc9'}
    for name,expected_sha in expected.items():assert sha(RELEASE/name)==sha(EP/'outputs/private-release-v2'/name)==expected_sha
    meta=read(RELEASE/'metadata_measured.json');description=(RELEASE/'description_measured.md').read_text(encoding='utf-8-sig')
    assert meta['visibility']=='private' and meta['published'] is False and meta['scheduled'] is False
    assert meta['edl_sha256']==sha(edlp) and meta['description']=='description_measured.md' and meta['description_bytes']==len(description.encode('utf-8'))
    assert '\ufffd' not in description+json.dumps(meta,ensure_ascii=False)+srt.read_text(encoding='utf-8-sig')
    chapter_checks=[]
    for c in meta['chapters']:
        start=0 if c['chapter']==1 else next(s['global_start_s'] for s in edl['segments'] if s['id']==f'chapter_{c["chapter"]}')
        stamp=f'{math.floor(start)//60:02}:{math.floor(start)%60:02}'
        assert abs(start-c['start_s'])<1e-6 and stamp==c['timestamp'] and f'{stamp} {c["title"]}' in description
        chapter_checks.append({'chapter':c['chapter'],'global_start_s':start,'timestamp':stamp})
    last=timing['chapters'][-1];offset=next(o['global_offset_s'] for o in edl['offset_map'] if o['chapter']==10)
    speech=offset+last['last_speech_end_s'];outro=next(s['global_start_s'] for s in edl['segments'] if s['id']=='clean_brand_outro')
    assert outro-speech>=3
    dsp=EP/'director/two-episode-production-v1/final_signal_v6/receipt.json';dr=read(dsp)
    assert dr['exit_code']==0 and dr['video_sha256']==sha(prior)
    paths={'script':script,'video':video,'subtitles':srt,'metadata':RELEASE/'metadata_measured.json','description':RELEASE/'description_measured.md','thumbnail':RELEASE/'thumbnail.png','edl':edlp,'narration_timing':timingp}
    report={'status':'pass_independent_final_v7_technical_package_checks','checked_at':datetime.now(timezone.utc).isoformat(),
      **{k+'_sha256':sha(p) for k,p in paths.items()},'artifacts':{k:pin(p) for k,p in paths.items()},
      'video_bytes':video.stat().st_size,'duration_s':duration,'streams':streams,'completed_render_receipt':pin(rp),'source_pass_receipt':pin(sourcep),
      'full_AV_decode':{'returncode':decoded.returncode,'stderr_empty':True,'argv':argv,'log':pin(log),'ffmpeg_sha256':sha(ffmpeg)},
      'AAC_identity':{'new_payload_sha256':new_aac,'prior_payload_sha256':old_aac,'prior_MP4':pin(prior),'exact_prior_stream_copied':True,'own_comparison_performed':True},
      'source_all206_caption_conservation_reused':{'receipt':pin(QA/'caption-v7/source_precheck.json'),'current10_HTML_timing_match_render_receipts':True,'SRT206_exact_SHA_unchanged':True,'cue_semantics_and_actual_source_fit':'Prior exact206 source approval; actual final burned-in samples inspected separately'},
      'packaging':{'unchanged_private_metadata_description_thumbnail':True,'prior_content_visual_review_reused':pin(QA/'final_media_v6_reaudit.json'),'chapter_alignment':chapter_checks,'description_raw_bytes':(RELEASE/'description_measured.md').stat().st_size,'description_LF_UTF8_bytes':len(description.encode('utf-8'))},
      'last_speech':{'global_end_estimate_s':speech,'outro_start_s':outro,'gap_s':outro-speech,'basis':last['last_speech_end_basis'],'actual_listening':False},
      'prior_audio_evidence_reused':{'ASR_v6_delta':pin(QA/'audio_v6_delta_handoff.json'),'DSP_receipt':pin(dsp),'basis':'Exact final AAC payload identity verified independently; no new ASR, DSP or listening performed','v6_integrated_LUFS':-17.2,'v6_LRA_LU':4.1,'v6_truepeak_dBFS':-2.8},
      'code_sha256':sha(Path(__file__)),'required_issues':[],'critical_issues':[],'actual_listening':False,'continuous_playback':False,'final_media_approved':False}
    dump(dest/'package_checks.json',report)
    print(json.dumps({'status':report['status'],'dest':str(dest),'video_sha256':vsha,'video_bytes':video.stat().st_size,'duration_s':duration,'AAC_identical':True,'decode_returncode':decoded.returncode,'required_issues':[]}))

if __name__=='__main__':main()
