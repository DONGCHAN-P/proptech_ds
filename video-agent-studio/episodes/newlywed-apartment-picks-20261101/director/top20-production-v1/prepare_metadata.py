"""Prepare exact source credits and private-upload metadata from the frozen inputs."""
from pathlib import Path
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=EP/"outputs/top20-production-v1/metadata"
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    photos=read(EP/"visual/top20-8min-v2/photo_assets_v2.json")["assets"]
    credits=[];licenses={}
    for p in photos:
        src=p["source_or_prompt"];lic=p["license"]
        author=re.sub("<[^>]+>","",str(src["author"])).strip()
        label=lic["name"]
        if lic.get("version") and lic["version"] not in label:label+=" "+lic["version"]
        url=src.get("fixed_revision_url") or src["file_page"]
        credits.append(f'{p["rank"]:02d} {author} | {src["title"]} | {label} | {url}')
        licenses[label]=lic["license_url"]
    source_intro=("자료: 2024년 신혼부부통계(기준일 2024.11.1), 2023년 신혼부부통계.\n"
      "2024년 당시 수도권 53개 구 중 신혼부부 전체 수 순위입니다. 단위는 쌍이며 초혼·재혼을 포함합니다.\n"
      "옛 인천 서구는 당시 구역으로 비교합니다. 부천 원미구의 2023년 동일 구역 비교값은 별도 확인 대상입니다.\n"
      "https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3\n"
      "https://sri.kostat.go.kr/boardDownload.es?bid=11815&list_no=434122&seq=3\n")
    map_credit=("지도: SGIS 공공누리1·vuski/admdongkor, 2024.10.1 행정동 경계 가공(CC BY4.0).\n"
      "https://github.com/vuski/admdongkor/tree/master/ver20241001\n")
    photo_credit="사진(원본 비율 유지 배치·영상 위 문자 레이어):\n"+"\n".join(credits)+"\n"
    license_credit="\n".join(f'{name}: {url}' for name,url in licenses.items())
    music_credit="\nThinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0\nhttps://creativecommons.org/licenses/by/4.0/\n"
    common=source_intro+map_credit+photo_credit+license_credit+music_credit
    shorts=read(HERE/"shorts_story_plan.json")["items"]
    data=[{"id":"main","title":"신혼부부가 많이 사는 곳 TOP20｜수도권 53개 구 비교",
      "lead":"서울·경기·인천에서 신혼부부가 많이 사는 구는 어디일까요? 20위부터 1위까지, 거주 규모와 전년 변화·구성의 차이를 함께 살펴봅니다.\n\n"}]
    if (HERE/"locked_timing.json").exists():
        timing=read(HERE/"locked_timing.json")
        starts={s["scene_id"]:s["start_s"] for s in timing["scenes"]}
        chapter_titles=[("O001","신혼부부는 어디에 살까"),("O002","집계 기준"),("S003","20위부터 16위"),
          ("I001","같은 규모, 다른 변화"),("S008","15위부터 11위"),("I002","전체와 초혼·재혼 구성"),
          ("S013","10위부터 6위"),("I003","서울·경기·인천 분포"),("S018","5위부터 1위"),("C001","우리 부부의 지역 비교")]
        data[0]["lead"]+="\n".join(f'{int(starts[s])//60:02d}:{int(starts[s])%60:02d} {title}' for s,title in chapter_titles)+"\n\n"
    data += [{"id":x["id"],"title":x["title"],"lead":x["viewer_question"]+"\n전체 TOP20은 본편에서 확인하세요.\n\n"} for x in shorts]
    results=[]
    for item in data:
        desc=item["lead"]+common
        # The existing proven upload guard conservatively uses a 5KB limit.
        if len(desc.encode("utf-8"))>5000:
            short_lines=[]
            for p in photos:
                s=p["source_or_prompt"];l=p["license"]
                author=re.sub("<[^>]+>","",str(s["author"])).strip()
                url=s.get("fixed_revision_url") or s["file_page"]
                title=(s["title"]+" | ") if str(l.get("version","")).startswith("3") else ""
                short_lines.append(f'{p["rank"]:02d} {author} | {title}{l["name"]} {l.get("version","")} | {url}')
            desc=item["lead"]+source_intro+map_credit+"사진 출처·저자·이용조건\n"+"\n".join(short_lines)+"\n"+license_credit+music_credit
        assert len(desc.encode("utf-8"))<=5000,(item["id"],len(desc.encode("utf-8")))
        meta={"id":item["id"],"title":item["title"],"description":desc,"privacy":"private",
          "tags":["신혼부부","수도권","지역분석","아파트","부동산데이터"]+(["Shorts"] if item["id"]!="main" else []),
          "statistical_reference_date":"2024-11-01","description_utf8_bytes":len(desc.encode("utf-8")),
          "caption_language":"ko","voice":"free_TTS_selected_by_user","new_paid_generation":False,
          "main_video_link_pending":item["id"]!="main"}
        save(OUT/(item["id"]+".json"),meta)
        (OUT/(item["id"]+"_설명.txt")).write_text(desc,encoding="utf-8")
        results.append({"id":item["id"],"description_bytes":meta["description_utf8_bytes"]})
    (OUT/"사진_전체귀속문.md").write_text((EP/"outputs/top20-research-v2/사진20장_출처.md").read_text(encoding="utf-8"),encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False))

if __name__=="__main__":main()
