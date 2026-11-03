"""Remove repeated editorial sentences to fit the requested eight-minute film."""
from pathlib import Path
import hashlib,json

EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")

REMOVE=["S003-04","S004-04","S005-03","S005-04","S006-04","S008-04","S009-04",
        "S010-04","S011-03","S017-04","S019-04","S020-03","C001-06"]

def main():
    source=EP/"writer/top20-8min-v2/scene_proposals_v3.json"
    original=read(source)
    timing=read(EP/"narration/top20-production-v1/timing_proposals.json")
    index={x["sentence_id"]:x for s in timing["scenes"] for x in s.get("sentences",[])}
    edited=json.loads(json.dumps(original))
    removed=[]
    for s in edited["scenes"]:
        for line in s["sentences"]:
            if line["sentence_id"] in REMOVE:
                t=index[line["sentence_id"]]
                removed.append({"sentence_id":line["sentence_id"],"text":line["text"],
                  "reason":"Repeated editorial bridge or general comparison advice; core figures remain in retained sentences",
                  "provider_scaled_spoken_duration_s":t["end_s"]-t["start_s"]})
        s["sentences"]=[x for x in s["sentences"] if x["sentence_id"] not in REMOVE]
        s["narration_text"]="\n".join(x["text"] for x in s["sentences"])
        s["script_revision"]="top20-production-editorial-v4"
    assert len(removed)==13
    assert [s["rank"] for s in edited["scenes"] if s.get("region_id")]==list(range(20,0,-1))
    edited.update(revision="top20-production-editorial-v4",base_script_revision="top20-8min-v3",
      source_script_preserved=True,production_edit_basis="Current eight-minute production request and common guideline against repetitive narration",
      removed_sentence_ids=REMOVE,timing_locked=False,audio_confirmed=True)
    save(HERE/"scene_proposals_v4.json",edited)
    script=["# 신혼부부가 많이 사는 수도권 구 TOP20 — 제작 편집본 v4\n",
      "원고 v3는 보존했습니다. 순위·지역별 전체 수·핵심 증감·구성 비교를 유지하고, 반복되는 연결 문장 13개를 덜어 약 8분으로 편집합니다. 새 유료 음성 생성 없이 무료 음성의 완결 문장을 사용합니다.\n"]
    for s in edited["scenes"]:
        if s["sentences"]:script.extend([f'## {s["scene_id"]} · {s["title"]}\n',s["narration_text"]+"\n"])
    (HERE/"script_v4.md").write_text("\n".join(script),encoding="utf-8")
    save(HERE/"editorial_cut_plan.json",{"revision":"top20-production-editorial-v4","source":str(source.relative_to(EP)),
      "source_sha256":sha(source),"source_audio_revision":timing["audio_revision"],"drop_sentence_ids":REMOVE,
      "keep_sentence_ids":[x["sentence_id"] for s in edited["scenes"] for x in s["sentences"]],
      "removed_sentences":removed,"removed_scaled_spoken_seconds":sum(x["provider_scaled_spoken_duration_s"] for x in removed),
      "target_total_seconds":480,"acceptable_natural_duration_range_seconds":[468,492],
      "no_new_factual_claims":True,"new_tts_calls_required":False,"all_20_ranks_preserved":True,
      "approval_basis":"Producer's routine editorial timing adjustment within the latest production request; no claim of separate user review of this edit",
      "v3_user_accepted_script_preserved":True,"script_v4_sha256":sha(HERE/"script_v4.md")})
    print(json.dumps({"removed_sentences":len(removed),"retained_sentences":sum(len(s["sentences"]) for s in edited["scenes"]),
      "removed_scaled_spoken_s":round(sum(x["provider_scaled_spoken_duration_s"] for x in removed),2)},ensure_ascii=False))

if __name__=="__main__":main()
