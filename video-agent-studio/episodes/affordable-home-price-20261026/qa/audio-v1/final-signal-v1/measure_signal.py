"""One completed-final AAC DSP pass; no video decode, ASR, TTS or edits."""
import argparse,hashlib,json,math,re,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;QA=OUT.parent
sys.path.insert(0,str(QA))
from prepare import EP,ROOT,read,sha,pin,dump
FROZEN_GATE_SHA='52b3c4284925f68225974aebcde9aa77ae1838d4c8ca32d1925897829164b639'
FIELDS='Peak_level+Min_level+Max_level+Number_of_samples+Number_of_NaNs+Number_of_Infs+Number_of_denormals'
FILTER=f'aformat=sample_fmts=fltp,astats=metadata=0:reset=0:measure_perchannel={FIELDS}:measure_overall={FIELDS},ebur128=peak=true:framelog=quiet'

def frozen():assert sha(QA/'audio_gate_v3.json')==FROZEN_GATE_SHA,'Frozen audio gate changed'

def numpy_module():
    sys.path.insert(0,read(QA/'config.json')['shared_deps_readonly'])
    import numpy as np
    return np

def parse_log(text):
    summary=text.rsplit('Summary:',1)[-1]
    def get(pattern):
        m=re.search(pattern,summary);assert m,('missing DSP summary',pattern)
        return float(m[1])
    return {'integrated_LUFS':get(r'\bI:\s*([-+\d.]+)\s*LUFS'),'LRA_LU':get(r'\bLRA:\s*([-+\d.]+)\s*LU'),'true_peak_dBTP':get(r'True peak:\s*\n\s*Peak:\s*([-+\d.]+)\s*dBFS'),'astats_relevant_lines':[s.strip() for s in text.splitlines() if any(k in s for k in ['Number of NaNs:','Number of Infs:','Number of denormals:','Peak level dB:','Number of samples:'])]}

def stream_measure(prefix,sample_rate,channels,joins,logp):
    np=numpy_module();frames=0;nan=inf=denorm=rail=0;peak=0.0
    windows=[{'global_join_s':float(t),'center':round(float(t)*sample_rate),'start':max(0,round((float(t)-.025)*sample_rate)),'end':round((float(t)+.025)*sample_rate),'parts':[]} for t in joins]
    argv=prefix+['-map','0:a:0','-vn','-sn','-dn','-af',FILTER,'-c:a','pcm_f32le','-f','f32le','pipe:1']
    begin=time.monotonic()
    with logp.open('wb') as log:
        process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=log)
        while True:
            data=process.stdout.read(65536*channels*4)
            if not data:break
            assert len(data)%(channels*4)==0,'Incomplete PCM frame'
            a=np.frombuffer(data,dtype='<f4').reshape(-1,channels);finite=np.isfinite(a);ab=np.abs(a)
            nan+=int(np.count_nonzero(np.isnan(a)));inf+=int(np.count_nonzero(np.isinf(a)))
            denorm+=int(np.count_nonzero(finite&(ab>0)&(ab<np.finfo(np.float32).tiny)))
            rail+=int(np.count_nonzero(finite&(ab>=1)))
            if np.any(finite):peak=max(peak,float(np.max(ab[finite])))
            end=frames+len(a)
            for w in windows:
                lo=max(frames,w['start']);hi=min(end,w['end'])
                if hi>lo:w['parts'].append(a[lo-frames:hi-frames].copy())
            frames=end
        code=process.wait();assert code==0,('FFmpeg DSP failed',code,str(logp))
    parsed=parse_log(logp.read_text(encoding='utf-8',errors='replace'));join_metrics=[]
    for w in windows:
        a=np.concatenate(w.pop('parts'));assert len(a)==w['end']-w['start']
        k=w['center']-w['start'];assert 0<k<len(a)
        step=np.abs(a[k]-a[k-1]);steps=np.abs(np.diff(a,axis=0));n=round(.008*sample_rate)
        rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)))
        join_metrics.append({**w,'sample_rate':sample_rate,'window_seconds':.05,'sample_count_frames':len(a),'boundary_adjacent_step_per_channel_FS':step.tolist(),'max_adjacent_step_in_window_FS':float(np.max(steps)),'median_adjacent_step_in_window_FS':float(np.median(steps)),'RMS_last8ms_before_FS':rms(a[k-n:k]),'RMS_first8ms_after_FS':rms(a[k:k+n]),'peak_last8ms_before_FS':float(np.max(np.abs(a[k-n:k]))),'peak_first8ms_after_FS':float(np.max(np.abs(a[k:k+n]))),'meaning':'Encoded signal sample only; not listening, perceived click approval or proof of an exact lossless8ms fade.'})
    return {'ffmpeg_command':argv,'elapsed_s':time.monotonic()-begin,'numpy_version':np.__version__,'streamed_PCM_format':'f32le','audio_full_decode_passes':1,'video_decoded_here':False,'decoded_PCM_frames':frames,'decoded_sample_values':frames*channels,'decoded_duration_s':frames/sample_rate,'sample_rate':sample_rate,'channels':channels,'sample_peak_linear':peak,'sample_peak_dBFS':20*math.log10(peak) if peak else None,'rail_or_over_full_scale_sample_values':rail,'clipped_definition':'Count of finite decoded float32 sample values with abs(sample)>=1.0; distinct from ASTATS Peak count and from true intersample peaks.','NaN_sample_values':nan,'Inf_sample_values':inf,'denormal_float32_sample_values':denorm,**parsed,'encoded_EDL_join_signal_samples':join_metrics,'analysis_log':pin(logp)}

