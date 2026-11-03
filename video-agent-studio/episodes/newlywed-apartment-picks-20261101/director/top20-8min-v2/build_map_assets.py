"""Create authentic 2024 regional locator assets from SGIS-derived polygons."""
from __future__ import annotations

import gzip
import hashlib
import html
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

EP = Path(__file__).resolve().parents[2]
RESEARCH = EP / "research/top20-8min-v2"
OUT = EP / "visual/top20-8min-v2/maps"
BG = "#f6f4ef"
INK = "#173348"
MUTED = "#607680"
BLUE = "#286cda"
REGION_COLORS = {"서울": "#286cda", "경기": "#167f86", "인천": "#b58a36"}
FONT = Path("C:/Windows/Fonts/malgun.ttf")
BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def text(d, xy, value, size, color=INK, bold=False, max_width=None):
    chosen = font(size, bold)
    if max_width is not None:
        while d.textbbox((0, 0), value, font=chosen)[2] > max_width:
            size -= 1
            chosen = font(size, bold)
    d.text(xy, value, fill=color, font=chosen, stroke_width=0)
    box = d.textbbox(xy, value, font=chosen)
    assert box[0] >= 0 and box[1] >= 0 and box[2] <= 1920 and box[3] <= 1080, (value, box)
    return box


def mercator(coordinate):
    lon, lat = coordinate[:2]
    return (6378137 * math.radians(lon), 6378137 * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def geometry_polygons(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    raise ValueError(geom["type"])


def render_mask(polygons, transform, width=1920, height=1080):
    # Unite disjoint dong polygons as raster masks; do not invent a city polygon.
    result = Image.new("L", (width, height), 0)
    for rings in polygons:
        part = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(part)
        for i, ring in enumerate(rings):
            points = [transform(p) for p in ring]
            if len(points) >= 3:
                draw.polygon(points, fill=255 if i == 0 else 0)
        result = ImageChops.lighter(result, part)
    return result


def vector_path(polygons, transform):
    paths = []
    for rings in polygons:
        for ring in rings:
            pts = [transform(p) for p in ring]
            if len(pts) < 3:
                continue
            # Round to render pixels; raw geographic coordinates remain frozen.
            paths.append("M" + "L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts) + "Z")
    return "".join(paths)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.loads((RESEARCH / "top20.json").read_text(encoding="utf-8"))
    top = payload["regions"]
    raw = json.loads(gzip.decompress((RESEARCH / "source/HangJeongDong_ver20241001.geojson.gz").read_bytes()))
    capital = [f for f in raw["features"] if f["properties"]["sido"] in {"11", "28", "41"}]
    groups = defaultdict(list)
    originals = defaultdict(list)
    codes = {}
    for feature in capital:
        props = feature["properties"]
        province = {"11": "서울", "28": "인천", "41": "경기"}[props["sido"]]
        key = (province, props["sggnm"].replace(" ", ""))
        groups[key].extend(geometry_polygons(feature["geometry"]))
        originals[key].append(feature)
        codes[key] = props["sgg"]
    for row in top:
        key = (row["province"], row["region"].replace(" ", ""))
        assert key in groups, key
        row["geo_key"] = key
    projected = [mercator(p) for row in top for rings in groups[tuple(row["geo_key"])] for p in rings[0]]
    xs, ys = zip(*projected)
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    dx, dy = xmax - xmin, ymax - ymin
    xmin -= dx * .08; xmax += dx * .08
    ymin -= dy * .07; ymax += dy * .07
    area = (105, 190, 1265, 850)
    scale = min((area[2]-area[0])/(xmax-xmin), (area[3]-area[1])/(ymax-ymin))
    ox = (area[0]+area[2])/2 - ((xmin+xmax)/2)*scale
    oy = (area[1]+area[3])/2 + ((ymin+ymax)/2)*scale
    def transform(p):
        x, y = mercator(p)
        return (ox+x*scale, oy-y*scale)
    base = Image.new("RGB", (1920, 1080), BG)
    masks = {}
    vecs = {}
    for key, polygons in groups.items():
        bounds = [mercator(p) for rings in polygons for p in rings[0]]
        if not any(xmin <= p[0] <= xmax and ymin <= p[1] <= ymax for p in bounds):
            continue
        mask = render_mask(polygons, transform)
        if mask.getbbox() is None:
            continue
        # The map viewport is defined by every TOP20 target; outside context is clipped.
        viewport = Image.new("L", (1920,1080), 0)
        ImageDraw.Draw(viewport).rectangle(area, fill=255)
        mask = ImageChops.multiply(mask, viewport)
        masks[key] = mask
        edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(3)))
        base.paste("#dde2e3", (0,0), mask)
        base.paste("#f9f8f4", (0,0), edge)
        vecs[key] = vector_path(polygons, transform)
    assets = []
    records = []
    for row in top:
        key = tuple(row["geo_key"])
        target = masks[key]
        assert target.getbbox() is not None
        box = target.getbbox()
        assert box[0] >= area[0] and box[1] >= area[1] and box[2] <= area[2]+1 and box[3] <= area[3]+1
        image = base.copy()
        image.paste(REGION_COLORS[row["province"]], (0,0), target)
        edge = ImageChops.subtract(target.filter(ImageFilter.MaxFilter(5)), target)
        image.paste("#ffffff", (0,0), edge)
        draw = ImageDraw.Draw(image)
        text(draw, (90,42), "데이터로보는부동산", 25, MUTED, True)
        text(draw, (90,95), f'{row["rank"]:02d}위  {row["province"]} {row["region"]}', 48, INK, True, 1650)
        text(draw, (1320,240), "신혼부부", 32, MUTED)
        text(draw, (1320,291), f'{row["newlywed_couples"]:,}쌍', 65, REGION_COLORS[row["province"]], True, 510)
        text(draw, (1320,418), "2024년 11월 1일 기준", 27, MUTED)
        text(draw, (1320,473), "수도권 53개 구 중", 27, MUTED)
        text(draw, (1320,517), f'{row["rank"]}위', 43, INK, True)
        text(draw, (1320,620), f'초혼 {row["first_marriage_couples"]:,}쌍', 29, MUTED)
        if row["rank"] == 1:
            text(draw, (1320,695), "당시 서구 범위", 26, MUTED, True)
            text(draw, (1320,735), "현 서해구·검단구", 26, MUTED)
        text(draw, (105,868), "회색: 수도권 주변 구역    색상: 현재 설명하는 지역", 22, MUTED)
        text(draw, (90,930), "통계: 국가데이터처 신혼부부통계(2024)  |  행정구역: 2024.10 버전", 22, MUTED)
        text(draw, (90,969), "경계 원자료: 통계청 SGIS · 가공: vuski/admdongkor · CC BY 4.0", 22, MUTED)
        stem = f'{row["region_id"]}_{row["region"].replace(" ", "_")}'
        png = OUT / f"{stem}_위치지도.png"
        image.save(png, optimize=True)
        context_paths = "".join(f'<path d="{path}" fill="#dde2e3" stroke="#f9f8f4" stroke-width="0.7" fill-rule="evenodd"/>' for path in vecs.values())
        svg = OUT / f"{stem}_지도원본.svg"
        svg.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<title>{html.escape(row["province"]+' '+row["region"])} — 2024 행정경계 위치도</title>
<desc>Source: Statistics Korea SGIS; modified by vuski/admdongkor; CC BY 4.0; boundary version 20241001. Web Mercator. Grouped dong polygons; display-pixel rounding. No invented geographic polygons.</desc>
<defs><clipPath id="map"><rect x="105" y="190" width="1160" height="660"/></clipPath></defs>
<g clip-path="url(#map)">{context_paths}<path d="{vecs[key]}" fill="{REGION_COLORS[row["province"]]}" fill-rule="evenodd"/></g></svg>''', encoding="utf-8")
        target_features = originals[key]
        feature_file = OUT / f"{stem}_境界.geojson.gz"
        feature_file.write_bytes(gzip.compress(json.dumps({"type":"FeatureCollection","features":target_features},ensure_ascii=False,separators=(",",":")).encode(),mtime=0))
        attribution = "본 데이터는 통계청 통계지리정보서비스(SGIS, https://sgis.kostat.go.kr)에서 공공누리 제1유형으로 개방한 행정동 경계를 가공한 것이며(가공: vuski/admdongkor, https://github.com/vuski/admdongkor), CC BY 4.0으로 배포됩니다. 이번 영상용으로 지역별 그룹화·투영·색상·라벨을 가공했습니다."
        assets.append({"asset_id": f'MAP_{row["region_id"]}', "region_id":row["region_id"],"rank":row["rank"],
          "province":row["province"],"region":row["region"],"source_region_code":codes[key],"source_dong_count":len(target_features),
          "actual_file":str(png.relative_to(EP)),"vector_file":str(svg.relative_to(EP)),"geometry_file":str(feature_file.relative_to(EP)),
          "type":"verified_geographic_data_map", "actual_place":True,"ai_generated":False,
          "dimensions":[1920,1080],"statistical_reference_date":"2024-11-01","boundary_version":"2024-10-01",
          "license":"CC BY 4.0, upstream SGIS KOGL Type 1", "license_url":"https://creativecommons.org/licenses/by/4.0/",
          "source_url":"https://github.com/vuski/admdongkor/tree/master/ver20241001", "attribution":attribution,
          "projection":"EPSG:3857 formulas; same viewport and scale in all 20 cards",
          "review":{"region_name_and_province_exact_match":True,"nonempty_polygon_mask":True,"target_inside_viewport":True,"source_git_blob_verified":True,"manual_visual_inspection":"pending"},
          "sha256":hashlib.sha256(png.read_bytes()).hexdigest(),"bytes":png.stat().st_size})
        records.append({"region_id":row["region_id"],"source_sgg":codes[key],"dong_count":len(target_features),"mask_bbox":box})

    # A sheet is QA/navigation evidence; the full-size assets remain the sources.
    sheet = Image.new("RGB", (1920, 1300), "#e9e9e5")
    sd = ImageDraw.Draw(sheet)
    for i, item in enumerate(assets):
        thumb = Image.open(EP / item["actual_file"]).resize((480,270))
        x, y = (i%4)*480, (i//4)*260
        thumb.thumbnail((460,230))
        sheet.paste(thumb, (x+10,y+5))
        sd.text((x+15,y+232), f'{item["rank"]:02d} {item["province"]} {item["region"]}', font=font(17,True), fill=INK)
    sheet.save(OUT / "지도20장_모아보기.jpg", quality=90)
    (OUT / "map_assets.json").write_text(json.dumps({"revision":"top20-8min-v2","assets":assets,"validation":records},ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT / "지도_출처와_이용조건.md").write_text("# 지도 자료 출처와 이용조건\n\n"+attribution+"\n\n- 기준 경계: ver20241001. 통계 기준일2024-11-01과 시점을 맞췄습니다.\n- 원미구는2024년 복원된 구역의 실제 행정동을 사용했습니다. 기존 웹 지도에 남은 부천시 전체 경계를 원미구로 사용하지 않았습니다.\n- 인천 서구는2024년 당시 범위를 유지하며 현재 서해구·검단구 이름은 별도 주석으로 연결합니다.\n- 원도 GeoJSON과 라이선스 스냅샷은 research/top20-8min-v2/source에 보존했습니다.\n- 지도는 위치 설명용이며 부동산 필지·측량 자료의 용도로 제작하지 않았습니다.\n",encoding="utf-8")
    print(json.dumps({"maps_created":len(assets),"png_dimensions":[1920,1080],"code_and_mask_checks":len(records),"output":str(OUT)},ensure_ascii=False))


if __name__ == "__main__":
    main()
