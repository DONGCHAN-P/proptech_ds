"""Independent exact PCM, frozen-cue and native-character boundary checks; no source writes."""
import sys,json,hashlib,wave,re,array,math
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;E=Q.parent.parent;R=E.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def resolve(s):
 p=Path(s)
 return p if p.is_absolute() else R/p if str(p).replace('\\','/').startswith('video-agent-studio/') else E/p
def pcm(p):
 with wave.open(str(p),'rb') as w:
  assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(44100,1,2)
  return w.readframes(w.getnframes())
def bounds(b):
 a=array.array('h');a.frombytes(b);hit=[i for i,x in enumerate(a) if abs(x)>=32768*.001]
 return dict(first=hit[0]/44100,last=(hit[-1]+1)/44100,peak_dbfs=20*math.log10(max(abs(x) for x in a)/32768),saturated_samples=sum(abs(x)>=32767 for x in a))
def main():
 tp=E/'narration/jun-production-v1/final_timing.json';t=read(tp);old=read(Q/'cue_text_lock.json');lock=read(E/'narration/jun-production-v1/input_lock.json')
 prepared=read(E/'narration/free-tts-v1/prepare-v6/prepared.json');prepared={p['paragraph_id']:p for c in prepared['chapters'] for p in c['paragraphs']}
 ledgerp=E/'narration/jun-production-v1/generation_ledger.json';ledger=read(ledgerp);checks=[];paragraphs=[];cues=[];chapterrows=[];bodyhash=hashlib.sha256()
 def ck(n,v,**ev):checks.append(dict(check=n,pass_=bool(v),**ev))
 ck('locked_script',t['script_sha256']==lock['script_sha256']==old['script']['sha256'])
 ck('all54_complete',len(ledger['requests'])==54 and all(p['status']=='complete' for p in ledger['requests']))
 ck('credit_cap_and_no_retries',sum(p['actual_credits'] for p in ledger['requests'])==3577==ledger['actual_credits']<=10739 and ledger['submitted_characters']==8949 and ledger['automatic_retries']==0)
 bodycursor=0
 for c in t['chapters']:
  cp=resolve(c['audio_file']);b=pcm(cp);datahash=hashlib.sha256(b).hexdigest();bodyhash.update(b)
  ck(f'CH{c["chapter"]} PCM header/count/hash',len(b)//2==c['pcm_frames'] and abs(len(b)/2/44100-c['total_seconds'])<1e-9 and sha(cp)==c['audio_sha256'])
  ck(f'CH{c["chapter"]} body_offset',abs(c['body_offset_s']-bodycursor)<1e-9)
  bodycursor+=c['total_seconds'];cursor=0;chbounds=bounds(b)
  for p in c['paragraphs']:
   pid=p['paragraph_id'];src=resolve(p['wave_file']);raw=pcm(src);a=read(resolve(p['provider_alignment']));pre=prepared[pid];s=pre['spoken_text'];off=p['offset_s'];start=round(off*44100)*2
   ck(pid+' exact input/PCM placement',sha(src)==p['wave_sha256'] and b[start:start+len(raw)]==raw and all(x==0 for x in b[cursor:start]))
   ck(pid+' no clipping of raw audio',p['pcm_frames']==len(raw)//2 and abs(p['measured_seconds']-len(raw)/2/44100)<1e-9)
   ck(pid+' exact spoken chars',a['characters']==list(s))
   times=a['character_start_times_seconds'];ends=a['character_end_times_seconds'];nonspace=[i for i,x in enumerate(s) if not x.isspace()]
   ck(pid+' finite monotonic native character times',len(times)==len(ends)==len(s) and all(math.isfinite(x) for x in times+ends) and all(0<=x<=y for x,y in zip(times,ends)) and all(y>=x for x,y in zip(times,times[1:])) and all(y>=x for x,y in zip(ends,ends[1:])))
   native_last=max(ends[i] for i in nonspace);raw_seconds=len(raw)/2/44100;overhang=max(0,native_last-raw_seconds);slotend=round(p['end_s']*44100)*2
   ck(pid+' transparent overhang silence',overhang<=.100001 and p['padded_slot_seconds']+1/44100>=native_last and all(x==0 for x in b[start+len(raw):slotend]) and abs(p['end_s']-off-p['padded_slot_seconds'])<1e-9)
   rb=bounds(raw);ck(pid+' measured signal boundary',abs(p['last_pcm_signal_end_s']-off-rb['last'])<1e-9 and abs(p['last_native_word_end_s']-off-native_last)<1e-9)
   cursor=slotend
   paragraphs.append(dict(paragraph_id=pid,audio=pin(src),decoded_seconds=raw_seconds,provider_last_end_s=native_last,provider_minus_PCM_s=native_last-raw_seconds,padding_s=p['alignment_overhang_padding_s'],signal=rb))
   for q in [q for q in c['cues'] if q['paragraph_id']==pid]:
    frozen=next(x for x in old['cues'] if x['id']==q['id']);bs,be=q['spoken_start'],q['spoken_end'];used=[i for i in range(bs,be) if not s[i].isspace()]
    ck(q['id']+' frozen text/lines',all(q[k]==frozen[k] for k in ['text','spoken_text','display_lines','source_start','source_end']) and pre['text'][q['source_start']:q['source_end']]==q['text'] and s[bs:be]==q['spoken_text'])
    ns=min(times[i] for i in used)+off;ne=max(ends[i] for i in used)+off
    ck(q['id']+' exact native cue bounds',abs(q['start_s']-ns)<1e-9 and abs(q['end_s']-ne)<1e-9 and q['native_start_s']==q['start_s'] and q['native_end_s']==q['end_s'] and 0<=q['start_s']<q['end_s']<=c['total_seconds'])
    cues.append(dict(id=q['id'],chapter=c['chapter'],start_s=q['start_s'],end_s=q['end_s'],text=q['text'],lines=q['display_lines']))
  ck(f'CH{c["chapter"]} all silence tail',all(x==0 for x in b[cursor:]))
  tail=c['total_seconds']-max(c['last_native_word_end_s'],chbounds['last'])
  ck(f'CH{c["chapter"]} actual speech tail',tail+1e-9>=(3 if c['chapter']==10 else 1.2) and abs(c['tail_from_last_spoken_s']-tail)<1e-9)
  ck(f'CH{c["chapter"]} cue monotonic',all(y['start_s']>=x['end_s'] for x,y in zip(c['cues'],c['cues'][1:])))
  chapterrows.append(dict(chapter=c['chapter'],audio=pin(cp),PCM_payload_sha256=datahash,seconds=c['total_seconds'],last_signal_s=chbounds['last'],last_native_end_s=c['last_native_word_end_s'],tail_s=tail))
 bodyp=resolve(t['body_audio_file']);body=pcm(bodyp)
 ck('body_exact_chapter_concatenation',hashlib.sha256(body).hexdigest()==bodyhash.hexdigest() and sha(bodyp)==t['body_audio_sha256'] and len(body)//2==t['body_pcm_frames'])
 ck('all206_unique_ordered_cues',len(cues)==206 and [q['id'] for q in cues]==[q['id'] for q in old['cues']])
 failures=[x for x in checks if not x['pass_']]
 result=dict(status='pass' if not failures else 'required_review',checked_at=datetime.now(timezone.utc).isoformat(),timing=pin(tp),ledger=pin(ledgerp),input_lock=pin(E/'narration/jun-production-v1/input_lock.json'),script_sha256=t['script_sha256'],checks_count=len(checks),failures=failures,checks=checks,paragraphs=paragraphs,chapters=chapterrows,cues=cues,body=pin(bodyp),body_seconds=len(body)/2/44100,actual_listening=False,continuous_playback=False,speech_naturalness='unchecked',full_AV_decode=False,method='Independent PCM/header/sample comparisons and raw provider character times; no estimated speech boundaries and no alignment stretching')
 (Q/'timing_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(status=result['status'],checks=len(checks),failures=failures,body_seconds=result['body_seconds']),ensure_ascii=False))
if __name__=='__main__':main()
