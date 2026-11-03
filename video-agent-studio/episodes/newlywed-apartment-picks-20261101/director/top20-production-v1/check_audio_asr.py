"""Offline ASR evidence for important counts and the ending, not a listening verdict."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,difflib,hashlib,json,os,re,socket,sys,time,wave

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def norm(s):return re.sub(r"[^가-힣0-9]","",s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--timing",required=True)
    ap.add_argument("--model",choices=["small","medium"],default="medium")
    ap.add_argument("--source-raw",action="store_true")
    ap.add_argument("--scenes",nargs="+",default=["O002","S003","I001","I002","S013","S017","S022","C001"])
    a=ap.parse_args();tp=ROOT/a.timing;timing=read(tp)
    out=HERE/"evidence/audio-asr";out.mkdir(parents=True,exist_ok=True)
    deps=ROOT/"video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/deps"
    models=deps.parent/"models"/("medium" if a.model=="medium" else "systran-faster-whisper-small")
    assert (models/"model.bin").is_file()
    os.environ.update(HF_HUB_OFFLINE="1",HF_HUB_DISABLE_TELEMETRY="1",DO_NOT_TRACK="1",TOKENIZERS_PARALLELISM="false",OMP_NUM_THREADS="4")
    def denied(*args,**kwargs):raise RuntimeError("Network disabled for offline audio evidence")
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=denied
    sys.path.insert(0,str(deps));import faster_whisper
    model=None;reports=[]
    for row in timing["scenes"]:
        if row["scene_id"] not in a.scenes:continue
        path=Path(row["audio_path"])
        if not path.is_absolute():path=ROOT/path
        if a.source_raw:path=EP/"narration/top20-production-v1/free-edge-v1"/(row["scene_id"]+".wav")
        digest=sha(path)
        suffix=("_"+a.model if a.model!="medium" else "")+("_raw" if a.source_raw else "")
        dest=out/(row["scene_id"]+suffix+"_"+digest[:12]+".json")
        if dest.exists():reports.append(read(dest));continue
        if model is None:model=faster_whisper.WhisperModel(str(models),device="cpu",compute_type="int8",cpu_threads=4,num_workers=1,local_files_only=True)
        started=time.monotonic()
        segments,info=model.transcribe(str(path),language="ko",beam_size=5,temperature=0,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
        rows=[{"start_s":s.start,"end_s":s.end,"text":s.text,
          "words":[{"word":w.word,"start_s":w.start,"end_s":w.end,"probability":w.probability} for w in s.words or []]} for s in segments]
        transcript=" ".join(s["text"] for s in rows)
        expected=row.get("reading_text",row["narration_text"])
        report={"scene_id":row["scene_id"],"audio_sha256":digest,"audio_file":str(path),"timing_sha256":sha(tp),
          "expected_display":row["narration_text"],"expected_reading":expected,"recognized":transcript,"segments":rows,
          "digits_in_recognized":re.findall(r"\d[\d,.]*",transcript),"input_seconds":info.duration,
          "literal_text_similarity_not_numeric_normalized":round(difflib.SequenceMatcher(a=norm(expected),b=norm(transcript),autojunk=False).ratio(),4),
          "elapsed_s":round(time.monotonic()-started,2),"model":"cached faster-whisper "+a.model+" CPU int8",
          "prompted":False,"external_audio_transfer":False,"actual_listening":False,
          "interpretation":"ASR is supporting evidence; spelling and digit-versus-Hangul differences require review, not automatic speech failure."}
        save(dest,report);reports.append(report)
        print(json.dumps({"scene_id":row["scene_id"],"elapsed_s":report["elapsed_s"],"recognized":transcript},ensure_ascii=False),flush=True)
    summary_name="summary"+("_"+a.model if a.model!="medium" else "")+("_raw" if a.source_raw else "")+".json"
    save(out/summary_name,{"checked_at":datetime.now(timezone(timedelta(hours=9))).isoformat(),"timing_sha256":sha(tp),
      "scenes":[r["scene_id"] for r in reports],"reports":[{"scene_id":r["scene_id"],"audio_sha256":r["audio_sha256"],"recognized":r["recognized"]} for r in reports],
      "status":"offline_ASR_evidence_requires_interpretation","actual_listening":False,"continuous_playback":False})

if __name__=="__main__":main()
