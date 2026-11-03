"""Prepare reusable chart artwork with fixed scales and explicit observation periods."""
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
OUT = EP / "visual/top20-8min-v2/data_cards"
RESEARCH = EP / "research/top20-8min-v2"
spec = importlib.util.spec_from_file_location("map_styles", HERE / "build_map_assets.py")
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)


def canvas(title):
    im = Image.new("RGB", (1920,1080),style.BG)
    d = ImageDraw.Draw(im)
    style.text(d,(90,42),"데이터로보는부동산",25,style.MUTED,True)
    style.text(d,(90,105),title,45,style.INK,True,1730)
    return im,d


def footer(d, description="2024년 11월 1일 · 수도권 53개 구 중 · 혼인신고 후 5년 미경과"):
    style.text(d,(90,928),description,24,style.MUTED,max_width=1740)
    style.text(d,(90,970),"출처: 국가데이터처 2024년 신혼부부통계",22,style.MUTED,max_width=1740)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    top = json.loads((RESEARCH / "top20.json").read_text(encoding="utf-8"))["regions"]
    assets = []
    for low,high in [(16,20),(11,15),(6,10),(1,5)]:
        rows = sorted([r for r in top if low<=r["rank"]<=high],key=lambda r:-r["rank"])
        im,d = canvas(f'수도권 신혼부부 TOP20  |  {high}위 → {low}위')
        x0, bar_width, ceiling = 665, 870, 16000
        for i,r in enumerate(rows):
            y = 245 + i*116
            color = style.REGION_COLORS[r["province"]]
            style.text(d,(92,y-7),f'{r["rank"]}위',36,style.INK,True)
            style.text(d,(223,y-5),r["province"]+" "+r["region"],33,style.INK,True,415)
            d.rounded_rectangle((x0,y,x0+bar_width,y+52),radius=5,fill="#e8ebea")
            length = bar_width*r["newlywed_couples"]/ceiling
            d.rounded_rectangle((x0,y,x0+length,y+52),radius=5,fill=color)
            style.text(d,(1570,y-3),f'{r["newlywed_couples"]:,}쌍',34,color,True,265)
        for value in [0,4000,8000,12000,16000]:
            x = x0+bar_width*value/ceiling
            d.line((x,838,x,848),fill=style.MUTED,width=1)
            style.text(d,(x-20 if value==0 else x-37,858),f'{value:,}',20,style.MUTED)
        footer(d)
        path = OUT / f"순위_{high:02d}위부터_{low:02d}위.png"
        im.save(path,optimize=True)
        assets.append({"asset_id":f"RANK_GROUP_{high}_{low}","actual_file":str(path.relative_to(EP)),
          "type":"data_chart","ai_generated":False,"axis_max_couples":ceiling,"scale_common_to_all_groups":True,
          "rank_order":[r["rank"] for r in rows],"source":"research/top20-8min-v2/top20.json"})

    im,d = canvas("TOP20에 포함된 구는 어디에 있을까?")
    for i,province in enumerate(["서울","경기","인천"]):
        count = sum(r["province"]==province for r in top)
        y = 290 + i*174
        style.text(d,(135,y),province,45,style.INK,True)
        d.rounded_rectangle((420,y+5,420+110*count,y+85),radius=10,fill=style.REGION_COLORS[province])
        style.text(d,(1490,y+6),f"{count}개 구",53,style.REGION_COLORS[province],True)
    style.text(d,(135,825),"비교 대상: 2024년 수도권 53개 구 중 상위 20개 구",29,style.MUTED)
    footer(d)
    path = OUT/"TOP20_서울9_경기6_인천5.png";im.save(path,optimize=True)
    assets.append({"asset_id":"TOP20_PROVINCE_COUNTS","actual_file":str(path.relative_to(EP)),"type":"data_chart",
        "ai_generated":False,"metric":"number of districts within TOP20, not couple share","values":{"서울":9,"경기":6,"인천":5}})

    im,d = canvas("신혼부부의 구성도 지역마다 다릅니다")
    for i,rank in enumerate([12,1,16]):
        r=next(x for x in top if x["rank"]==rank)
        total,first,remarried=r["newlywed_couples"],r["first_marriage_couples"],r["remarried_couples"]
        unknown=total-first-remarried
        assert unknown>=0
        y=250+i*175
        style.text(d,(110,y),r["province"]+" "+r["region"],33,style.INK,True,600)
        style.text(d,(1220,y),f"초혼 비중 {first/total*100:.1f}%",35,style.BLUE,True,590)
        start=110
        for value,color in [(first,style.BLUE),(remarried,"#c29a44"),(unknown,"#bcc6c8")]:
            width=1680*value/total
            d.rectangle((start,y+64,start+width,y+115),fill=color)
            start+=width
    style.text(d,(110,832),"초혼",26,style.BLUE,True)
    style.text(d,(260,832),"재혼",26,"#a07a24",True)
    style.text(d,(410,832),"혼인종류 미상",26,style.MUTED)
    footer(d)
    path=OUT/"신혼부부_초혼재혼_구성비교.png";im.save(path,optimize=True)
    assets.append({"asset_id":"NEWLYWED_COMPOSITION","actual_file":str(path.relative_to(EP)),"type":"data_chart",
        "ai_generated":False,"source":"research/top20-8min-v2/top20.json","ranks":[12,1,16]})
    (OUT/"data_card_assets.json").write_text(json.dumps({"assets":assets,"dimensions":[1920,1080],
      "license":"original chart artwork using openly published statistical facts; source attribution retained",
      "manual_visual_review":"pending"},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"data_cards_created":len(assets),"dimensions":[1920,1080]},ensure_ascii=False))


if __name__=="__main__":
    main()
