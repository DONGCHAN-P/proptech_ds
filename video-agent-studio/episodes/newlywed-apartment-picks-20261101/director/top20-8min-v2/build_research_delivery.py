"""Build the user-facing research and image handoff from actual, frozen files."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
RESEARCH=EP/"research/top20-8min-v2"
VISUAL=EP/"visual/top20-8min-v2"
OUT=EP/"outputs/top20-research-v2"


def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
def local_link(path):
    # These docs are also exposed by hardlinks in the short video shelf.
    # Absolute file targets work from both locations.
    return Path(path).resolve().as_posix()
def source_link(s):
    url=s.get("url",s.get("source_url"))
    return f'[{s.get("title",s.get("source_id","원문"))}]({url})' if url else "원자료 참조"


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    research=read(RESEARCH/"combined_facts.json")
    regions=research["regions"]
    photo_file=VISUAL/("photo_assets_v2.json" if (VISUAL/"photo_assets_v2.json").exists() else "photo_assets.json")
    photos=read(photo_file)
    photo_index={p["region_id"]:p for p in photos["assets"]}
    assert len(photo_index)==20
    maps=read(VISUAL/"maps/map_assets.json")["assets"]
    map_index={a["region_id"]:a for a in maps}
    all_cards=read(VISUAL/"data_cards/data_card_assets.json")["assets"]+read(VISUAL/"data_cards/additional_data_cards.json")["assets"]
    images=[]
    warnings=[]
    image_doc=["# TOP20 지역별 이미지 자료 안내\n", "2026-11-01 · 통계 기준2024-11-01 · 사진의 촬영 시점은 아래 원장에 별도 보존\n",
       "**지역별 실제 사진20장, 위치 지도PNG20장·편집용SVG20장, 데이터 이미지9장**을 연결했다. 표의 사진은 지역 소개용, 지도는 위치와2024 구역 설명용, 차트는 수치 비교용으로 배치한다.\n",
       "| 순위 | 지역 | 실제 확보한 사진 | 촬영 | 크기 | 이용조건 | 지도 |",
       "|---:|---|---|---|---|---|---|"]
    hashes=[]
    for region in regions:
        rid=region["region_id"];p=photo_index[rid];m=map_index[rid]
        path=Path(p["absolute_file"]) if p.get("absolute_file") else VISUAL/p["actual_file"]
        assert path.is_file(),path
        with Image.open(path) as im:
            im.load();actual=ImageOps.exif_transpose(im).size
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest==p["sha256"]
        hashes.append(digest)
        assert max(actual)>=1200
        license_info=p["license"]
        assert license_info["commercial_copyright_use"] and license_info["adaptation_allowed"]
        notes=license_info.get("third_party_content_notes",[])
        specific_rights=[n for n in notes if "NoFoP" in n or "제3자" in n or "추가 권리" in n]
        reviewed_alternate=p.get("inspection",{}).get("same_unresolved_trigger_detected") is False and p.get("inspection",{}).get("positive_copyright_permission_evidence") is True
        if reviewed_alternate:
            specific_rights=[]
        if specific_rights:warnings.append({"region_id":rid,"notes":specific_rights})
        year=p.get("photo_capture_year") or "원문 미표시"
        image_doc.append(f'| {region["rank"]} | {region["province"]} {region["region"]} | [{p["actual_place"]}]({local_link(path)}) | {year} | {actual[0]}×{actual[1]} | [{license_info["name"]}]({license_info["license_url"]}) | [위치도]({local_link(EP/m["actual_file"])}) |')
        images.append({"region_id":rid,"rank":region["rank"],"province":region["province"],"region":region["region"],
          "photo":p,"photo_path":path,"map":m,"width":actual[0],"height":actual[1]})
    assert len(set(hashes))==20,"A photo was reused across two regions"
    image_doc.extend(["\n## 장면에 넣는 방법\n",
       "- 순위와 지역명은 고정 위치에 두고, 지도에서 현재 지역을 짚은 다음 실제 사진으로 생활권의 모습을 보여준다.\n- 사진을 보여줄 때는 사진에 있는 장소를 정확히 말한다. 신도림역 사진에 G밸리 박물관 설명을 붙이거나, 권선동 터미널 사진을 호매실 체육관으로 표시하지 않는다.\n- 같은 위치도 배경은 현재 지역 강조와 연결하며, 지역 사진은각각 다른 파일을 쓴다. 5곳 단위 요약에서만 순위 비교 차트를 사용한다.\n- 지도 편집 원본SVG는 문구가 분리된 지리 레이어다. PNG는 수치·출처를 포함한 자료 확인용이다. 본편에서는 실제 발화에 맞춰 숫자와 강조를 따로 움직인다.\n- 세로·와이드 사진은 원래 비율을 살린 패널로 배치한다. 낮은 세로 해상도의 사진을 화면 전체로 늘리거나 과도하게 확대하지 않는다.\n- 사진 촬영 연도와 통계 기준 연도를 구분한다. 과거 자료사진은 해당 장소의 소개에 쓰고 현재 공사·상권·시설 운영 상태를 입증하는 화면은 확인한 시점 자료로 보강한다.\n",
       "## 출처·이용조건\n",
       f'선택된 사진20장의 전체 귀속문·원문·촬영일·변형 표시는 [사진20장 출처]({local_link(OUT/"사진20장_출처.md")})에 모았다. 영상 설명란과 이미지별 크레딧을 만들 때 이 원장을 사용한다.\n',
       f'지도는 [SGIS·vuski/admdongkor 출처와 이용조건]({local_link(VISUAL/"maps/지도_출처와_이용조건.md")})을 함께 유지한다.\n'])
    if warnings:
        image_doc.append("### 추가 확인 대상\n\n"+"\n".join(f'- {w["region_id"]}: '+" / ".join(w["notes"]) for w in warnings)+"\n\n해당 파일은 후보 자료로 보관하며 최종 상업 영상 적용 범위를 확인한 뒤 채택한다.\n")
    else:
        image_doc.append("개별 원장에 기록한 출처표시·변형·동일조건 등의 이용조건을 최종 편집과 설명란에 반영한다.\n")
    image_doc.append("\n## 준비된 데이터 이미지\n\n"+"\n".join(f'- [{Path(a["actual_file"]).name}]({local_link(EP/a["actual_file"])})' for a in all_cards))
    (OUT/"이미지자료_안내.md").write_text("\n".join(image_doc),encoding="utf-8")
    credit_lines=["# TOP20 선택 사진20장 출처\n",
      "대표 이미지 원본은 변경하지 않았다. 모아보기 파일에는 비율 유지 축소·배치를 적용했다. 영상에서 크롭·색보정 등 변형을 적용하면 아래 원장에 변형 사항을 덧붙이고 각 원본의 이용조건을 유지한다.\n"]
    for r in regions:
        p=photo_index[r["region_id"]];credit=p["license"];src=p["source_or_prompt"]
        credit_lines.extend([f'## {r["rank"]}위 {r["province"]} {r["region"]} — {p["actual_place"]}\n',
          credit["attribution_ko"]+"\n",
          f'- 촬영: {p.get("photo_capture_date_raw",p.get("photo_capture_year"))}\n- 원문: {src.get("file_page")}\n- 이용조건: {credit.get("usage_conditions_ko")}\n'])
    (OUT/"사진20장_출처.md").write_text("\n".join(credit_lines),encoding="utf-8")

    # Navigation sheet: preserve each photo's aspect rather than force a 16:9 crop.
    sheet=Image.new("RGB",(2160,1600),"#f6f4ef");d=ImageDraw.Draw(sheet)
    ftitle=ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf",22)
    fbody=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",17)
    for i,rec in enumerate(images):
        x,y=(i%4)*540,(i//4)*320
        photo=ImageOps.exif_transpose(Image.open(rec["photo_path"])).convert("RGB")
        photo.thumbnail((510,232))
        sheet.paste(photo,(x+15+(510-photo.width)//2,y+55+(232-photo.height)//2))
        d.text((x+16,y+5),f'{rec["rank"]:02d}위 {rec["province"]} {rec["region"]}',font=ftitle,fill="#173348")
        title=rec["photo"]["actual_place"]
        if len(title)>27:title=title[:26]+"…"
        d.text((x+16,y+32),title,font=fbody,fill="#607680")
        d.text((x+16,y+290),f'촬영 {rec["photo"].get("photo_capture_year") or "미상"} · {rec["width"]}×{rec["height"]}',font=fbody,fill="#607680")
    sheet.save(OUT/"사진20장_미리보기.jpg",quality=91)

    summary=research["summary"]
    report=["# 수도권 신혼부부 TOP20 — 자료조사 결과\n",
      "**영상 목표: 8분, 수도권53개 구의2024년 신혼부부 전체 수 중 TOP20을20위부터1위까지 소개.** 기존 청라·검단·루원 중심 대본은 보존하고 이번 편의 순위 구성과 분리했다.\n",
      "## 영상에서 먼저 말할 발견\n",
      "1. **거주 규모와 전년 대비 변화는 구분해서 볼 수 있다.** 1위 인천 옛 서구는2023년15,941쌍에서2024년15,737쌍으로1.3% 감소했다. 강남구는8,523쌍에서9,321쌍으로9.4% 증가했다.\n2. **상위20개 구는 서울·경기·인천에 함께 분포한다.** 서울9개, 경기6개, 인천5개다. 각 구의 지역 규모와 주택 구성이 다른 점을 다음 비교의 조건으로 연결한다.\n3. **비교 가능한19개 지역 중6곳은 증가,13곳은 감소했다.** 원미구의2023 동일 구역값은 지정 원표에서 확인하지 못해 비교에서 분리했다.\n4. **순위 차이와 수치 차이는 함께 보여줄 수 있다.** 미추홀구8,483쌍과 노원구8,473쌍은10쌍 차이다. 집을 고를 때는 위치·예산·생활 조건을 더해 후보를 좁힌다.\n5. **전체 신혼부부의 구성도 지역마다 다르다.** 초혼 비중은 영통구91.0%, 옛 서구81.0%, 남동구69.9%다. 이번 순위는 초혼·재혼·혼인종류 미상을 포함한 전체 수를 사용한다.\n",
      "증감은 두 기준일의 거주 규모 차이다. 혼인 후5년 범위의 진입·이탈, 혼인관계 변화, 이동 등이 함께 반영된다. 원인별 설명은 해당 원인 자료를 연결한 후 확정한다.\n",
      "출처: [2024년 신혼부부통계](https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3#page=32), [2023년 신혼부부통계](https://sri.kostat.go.kr/boardDownload.es?bid=11815&list_no=434122&seq=3#page=32). 기존2024 표86행·258개 숫자는 독립 검토를 통과한 값을 승계했다.\n",
      "## 지역별 확인 결과와 확보한 화면\n",
      "| 순위 | 지역 | 2024 신혼부부(쌍) | 2023 대비 | 실제 사진 소재 |",
      "|---:|---|---:|---:|---|"]
    for r in regions:
        p=photo_index[r["region_id"]]
        delta="동일 구역값 미확인" if r["change_percent"] is None else f'{r["change_percent"]:+.1f}%'
        report.append(f'| {r["rank"]} | {r["province"]} {r["region"]} | {r["count2024"]:,} | {delta} | {p["actual_place"]} |')
    report.extend(["\n## 자료 준비 범위\n",
      f'- 지역20곳의 원문 자료와 설명 후보를 정리했다. 지역 특징{summary["feature_claim_count"]}건 중 원문 확인{summary["verified_feature_claim_count"]}건, 검색 색인 등 추가 확인 대상{summary["qualified_feature_claim_count"]}건이다.\n- 출처 원문은{summary["unique_source_urls"]}개 URL을 기록했다. 기관·운영사 페이지, 자료 기준일·확인일·주장별 근거를JSON에 연결했다.\n- 지역별 실사20장, 지도PNG20장·SVG20장, 비교 차트9장을 저장했다. 사진은 서로 다른 파일이며 각 파일의 크기·해상도·해시·출처·이용조건을 확인한다.\n- 59㎡·84㎡의 지역별 실거래 문맥40행을 별도로 집계했다. 계약기간2026.4~9,3층 이상, 전용59~60㎡ 미만/84~85㎡ 미만 기준이다.40개 집계 모두20건 이상의 표본을 확보했다. 해당 표는 지역 안 여러 단지의 거래 분포를 보여주는 보조자료로 사용한다.\n',
      "## 화면의 의미를 맞추기\n",
      "사진은 지명과 생활권을 떠올리게 하는 역할, 지도는2024 구역과 위치를 보여주는 역할, 차트는 수와 변화를 설명하는 역할을 맡긴다. 공원·역·기업이 있다는 사실을 신혼부부 거주 증가의 원인으로 단정하는 문장은 넣지 않는다.\n",
      "옛 인천 서구는 현재 서해구·검단구를 함께 포함한 과거 구역으로 안내한다. 원미구는2024년에 복원된 구의 실제 경계를 확보했다. 화성 등 구가 없었던 시·군의 순위는 기존 별도 표에 보존했다.\n",
      "## 자료 파일\n",
      f'- [지역20곳 통합 근거JSON]({local_link(RESEARCH/"combined_facts.json")})\n- [전년 비교 표CSV]({local_link(RESEARCH/"top20_comparison.csv")})\n- [같은 면적의 실거래 문맥CSV]({local_link(RESEARCH/"price_context.csv")})\n- [지역별 이미지 안내]({local_link(OUT/"이미지자료_안내.md")})\n- [사진20장 미리보기]({local_link(OUT/"사진20장_미리보기.jpg")})\n- [지도20장 미리보기]({local_link(VISUAL/"maps/지도20장_모아보기.jpg")})\n',
      "## 아직 제작 전에 확인할 것\n",
      "정지 이미지·지도·통계 자료 준비 단계다. 실제 음성에 맞춘 타이밍, 자막·모션, 최종 렌더와 재생·청취 검수는 후속 제작 단계에서 진행한다. 촬영 시점이 오래된 사진의 용도를 지역 소개로 맞추고, 자료 원장의 이용조건과 크레딧을 최종 편집에 반영한다.\n"])
    if warnings:report.append("현재 사진 원장에 추가 권리 검토 표시가 있는 지역: "+", ".join(w["region_id"] for w in warnings)+". 대체 사진 또는 최종 적용 범위를 확인한 뒤 채택한다.\n")
    (OUT/"자료조사_결과.md").write_text("\n".join(report),encoding="utf-8")

    timeline=[("00:00~00:35",35,"훅·질문","다른 도시 실사3곳과 수도권 위치도"),
      ("00:35~00:55",20,"집계 기준","2024년·쌍 단위·수도권53개 구·초혼/재혼"),
      ("00:55~02:15",80,"20위→16위","각16초, 사진·위치·숫자"),
      ("02:15~02:31",16,"중간 비교1","서울·경기·인천 분포"),
      ("02:31~03:51",80,"15위→11위","각16초, 실제 지역 자료 교체"),
      ("03:51~04:07",16,"중간 비교2","미추홀·노원 수치 간격"),
      ("04:07~05:37",90,"10위→6위","각18초, 전년 변화와 지역 특징"),
      ("05:37~05:52",15,"중간 비교3","거주 규모와 전년 대비 변화"),
      ("05:52~07:32",100,"5위→1위","각20초, 전년 변화·현재 지명 연결"),
      ("07:32~08:00",28,"정리·다음 선택","조건별 단지 탐색으로 연결·CTA")]
    assert sum(x[1] for x in timeline)==480
    schedule=["# TOP20 8분 구성안\n","목표480초의 설계안. 실제 음성 생성·정렬 전에는 구간별 길이가 잠정값이다. 낭독 속도를 무리하게 바꾸지 않고 실제 호흡에 맞춰 최종 시간을 조정한다.\n",
       "| 목표 구간 | 길이 | 설명 | 화면 |","|---|---:|---|---|"]
    schedule.extend(f"| {a} | {b}초 | {c} | {d} |" for a,b,c,d in timeline)
    schedule.extend(["\n## 연결 방식\n","지역명·순위 표식과 지도 locator는 위치를 유지한다. 새 지역으로 넘어갈 때 사진과 강조 지역을 함께 넘기고, 숫자는 발화에 맞춰 나타낸다. 전환마다 빈 화면·전체 지도 재등장·반복 줌을 끼우지 않는다.\n",
       "각 지역을 지도 한 장으로 오래 설명하지 않는다. 위치 확인 → 실제 사진 → 수치·필요한 비교의 순서로 자료 기능을 바꾼다. 같은 장소를 계속 설명할 때에는 같은 원도에서 초점을 이어간다.\n"])
    writer_root=EP/"writer/top20-8min-v2"
    proposal=writer_root/("scene_proposals_v3.json" if (writer_root/"scene_proposals_v3.json").exists() else "scene_proposals.json")
    if proposal.exists():
        proposed=read(proposal)
        units=proposed["scenes"]
        assert abs(sum(s["duration_s"] for s in units)-480)<0.01
        def mmss(seconds):return f"{int(seconds)//60:02d}:{int(seconds)%60:02d}"
        schedule=["# TOP20 8분 구성안\n","목표480초의 잠정 배치다. 현재 대본의 장면 제안표와 같은 시간을 사용한다. 실제 음성 생성·정렬 후 호흡·자막·컷의 시간을 확정한다.\n",
          "| 목표 구간 | 길이 | 장면 | 내용 |","|---|---:|---|---|"]
        schedule.extend(f'| {mmss(s["start_s"])}~{mmss(s["end_s"])} | {s["duration_s"]:g}초 | {s["scene_id"]} | {s["title"]} |' for s in units)
        schedule.extend(["\n지역명·순위 표식과 지도 locator는 위치를 유지한다. 현재 지역 사진과 강조를 함께 연결하고, 실제 발화에 맞춰 숫자·지도·자료를 순차적으로 바꾼다. 구역 지도는 위치, 실제 사진은 해당 장소, 차트는 수치를 맡긴다.\n",
          "사진과 낭독의 장소가 다른 경우 지역 개요용 사진과 해당 주장의 근거 화면을 구분한다. 자료 매칭 결과는 `director/top20-8min-v2/scene_asset_plan.json`에 기록한다.\n"])
    (OUT/"8분_구성안.md").write_text("\n".join(schedule),encoding="utf-8")

    manifest={"revision":"top20-8min-v2","stage":"research_and_media_preparation","created_at":datetime.now().astimezone().isoformat(),
      "regions":20,"primary_photo_count":20,"primary_photo_unique_hash_count":len(set(hashes)),"map_png_count":20,"map_svg_count":20,
      "data_card_png_count":len(all_cards),"photo_manifest":str(photo_file.relative_to(EP)),"rights_context_review_required":warnings,
      "research_summary":summary,"script_file":str(EP/"writer/top20-8min-v2/script_v2.md") if (EP/"writer/top20-8min-v2/script_v2.md").exists() else None,
      "video_rendered":False,"actual_audio_listening_performed":False,"continuous_video_playback_performed":False,
      "guides_applied":["영상제작_마스터가이드","지역_상세지도와_의미단위_자막","media-use provenance"],
      "hyperframes_usage":{"status":"unknown","reason":"usage_request_failed","render_not_started":True}}
    write(OUT/"delivery_manifest.json",manifest)
    print(json.dumps({k:manifest[k] for k in ["regions","primary_photo_count","map_png_count","map_svg_count","data_card_png_count","rights_context_review_required","video_rendered"]},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
