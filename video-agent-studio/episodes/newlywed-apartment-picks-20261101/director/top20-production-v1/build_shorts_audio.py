"""Reuse complete main sentences, cut in measured quiet gaps, and hold three seconds."""
from pathlib import Path
from array import array
import hashlib,json,math,wave

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RATE=44100
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def quiet(samples,left,right,target):
    lo=max(0,round(left*RATE));hi=min(len(samples),round(right*RATE));center=round(target*RATE)
    if hi-lo<round(.02*RATE):return max(lo,min(hi,center)),None
    half=round(.01*RATE);step=round(.005*RATE);options=[]
    for n in range(lo+half,hi-half+1,step):
        window=samples[n-half:n+half]
        mean=sum(x*x for x in window)/len(window)
        options.append((mean,abs(n-center),n))
    power,_,idx=min(options)
    zero=min(range(max(lo,idx-80),min(hi,idx+81)),key=lambda n:(abs(samples[n]),abs(n-idx)))
    return zero,{"rms_dbfs":round(20*math.log10(max(math.sqrt(power),1e-12)/32768),2),"sample_value":samples[zero]}

def main():
    tp=HERE/"locked_timing.json";timing=read(tp);plan=read(HERE/"shorts_story_plan.json")
    path=Path(timing["audio_file"])
    with wave.open(str(path),"rb") as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,RATE)
        samples=array("h",w.readframes(w.getnframes()))
    speech=[];scene_by_sentence={}
    for scene in timing["scenes"]:
        for line in scene.get("sentences",[]):
            speech.append(line);scene_by_sentence[line["sentence_id"]]=scene
    speech.sort(key=lambda x:x["start_s"])
    index={s["sentence_id"]:i for i,s in enumerate(speech)}
    out=HERE/"shorts-audio";out.mkdir(exist_ok=True)
    results=[]
    for item in plan["items"]:
        selected=[index[s] for s in item["sentence_ids"]]
        groups=[]
        for n in selected:
            if groups and n==groups[-1][-1]+1 and scene_by_sentence[speech[n]["sentence_id"]]["scene_id"]==scene_by_sentence[speech[groups[-1][-1]]["sentence_id"]]["scene_id"]:
                groups[-1].append(n)
            else:groups.append([n])
        pcm=array("h");clips=[];captions=[];last_spoken=0
        for k,group in enumerate(groups):
            first,last=speech[group[0]],speech[group[-1]]
            scene=scene_by_sentence[first["sentence_id"]]
            before=speech[group[0]-1]["end_s"] if group[0]>0 else scene["start_s"]
            after=speech[group[-1]+1]["start_s"] if group[-1]+1<len(speech) else scene["end_s"]
            # Stay in this source scene, never taking a brand's sound or another sentence.
            lo=max(scene["start_s"],before+.04 if before<first["start_s"] else scene["start_s"])
            hi=max(lo,first["start_s"]-.04)
            start,evidence_in=quiet(samples,lo,hi,first["start_s"]-.10)
            lo=last["end_s"]+.04
            hi=min(scene["end_s"],after-.04 if after>last["end_s"] else scene["end_s"])
            end,evidence_out=quiet(samples,lo,max(lo,hi),last["end_s"]+.14)
            assert start<end and start/RATE<=first["start_s"] and end/RATE>=last["end_s"]
            segment=samples[start:end];target_start=len(pcm)/RATE
            # A 3ms de-click inside measured quiet tails; retain frame count and timing.
            fade=min(round(.003*RATE),len(segment)//2)
            for i in range(fade):
                segment[i]=round(segment[i]*i/fade)
                segment[-1-i]=round(segment[-1-i]*i/fade)
            pcm.extend(segment);target_end=len(pcm)/RATE
            ids=[speech[n]["sentence_id"] for n in group]
            last_spoken=target_start+last["end_s"]-start/RATE
            clips.append({"clip_id":f'{item["id"]}_{k+1:02d}',"source_scene_id":scene["scene_id"],"source_start_s":start/RATE,"source_end_s":end/RATE,
              "start_s":target_start,"end_s":target_end,"duration_s":target_end-target_start,"sentence_ids":ids,
              "text":" ".join(speech[n]["text"] for n in group),"region_id":next((s.get("region_id") for s in read(EP/"scenes.json")["scenes"] if s["scene_id"]==scene["scene_id"]),None),
              "cut_in":evidence_in,"cut_out":evidence_out,"cut_basis":"provider words plus measured PCM quiet gap, not actual listening"})
            for cue in scene["captions"]:
                if cue["end_s"]>start/RATE and cue["start_s"]<end/RATE:
                    # Quiet-gap bounds isolate complete selected sentences.
                    captions.append({"text":cue["text"],"start_s":target_start+max(cue["start_s"],start/RATE)-start/RATE,
                      "end_s":target_start+min(cue["end_s"],end/RATE)-start/RATE})
        total_frames=math.ceil((last_spoken+3)*RATE)
        assert total_frames>=len(pcm)
        pcm.extend([0]*(total_frames-len(pcm)))
        dest=out/(item["id"]+"_narration.wav")
        with wave.open(str(dest),"wb") as w:w.setparams((1,2,RATE,0,"NONE","not compressed"));w.writeframes(pcm.tobytes())
        results.append({"id":item["id"],"title":item["title"],"audio_file":str(dest),"audio_sha256":sha(dest),"duration_s":len(pcm)/RATE,
          "last_spoken_end_s":last_spoken,"hold_after_last_word_s":len(pcm)/RATE-last_spoken,
          "clips":clips,"captions":captions,"end_card":item["end_card"],"sentence_ids":item["sentence_ids"],"source_region_ids":item["source_region_ids"],
          "actual_listening":False,"voice_cost_krw":0,"source_audio_sha256":sha(path)})
    save(HERE/"shorts_locked_timing.json",{"revision":"top20-shorts-audio-v1","main_timing_sha256":sha(tp),"privacy":"private",
      "profile":plan["profile"],"items":results,"timing_locked":True,"alignment_basis":"reuse measured main word boundaries and quiet sample cuts",
      "actual_listening":False,"continuous_playback":False})
    print(json.dumps([{"id":x["id"],"duration_s":round(x["duration_s"],3),"clips":len(x["clips"]),"hold_s":round(x["hold_after_last_word_s"],3)} for x in results]))

if __name__=="__main__":main()
