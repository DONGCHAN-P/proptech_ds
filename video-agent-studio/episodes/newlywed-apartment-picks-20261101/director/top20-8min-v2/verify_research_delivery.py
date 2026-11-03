"""Verify the delivered materials and shelf links, without creating any media."""
import ast
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
OUT=EP/"outputs/top20-research-v2"
VIS=EP/"visual/top20-8min-v2"
QA=EP/"qa/top20-8min-v2"

def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    pack=read(OUT/"delivery_manifest.json")
    state=read(EP/"state.json")
    scenes=read(EP/"scenes.json")
    proposals=read(EP/state["scene_proposals"])
    regions=read(EP/"research/top20-8min-v2/top20.json")["regions"]
    photos=read(EP/pack["photo_manifest"])["assets"]
    maps=read(VIS/"maps/map_assets.json")["assets"]
    cards=read(VIS/"data_cards/data_card_assets.json")["assets"]+read(VIS/"data_cards/additional_data_cards.json")["assets"]
    assert len(regions)==len(photos)==len(maps)==20 and len(cards)==9
    assert {p["region_id"] for p in photos}=={r["region_id"] for r in regions}
    photo_hashes=[]
    for p in photos:
        f=Path(p["absolute_file"]) if p.get("absolute_file") else VIS/p["actual_file"]
        assert sha(f)==p["sha256"],str(f)
        photo_hashes.append(sha(f))
        with Image.open(f) as im:
            im.load()
            assert max(ImageOps.exif_transpose(im).size)>=1200
        assert p["license"]["commercial_copyright_use"] and p["license"]["adaptation_allowed"]
    assert len(set(photo_hashes))==20
    for a in maps+cards:
        f=EP/a["actual_file"]
        with Image.open(f) as im:
            im.load()
            assert im.size==(1920,1080),str(f)
        if a.get("sha256"): assert sha(f)==a["sha256"]
    for m in maps:
        assert (EP/m["vector_file"]).is_file()
        assert (EP/m["geometry_file"]).is_file()
    regional=[s for s in proposals["scenes"] if s.get("region_id")]
    assert [s["rank"] for s in regional]==list(range(20,0,-1))
    assert sum(s["duration_s"] for s in proposals["scenes"])==480
    assert not proposals["timing_locked"] and not proposals["audio_confirmed"]
    asset_plan=read(EP/"director/top20-8min-v2/scene_asset_plan.json")["scene_assets"]
    assert len(asset_plan)==20
    pi={p["region_id"]:p for p in photos}
    for a in asset_plan:
        p=pi[a["region_id"]]
        assert a["actual_photo_place"]==p["actual_place"]
        assert a["photo_asset_id"]==p["asset_id"]
        assert (EP/a["photo_file"]).is_file()
    assert pack["script_sha256"]==state["script_sha256"]==sha(EP/state["script"])
    assert sha(ROOT/"analysis/newlywed_region_2024/rankings.json")=="275ce96232e523428bcea02aa3f11bd0f29ca70f2e8a13bbc55aa40b389d1d61"
    assert sha(ROOT/"analysis/newlywed_region_2024/source/newlyweds_2024.pdf")=="d7e883c41ba0add0b26433edb4aeb45dbd56b5390eb4ccdeb0ebc6f5361cb0c0"
    assert sha(EP/"writer/대본초안_v1.md")
    v3checks=read(EP/"writer/top20-8min-v2/verification_v3.json")
    for name,digest in v3checks["v2_protected_hashes"].items():
        assert sha(EP/"writer/top20-8min-v2"/name)==digest
    checked_links=0
    for name in ["자료조사_결과.md","이미지자료_안내.md","사진20장_출처.md","8분_구성안.md"]:
        for target in re.findall(r"\]\(([^)]+)\)",(OUT/name).read_text(encoding="utf-8")):
            if re.match(r"https?://",target): continue
            f=Path(target) if Path(target).is_absolute() else OUT/target
            assert f.exists(),(name,target)
            checked_links+=1
    entry=next(e for e in read(ROOT/"config/video_shelf.json")["entries"] if e["name"]=="신혼부부_지역별아파트")
    aliases=[]
    for name,target in entry["files"].items():
        if name.startswith("TOP20_"):
            assert os.path.samefile(ROOT/"영상"/entry["name"]/name,ROOT/target),name
            aliases.append(name)
    followup=read(QA/"media_followup.json")
    assert followup["verdict"]["required_open"]==0
    assert not state["render_created"] and not pack["video_rendered"]
    assert not state["actual_listening_performed"] and not state["continuous_playback_performed"]
    assert not list(OUT.glob("*.mp4"))
    for f in (EP/"director/top20-8min-v2").glob("*.py"):
        ast.parse(f.read_text(encoding="utf-8"))
    result={"status":"materials_and_delivery_links_verified","checked_at":datetime.now().astimezone().isoformat(),
      "photos":20,"unique_photo_hashes":20,"map_png":20,"map_svg":20,"data_card_png":9,
      "local_document_links":checked_links,"shelf_aliases_verified":aliases,
      "countdown_rank_order":"20_to_1","scene_count":len(scenes["scenes"]),"estimated_duration_s":480,
      "original_rank_source_unchanged":True,"older_script_versions_preserved":True,
      "independent_material_qa_required_open":0,
      "visual_inspection_evidence":["qa/top20-8min-v2/findings.json","qa/top20-8min-v2/media_followup.json"],
      "parent_actually_viewed":"20-photo final contact sheet and three-replacement contact sheet; map/card checks recorded separately",
      "final_video_render_review":False,"continuous_playback":False,"actual_listening":False,
      "remaining":["new script review","voice choice and any applicable budget","audio alignment and final composition/render QA"]}
    (QA/"delivery_verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["status","photos","map_png","map_svg","data_card_png","local_document_links","estimated_duration_s","independent_material_qa_required_open"]},ensure_ascii=False))

if __name__=="__main__": main()
