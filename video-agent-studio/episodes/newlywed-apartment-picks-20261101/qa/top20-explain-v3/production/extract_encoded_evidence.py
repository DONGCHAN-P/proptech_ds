"""최종MP4에서만 프레임·오디오 증거를 추출한다. 제작 소스/영상 수정 없음."""
import datetime
import hashlib
import json
import math
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PROJECT = ROOT.parents[2]
E = OUT / "encoded-v1"
E.mkdir(exist_ok=True)
FRAMES = E / "frames"
FRAMES.mkdir(exist_ok=True)
VIDEO = ROOT / "outputs/top20-explain-v3/main/top20_v6_free_v1.mp4"
FFMPEG = PROJECT / "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe"
FFPROBE = PROJECT / "video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe"
EXPECTED_SHA = "80b7cd14b0fa15de21a696796b2a996f0fa47e29ad02ab067ab8ca20448220d1"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name,value):
    (E/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv,name):
    result = subprocess.run([str(x) for x in argv],capture_output=True,text=True,encoding="utf-8",errors="replace")
    (E/(name+".stdout.log")).write_text(result.stdout,encoding="utf-8")
    (E/(name+".stderr.log")).write_text(result.stderr,encoding="utf-8")
    assert result.returncode == 0,(name,result.returncode,result.stderr[-1000:])
    return result


assert VIDEO.is_file() and sha(VIDEO)==EXPECTED_SHA
receipt=load(ROOT/"director/top20-explain-v3/render_receipt_v1.json")
assert receipt["status"]=="encoded_decode_passed_for_independent_QA" and receipt["output_sha256"]==EXPECTED_SHA
probe_result=run([FFPROBE,"-v","error","-show_streams","-show_format","-of","json",VIDEO],"probe")
probe=json.loads(probe_result.stdout)
write("probe.json",probe)
v=next(x for x in probe["streams"] if x["codec_type"]=="video")
a=next(x for x in probe["streams"] if x["codec_type"]=="audio")
assert (v["width"],v["height"],v["codec_name"],v["r_frame_rate"])==(1920,1080,"h264","30/1")
assert a["codec_name"]=="aac" and int(a["sample_rate"])==48000 and a["channels"]==2
duration=float(probe["format"]["duration"])
fps=30
frame_count=int(v.get("nb_frames",round(duration*fps)))
plan=load(OUT/"mp4_review_plan.json")
lock=load(ROOT/"director/top20-explain-v3/locked_timing.json")
phase=load(ROOT/"editor/top20-explain-v3/main/v2-bgm/phase_audit.json")
targets=load(OUT/"price_timing_targets.json")["events"]
points={}


def point(frame,reason):
    frame=max(0,min(frame_count-1,int(frame)))
    points.setdefault(frame,[]).append(reason)


for row in plan["samples"]:
    point(round(row["time_s"]*fps),{"kind":"planned_257","time_s":row["time_s"],"purpose":row["purpose"],"scene_id":row["scene_id"]})
boundaries=[]
for scene in lock["scenes"]:
    boundaries.append((scene["start_s"],scene["scene_id"],"scene_cut"))
for p in phase:
    s=next(x for x in lock["scenes"] if x["scene_id"]==p["scene_id"])
    boundaries.append((s["start_s"]+p["switch_s"],p["scene_id"],"price_phase"))
for name in ["brand_intro","brand_outro"]:
    boundaries.extend([(lock[name]["start_s"],name,"brand_start"),(lock[name]["end_s"],name,"brand_end")])
boundaries.append((lock["last_speech_end_s"],"C001","last_speech_caption_end"))
for time_s,sid,kind in boundaries:
    center=math.ceil(time_s*fps)
    for delta in [-2,-1,0,1,2]:
        point(center+delta,{"kind":"boundary_burst","boundary_kind":kind,"scene_id":sid,"boundary_s":time_s,"relative_frame":delta})
# 화장용 정수억원 표기와 마지막 인코딩 꼬리도 실제영상에서 확인한다.
for t in [649.901,duration-1/30,duration-3/30]:
    point(round(t*fps),{"kind":"additional","time_s":t,"purpose":"정수억원 표기/최종꼬리"})
ordered=sorted(points)
select="select="+"+".join("eq(n\\,"+str(n)+")" for n in ordered)
filters=run([FFMPEG,"-hide_banner","-filters"],"filter_capabilities").stdout
assert "select" in filters and "astats" in filters
print(json.dumps({"stage":"영상SHA/probe확인·추출시작","planned_points":len(plan["samples"]),"unique_frames":len(ordered),"evidence":str(E)},ensure_ascii=False),flush=True)
extract=run([FFMPEG,"-hide_banner","-loglevel","error","-xerror","-i",VIDEO,"-an","-vf",select,"-vsync","0","-threads","2",FRAMES/"frame_%04d.png"],"extract_and_full_decode")
files=sorted(FRAMES.glob("frame_*.png"))
assert len(files)==len(ordered),(len(files),len(ordered))
manifest=[]
for number,path in zip(ordered,files):
    manifest.append({"frame_n":number,"time_s":number/fps,"path":str(path.relative_to(OUT)).replace("\\","/"),"sha256":sha(path),"purposes":points[number]})
write("frame_manifest.json",{"video_sha256":EXPECTED_SHA,"planned_points":len(plan["samples"]),"unique_frames":len(manifest),"boundary_groups":len(boundaries),"frames":manifest})
print(json.dumps({"stage":"실제MP4프레임추출완료·전체decode통과","unique_frames":len(manifest),"boundary_groups":len(boundaries),"evidence":str(FRAMES)},ensure_ascii=False),flush=True)
run([FFMPEG,"-hide_banner","-loglevel","error","-xerror","-i",VIDEO,"-vn","-acodec","pcm_s16le","-ar","48000","-ac","2",E/"final_mix.wav"],"decode_final_mix")
voice=Path(lock["audio_file"])
run([FFMPEG,"-hide_banner","-loglevel","error","-i",voice,"-ar","48000","-ac","1","-acodec","pcm_s16le",E/"reference_voice_48k.wav"],"resample_reference_voice")
write("technical_receipt.json",{"status":"passed_encoded_probe_full_decode_and_extraction","checked_at":NOW,"video_path":str(VIDEO),"video_sha256":EXPECTED_SHA,"bytes":VIDEO.stat().st_size,"duration_s":duration,"frame_count":frame_count,"render_receipt_sha256":sha(ROOT/"director/top20-explain-v3/render_receipt_v1.json"),"source_project_sha256":receipt["source_project_sha256"],"timing_sha256":receipt["timing_sha256"],"independent_full_decode_exit_code":0,"frame_extract_count":len(manifest),"planned_points":len(plan["samples"]),"boundary_groups":len(boundaries),"decoded_mix_path":str(E/"final_mix.wav"),"actual_listening_performed":False,"continuous_playback_performed":False,"full_media_pass":False})
print(json.dumps({"stage":"프레임·실제믹스PCM추출완료","frame_count":len(manifest),"audio_PCM_files":2,"technical_receipt":str(E/"technical_receipt.json")},ensure_ascii=False),flush=True)
