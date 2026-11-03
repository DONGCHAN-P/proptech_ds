"""Upload only the exact reviewed main/Shorts, private, preserving existing uploads."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,importlib.util,json,sys

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RELEASE=EP/"outputs/top20-production-v1"
sys.path.insert(0,str(ROOT/"analysis"))
import upload_gyosan_private_v1 as base
base.EP=EP

def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def local(s):
    p=(ROOT/s).resolve()
    assert p.is_relative_to(EP.resolve()) and p.is_file(),str(p)
    return p
def now():return datetime.now(timezone(timedelta(hours=9))).isoformat()

def prepare(only_item=None):
    auth=read(HERE/"authorization.json")
    assert auth["private_upload_authorized"] and not auth["public_publication_authorized"]
    assert not auth["delete_existing_videos"]
    package=read(RELEASE/"release_manifest.json")
    assert package["privacy"]=="private" and package["channel_id"]==base.CHANNEL
    assert {i["id"] for i in package["items"]}=={"main","promo","analysis"}
    for item in package["items"]:
        if only_item and item["id"]!=only_item:continue
        video=local(item["video"])
        assert sha(video)==item["sha256"]
        qa=read(local(item["qa"]))
        assert qa["video_sha256"]==item["sha256"]
        assert qa["required_open"]==0 and qa["critical_open"]==0
        assert qa["whole_decode"]=="pass"
        metadata=read(local(item["metadata"]))
        assert 0<len(metadata["title"])<=100
        assert len(metadata["description"].encode("utf-8"))<=5000
        sub=local(item["subtitles"])
        folder=HERE/"uploads"/item["id"]
        assert not (folder/"upload_receipt.json").exists(),"Reuse an existing upload job; do not prepare over a receipt"
        save(folder/"qa_gate.json",{"status":"passed_with_limits","checked_revision":item["sha256"],
          "required_open":[],"critical_open":[],"source_review":item["qa"],
          "actual_listening":qa.get("actual_listening",False),"continuous_playback":qa.get("continuous_playback",False)})
        save(folder/"completed_decision.json",{"id":item["id"]+"-completed","gate":"completed","status":"approved",
          "video_sha256":item["sha256"],"basis":"Current direct production/private-upload request, followed by exact-version QA",
          "authorization":rel(HERE/"authorization.json")})
        job={"id":item["id"],"channel_id":base.CHANNEL,"privacy":"private","video":item["video"],"sha256":item["sha256"],
          "title":metadata["title"],"description":metadata["description"],"tags":metadata.get("tags",[]),
          "qa":rel(folder/"qa_gate.json"),"approval_file":rel(folder/"pre_upload.json"),
          "authorization":rel(HERE/"authorization.json"),"subtitles":item["subtitles"],"subtitles_sha256":sha(sub),
          "notify_subscribers":False}
        if item.get("thumbnail"):
            thumb=local(item["thumbnail"])
            job.update(thumbnail=item["thumbnail"],thumbnail_sha256=sha(thumb))
        save(folder/"upload_job.json",job)
        save(folder/"pre_upload.json",{"id":item["id"]+"-private","gate":"pre_upload","status":"approved",
          "video_sha256":item["sha256"],"job_sha256":sha(folder/"upload_job.json"),"channel_id":base.CHANNEL,"privacy":"private",
          "new_paid_generation_authorized":False,"completed_decision_file":rel(folder/"completed_decision.json"),
          "basis":"Current direct user instruction authorizes private upload of the completed three artifacts", "at":now()})
        base.validate(folder/"upload_job.json")
    print(json.dumps({"local_preflight":"passed","items":3,"privacy":"private","new_uploads":0}))

def extras(y,folder):
    from googleapiclient.http import MediaFileUpload
    job=read(folder/"upload_job.json");rp=folder/"upload_receipt.json";record=read(rp)
    vid=record["video_id"]
    if job.get("thumbnail") and not record.get("thumbnail_uploaded"):
        y.thumbnails().set(videoId=vid,media_body=MediaFileUpload(str(local(job["thumbnail"])),mimetype="image/png")).execute(num_retries=0)
        record["thumbnail_uploaded"]=True;save(rp,record)
    processing=record.get("verification",{}).get("processingDetails",{}).get("processingStatus")
    assert processing not in ["failed","terminated"]
    if processing!="succeeded":
        print(json.dumps({"video_id":vid,"processing":processing,"captions":"waiting_for_processing"}))
        return
    tracks=y.captions().list(part="snippet",videoId=vid).execute(num_retries=0).get("items",[])
    matches=[t for t in tracks if t["snippet"].get("language")=="ko" and t["snippet"].get("name")=="한국어"]
    assert len(matches)<=1
    if matches:record["caption_id"]=matches[0]["id"]
    elif not record.get("caption_id"):
        assert not record.get("caption_insert_started"),"Inspect an uncertain previous caption insert before retry"
        record["caption_insert_started"]=True;save(rp,record)
        response=y.captions().insert(part="snippet",body={"snippet":{"videoId":vid,"language":"ko","name":"한국어","isDraft":False}},
          media_body=MediaFileUpload(str(local(job["subtitles"])),mimetype="application/octet-stream")).execute(num_retries=0)
        record["caption_id"]=response["id"]
    record["caption_tracks"]=y.captions().list(part="snippet",videoId=vid).execute(num_retries=0).get("items",[])
    save(rp,record)
    base.verify(y,rp,record,job)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("action",choices=["prepare","upload","verify"])
    ap.add_argument("--item",choices=["main","promo","analysis"]);args=ap.parse_args()
    if args.action=="prepare":prepare(args.item);return
    assert args.item
    folder=HERE/"uploads"/args.item;jp=folder/"upload_job.json"
    base.validate(jp)
    sys.argv=["existing_private_uploader",args.action,"--job",rel(jp)]
    base.main()
    extras(base.service(),folder)

if __name__=="__main__":main()
