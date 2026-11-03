"""Measure the final encoded mix. No listening or speech-naturalness claim."""
import json,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import HERE,EP,ROOT,OUT,read,sha,dump
def main():
    receipt=read(HERE/'render_receipt.json');video=Path(receipt['final_file']);assert sha(video)==receipt['final_sha256']
    ff=ROOT/read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json')['binary'];folder=OUT/'qa_signal';folder.mkdir(exist_ok=True)
    jobs={'loudness':['ebur128=peak=true'],'activity':['astats=metadata=0:reset=0','silencedetect=noise=-60dB:d=0.5']}
    results={}
    for name,filters in jobs.items():
        argv=[str(ff),'-hide_banner','-nostdin','-i',str(video),'-map','0:a:0','-vn','-af',','.join(filters),'-f','null','-']
        with (folder/f'{name}.log').open('w',encoding='utf8') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
        results[name]={'argv':argv,'returncode':r.returncode,'log':(folder/f'{name}.log').relative_to(OUT).as_posix(),'log_sha256':sha(folder/f'{name}.log')}
        assert r.returncode==0,'Signal measurement failed'
    text=(folder/'loudness.log').read_text(encoding='utf8');summary=text[text.rfind('Summary:'):]
    activity=(folder/'activity.log').read_text(encoding='utf8')
    def value(pattern,text):
        found=re.findall(pattern,text,re.M);return float(found[-1]) if found else None
    values={'integrated_LUFS':value(r'I:\s+(-?[\d.]+) LUFS',summary),'true_peak_dBFS':value(r'Peak:\s+(-?[\d.]+) dBFS',summary),'RMS_level_dBFS':value(r'RMS level dB:\s+(-?[\d.]+)',activity),'peak_level_dBFS':value(r'Peak level dB:\s+(-?[\d.]+)',activity),'number_of_samples':value(r'Number of samples:\s+(\d+)',activity)}
    assert all(v is not None for v in values.values()),'Missing signal statistics'
    assert values['RMS_level_dBFS']>-55,'No meaningful audio activity measured'
    report={'status':'signal_measurement_complete_human_audio_review_pending','final_sha256':sha(video),'measurements':values,'logs':results,'actual_listening':False,'pronunciation_naturalness':'unverified; ASR/alignment/signal cannot establish listening','continuous_playback':False}
    dump(HERE/'signal_receipt.json',report);print(json.dumps(report['measurements']))
if __name__=='__main__':main()
