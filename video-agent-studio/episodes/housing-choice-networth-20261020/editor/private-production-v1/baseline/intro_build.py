"""인트로 모션그래픽 index.html 생성기.

음성이 아직 없으므로 큐 시간은 Jun 실측 속도(교산 v5 자막 6.19자/초)로 추정한 provisional 값이다.
확정 음성이 나오면 CUES의 시간을 실제 정렬로 바꾸고 다시 실행한다.
실행: python -X utf8 build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
CPS = 6.19          # 교산 v5 Jun 자막 기준 글자/초 (공백 제외, 큐 사이 쉼 포함)
CUE_GAP = 0.25      # 큐 사이 쉼
PARA_GAP = 0.6      # 문단 끝 추가 쉼
LEAD_IN = 0.6
TAIL = 1.2

# (화면 자막, 낭독 읽기 표기 또는 None, 문단 끝 여부)
CUES = [
    ("같은 아파트에서 같은 기간을 살아도,", None, False),
    ("집을 산 가구와 전세로 산 가구, 월세로 산 가구의 자산은 다르게 남습니다.", None, False),
    ("집값 상승률과 주식 수익률만 나란히 놓으면", None, False),
    ("이 차이를 설명하기 어렵습니다.", None, False),
    ("세 가구 모두 매달 살 집이 필요하고,", None, False),
    ("그 집을 마련하는 데 들어가는 돈이 다르기 때문입니다.", None, True),
    ("이번 비교에서는 초기 순자산이 2억5천만원이고", "이번 비교에서는 초기 순자산이 이억오천만원이고", False),
    ("매달 주거와 저축에 쓸 수 있는 돈이 300만원인 세 가구를 놓겠습니다.", "매달 주거와 저축에 쓸 수 있는 돈이 삼백만원인 세 가구를 놓겠습니다.", False),
    ("같은 수준의 6억원 집에서 10년을 사는 설정입니다.", "같은 수준의 육억원 집에서 십년을 사는 설정입니다.", False),
    ("한 가구는 집을 사고, 한 가구는 전세를,", None, False),
    ("다른 가구는 월세를 선택합니다.", None, False),
    ("남은 돈은 세 가구 모두 같은 투자 규칙을 적용합니다.", None, True),
    ("그 결과 기본 가정에서는 10년 후 순자산이", "그 결과 기본 가정에서는 십년 후 순자산이", False),
    ("매매 약 6억1천만원, 전세 약 6억6천만원, 월세 약 6억9천만원으로 계산됩니다.", "매매 약 육억천만원, 전세 약 육억육천만원, 월세 약 육억구천만원으로 계산됩니다.", False),
    ("여기서 집값과 투자수익 가정을 바꾸면", None, False),
    ("매매가 가장 크게 남는 경우도, 전세가 가장 크게 남는 경우도 나옵니다.", None, False),
    ("오늘 살펴볼 것은 이 순서가 바뀌는 이유입니다.", None, True),
    ("지난 교산편에서는 지역의 입지와 가격을 살펴봤습니다.", None, False),
    ("이번부터는 그다음 선택으로 이어갑니다.", None, False),
    ("좋은 지역을 찾은 뒤 집을 어떤 방식으로 마련할지,", None, False),
    ("얼마까지 감당할 수 있을지,", None, False),
    ("그 예산에서 어떤 단지를 고를지를 차례로 연결하겠습니다.", None, False),
    ("오늘은 그 첫 단계인 주거 방식과 순자산 비교입니다.", None, True),
]

# 장면: (id, 제목, 첫 큐 index, 마지막 큐 index)
SCENES = [
    ("s1", "같은 집 · 세 가구", 0, 1),
    ("s2", "매달 드는 주거비", 2, 5),
    ("s3", "비교 조건", 6, 11),
    ("s4", "10년 후 순자산", 12, 16),
    ("s5", "시리즈 순서", 17, 22),
]

SOURCES = {
    "s1": "자체 예시 모형(2026.10) · 같은 6억원 집에서 10년 거주 · 막대 높이는 기본 가정의 10년 후 순자산 비율",
    "s2": "자체 예시 모형(2026.10) · 막대 길이는 기본 가정 첫 달 주거비 비율 · 공통 생활비 제외",
    "s3": "자체 예시 모형(2026.10) · 초기 순자산 2억5천만원 · 월 300만원 · 6억원 집 · 10년",
    "s4": "자체 예시 모형(2026.10) · 금리 연 4% · 월세 100만원 · 세금 미반영 · 10년 시점 보유 평가 · 과거 실적·전망 아님",
    "s5": "지난 편: 하남 교산 v5 화면(국토교통부 고시 2026-535호 · LH 공개 토지이용계획 재구성)",
}


def timings():
    t = LEAD_IN
    out = []
    for text, spoken, para_end in CUES:
        n = len((spoken or text).replace(" ", "").replace(",", "").replace(".", ""))
        d = round(n / CPS, 2)
        out.append({"text": text, "start": round(t, 2), "dur": d})
        t += d + CUE_GAP + (PARA_GAP if para_end else 0)
    return out, round(t - CUE_GAP + TAIL, 2)


def main():
    cues, total = timings()
    scenes = []
    for i, (sid, title, a, b) in enumerate(SCENES):
        start = 0 if i == 0 else cues[a]["start"] - 0.3
        end = total if i == len(SCENES) - 1 else cues[SCENES[i + 1][2]]["start"] - 0.3
        scenes.append({"id": sid, "title": title, "start": round(start, 2), "dur": round(end - start, 2),
                       "source": SOURCES[sid]})

    cue_html = "\n".join(
        f'        <p id="cue{i+1:02d}" class="clip cue" data-start="{c["start"]}" data-duration="{c["dur"] + CUE_GAP:.2f}" data-track-index="9">{c["text"]}</p>'
        for i, c in enumerate(cues))
    title_html = "\n".join(
        f'      <h2 id="title-{s["id"]}" class="clip title" data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="2">{s["title"]}</h2>'
        for s in scenes)
    src_html = "\n".join(
        f'      <p id="src-{s["id"]}" class="clip source" data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="8">{s["source"]}</p>'
        for s in scenes)

    tpl = (ROOT / "src" / "template.html").read_text(encoding="utf8")
    html = (tpl.replace("{{TOTAL}}", str(total))
               .replace("{{TITLES}}", title_html)
               .replace("{{SOURCES}}", src_html)
               .replace("{{CUES}}", cue_html)
               .replace("{{CUE_JSON}}", json.dumps([c["start"] for c in cues]))
               .replace("{{SCENE_JSON}}", json.dumps({s["id"]: [s["start"], s["dur"]] for s in scenes})))
    for s in scenes:
        html = html.replace("{{%s_START}}" % s["id"], str(s["start"])).replace("{{%s_DUR}}" % s["id"], str(s["dur"]))
    (ROOT / "index.html").write_text(html, encoding="utf8")
    (ROOT / "timing_provisional.json").write_text(json.dumps(
        {"basis": f"estimated from Jun speed {CPS} chars/s (gyosan v5 SRT); not aligned to real audio",
         "total_seconds": total, "scenes": scenes, "cues": cues}, ensure_ascii=False, indent=2), encoding="utf8")
    print("total", total, "s;", len(cues), "cues")
    for s in scenes:
        print(s["id"], s["start"], "+", s["dur"])


if __name__ == "__main__":
    main()