def prepare():
    frozen();cmdp=EP/'editor/render_commands.json';cmd=read(cmdp)
    mixp=EP/'editor/mix_receipt.json';mix=read(mixp);edlp=EP/'outputs/private-production-v1/assembly_edl.json';edl=read(edlp)
    receiptp=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/director/two-episode-production-v1/ffmpeg_receipt.json';fr=read(receiptp)
    f=ROOT/fr['binary'];assert sha(f)==fr['binary_sha256']=='2ce797a0f88d7f067180338fb227f7b1928ea727bd9a4d7a1d022f7c52af71a3'
    assert mix['status']=='canonical_carve_pass' and mix['timing_sha256']==edl['timing_sha256']==cmd['timing_sha256']
    assert sha(edlp)==cmd['EDL_sha256']==mix['EDL_sha256']
    graph=Path(cmd['assembly_command'][cmd['assembly_command'].index('-filter_complex_script')+1]);assert sha(graph)==cmd['assembly_filter_sha256']
    text=graph.read_text(encoding='utf-8');fadeins=text.count('afade=t=in:st=0:d=0.008');outs=re.findall(r'afade=t=out:st=([0-9.]+):d=0.008',text)
    assert fadeins==len(outs)==len(edl['segments'])==13
    for s,start in zip(edl['segments'],outs):assert abs(float(start)-(s['source_end_s']-s['source_start_s']-.008))<1e-8
    plan={'status':'prepared_waiting_actual_completed_MP4','frozen_audio_gate':pin(QA/'audio_gate_v3.json'),'script_sha256':edl['script_sha256'],'timing_sha256':edl['timing_sha256'],'ffmpeg':pin(f),'ffmpeg_source_receipt':pin(receiptp),'ffmpeg_version':fr['version'].splitlines()[0],'canonical_carve_receipt':pin(mixp),'EDL':pin(edlp),'render_commands':pin(cmdp),'source_assembly_filter':pin(graph),'source_8ms_fade_audit':{'segments':13,'fade_in_count':fadeins,'fade_out_count':len(outs),'all_end_fades_start_at_segment_length_minus8ms':True,'scope':'Source graph audit; encoded signal must be measured separately.'},'final_render_receipt_path':str(EP/'editor/render_receipt.json'),'planned_final_file':cmd['final_file'],'expected_duration_s':edl['total_seconds'],'EDL_joins_s':[s['global_end_s'] for s in edl['segments'][:-1]],'analysis_filter':FILTER,'analysis_method':'One audio-only FFmpeg decode; ebur128+astats and streamed float32 counts plus all12EDLjoin windows. No saved whole-film PCM or second join decode.','context_only_prior_film':{'integrated_LUFS':-17.2,'true_peak_dBTP':-2.8,'exact_match_required':False},'actual_MP4_opened':False,'DSP_actual_runs':0,'actual_listening':False,'continuous_playback':False,'new_ASR_or_TTS':False}
    dump(OUT/'prepared.json',plan);print({'prepared':True,'source_8ms_fades':13,'encoded_joins_planned':12,'actual_DSP_runs':0},flush=True)

