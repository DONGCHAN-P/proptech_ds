"""Lock sample-based narration timing and the approved clean brand placement."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,subprocess,wave

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wav(p):
    with wave.open(str(p),"rb") as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,44100)
        return w.readframes(w.getnframes())

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source",default="narration/top20-production-v1/timing_proposals_v2.json")
    a=ap.parse_args();source=EP/a.source
    t=read(source);assert t["sentence_count"]==103 and t["cash_cost_krw"]==0
    body=Path(t["audio_file"]);body_pcm=wav(body)
    media=read(ROOT/"video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json")["assets"]
    brands={"intro":media[0],"outro":media[1]}
    ffmpeg=ROOT/"video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
    audio=HERE/"locked-audio";audio.mkdir(exist_ok=True)
    for name,duration in [("intro",5),("outro",10)]:
        item=brands[name];video=ROOT/item["path"];assert sha(video)==item["sha256"]
        dest=audio/(name+"_clean_v7.wav")
        proc=subprocess.run([str(ffmpeg),"-v","error","-i",str(video),"-vn","-t",str(duration),"-ac","1","-ar","44100","-c:a","pcm_s16le","-y",str(dest)],capture_output=True)
        assert proc.returncode==0,proc.stderr.decode(errors="replace")[-300:]
        assert len(wav(dest))==duration*44100*2
    hook=t["scenes"][0];assert hook["scene_id"]=="O001" and hook["start_s"]==5
    hook_frames=round(hook["duration_s"]*44100)
    outro_start=t["brand_outro"]["start_s"]
    silence_frames=round(outro_start*44100)-(len(body_pcm)//2+5*44100)
    assert silence_frames>=0
    full_pcm=body_pcm[:hook_frames*2]+wav(audio/"intro_clean_v7.wav")+body_pcm[hook_frames*2:]+bytes(silence_frames*2)+wav(audio/"outro_clean_v7.wav")
    version="v3" if source.name.endswith("v3.json") else "v2"
    full=audio/("narration_with_clean_brand_"+version+".wav")
    with wave.open(str(full),"wb") as w:w.setparams((1,2,44100,0,"NONE","not compressed"));w.writeframes(full_pcm)
    duration=len(full_pcm)/2/44100
    assert abs(duration-t["total_duration_with_brand_and_hold_s"])<1/44100
    lock=json.loads(json.dumps(t))
    first=lock["scenes"][0]
    for key in ["start_s","end_s"]:first[key]-=5
    for key in ["sentences","captions"]:
        for cue in first[key]:
            cue["start_s"]-=5;cue["end_s"]-=5
    lock.update(timing_locked=True,status="director_measured_timing_locked",audio_file=str(full),audio_file_time_origin_global_s=0,
      source_body_audio_file=str(body),source_timing=str(source.relative_to(ROOT)),source_timing_sha256=sha(source),
      audio_sha256=sha(full),total_duration_s=duration,duration_s=duration,
      brand_visuals=[{"id":"brand_intro","path":brands["intro"]["path"],"sha256":brands["intro"]["sha256"],"start_s":hook_frames/44100,"duration_s":5},
        {"id":"brand_outro","path":brands["outro"]["path"],"sha256":brands["outro"]["sha256"],"start_s":outro_start,"duration_s":10}],
      opening_order="data_question_hook_then_5s_clean_brand_then_definition",
      audio_clock_basis="PCM sample counts plus explicit scaled provider-word and kept-cut translation; not actual listening",
      clean_brand_source="existing approved clean v7 video audio",actual_listening_performed=False,continuous_playback_performed=False)
    lock.pop("full_brand_audio_file",None)
    lock["brand_intro"].update(start_s=hook_frames/44100,end_s=hook_frames/44100+5,path=brands["intro"]["path"])
    lock["brand_outro"].update(path=brands["outro"]["path"])
    if (HERE/"locked_timing.json").exists() and version=="v3" and not (HERE/"locked_timing_before_i002.json").exists():
        save(HERE/"locked_timing_before_i002.json",read(HERE/"locked_timing.json"))
    save(HERE/"locked_timing.json",lock)
    script=read(HERE/"scene_proposals_v4.json")
    timing_by_id={s["scene_id"]:s for s in lock["scenes"]}
    for s in script["scenes"]:
        actual=timing_by_id[s["scene_id"]]
        s.update(start_s=actual["start_s"],end_s=actual["end_s"],duration_s=actual["duration_s"],
          audio_revision=lock["audio_revision"],timing_basis=lock["alignment_basis"],status="measured_timing_locked_composition_pending",
          sentence_times=actual["sentence_times"],captions=actual["captions"],anchors=actual["anchors"])
    script.update(timing_locked=True,audio_confirmed=True,actual_duration_s=duration,brand_visuals=lock["brand_visuals"])
    save(EP/"scenes.json",script)
    state=read(EP/"state.json")
    state.update(phase="timing_locked_visual_assembly",script="director/top20-production-v1/script_v4.md",script_sha256=sha(HERE/"script_v4.md"),
      script_approval="v3 accepted by user; v4 producer timing edit within production scope, original preserved",
      timing="director/top20-production-v1/locked_timing.json",audio_revision=lock["audio_revision"],
      actual_video_duration_s=duration,voice="free Microsoft Edge InJoonNeural; no paid generation",paid_budget="free_selected_zero_cost",
      updated_at=datetime.now(timezone(timedelta(hours=9))).isoformat())
    save(EP/"state.json",state)
    decisions=read(EP/"decisions.json")
    for row in [{"id":"D011","choice":"remove13 repetitive editorial sentences to fit roughly8minutes; all20ranks and coreinsights preserved","basis":"eight-minute production request and guide against repetition","owner":"director","status":"producer_editorial_decision","artifact":"director/top20-production-v1/editorial_cut_plan.json"},
      {"id":"D012","choice":"free TTS and actual PCM timing; question hook before clean5sbrand, lastword+3s then10soutro","basis":"user free TTS selection and existing channel guide","status":"timing_locked"}]:
        if not any(d["id"]==row["id"] for d in decisions["decisions"]):decisions["decisions"].append(row)
    save(EP/"decisions.json",decisions)
    print(json.dumps({"timing_locked":True,"duration_s":duration,"voice_sentences":103,"hook_s":hook_frames/44100,"outro_start_s":outro_start,"audio_sha256":sha(full)},ensure_ascii=False))

if __name__=="__main__":main()
