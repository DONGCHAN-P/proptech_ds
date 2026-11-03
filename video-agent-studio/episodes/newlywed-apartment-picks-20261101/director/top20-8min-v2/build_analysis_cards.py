"""Additional data-led comparisons, separate from the immutable six-card QA input."""
import importlib.util
import json
from pathlib import Path

from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
OUT=EP/"visual/top20-8min-v2/data_cards"
RESEARCH=EP/"research/top20-8min-v2"
spec=importlib.util.spec_from_file_location("styles",HERE/"build_map_assets.py")
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def canvas(title):
    im=Image.new("RGB",(1920,1080),s.BG);d=ImageDraw.Draw(im)
    s.text(d,(90,42),"데이터로보는부동산",25,s.MUTED,True)
    s.text(d,(90,105),title,45,s.INK,True,1740)
    return im,d


def main():
    regions=json.loads((RESEARCH/"combined_facts.json").read_text(encoding="utf-8"))["regions"]
    lookup={r["region_id"]:r for r in regions}
    assets=[]
    im,d=canvas("거주 규모와 전년 대비 변화는 다릅니다")
    for i,rid in enumerate(["R01","R06","R04"]):
        r=lookup[rid];y=240+i*194
        s.text(d,(100,y),r["province"]+" "+r["region"],34,s.INK,True,500)
        for j,(value,color) in enumerate([(r["count2023"],"#c2cacc"),(r["count2024"],s.REGION_COLORS[r["province"]])]):
            x0=640;yy=y+j*52
            d.rounded_rectangle((x0,yy,x0+value/16500*850,yy+34),radius=5,fill=color)
            s.text(d,(1510,yy-7),f"{value:,}쌍",29,color if j else s.MUTED,True,310)
        delta=f'{r["change_percent"]:+.1f}%'
        s.text(d,(105,y+66),delta,36,"#167f86" if r["change_couples"]>0 else "#996f36",True)
    s.text(d,(100,862),"회색 2023년    색상 2024년 · 각 해 11월 1일 기준",25,s.MUTED)
    s.text(d,(90,930),"출처: 국가데이터처·통계청 신혼부부통계(2023·2024) · 공표값으로 직접 계산",22,s.MUTED,max_width=1740)
    path=OUT/"분석_거주규모와_전년변화.png";im.save(path,optimize=True)
    assets.append({"asset_id":"ANALYSIS_STOCK_AND_CHANGE","actual_file":str(path.relative_to(EP)),"regions":["R01","R06","R04"],"type":"data_chart","source":"research/top20-8min-v2/combined_facts.json","scale_max":16500})

    im,d=canvas("10위와 11위의 차이, 10쌍")
    for i,rid in enumerate(["R10","R11"]):
        r=lookup[rid];y=300+i*195
        s.text(d,(105,y),f'{r["rank"]}위 {r["province"]} {r["region"]}',36,s.INK,True,535)
        d.rounded_rectangle((665,y+5,665+900*r["count2024"]/10000,y+85),radius=8,fill=s.REGION_COLORS[r["province"]])
        s.text(d,(1570,y+7),f'{r["count2024"]:,}쌍',39,s.REGION_COLORS[r["province"]],True,280)
    s.text(d,(105,765),"위치·예산·생활 조건을 더해 후보를 고릅니다",35,s.INK,True)
    s.text(d,(90,930),"출처: 국가데이터처 신혼부부통계(2024.11.1) · 수도권 53개 구 중 순위",22,s.MUTED,max_width=1740)
    path=OUT/"분석_10위와11위_10쌍차이.png";im.save(path,optimize=True)
    assets.append({"asset_id":"ANALYSIS_NEAR_EQUAL_RANKS","actual_file":str(path.relative_to(EP)),"regions":["R10","R11"],"type":"data_chart","difference_couples":10,"scale_max":10000})

    im,d=canvas("같은 전용59㎡급, 지역 안의 거래가격 폭")
    for i,rid in enumerate(["R01","R03","R02"]):
        r=lookup[rid];p=next(x for x in r["price_context"] if x["area_band"]=="59")
        assert p["n"]>=20
        y=290+i*185;x0=665;width=1040;ceiling=300000
        region_label = "인천 옛 서구" if rid=="R01" else r["province"]+" "+r["region"]
        s.text(d,(105,y),region_label,34,s.INK,True,490)
        s.text(d,(105,y+62),f'거래 {p["n"]:,}건 · 단지 {p["complex_count"]}곳',25,s.MUTED)
        color=s.REGION_COLORS[r["province"]]
        x25=x0+p["p25_manwon"]/ceiling*width;x75=x0+p["p75_manwon"]/ceiling*width
        xm=x0+p["median_manwon"]/ceiling*width
        d.line((x0,y+43,x0+width,y+43),fill="#d5dcdd",width=2)
        d.rounded_rectangle((x25,y+20,x75,y+70),radius=4,fill={"서울":"#b9cffa","경기":"#b1d2d5","인천":"#d9c899"}[r["province"]])
        d.line((xm,y+9,xm,y+81),fill=color,width=5)
        s.text(d,(min(xm+12,1580),y-45),f'{p["median_manwon"]/10000:.2f}억',30,color,True,280)
    for value in [0,100000,200000,300000]:
        x=665+1040*value/300000
        s.text(d,(x-23,858),f'{value//10000}억',22,s.MUTED)
    s.text(d,(105,815),"옅은 막대: 중간 50% 거래가격 · 진한 선: 중위값",23,s.MUTED)
    s.text(d,(90,932),"국토교통부 아파트 실거래 · 2026.4~9 계약 · 전용59~60㎡ 미만 · 3층 이상",22,s.MUTED,max_width=1740)
    s.text(d,(90,970),"지역별 여러 단지의 거래 분포 · 취소 제외 기준으로 집계 · 기간과 표본 수 함께 표시",22,s.MUTED,max_width=1740)
    path=OUT/"분석_동일면적_지역별가격분포.png";im.save(path,optimize=True)
    assets.append({"asset_id":"ANALYSIS_AREA_MATCHED_PRICE_SPREAD","actual_file":str(path.relative_to(EP)),"regions":["R01","R03","R02"],"type":"data_chart","source":"research/top20-8min-v2/price_context.json","scale_max_manwon":300000,"period":["2026-04-01","2026-09-30"]})
    (OUT/"additional_data_cards.json").write_text(json.dumps({"assets":assets,"dimensions":[1920,1080],"ai_generated":False,"qa":"director_visual_check_pending"},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"additional_data_cards":len(assets)},ensure_ascii=False))


if __name__=="__main__":main()