def selftest():
    frozen();p=read(OUT/'prepared.json');np=numpy_module()
    result=stream_measure([p['ffmpeg']['path'],'-hide_banner','-nostdin','-nostats','-v','info','-f','lavfi','-i','sine=frequency=1000:sample_rate=48000:duration=1.2','-ac','2'],48000,2,[.6],OUT/'synthetic_filter_test.log')
    assert result['decoded_PCM_frames']==57600 and result['rail_or_over_full_scale_sample_values']==0
    assert result['NaN_sample_values']==result['Inf_sample_values']==result['denormal_float32_sample_values']==0
    assert math.isfinite(result['integrated_LUFS']) and math.isfinite(result['true_peak_dBTP'])
    a=np.array([float('nan'),float('inf'),-float('inf'),1.,-1.,1e-40,0],dtype=np.float32);ab=np.abs(a);finite=np.isfinite(a)
    assert np.count_nonzero(np.isnan(a))==1 and np.count_nonzero(np.isinf(a))==2
    assert np.count_nonzero(finite&(ab>=1))==2 and np.count_nonzero(finite&(ab>0)&(ab<np.finfo(np.float32).tiny))==1
    dump(OUT/'preparation_tests.json',{'passed':True,'synthetic_only_not_final_MP4':True,'full_filter_summary_parser_and_PCM_stream_test':result,'nonfinite_rail_denormal_counter_unit_test':True,'actual_final_MP4_DSP_runs':0,'actual_listening':False})
    frozen();print({'synthetic_tests_passed':True,'actual_final_MP4_DSP_runs':0},flush=True)

