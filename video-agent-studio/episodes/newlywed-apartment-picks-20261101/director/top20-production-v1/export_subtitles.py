"""Export the exact captions actually authored in the three frozen projects."""
from pathlib import Path
import hashlib,json,re

EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
EDITOR=EP/"editor/top20-production-v1"
OUT=EP/"outputs/top20-production-v1/subtitles"
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def norm(s):return re.sub(r"\s|[.,?!·]","",s)
def stamp(t):
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    script=read(HERE/"scene_proposals_v4.json")
    sentences={x["sentence_id"]:x["text"] for s in script["scenes"] for x in s["sentences"]}
    plans=read(HERE/"shorts_story_plan.json")["items"]
    results=[]
    for name,project in [("main",EDITOR/"main"),("promo",EDITOR/"shorts/promo"),("analysis",EDITOR/"shorts/analysis")]:
        mapping=project/"caption_mapping.json";cues=read(mapping)["cues"]
        expected=list(sentences) if name=="main" else next(p["sentence_ids"] for p in plans if p["id"]==name)
        for sid in expected:
            displayed="".join(c["text"] for c in cues if c.get("sentence_id")==sid)
            assert norm(displayed)==norm(sentences[sid]),(name,sid,displayed,sentences[sid])
        text=[]
        for i,c in enumerate(cues):
            assert c["end_s"]>c["start_s"]>=0
            if i:assert c["start_s"]>=cues[i-1]["end_s"]-.001,(name,i)
            text.append(f'{i+1}\n{stamp(c["start_s"])} --> {stamp(c["end_s"])}\n{c["text"]}\n')
        dest=OUT/(name+".srt");dest.write_text("\n".join(text),encoding="utf-8")
        results.append({"id":name,"file":str(dest),"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
          "caption_source":str(mapping),"source_sha256":hashlib.sha256(mapping.read_bytes()).hexdigest(),
          "cues":len(cues),"sentence_ids_verified":len(expected),"last_cue_end_s":cues[-1]["end_s"]})
    (OUT/"export_verification.json").write_text(json.dumps({"status":"authored_caption_text_and_order_verified","items":results},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps([{k:x[k] for k in ["id","cues","sentence_ids_verified","last_cue_end_s"]} for x in results],ensure_ascii=False))

if __name__=="__main__":main()
