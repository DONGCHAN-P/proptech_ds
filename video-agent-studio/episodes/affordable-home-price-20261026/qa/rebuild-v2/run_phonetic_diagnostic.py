"""No-digit formatting diagnostic. Expected text never enters the decoder."""
import hashlib,json,os,re,socket,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
deps=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/deps'
os.environ.update(HF_HUB_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1')
def deny(*a,**k):raise RuntimeError('Offline diagnostic only')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=deny
sys.path.insert(0,str(deps))
import faster_whisper
model=faster_whisper.WhisperModel(str(deps.parent/'models/medium'),device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
tokens=[i for i in range(model.hf_tokenizer.get_vocab_size(with_added_tokens=True)) if re.search('[0-9]',model.hf_tokenizer.decode([i],skip_special_tokens=False))]
out=HERE/'asr-phonetic';out.mkdir(exist_ok=True)
data=json.loads((EP/'narration/rebuild-v2/audio-r2-recovered/final_timing.json').read_text(encoding='utf-8'))
for s in data['scenes']:
 if s['id'] not in ['R005','R008']:continue
 wp=ROOT/s['audio_path'];sha=hashlib.sha256(wp.read_bytes()).hexdigest();target=out/(s['id']+'_'+sha[:12]+'.json');assert not target.exists()
 segments,info=model.transcribe(str(wp),language='ko',beam_size=5,temperature=0,without_timestamps=True,word_timestamps=False,vad_filter=False,condition_on_previous_text=False,initial_prompt=None,hotwords=None,suppress_tokens=[-1]+tokens)
 rows=[{'text':x.text,'tokens':x.tokens} for x in segments];text=''.join(x['text'] for x in rows);assert not re.search('[0-9]',text)
 report={'scene_id':s['id'],'audio_sha256':sha,'recognized':text,'expected':s['spoken_text'],'segments':rows,'model':'medium','constraint':'All tokenizer entries whose individually decoded form contains ASCII0-9 are suppressed uniformly. No expected value, source text, prompt, grammar or hotwords supplied.','suppressed_token_ids':tokens,'actual_listening':False,'classification':'supporting diagnostic only, unconstrained ASR evidence preserved'}
 target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'id':s['id'],'recognized':text},ensure_ascii=False),flush=True)