def analyze():
    frozen();plan=read(OUT/'prepared.json')
    for key in ['ffmpeg','ffmpeg_source_receipt','canonical_carve_receipt','EDL','render_commands','source_assembly_filter']:assert sha(Path(plan[key]['path']))==plan[key]['sha256'],('prepared input changed',key)
    receiptp=Path(plan['final_render_receipt_path']);receipt=read(receiptp)
    assert receipt['status']=='rendered_technical_pass_independent_media_review_pending','Wait for completed renderer receipt; do not read partial MP4'
    assert receipt['decode_returncode']==0 and receipt['full_AV_decode'] is True
    mp4=Path(receipt['final_file']);assert str(mp4)==plan['planned_final_file'] and sha(mp4)==receipt['final_sha256']
    assert receipt['render_commands_sha256']==plan['render_commands']['sha256']
    assert not (OUT/'signal_receipt.json').exists(),'Preserve existing signal evidence; use a new stage for changed media'
    streams=[s for s in receipt['ffprobe']['streams'] if s['codec_type']=='audio'];assert len(streams)==1
    audio=streams[0];sr=int(audio['sample_rate']);channels=int(audio['channels']);assert (audio['codec_name'],sr,channels)==('aac',48000,2)
    assert abs(float(audio.get('start_time','0')))<1/sr
    assert not (OUT/'analysis_started.json').exists(),'An actual DSP attempt already exists; preserve evidence and review before any repeat'
    dump(OUT/'analysis_started.json',{'video':pin(mp4),'renderer_receipt':pin(receiptp),'runner':pin(OUT/'measure_signal.py'),'policy':'One actual AAC DSP pass; no automatic repeat after failure.'})
    print('Measuring exact completed final AAC once; no video decode',flush=True)
    measured=stream_measure([plan['ffmpeg']['path'],'-hide_banner','-nostdin','-nostats','-v','info','-i',str(mp4)],sr,channels,plan['EDL_joins_s'],OUT/'analysis.log')
    required=[];recommended=[]
    def issue(ident,evidence,fix):return {'id':ident,'evidence':evidence,'revision':fix,'fix':fix}
    if measured['NaN_sample_values'] or measured['Inf_sample_values']:required.append(issue('SIGNAL-NONFINITE-001',measured,'Investigate nonfinite decoded AAC values in exact MP4; preserve this artifact.'))
    if measured['rail_or_over_full_scale_sample_values']:required.append(issue('SIGNAL-RAIL-001',{'count':measured['rail_or_over_full_scale_sample_values'],'peak_dBFS':measured['sample_peak_dBFS']},'Investigate decoded full-scale/over-range samples; no normalization or render performed by QA.'))
    if measured['sample_peak_linear']==0:required.append(issue('SIGNAL-SILENT-001','Entire decoded track has zero sample peak','Investigate silent final audio.'))
    if abs(measured['decoded_duration_s']-float(audio['duration']))>1024/sr+.002:required.append(issue('SIGNAL-DURATION-001',{'decoded':measured['decoded_duration_s'],'stream':audio['duration']},'Investigate audio sample duration discrepancy beyond one AAC frame.'))
    if measured['true_peak_dBTP']>0:recommended.append(issue('SIGNAL-TRUEPEAK-001',measured['true_peak_dBTP'],'Review observed intersample headroom; no automatic rerender requirement.'))
    if measured['integrated_LUFS'] < -30 or measured['integrated_LUFS'] > -8:recommended.append(issue('SIGNAL-LEVEL-001',measured['integrated_LUFS'],'Review this material level departure; prior-17.2LUFS is context, not a required exact target.'))
    for j in measured['encoded_EDL_join_signal_samples']:
        if max(j['boundary_adjacent_step_per_channel_FS'])>.25 and max(j['boundary_adjacent_step_per_channel_FS'])>10*max(j['median_adjacent_step_in_window_FS'],1e-8):recommended.append(issue('SIGNAL-JOIN-CANDIDATE',j,'Review measured large boundary step in context; not a claim of an audible click.'))
    assert sha(mp4)==receipt['final_sha256'];frozen()
    signal={'status':'actual_final_AAC_signal_measured','approved_for_technical_signal_scope':not required,'script_sha256':plan['script_sha256'],'timing_sha256':plan['timing_sha256'],'video_sha256':receipt['final_sha256'],'video':pin(mp4),'renderer_receipt':pin(receiptp),'renderer_full_AV_decode_reused':True,'new_full_AV_decode_performed':False,'stream_metadata_from_exact_renderer_ffprobe':audio,'stream_metadata_independently_probed_here':False,'frozen_audio_gate':plan['frozen_audio_gate'],'canonical_carve_receipt':plan['canonical_carve_receipt'],'EDL':plan['EDL'],'source_8ms_fade_audit':plan['source_8ms_fade_audit'],'source_assembly_filter':plan['source_assembly_filter'],'ffmpeg':plan['ffmpeg'],'ffmpeg_version':plan['ffmpeg_version'],'measurements':measured,'critical_issues':[],'required_issues':required,'recommended_issues':recommended,'prior_film_context':plan['context_only_prior_film'],'coverage':{'actual_whole_final_AAC_DSP_passes':1,'encoded_join_windows':len(measured['encoded_EDL_join_signal_samples']),'all_EDL_joins_signal_sampled':True,'actual_listening':False,'continuous_playback':False,'perceived_music_voice_balance_approved':False,'encoded8msfade_perceptually_verified':False,'source_carve_settings_audited_from_receipt':True,'new_ASR':False,'new_TTS':False,'new_weights':False,'video_visual_approval':False},'runner':pin(OUT/'measure_signal.py')}
    dump(OUT/'signal_receipt.json',signal)
    dump(OUT/'handoff.json',{'status':'final_AAC_technical_signal_complete','approved_for_technical_signal_scope':not required,'video_sha256':receipt['final_sha256'],'signal_receipt':pin(OUT/'signal_receipt.json'),'required_issues':required,'recommended_issues':recommended,'frozen_audio_gate_SHA_unchanged':FROZEN_GATE_SHA,'actual_listening':False,'continuous_playback':False})
    print({'signal_receipt':str(OUT/'signal_receipt.json'),'LUFS':measured['integrated_LUFS'],'LRA':measured['LRA_LU'],'dBTP':measured['true_peak_dBTP'],'required':len(required)},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['prepare','selftest','analyze']);a=ap.parse_args()
    {'prepare':prepare,'selftest':selftest,'analyze':analyze}[a.command]()
