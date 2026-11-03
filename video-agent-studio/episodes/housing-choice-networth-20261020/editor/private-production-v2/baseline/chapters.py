"""2~10장 장면 정의. 숫자는 research/illustrative_results.json(및 같은 모형 재계산)과 script_v1.md 낭독값.

좌표: 패널 안 요소는 패널 기준, 카드는 프레임 기준(교산 v5 셸).
JS 앵커 T('문구')는 자막 큐 문구 일부다.
"""
from framework import (BUY, JEONSE, JEONSE_INK, WOLSE, HH, arrow, box, card, gridlines, hstack, mark, panel, sub, tx,
                       vbars)

INK = "#173348"
GREY = "#9aa4a8"
GREY_INK = "#5f6d74"
MODEL = "자체 예시 모형(2026.10)"
SRC_BASE = f"{MODEL} · 초기 순자산 2억5천만원 · 월 300만원 · 6억원 집 · 10년 · 집값 연 2% · 투자 연 6% · 금리 연 4%"


def scene(id, title, html, js, src=SRC_BASE, at=None, assets=None):
    return {"id": id, "title": title, "html": html, "js": js, "src": src, "at": at, "assets": assets or []}


def col(id, x, y, w, h, head, color, rows, extra=""):
    r = "".join(f'<div id="{id}-r{i}" class="rowpill">{t}</div>' for i, t in enumerate(rows))
    return (f'<div id="{id}" class="box" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:#fff;'
            f'justify-content:flex-start;padding-top:24px;gap:14px;{extra}">'
            f'<div style="font-size:32px;font-weight:700;color:{color}">{head}</div>{r}</div>')


ROWPILL_CSS = ""  # shell.css 에 .rowpill 정의


# ======================================================================= 2. 기준
def ch2():
    s = []
    cols = "".join(col(f"s2a-c{k}", 40 + k * 340, 36, 310, 300, n, ink, ["같은 집", "월 300만원"]) for k, (n, c, ink) in enumerate(HH))
    tags = "".join(f'<div id="s2a-t{k}" class="pill" style="left:{40 + k * 340}px;top:356px;width:310px;justify-content:center;font-size:21px;color:var(--muted)">{t}</div>'
                   for k, t in enumerate(["보유·유지비 따로", "임차 추가비용 따로", "임차 추가비용 따로"]))
    shared = box("s2a-sh", 40, 430, 1000, 66, "공통 생활비 · 세 가구 동일하게 처리", bg="#dedcd3", size=24)
    s.append(scene("s2a", "같은 출발선", panel("s2a-p", cols + tags + shared) +
                   card("s2a-k1", 240, "같은 조건", "면적·위치·생활 편의", vsize=34) +
                   card("s2a-k2", 420, "주거비·저축 예산", "월 300만원") +
                   card("s2a-k3", 600, "따로 넣는 비용", None, "집주인·임차인 부담이 다른 항목"),
                   """stagger(["#s2a-c0","#s2a-c1","#s2a-c2"], S0("s2a",0.4), 0.2);
tl.set("[id^=s2a-c] .rowpill", {opacity:0}, 0);
enter("#s2a-k1", T("면적과 위치")); stagger(["#s2a-c0-r0","#s2a-c1-r0","#s2a-c2-r0"], T("면적과 위치",0.4), 0.15, fade);
enter("#s2a-k2", T("쓸 수 있는 돈이")); stagger(["#s2a-c0-r1","#s2a-c1-r1","#s2a-c2-r1"], T("쓸 수 있는 돈이",0.3), 0.15, fade);
enter("#s2a-sh", T("전기나 수도"));
enter("#s2a-k3", T("다르게 부담하는")); stagger(["#s2a-t0","#s2a-t1","#s2a-t2"], T("다르게 부담하는",0.5), 0.2);""",
                   src=f"{MODEL} · 같은 집·같은 예산·같은 기간 설정"))

    tiles = [("집값", "연 2%", ""), ("투자계좌", "원화 연 6%", "배당·환율 효과 포함"), ("금리", "연 4% 고정", ""),
             ("월세·보증금", "10년 동안 동일", ""), ("세금·운용비용", "계산 안 함", "")]
    th = "".join(box(f"s2b-t{i}", 40 + i * 336, 100, 312, 210,
                     f'{sub(k, 24, "#4b5d68", 600)}<span style="font-size:{40 if len(v) < 8 else 34}px;color:var(--primary)">{v}</span>{sub(sv, 20) if sv else ""}')
                 for i, (k, v, sv) in enumerate(tiles))
    lab = tx("s2b-l", 0, 40, "돈이 움직이는 구조를 설명하는 가정 · 실제 단지의 지난 10년 성과가 아닙니다", 22, 400, "var(--muted)", w=1740, align="center")
    res = box("s2b-r", 370, 370, 1000, 100, "결과 = 이 조건의 명목 평가 순자산", border=BUY, size=30, color=BUY)
    s.append(scene("s2b", "계산 가정", panel("s2b-p", lab + th + res, wide=True),
                   """fade("#s2b-l", T("화면의 숫자는",0.4));
enter("#s2b-t0", T("집값은 연 2%")); enter("#s2b-t1", T("투자계좌는 배당")); enter("#s2b-t2", T("금리는 연 4%"));
enter("#s2b-t3", T("월세와 보증금도")); enter("#s2b-t4", T("세금과 운용비용")); enter("#s2b-r", T("명목 평가"));""",
                   at="화면의 숫자는"))

    a = box("s2c-a", 40, 40, 480, 150, f'{sub("집값 변화", 22)}집값이 얼마나 올랐는지', size=28)
    b = box("s2c-b", 560, 40, 480, 150, f'{sub("저축", 22)}매달 얼마를 저축했는지', size=28)
    sep = '<div id="s2c-sep" class="pill" style="left:420px;top:212px;width:240px;justify-content:center;color:var(--primary)">따로 계산</div>'
    c = box("s2c-c", 40, 300, 480, 120, "출발 자금이 더 많은 가구", bg="#f3f2ec", size=26, color="var(--muted)")
    d = box("s2c-d", 560, 300, 480, 120, "더 싼 집에 사는 가구", bg="#f3f2ec", size=26, color="var(--muted)")
    m = mark("s2c-m", 40, 450, False, "주거 방식 외의 차이가 결과에 섞임")
    s.append(scene("s2c", "조건을 고정하는 이유", panel("s2c-p", a + b + sep + c + d + m) +
                   card("s2c-k", 240, "비교 원칙", "같은 집 · 같은 예산", vsize=36),
                   """enter("#s2c-a", T("이렇게 조건을 먼저",0.2)); enter("#s2c-b", T("매달 얼마를 저축")); fade("#s2c-sep", T("분리할 수",0.6));
enter("#s2c-c", T("출발 자금이 많은")); enter("#s2c-d", T("더 싼 집에")); enter("#s2c-m", T("다른 조건의 차이가"));
enter("#s2c-k", T("같은 집과 같은"));""", at="이렇게 조건을 먼저", src=f"{MODEL} · 같은 집·같은 예산 비교"))

    rows = ""
    for k, (n, c_, ink) in enumerate(HH):
        y = 50 + k * 70
        rows += tx(f"s2d-n{k}", 60, y + 4, n, 26, 700, ink)
        rows += f'<div id="s2d-b{k}" class="seg" style="left:230px;top:{y}px;width:840px;height:40px;background:{c_};border-radius:6px"></div>'
    rows += '<div id="s2d-mk" class="dash" style="left:1070px;top:30px;width:0;height:230px;border-width:0 0 0 2px;border-radius:0"></div>'
    rows += tx("s2d-ml", 1000, 266, "120개월", 22, 700, "var(--ink)", w=140, align="center")
    chips = "".join(f'<div id="s2d-c{i}" class="pill" style="left:1110px;top:{36 + i * 56}px">{t}</div>' for i, t in enumerate(["집", "금융자산", "보증금", "남은 빚"]))
    wrong = tx("s2d-wl", 60, 330, "종료 시점이 다르면", 24, 700, "var(--muted)")
    wrong += f'<div id="s2d-w0" class="seg" style="left:230px;top:380px;width:840px;height:36px;background:{BUY};opacity:.45;border-radius:6px;color:#fff;font-size:20px">매매 10년</div>'
    wrong += (f'<div id="s2d-w1" class="seg" style="left:230px;top:426px;width:1470px;height:36px;border-radius:6px 0 0 6px;color:#fff;font-size:20px;font-weight:700;justify-content:flex-start;padding-left:24px;'
              f'background:linear-gradient(90deg,{INK} 70%,rgba(23,51,72,0.15))">투자 20년 →</div>')
    wrong += mark("s2d-m", 1110, 380, False, "결과의 의미가 달라짐")
    s.append(scene("s2d", "같은 종료 시점", panel("s2d-p", rows + chips + wrong, wide=True),
                   """[0,1,2].forEach(k=>{ fade("#s2d-n"+k, T("비교 기간도")); growX("#s2d-b"+k, T("비교 기간도",0.2+k*0.2), 1.4); });
fade("#s2d-mk, #s2d-ml", T("비교 기간도",1.6));
fade("#s2d-wl", T("매매는 10년")); growX("#s2d-w0", T("매매는 10년",0.2), 1.0); growX("#s2d-w1", T("투자는 20년"), 1.6);
enter("#s2d-m", T("결과의 의미가"));
dim("#s2d-wl, #s2d-w0, #s2d-w1, #s2d-m", T("120개월이 지난"), 0.25);
stagger(["#s2d-c0","#s2d-c1","#s2d-c2","#s2d-c3"], T("120개월이 지난",1.0), 0.45);""",
                   at="비교 기간도", src=f"{MODEL} · 세 가구 모두 120개월 시점 비교"))
    return s


# ======================================================================= 3. 출발 자금
def bar_label(id, x, y, text):
    return tx(id, x, y, text, 26, 700, "var(--ink)")


def ch3():
    s = []
    h = bar_label("s3a-l1", 40, 34, "자기자금 2억5천만원")
    h += hstack("s3a-h1", 40, 80, 1000, 64, 2.5, [(2.4, BUY, "집에 넣는 돈 2억4천만원", "#fff"), (0.06, "#8fb2ec", "", ""), (0.04, INK, "", "")])
    h += tx("s3a-sm", 540, 156, "거래비용 600만원 · 투자계좌 400만원 →", 22, 600, "var(--muted)", w=500, align="right")
    h += bar_label("s3a-l2", 40, 236, "집값 6억원")
    h += hstack("s3a-h2", 40, 282, 1000, 64, 6, [(2.4, BUY, "자기자금 2억4천만원", "#fff"), (3.6, GREY, "대출 3억6천만원", INK)])
    h += box("s3a-eq", 40, 400, 1000, 100, "집 6억원 + 투자 400만원 − 대출 3억6천만원 = 2억4천400만원", size=27)
    s.append(scene("s3a", "매매 · 출발 자금", panel("s3a-p", h) +
                   card("s3a-k1", 240, "집값", "6억원") + card("s3a-k2", 420, "대출", "3억6천만원", color=GREY_INK) +
                   card("s3a-k3", 600, "거래 직후 순자산", "2억4천400만원"),
                   """const a0=T("자기자금 2억4천만원");
fade("#s3a-l1, #s3a-h1-t", a0); growX("#s3a-h1-s0", a0+0.3, 1.2); enter("#s3a-k1", a0+0.4);
fade("#s3a-l2, #s3a-h2-t", a0+1.6); growX("#s3a-h2-s0", a0+1.8, 0.9); growX("#s3a-h2-s1", a0+2.6, 1.0); enter("#s3a-k2", a0+2.6);
growX("#s3a-h1-s1", T("거래를 시작하는",0.3), 0.5); growX("#s3a-h1-s2", T("투자계좌에 남는 돈은",0.3), 0.5); fade("#s3a-sm", T("투자계좌에 남는 돈은",0.6));
enter("#s3a-eq", T("대출 3억6천만원을 빼야")); enter("#s3a-k3", T("거래비용을 낸 직후"));""",
                   src=f"{MODEL} · 거래 시작 비용 600만원은 설명용 가정"))

    h = bar_label("s3b-l1", 40, 34, "보증금 4억원")
    h += hstack("s3b-h1", 40, 80, 1000, 64, 4, [(2, JEONSE, "자기자금 2억원", INK), (2, GREY, "전세대출 2억원", INK)])
    h += (f'<div id="s3b-as" class="box" style="left:40px;top:200px;width:490px;height:250px;background:#fff;justify-content:flex-start;padding-top:22px;gap:12px">'
          f'<div style="font-size:26px;font-weight:700;color:var(--muted)">자산</div>'
          f'<div id="s3b-a1" class="rowpill wide">보증금 4억원 · 돌려받을 자산</div><div id="s3b-a2" class="rowpill wide">투자계좌 4,900만원</div></div>')
    h += (f'<div id="s3b-db" class="box" style="left:550px;top:200px;width:490px;height:250px;background:#fff;justify-content:flex-start;padding-top:22px;gap:12px">'
          f'<div style="font-size:26px;font-weight:700;color:var(--muted)">부채</div>'
          f'<div id="s3b-d1" class="rowpill wide">전세대출 2억원 · 별도의 빚</div></div>')
    h += tx("s3b-fee", 40, 470, "초기 계약비용 100만원", 22, 600, "var(--muted)")
    s.append(scene("s3b", "전세 · 출발 자금", panel("s3b-p", h) +
                   card("s3b-k1", 240, "보증금", "4억원", "돌려받을 자산", color=JEONSE_INK) +
                   card("s3b-k2", 420, "전세대출", "2억원", "별도의 빚", color=GREY_INK) +
                   card("s3b-k3", 600, "투자계좌 출발", "4,900만원", color=JEONSE_INK),
                   """const b0=T("자기자금 2억원과");
fade("#s3b-l1, #s3b-h1-t", S0("s3b",0.3)); growX("#s3b-h1-s0", b0, 1.0); growX("#s3b-h1-s1", b0+1.2, 1.0); enter("#s3b-k1", b0+0.6);
tl.set("#s3b-a1, #s3b-a2, #s3b-d1", {opacity:0}, 0);
fade("#s3b-as, #s3b-db", T("계약비용을 100만원",0)); fade("#s3b-fee", T("계약비용을 100만원",0.3));
fade("#s3b-a2", T("투자계좌에는 4천900만원")); enter("#s3b-k3", T("투자계좌에는 4천900만원"));
fade("#s3b-a1", T("보증금 4억원은 돌려받을")); fade("#s3b-d1", T("대출 2억원은 별도의")); enter("#s3b-k2", T("대출 2억원은 별도의"));""",
                   at="전세 가구는 보증금", src=f"{MODEL} · 초기 계약비용 100만원은 설명용 가정"))

    h = bar_label("s3c-l1", 40, 34, "보증금 1억원")
    h += hstack("s3c-h1", 40, 80, 1000, 64, 1, [(0.8, WOLSE, "자기자금 8천만원", "#fff"), (0.2, GREY, "대출 2천만원", INK)])
    h += tx("s3c-l2", 40, 200, "투자계좌 출발 금액", 26, 700, "var(--ink)")
    items = [("매매", 0.04, BUY, BUY, "400만원"), ("전세", 0.49, JEONSE, JEONSE_INK, "4,900만원"), ("월세", 1.69, WOLSE, WOLSE, "1억6,900만원")]
    h += vbars("s3c-v", 260, 480, items, 136, barw=120, gap=140)
    s.append(scene("s3c", "월세 · 출발 자금", panel("s3c-p", h) +
                   card("s3c-k1", 240, "월세 조건", "보증금 1억원 · 월 100만원", vsize=32, color=WOLSE) +
                   card("s3c-k2", 420, "투자계좌 출발", "1억6,900만원", color=WOLSE) +
                   card("s3c-k3", 600, "차이의 이유", None, "보증금에 묶인 자기자금이 적음", color=WOLSE),
                   """enter("#s3c-k1", S0("s3c",0.5)); fade("#s3c-l1, #s3c-h1-t", S0("s3c",0.5));
growX("#s3c-h1-s0", T("보증금에는 자기자금"), 1.0); growX("#s3c-h1-s1", T("보증금에는 자기자금",1.2), 0.6);
const c0=T("투자계좌의 출발 금액은");
fade("#s3c-l2", c0); [0,1,2].forEach(i=>{ grow("#s3c-v-b"+i, c0+0.2+i*0.5, 1.2); fade("#s3c-v-v"+i+", #s3c-v-x"+i, c0+1.2+i*0.5); });
enter("#s3c-k2", c0+1.8);
dim("#s3c-v-b0, #s3c-v-b1, #s3c-v-v0, #s3c-v-v1", T("처음부터 돈이"), 0.35); enter("#s3c-k3", T("처음부터 돈이"));""",
                   at="월세 가구는 보증금 1억원", src=f"{MODEL} · 초기 계약비용 100만원은 설명용 가정"))

    bx = [("s3d-b0", "매달 이자만 납부", "원금은 그대로"), ("s3d-b1", "만기 · 보증금 반환", "전액 정상 반환 가정"), ("s3d-b2", "대출 원금 상환", "돌려받은 보증금으로")]
    h = "".join(box(id, 60 + i * 580, 60, 420, 140, f"{t}{sub(sv, 22)}", size=30) for i, (id, t, sv) in enumerate(bx))
    h += arrow("s3d-a0", 490, 130, 140) + arrow("s3d-a1", 1070, 130, 140)
    h += box("s3d-b3", 60, 300, 420, 140, f"초기 금융자산{sub('즉시 투자', 22)}", size=30)
    h += box("s3d-b4", 640, 300, 420, 140, f"매달 남는 예산{sub('같은 방식으로 투자', 22)}", size=30)
    h += arrow("s3d-a2", 490, 370, 140)
    h += tx("s3d-l", 60, 250, "전세·월세 대출", 22, 700, "var(--muted)") + tx("s3d-l2", 60, 470, "세 가구 공통", 22, 700, "var(--muted)")
    s.append(scene("s3d", "대출과 보증금 반환", panel("s3d-p", h, wide=True),
                   """fade("#s3d-l", S0("s3d",0.4)); enter("#s3d-b0", T("매달 이자만"));
enter("#s3d-b1", T("만기에 보증금을")); growX("#s3d-a0", T("만기에 보증금을"), 0.5);
growX("#s3d-a1", T("만기에 보증금을",1.4), 0.5); enter("#s3d-b2", T("만기에 보증금을",1.6));
tl.fromTo("#s3d-b1", {borderColor:"rgba(0,0,0,0)"}, {borderColor:"#286cda", duration:0.4}, T("정상적으로 돌려받는"));
fade("#s3d-l2", T("초기 금융자산은")); enter("#s3d-b3", T("초기 금융자산은"));
growX("#s3d-a2", T("남는 예산을 같은"), 0.5); enter("#s3d-b4", T("남는 예산을 같은",0.3));""",
                   at="전세와 월세의 대출은", src=f"{MODEL} · 임차 대출은 이자만 납부·만기 상환 · 보증금 정상 반환 가정"))
    s[3]["html"] = s[3]["html"].replace('id="s3d-b1" class="box" style="', 'id="s3d-b1" class="box" style="border:3px solid rgba(0,0,0,0);')
    return s


# ======================================================================= 4. 매달 나가는 돈
def ch4():
    s = []
    h = tx("s4a-l", 120, 40, "월 예산 300만원", 28, 700)
    h += hstack("s4a-h", 120, 96, 1500, 84, 300, [(171.87, BUY, "원리금 약 172만원", "#fff"), (30, "#8fb2ec", "보유비 30만원", INK), (98.13, INK, "투자 약 98만원", "#fff")], label_size=24)
    w1 = 1500 * 201.87 / 300
    h += f'<div id="s4a-br" class="dash" style="left:120px;top:196px;width:{w1:.0f}px;height:16px;border-width:0 2px 2px 2px;border-style:solid;border-color:#8a979d;border-radius:0"></div>'
    h += tx("s4a-bl", 120, 222, "주거 관련 현금지출 약 202만원", 24, 700, "var(--ink)", w=w1, align="center")
    h += tx("s4a-n", 120, 290, "대출 3억6천만원 · 30년 원리금균등 상환 · 연 4%", 22, 400, "var(--muted)")
    h += mark("s4a-m", 120, 380, True, "집을 산 가구도 남는 돈을 투자")
    h += '<div id="s4a-pl" class="pill" style="left:620px;top:380px;color:var(--primary)">세 가구 모두 같은 투자수익률</div>'
    s.append(scene("s4a", "매매 · 월 300만원", panel("s4a-p", h, wide=True),
                   """fade("#s4a-l, #s4a-h-t", S0("s4a",0.4)); fade("#s4a-n", T("30년 동안"));
growX("#s4a-h-s0", T("월 상환액은 약 172만원"), 1.2); growX("#s4a-h-s1", T("유지·보유 비용을"), 0.6);
fade("#s4a-br, #s4a-bl", T("현금지출은 약 202만원")); growX("#s4a-h-s2", T("투자계좌에는 매달"), 1.0);
enter("#s4a-m", T("집을 산 가구도")); enter("#s4a-pl", T("같은 투자수익률을"));""",
                   src=f"{MODEL} · 보유·유지비 월 30만원은 설명용 가정"))

    rows = [("매매", BUY, BUY, [(171.87, BUY, "원리금 172만", "#fff"), (30, "#8fb2ec", "", ""), (98.13, INK, "투자 98만", "#fff")], "주거 지출 약 202만원"),
            ("전세", JEONSE, JEONSE_INK, [(66.67, JEONSE, "이자 67만", INK), (5, "#e3cf9f", "", ""), (228.33, INK, "투자 228만", "#fff")], "주거 지출 약 72만원"),
            ("월세", WOLSE, WOLSE, [(100, WOLSE, "월세 100만", "#fff"), (6.67, "#8cc0b4", "", ""), (5, "#bcdcd4", "", ""), (188.33, INK, "투자 188만", "#fff")], "주거 지출 약 112만원")]
    h = ""
    for k, (n, c_, ink, segs, note) in enumerate(rows):
        y = 60 + k * 150
        h += tx(f"s4b-n{k}", 40, y + 18, n, 30, 700, ink)
        h += hstack(f"s4b-h{k}", 170, y, 1200, 76, 300, segs, label_size=23)
        h += tx(f"s4b-t{k}", 1400, y + 22, note, 23, 600, "var(--ink)")
    h += tx("s4b-lg", 170, 480, "막대 전체 = 월 300만원 · 진한 남색 = 투자금", 21, 400, "var(--muted)")
    s.append(scene("s4b", "세 가구 · 월 300만원", panel("s4b-p", h, wide=True),
                   """tl.set("#s4b-h1-t, #s4b-h2-t, #s4b-n1, #s4b-n2, #s4b-t1, #s4b-t2", {opacity:0}, 0);
fade("#s4b-n1, #s4b-h1-t", T("이자로 월 약 67만원")); growX("#s4b-h1-s0", T("이자로 월 약 67만원",0.3), 0.8);
growX("#s4b-h1-s1", T("임차인 추가비용을"), 0.4); fade("#s4b-t1", T("임차인 추가비용을",1.8)); growX("#s4b-h1-s2", T("투자금은 약 228만원"), 1.0);
fade("#s4b-n2, #s4b-h2-t", T("월세 100만원에")); growX("#s4b-h2-s0", T("월세 100만원에",0.3), 0.9); growX("#s4b-h2-s1", T("월세 100만원에",1.8), 0.4);
growX("#s4b-h2-s2", T("추가비용 5만원을"), 0.4); fade("#s4b-t2", T("총지출은")); growX("#s4b-h2-s3", T("투자금은 약 188만원"), 1.0);""",
                   at="전세 가구는 대출 2억원의", src=f"{MODEL} · 임차인 추가비용 월 5만원은 설명용 가정 · 금액은 첫 달 기준"))

    h = tx("s4c-lt", 140, 30, "처음 투자하는 돈", 26, 700) + tx("s4c-rt", 1000, 30, "매달 투자하는 돈", 26, 700)
    h += vbars("s4c-l", 160, 400, [("매매", 0.04, BUY, BUY, "400만원"), ("전세", 0.49, JEONSE, JEONSE_INK, "4,900만원"), ("월세", 1.69, WOLSE, WOLSE, "1억6,900만원")], 165, barw=110, gap=90)
    h += vbars("s4c-r", 1020, 400, [("매매", 98.13, BUY, BUY, "약 98만원"), ("전세", 228.33, JEONSE, JEONSE_INK, "약 228만원"), ("월세", 188.33, WOLSE, WOLSE, "약 188만원")], 1.2, barw=110, gap=90)
    h += box("s4c-f", 300, 470, 760, 54, "결과 = 초기 투자금 + 월 적립금 + 투자수익", border=BUY, size=24, color=BUY)
    h += mark("s4c-m", 1100, 475, False, "한 가지 흐름만 보면 놓침")
    s.append(scene("s4c", "처음 투자금과 매달 투자금", panel("s4c-p", h, wide=True),
                   """const r0=T("매달 투자할 돈이 가장"), l0=T("처음 투자할 돈이 가장");
fade("#s4c-rt", r0); [0,1,2].forEach(i=>{ grow("#s4c-r-b"+i, r0+0.2+i*0.3, 1.2); fade("#s4c-r-v"+i+", #s4c-r-x"+i, r0+1.1+i*0.3); });
dim("#s4c-r-b0, #s4c-r-b2, #s4c-r-v0, #s4c-r-v2", r0+2.2, 0.35);
fade("#s4c-lt", l0); [0,1,2].forEach(i=>{ grow("#s4c-l-b"+i, l0+0.2+i*0.3, 1.2); fade("#s4c-l-v"+i+", #s4c-l-x"+i, l0+1.1+i*0.3); });
dim("#s4c-l-b0, #s4c-l-b1, #s4c-l-v0, #s4c-l-v1", l0+2.2, 0.35);
enter("#s4c-f", T("어느 쪽이 더 크게")); lit("#s4c-r-b0, #s4c-r-b2, #s4c-r-v0, #s4c-r-v2, #s4c-l-b0, #s4c-l-b1, #s4c-l-v0, #s4c-l-v1", T("그리고 투자수익이"));
enter("#s4c-m", T("월세가 나간다는"));""",
                   at="전세는 이 설정에서"))

    h = box("s4d-a", 80, 70, 400, 200, f'{sub("매매 · 보유·유지비", 23, "#4b5d68", 600)}<span style="font-size:46px;color:var(--buy)">월 30만원</span>', size=30)
    h += box("s4d-b", 600, 70, 400, 200, f'{sub("임차 · 추가비용", 23, "#4b5d68", 600)}<span style="font-size:46px;color:var(--jeonse-ink)">월 5만원</span>', size=30)
    h += '<div id="s4d-d" class="pill" style="left:420px;top:300px;width:240px;justify-content:center;color:var(--primary)">차이 25만원</div>'
    for i, (t, x) in enumerate([("보유세", 80), ("수선", 240), ("보증료", 370), ("계약 갱신비용", 530)]):
        h += f'<div id="s4d-i{i}" class="pill" style="left:{x}px;top:420px;background:#f3f2ec">{t}</div>'
    h += tx("s4d-il", 80, 380, "현실에서 각각 확인할 항목", 21, 600, "var(--muted)")
    s.append(scene("s4d", "비용 묶음", panel("s4d-p", h) +
                   card("s4d-k1", 240, "설명용 비용 묶음", "차이 25만원") +
                   card("s4d-k2", 420, "공통 관리비", None, "양쪽에 같게 둠") +
                   card("s4d-k3", 600, "따로 구분할 것", None, "실제 부담이 다른 항목"),
                   """enter("#s4d-a", S0("s4d",0.4)); enter("#s4d-b", S0("s4d",0.8));
enter("#s4d-d", T("두 가구의 차이는")); enter("#s4d-k1", T("두 가구의 차이는",0.3));
fade("#s4d-il", T("보유세와 수선")); stagger(["#s4d-i0","#s4d-i1","#s4d-i2"], T("보유세와 수선",0.2), 0.5); enter("#s4d-i3", T("계약 갱신비용"));
enter("#s4d-k2", T("같은 관리비를")); enter("#s4d-k3", T("실제 부담이 다른"));""",
                   at="월 30만원과 5만원은", src=f"{MODEL} · 월 30만원·5만원은 설명용 비용 묶음"))
    return s


# ======================================================================= 5. 원금과 보증금
def ch5(ledger_debt):
    s = []
    w_int = 1000 * 120 / 171.87
    h = tx("s5a-l", 40, 34, "첫 달 상환액 약 172만원", 26, 700)
    h += hstack("s5a-h", 40, 84, 1000, 80, 171.87, [(120, GREY, "이자 120만원", INK), (51.87, BUY, "원금 약 52만원", "#fff")], label_size=24)
    ci, cp = 40 + w_int / 2, 40 + w_int + (1000 - w_int) / 2
    h += arrow("s5a-a0", ci, 180, 80, "d", GREY) + box("s5a-c", ci - 170, 276, 340, 90, f"그달의 비용{sub('이자는 사라짐', 21)}", bg="#e4e2d9", size=26)
    h += arrow("s5a-a1", cp, 180, 80, "d") + box("s5a-p1", cp - 150, 276, 300, 90, f"현금 −52만원{sub('통장에서 나감', 21)}", size=26)
    h += box("s5a-p2", cp - 150, 390, 300, 90, f"대출잔액 −52만원{sub('빚이 줄어듦', 21)}", border=BUY, size=26, color=BUY)
    s.append(scene("s5a", "원리금 나누기", panel("s5a-p", h) +
                   card("s5a-k1", 240, "첫 달 이자", "120만원", "그달의 비용", color=GREY_INK) +
                   card("s5a-k2", 420, "첫 달 원금", "약 52만원", "현금 감소 = 빚 감소") +
                   card("s5a-k3", 600, "순자산에 남는 결과", None, "통장에서 나간 돈은 같아도 결과가 다름"),
                   """fade("#s5a-l, #s5a-h-t", S0("s5a",0.4)); const f0=T("첫 달 이자는");
growX("#s5a-h-s0", f0+0.2, 1.0); growX("#s5a-h-s1", f0+1.4, 0.6); enter("#s5a-k1", f0+0.6); enter("#s5a-k2", f0+1.8);
grow("#s5a-a0", T("그달의 비용으로"), 0.5); enter("#s5a-c", T("그달의 비용으로",0.4));
grow("#s5a-a1", T("원금 52만원은"), 0.5); enter("#s5a-p1", T("원금 52만원은",0.6)); enter("#s5a-p2", T("원금 52만원은",2.2));
enter("#s5a-k3", T("순자산에 남기는"));""",
                   src=f"{MODEL} · 대출 3억6천만원 · 30년 원리금균등 · 연 4%"))

    x0, x1, base, sc = 140, 1150, 470, 100
    pts = [(x0 + m * (x1 - x0) / 120, base - d / 1e8 * sc) for m, d in enumerate([360_000_000] + ledger_debt)]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    h = gridlines(x0, x1 - x0 + 20, base, sc, [1, 2, 3, 4])
    h += (f'<svg class="abs" style="left:0;top:0" width="1740" height="540"><path id="s5b-line" d="{path}" pathLength="1" fill="none" stroke="{BUY}" stroke-width="5" '
          f'stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="1"/></svg>')
    h += f'<div id="s5b-d0" class="dot" style="left:{x0 - 9}px;top:{pts[0][1] - 9:.0f}px"></div>'
    h += tx("s5b-t0", x0 + 10, pts[0][1] - 52, "3억6천만원", 23, 700, BUY)
    h += tx("s5b-t1", x0 + 60, pts[0][1] + 16, "1개월 후 약 3억5,950만원", 21, 600, "var(--ink)")
    ex, ey = pts[-1]
    h += f'<div id="s5b-d1" class="dot" style="left:{ex - 9:.0f}px;top:{ey - 9:.0f}px"></div>'
    h += tx("s5b-t2", ex - 300, ey + 18, "10년 후 약 2억8,400만원", 23, 700, BUY, w=300, align="right")
    h += f'<div id="s5b-br" class="dash" style="left:{ex + 18:.0f}px;top:{pts[0][1]:.0f}px;width:14px;height:{ey - pts[0][1]:.0f}px;border-width:2px 2px 2px 0;border-style:solid;border-radius:0"></div>'
    h += tx("s5b-bt", ex + 40, (pts[0][1] + ey) / 2 - 30, "갚은 원금<br>약 7,600만원", 22, 700, "var(--ink)")
    h += tx("s5b-xa", x0 - 20, base + 10, "0개월", 19, 400, "var(--muted)") + tx("s5b-xb", x1 - 40, base + 10, "120개월", 19, 400, "var(--muted)")
    # 원리금 구성 비교(1개월·120개월)
    mb, ms = 470, 1.6
    for j, (lab, ii, pp) in enumerate([("1개월", 120, 51.87), ("120개월", 94.80, 77.07)]):
        bx = 1520 + j * 110
        h += f'<div id="s5b-m{j}i" class="bar" style="left:{bx}px;top:{mb - ii * ms:.0f}px;width:72px;height:{ii * ms:.0f}px;background:{GREY};border-radius:0"></div>'
        h += f'<div id="s5b-m{j}p" class="bar" style="left:{bx}px;top:{mb - (ii + pp) * ms:.0f}px;width:72px;height:{pp * ms:.0f}px;background:{BUY}"></div>'
        h += tx(f"s5b-m{j}l", bx - 24, mb + 10, lab, 19, 600, "var(--ink)", w=120, align="center")
    h += tx("s5b-lg", 1500, 140, '<span style="color:#286cda">■</span> 원금 <span style="color:#7f8a8f">■</span> 이자', 20, 600, "var(--ink)")
    h += tx("s5b-mt", 1500, 104, "매달 172만원의 구성", 21, 700, "var(--ink)")
    s.append(scene("s5b", "대출 잔액", panel("s5b-p", h, wide=True),
                   """enter("#s5b-d0, #s5b-t0", S0("s5b",0.4)); fade("#s5b-t1", T("3억5천950만원",1.6));
tl.fromTo("#s5b-line", {strokeDashoffset:1}, {strokeDashoffset:0, duration:7, ease:"none"}, T("다음 달 이자는"));
fade("#s5b-mt, #s5b-lg", T("이자의 비중은")); grow("#s5b-m0i, #s5b-m0p", T("이자의 비중은",0.2), 0.8); grow("#s5b-m1i, #s5b-m1p", T("원금의 비중은"), 0.8); fade("#s5b-m0l", T("이자의 비중은",0.6)); fade("#s5b-m1l", T("원금의 비중은",0.6));
fade("#s5b-br, #s5b-bt", T("10년 동안 갚은 원금")); enter("#s5b-d1, #s5b-t2", T("남은 대출은"));""",
                   at="첫 달이 지나면", src=f"{MODEL} · 매월 대출잔액(120개월) · 세로축 0부터"))
    s[-1]["html"] = s[-1]["html"].replace("<br>", " ")  # 줄바꿈 대신 폭으로 감싼다
    s[-1]["html"] = s[-1]["html"].replace('id="s5b-bt" class="tx" style="', 'id="s5b-bt" class="tx" style="width:150px;white-space:normal;')

    rows = [("원금을 지출로 빼고 + 처음 대출 3억6천만원 차감", False, "갚은 빚 미반영"),
            ("원금 상환을 수익으로 더하고 + 줄어든 대출 적용", False, "두 번 반영"),
            ("매달 대출잔액 계산 → 마지막 잔액만 차감", True, "한 번 반영")]
    h = ""
    for i, (t, ok, m) in enumerate(rows):
        y = 40 + i * 150
        h += box(f"s5c-r{i}", 40, y, 1000, 120, t, size=25, extra="align-items:flex-start;padding:0 30px;" + ("border:3px solid #2f7d5b;" if ok else ""))
        h += mark(f"s5c-m{i}", 760, y + 38, ok, m)
    s.append(scene("s5c", "남은 빚은 한 번만", panel("s5c-p", h) +
                   card("s5c-k1", 240, "10년 후 남은 대출", "약 2억8,400만원") +
                   card("s5c-k2", 420, "빼는 시점", None, "마지막에 남은 잔액을 한 번"),
                   """enter("#s5c-r0", T("월 지출에서 원금을")); enter("#s5c-m0", T("갚아서 줄어든 빚을"));
enter("#s5c-r1", T("반대로 원금 상환을")); enter("#s5c-m1", T("같은 효과를 두 번"));
dim("#s5c-r0, #s5c-m0, #s5c-r1, #s5c-m1", T("매달 대출잔액을"), 0.45);
enter("#s5c-r2", T("매달 대출잔액을")); enter("#s5c-m2", T("매달 대출잔액을",1.4)); enter("#s5c-k1", T("매달 대출잔액을",1.0)); enter("#s5c-k2", T("매달 대출잔액을",1.8));""",
                   at="월 지출에서 원금을"))
    s[-1]["html"] = s[-1]["html"].replace('id="s5c-r0" class="box" style="', 'id="s5c-r0" class="box" style="padding-right:300px;').replace(
        'id="s5c-r1" class="box" style="', 'id="s5c-r1" class="box" style="padding-right:300px;')

    chain = [("s5d-b0", "현금", "보증금 4억원 지급"), ("s5d-b1", "보증금 채권 4억원", "돌려받을 권리"),
             ("s5d-b2", "반환된 현금 4억원", "계약 종료 · 정상 반환"), ("s5d-b3", "전세대출 2억원 상환", "순자산에서 빚을 함께 뺌")]
    h = "".join(box(id, 40 + i * 430, 110, 340, 160, f"{t}{sub(sv, 21)}", size=27, border=(JEONSE if i == 1 else None)) for i, (id, t, sv) in enumerate(chain))
    h += "".join(arrow(f"s5d-a{i}", 390 + i * 430, 190, 70, "r", JEONSE) for i in range(3))
    h += mark("s5d-m", 470, 340, False, "돌려받은 원금 = 새 수익 아님")
    s.append(scene("s5d", "보증금의 흐름", panel("s5d-p", h, wide=True),
                   """const d0=T("맡기는 순간");
enter("#s5d-b0", d0); growX("#s5d-a0", d0+1.2, 0.5); enter("#s5d-b1", d0+1.6);
growX("#s5d-a1", T("정상 반환되면"), 0.5); enter("#s5d-b2", T("정상 반환되면",0.4));
enter("#s5d-m", T("새 수익으로 더하지"));
growX("#s5d-a2", T("대출로 마련한 부분은"), 0.5); enter("#s5d-b3", T("대출로 마련한 부분은",0.4));""",
                   at="보증금도 같은 원리로", src=f"{MODEL} · 전세보증금 4억원 · 전세대출 2억원 · 정상 반환 가정"))

    h = tx("s5e-l", 60, 40, "투자계좌 출발 금액", 26, 700)
    h += vbars("s5e-v", 120, 430, [("매매", 0.04, BUY, BUY, "400만원"), ("전세", 0.49, JEONSE, JEONSE_INK, "4,900만원"), ("월세", 1.69, WOLSE, WOLSE, "1억6,900만원")], 136, barw=100, gap=70)
    h += box("s5e-x", 640, 110, 400, 150, f"포기한 투자수익을{sub('다시 비용으로 빼기', 24, 'var(--muted)', 700)}", bg="#f3f2ec", size=26, color="var(--muted)")
    h += mark("s5e-m", 660, 290, False, "같은 차이가 두 번")
    s.append(scene("s5e", "기회비용은 한 번", panel("s5e-p", h) +
                   card("s5e-k1", 240, "기회비용", None, "작아진 출발 계좌에 이미 반영") +
                   card("s5e-k2", 420, "모형이 계산하는 것", None, "작은 계좌에서 실제로 쌓이는 수익") +
                   card("s5e-k3", 600, "집에 들어간 자기자금", None, "같은 방식으로 처리"),
                   """fade("#s5e-l", S0("s5e",0.4)); [0,1,2].forEach(i=>{ grow("#s5e-v-b"+i, S0("s5e",0.5+i*0.3), 1.0); fade("#s5e-v-v"+i+", #s5e-v-x"+i, S0("s5e",1.3+i*0.3)); });
enter("#s5e-k1", T("처음 투자계좌가")); enter("#s5e-k2", T("이번 모형은"));
enter("#s5e-x", T("포기한 투자수익을")); enter("#s5e-m", T("같은 차이가 두 번")); enter("#s5e-k3", T("집에 들어간 자기자금도"));""",
                   at="보증금에 묶인 돈의"))
    return s


# ======================================================================= 6. 투자수익
SP_SRC = "S&P Dow Jones Indices, Index Mathematics Methodology(Derived Indices) · S&P500 Total Return FAQ · 2026.10.20 확인"


def ch6():
    s = []
    h = '<div id="s6a-pl" class="pill" style="left:140px;top:24px;color:var(--primary)">S&amp;P500을 따라가는 ETF</div>'
    tiers = [("s6a-t0", "지수의 총수익", "가격 상승 + 배당"), ("s6a-t1", "실제 ETF의 수익", "상품 단위"), ("s6a-t2", "원화로 받는 수익", "한국 가구 기준")]
    h += "".join(box(id, 140 + i * 500, 90, 460, 120, f"{t}{sub(sv, 21)}", size=28) for i, (id, t, sv) in enumerate(tiers))
    h += tx("s6a-fl", 140, 250, "총수익지수", 22, 700, "var(--muted)")
    f = [("s6a-f0", "가격 변동"), ("s6a-f1", "배당 재투자"), ("s6a-f2", "S&amp;P 총수익지수")]
    for i, (id, t) in enumerate(f):
        h += box(id, 140 + i * 500, 290, 400, 100, t, size=28, border=(BUY if i == 2 else None), color=(BUY if i == 2 else "var(--ink)"))
    h += tx("s6a-o0", 560, 312, "+", 48, 700, "var(--muted)") + tx("s6a-o1", 1058, 312, "=", 48, 700, "var(--muted)")
    h += mark("s6a-m", 140, 440, False, "배당이 들어 있는 수익률에 배당을 다시 더하면 실제보다 높아짐")
    s.append(scene("s6a", "총수익과 배당", panel("s6a-p", h, wide=True),
                   """fade("#s6a-pl", S0("s6a",0.4)); const a=T("가격 상승과 배당을");
enter("#s6a-t0", a); enter("#s6a-t1", a+2.4); enter("#s6a-t2", T("원화로 손에 쥐는"));
const f=T("총수익지수는 배당"); fade("#s6a-fl", f); enter("#s6a-f0", f+0.2); fade("#s6a-o0", f+0.8); enter("#s6a-f1", f+1.0); fade("#s6a-o1", f+1.8); enter("#s6a-f2", f+2.0);
enter("#s6a-m", T("배당을 다시 더하면"));""", src=SP_SRC))

    def fx(id, x, k, v, sv, border=None):
        return box(id, x, 110, 340, 170, f'{sub(k, 23, "#4b5d68", 600)}<span style="font-size:52px;color:var(--primary)">{v}</span>{sub(sv, 21)}', border=border, size=28)
    h = fx("s6b-b0", 80, "달러 자산", "×1.1", "+10%") + tx("s6b-o0", 452, 160, "×", 52, 700, "var(--muted)")
    h += fx("s6b-b1", 520, "원·달러 환율", "×1.1", "+10%") + tx("s6b-o1", 892, 160, "=", 52, 700, "var(--muted)")
    h += fx("s6b-b2", 960, "원화 자산", "×1.21", "", border=BUY)
    h += arrow("s6b-a", 1320, 195, 80) + box("s6b-r", 1420, 140, 280, 110, f'{sub("원화 수익률", 22)}<span style="font-size:44px;color:var(--primary)">21%</span>', size=28)
    h += mark("s6b-m", 80, 380, False, "원화 ETF 수익률에 환율 상승을 한 번 더 붙이면 중복")
    s.append(scene("s6b", "환율", panel("s6b-p", h, wide=True),
                   """const a=T("달러 자산이 10%"); enter("#s6b-b0", a); fade("#s6b-o0", a+1.6); enter("#s6b-b1", a+1.8);
fade("#s6b-o1", T("1.21배가 됩니다")); enter("#s6b-b2", T("1.21배가 됩니다",0.6));
growX("#s6b-a", T("원화 수익률은"), 0.4); enter("#s6b-r", T("원화 수익률은",0.4)); enter("#s6b-m", T("한 번 더 붙이면"));""",
                   at="환율도 같은 방식", src="달러 +10% × 환율 +10% 계산 예시 · FRED DEXKOUS(원/달러) 계열 정의 참고"))

    h = box("s6c-t", 290, 70, 500, 200, f'{sub("투자계좌 가정", 24, "#4b5d68", 600)}<span style="font-size:64px;color:var(--primary)">원화 연 6%</span>', size=30)
    for i, (t, x) in enumerate([("예측 아님", 90), ("지난 10년 실제 성과 아님", 270), ("배당·환율 추가 적용 안 함", 630)]):
        h += f'<div id="s6c-g{i}" class="pill" style="left:{x}px;top:330px;background:#fff">{t}</div>'
    s.append(scene("s6c", "원화 연 6% 가정", panel("s6c-p", h) +
                   card("s6c-k1", 240, "실제 상품 계산 시", None, "배당 세금 · 매도 시 과세") +
                   card("s6c-k2", 420, "함께 확인", None, "환전비용 · 운용보수 포함 여부"),
                   """enter("#s6c-t", S0("s6c",0.5));
enter("#s6c-g0", T("앞으로의 수익 예측이나")); enter("#s6c-g1", T("앞으로의 수익 예측이나",1.8)); enter("#s6c-g2", T("배당이나 환율을 추가"));
enter("#s6c-k1", T("실제 상품으로 계산할 때는")); enter("#s6c-k2", T("실제 상품으로 계산할 때는",2.4));""",
                   at="이번 계산은 이 복잡한", src=f"{MODEL} · 투자수익은 원화 기준 단일 가정"))

    h = '<div class="gl" style="left:100px;top:210px;width:1000px;height:3px;background:#9aa4a8"></div>'
    h += tx("s6d-x0", 60, 222, "월초", 21, 600, "var(--muted)") + tx("s6d-x1", 1080, 222, "월말", 21, 600, "var(--muted)")
    h += box("s6d-b0", 40, 60, 260, 110, f"월초 잔액{sub('그달 수익의 기준', 20)}", size=27)
    h += arrow("s6d-a0", 310, 115, 150) + box("s6d-b1", 470, 60, 260, 110, f"그달 수익 적용", size=27)
    h += arrow("s6d-a1", 740, 115, 150) + box("s6d-b2", 900, 60, 260, 110, f"월말 적립{sub('매달 남는 돈', 20)}", size=27, border=INK)
    h += mark("s6d-m0", 40, 290, False, "월말에 넣은 돈이 한 달 수익을 미리 얻기")
    h += box("s6d-r", 1240, 60, 460, 190, f'{sub("(1 + 0.06)<sup>1/12</sup> − 1", 24, "var(--ink)", 600)}<span style="font-size:44px;color:var(--primary)">월 약 0.487%</span>', size=28)
    h += mark("s6d-m1", 1240, 290, False, "월 0.5% 단순 적용")
    h += '<div id="s6d-p" class="pill" style="left:1240px;top:370px;color:var(--primary)">12개월 복리로 연결 → 연 6%</div>'
    s.append(scene("s6d", "납입 시점", panel("s6d-p0", h, wide=True),
                   """const a=T("월초에 있던"); enter("#s6d-b0", a); growX("#s6d-a0", a+1.2, 0.5); enter("#s6d-b1", a+1.5);
growX("#s6d-a1", T("매달 남는 돈은 월말에"), 0.5); enter("#s6d-b2", T("매달 남는 돈은 월말에",0.3));
enter("#s6d-m0", T("한 달 수익을"));
enter("#s6d-m1", T("매달 0.5%를")); enter("#s6d-r", T("12개월을 복리로")); enter("#s6d-p", T("12개월을 복리로",1.4));""",
                   at="납입 시점도", src=f"{MODEL} · 월초 잔액에 수익 적용 후 월말 적립 · 월 수익률 = 1.06^(1/12) − 1"))

    h = box("s6e-a", 40, 50, 480, 190, f'{sub("집에 넣는 것", 23, "#4b5d68", 600)}<span style="font-size:44px;color:var(--buy)">가격 상승 연 2%</span>', size=28)
    h += box("s6e-b", 560, 50, 480, 190, f'{sub("매매 가구 월 지출표", 23, "#4b5d68", 600)}<span style="font-size:44px;color:var(--ink)">월세 0원</span>{sub("살면서 얻는 효과는 이미 반영", 21)}', size=28)
    h += f'<div id="s6e-x" class="dash" style="left:40px;top:290px;width:1000px;height:100px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:700;color:var(--muted)">가상의 임대료를 현금수익으로 추가</div>'
    h += mark("s6e-m", 40, 420, False, "같은 주거 혜택이 겹침")
    s.append(scene("s6e", "집값에 넣는 것", panel("s6e-p", h) +
                   card("s6e-k", 240, "맞출 것", None, "집과 투자계좌 각각에 포함된 항목"),
                   """enter("#s6e-a", S0("s6e",0.5)); enter("#s6e-b", T("월세를 내지 않는 효과"));
enter("#s6e-x", T("가상의 임대료까지")); enter("#s6e-m", T("같은 주거 혜택이")); enter("#s6e-k", T("무엇이 포함됐는지를"));""",
                   at="집값에는 가격 상승만", src="FRBSF(2018) 주택 총수익 구성 설명 참고 · 이번 모형은 가격 상승만 반영"))
    return s


# ======================================================================= 7. 10년 후
def waterfall(id, gx, color, ink, first_lab, vals, base=470, sc=42):
    """vals: (자산1, 금융, 빚, 순). 아이디 id-b0..3 / id-v0..3 / id-x0..3."""
    a, f, d, n = vals
    bars = [(0, a, color, f"{a:.2f}억"), (a, a + f, "#7d98b3" if color == BUY else color, f"+{f:.2f}억"), (n, a + f, GREY, f"−{d:.2f}억"), (0, n, color, f"{n:.2f}억")]
    labs = [first_lab, "금융자산", "대출", "순자산"]
    h = tx(f"{id}-h", gx, 16, {BUY: "매매", JEONSE: "전세", WOLSE: "월세"}[color], 28, 700, ink, w=440, align="center")
    for i, (lo, hi, c, vt) in enumerate(bars):
        x = gx + 20 + i * 106
        top, hh = base - hi * sc, (hi - lo) * sc
        op = "opacity:.75;" if i == 1 else ""
        h += f'<div id="{id}-b{i}" class="bar{" neg" if i == 2 else ""}" style="left:{x}px;top:{top:.1f}px;width:86px;height:{hh:.1f}px;background:{c};{op}border-radius:4px"></div>'
        vy = (top - 30) if i != 2 else (top + hh + 6)
        h += tx(f"{id}-v{i}", x - 30, vy, vt, 21 if i < 3 else 22, 700, ink if i != 2 else "var(--muted)", w=146, align="center")
        h += tx(f"{id}-x{i}", x - 30, base + 10, labs[i], 19, 600, "var(--ink)", w=146, align="center")
    h += f'<div class="gl" style="left:{gx}px;top:{base}px;width:440px;background:#9aa4a8"></div>'
    return h


def ch7():
    s = []
    h = waterfall("s7a-g0", 70, BUY, BUY, "집", (7.314, 1.666, 2.836, 6.144))
    h += waterfall("s7a-g1", 650, JEONSE, JEONSE_INK, "보증금", (4.0, 4.587, 2.0, 6.587))
    h += waterfall("s7a-g2", 1230, WOLSE, WOLSE, "보증금", (1.0, 6.086, 0.2, 6.886))
    s.append(scene("s7a", "10년 후 순자산", panel("s7a-p", h, wide=True),
                   """tl.set("[id^=s7a-g] .bar, [id^=s7a-g][id*=-v]", {opacity:0}, 0);
const step=(g,i,t)=>{ tl.fromTo(`#s7a-g${g}-b${i}`, {opacity:0, scaleY:0}, {opacity: i===1?0.75:1, scaleY:1, duration:0.9, ease:"power2.inOut"}, t); fade(`#s7a-g${g}-v${i}`, t+0.7); };
fade("#s7a-g0-h, [id^=s7a-g0-x]", S0("s7a",0.4));
step(0,0,T("약 7억3천100만원")); step(0,1,T("금융자산은 약 1억6천700만원")); step(0,2,T("남은 대출 약")); step(0,3,T("순자산은 약 6억1천400만원"));
fade("#s7a-g1-h, [id^=s7a-g1-x]", T("보증금 4억원과 금융자산")); step(1,0,T("보증금 4억원과 금융자산",0.3)); step(1,1,T("보증금 4억원과 금융자산",1.8));
step(1,2,T("전세대출 2억원을 빼면")); step(1,3,T("전세대출 2억원을 빼면",1.6));
fade("#s7a-g2-h, [id^=s7a-g2-x]", T("월세 가구는 보증금 1억원")); step(2,0,T("월세 가구는 보증금 1억원",0.4)); step(2,1,T("금융자산 약 6억900만원"));
step(2,2,T("대출 2천만원을 빼")); step(2,3,T("대출 2천만원을 빼",1.4));""",
                   src=f"{SRC_BASE} · 120개월 시점 보유 평가"))

    vals = [6.144, 6.587, 6.886]
    tops = [470 - v * 50 for v in vals]
    h = f'<div id="s7b-l0" class="dash" style="left:340px;top:{tops[0]:.0f}px;width:640px;height:0;border-width:2px 0 0 0;border-radius:0"></div>'
    h += f'<div id="s7b-l1" class="dash" style="left:570px;top:{tops[1]:.0f}px;width:790px;height:0;border-width:2px 0 0 0;border-radius:0"></div>'
    h += f'<div id="s7b-l2" class="dash" style="left:800px;top:{tops[2]:.0f}px;width:560px;height:0;border-width:2px 0 0 0;border-radius:0"></div>'
    h += vbars("s7b-v", 200, 470, [(n, v, c, ink, f"약 {lab}") for (n, c, ink), v, lab in zip(HH, vals, ["6억1,400만원", "6억5,900만원", "6억8,900만원"])], 50, barw=140, gap=90)
    h += f'<div id="s7b-bA" class="brk" style="left:990px;top:{tops[2]:.0f}px;height:{tops[0] - tops[2]:.0f}px"></div>'
    h += tx("s7b-tA", 1012, tops[0] + 8, "매매보다 약 7,400만원", 23, 700, WOLSE)
    h += f'<div id="s7b-bB" class="brk" style="left:1370px;top:{tops[2]:.0f}px;height:{tops[1] - tops[2]:.0f}px"></div>'
    h += tx("s7b-tB", 1392, tops[2] - 40, "전세보다 약 3,000만원", 23, 700, WOLSE)
    h += f'<div id="s7b-c0" class="pill" style="left:1000px;top:270px">더 큰 초기 투자금의 수익</div>'
    h += f'<div id="s7b-c1" class="pill" style="left:1000px;top:330px">매달 차액 적립</div>'
    h += f'<div id="s7b-c2" class="pill" style="left:1000px;top:410px;color:var(--primary)">월세 누적표 + 금융자산표를 함께 볼 때 설명됨</div>'
    s.append(scene("s7b", "차이의 원인", panel("s7b-p", h, wide=True),
                   """[0,1,2].forEach(i=>{ grow("#s7b-v-b"+i, S0("s7b",0.3+i*0.2), 1.0); fade("#s7b-v-v"+i+", #s7b-v-x"+i, S0("s7b",1.0+i*0.2)); });
fade("#s7b-l0, #s7b-l2", T("매매 가구보다 약 7천400만원")); grow("#s7b-bA", T("매매 가구보다 약 7천400만원",0.3), 0.5); fade("#s7b-tA", T("매매 가구보다 약 7천400만원",0.6));
fade("#s7b-l1", T("전세 가구보다 약 3천만원")); grow("#s7b-bB", T("전세 가구보다 약 3천만원",0.3), 0.5); fade("#s7b-tB", T("전세 가구보다 약 3천만원",0.6));
enter("#s7b-c0", T("더 큰 초기 투자금이")); enter("#s7b-c1", T("매달 차액이 적립")); enter("#s7b-c2", T("월세만 따로 누적한"));""",
                   at="기본 조건에서 월세 가구는", src=f"{SRC_BASE} · 120개월 시점 보유 평가"))

    def ab(id, x, head, color, subtxt):
        return (f'<div id="{id}" class="box" style="left:{x}px;top:60px;width:320px;height:330px;background:#fff;border-top:6px solid {color};'
                f'justify-content:flex-start;padding:40px 20px 0;gap:18px;border-radius:12px"><div style="font-size:32px;font-weight:700;color:{color}">{head}</div>'
                f'<div id="{id}-s" style="font-size:23px;color:var(--ink);line-height:1.45;font-weight:400">{subtxt}</div></div>')
    h = ab("s7c-a0", 40, "집 지분", BUY, "생활비로 쓰려면 매도나 추가 대출 같은 절차 필요")
    h += ab("s7c-a1", 390, "보증금", JEONSE_INK, "반환 시점과 다음 집의 보증금이 연결")
    h += ab("s7c-a2", 740, "투자계좌", INK, "즉시 쓸 수 있는 자산")
    s.append(scene("s7c", "자산의 성격", panel("s7c-p", h) +
                   card("s7c-k", 240, "평가 기준", "계속 거주", "집에 계속 사는 상태의 평가 순자산", vsize=40),
                   """enter("#s7c-k", S0("s7c",0.5)); tl.set("#s7c-a0-s, #s7c-a1-s, #s7c-a2-s", {opacity:0}, 0);
enter("#s7c-a0", T("집 지분과 보증금은")); enter("#s7c-a1", T("집 지분과 보증금은",0.3));
enter("#s7c-a2", T("즉시 쓸 수 있는")); fade("#s7c-a2-s", T("즉시 쓸 수 있는",0.4));
fade("#s7c-a0-s", T("매도나 추가 대출")); fade("#s7c-a1-s", T("반환 시점과"));""",
                   at="이 숫자는 집에 계속", src=f"{MODEL} · 계속거주 평가 기준"))

    h = box("s7d-l", 80, 40, 700, 110, f"계속거주 평가{sub('오늘의 기본 그래프', 22)}", border=BUY, size=32, color=BUY)
    h += (f'<div id="s7d-r" class="dash" style="left:960px;top:40px;width:700px;height:110px;display:flex;flex-direction:column;align-items:center;justify-content:center;'
          f'font-size:32px;font-weight:700;color:var(--ink)">같은 날 매각 후 현금{sub("별도 계산", 22)}</div>')
    for i, t in enumerate(["집 매도비용", "조건에 맞는 세금", "ETF 매도세금과 비용", "그다음 주거비 · 계속 거주할 집"]):
        h += f'<div id="s7d-i{i}" class="pill" style="left:960px;top:{190 + i * 70}px;width:700px;height:54px;background:#fff;font-weight:600">{t}</div>'
    h += tx("s7d-n", 80, 190, "집에 계속 사는 상태에서 집 지분·보증금·투자계좌를 평가", 23, 400, "var(--ink)", w=700)
    s.append(scene("s7d", "매각 기준 비교", panel("s7d-p", h, wide=True),
                   """enter("#s7d-l", S0("s7d",0.3)); fade("#s7d-n", S0("s7d",0.8)); enter("#s7d-r", T("모두 같은 날"));
enter("#s7d-i0", T("집 매도비용과")); enter("#s7d-i1", T("집 매도비용과",1.6)); enter("#s7d-i2", T("ETF 매도세금과")); enter("#s7d-i3", T("청산 후에도"));
dim("#s7d-r, [id^=s7d-i]", T("오늘의 기본 그래프는"), 0.4);
tl.fromTo("#s7d-l", {scale:1}, {scale:1.03, duration:0.4, yoyo:true, repeat:1, ease:"power1.inOut"}, T("계속거주 평가"));""",
                   at="모두 같은 날", src=f"{MODEL} · 매각 기준 세후 금액은 계산하지 않음"))
    return s


# ======================================================================= 8. 조건의 변화
GRID = {(4, 2): [7.3952, 5.6249, 5.3573], (4, 8): [7.8992, 7.1707, 7.8409], (2, 6): [6.1437, 6.5873, 6.8864],
        (0, 2): [4.5137, 5.6249, 5.3573], (0, 8): [5.0177, 7.1707, 7.8409]}  # illustrative_results.json continuing_networth / 1e8


def grid(id):
    h = ""
    for j, inv in enumerate([2, 6, 8]):
        h += tx(f"{id}-ch{j}", 300 + j * 420, 18, f"투자 연 {inv}%", 23, 700, "var(--ink)", w=390, align="center")
    for r, hg in enumerate([4, 2, 0]):
        y = 60 + r * 155
        h += tx(f"{id}-rh{r}", 40, y + 54, f"집값 연 {hg}%", 23, 700, "var(--ink)", w=220, align="right")
        for j, inv in enumerate([2, 6, 8]):
            x = 300 + j * 420
            cid = f"{id}-c{hg}{inv}"
            vals = GRID.get((hg, inv))
            if not vals:
                h += f'<div id="{cid}" class="box hatch" style="left:{x}px;top:{y}px;width:390px;height:140px;font-size:22px;font-weight:600;color:var(--muted)">미계산</div>'
                continue
            top = max(range(3), key=lambda i: vals[i])
            inner = ""
            for i, ((n, c, ink), v) in enumerate(zip(HH, vals)):
                op = 1 if i == top else 0.45
                inner += (f'<div style="position:absolute;left:18px;top:{16 + i * 40}px;width:60px;font-size:19px;font-weight:700;color:{ink if i == top else "#546973"}">{n}</div>'
                          f'<div style="position:absolute;left:78px;top:{20 + i * 40}px;width:{v * 28:.0f}px;height:22px;border-radius:4px;background:{c};opacity:{op}"></div>'
                          f'<div style="position:absolute;left:{86 + v * 28:.0f}px;top:{16 + i * 40}px;font-size:19px;font-weight:{800 if i == top else 600};color:{ink if i == top else "#546973"};white-space:nowrap">{v:.2f}억</div>')
            border = "border:3px solid #286cda;" if (hg, inv) == (2, 6) else ""
            h += f'<div id="{cid}" class="box" style="left:{x}px;top:{y}px;width:390px;height:140px;background:#fff;{border}">{inner}</div>'
    return h


def ch8():
    s = []
    h = grid("s8a") + tx("s8a-b", 1530, 222, "기본", 20, 700, BUY)
    s.append(scene("s8a", "집값 × 투자수익", panel("s8a-p", h, wide=True),
                   """fade("[id^=s8a-ch], [id^=s8a-rh]", S0("s8a",0.3)); tl.set("#s8a-c46, #s8a-c22, #s8a-c28, #s8a-c06", {opacity:0.55}, 0);
enter("#s8a-c26, #s8a-b", S0("s8a",0.5)); enter("#s8a-c42", T("집값이 연 4% 오르고")); enter("#s8a-c08", T("반대로 집값 상승을"));
enter("#s8a-c02", T("연 0%와 2%")); enter("#s8a-c48", T("고정된 순위를"));""",
                   src=f"{MODEL} · 계산한 5개 조합만 표시 · 빗금 칸은 계산하지 않음 · 금리 연 4% · 월세 100만원"))
    s[-1]["html"] = s[-1]["html"].replace('id="s8a-b" class="tx" style="left:1530px;top:222px;', 'id="s8a-b" class="tx" style="left:1052px;top:222px;')

    h = vbars("s8b-v", 170, 470, [("전세", 6.587, JEONSE, JEONSE_INK, "약 6억5,900만원"), ("월세 100만", 6.886, WOLSE, WOLSE, "약 6억8,900만원"),
                                  ("월세 120만", 6.5615, WOLSE, WOLSE, "약 6억5,600만원")], 55, barw=150, gap=130)
    y = 470 - 6.587 * 55
    h += f'<div id="s8b-ln" class="dash" style="left:150px;top:{y:.0f}px;width:880px;height:0;border-width:2px 0 0 0;border-radius:0;border-color:#94702a"></div>'
    s.append(scene("s8b", "월세 수준", panel("s8b-p", h) +
                   card("s8b-k1", 240, "월세 가정", "100만 → 120만원", "같은 보증금 1억원", vsize=40, color=WOLSE) +
                   card("s8b-k2", 420, "확인할 것", None, "같은 집에서 가능한 계약인지 시장 자료로 확인", color=WOLSE),
                   """[0,1].forEach(i=>{ grow("#s8b-v-b"+i, S0("s8b",0.4+i*0.3), 1.0); fade("#s8b-v-v"+i+", #s8b-v-x"+i, S0("s8b",1.2+i*0.3)); });
tl.set("#s8b-v-b2, #s8b-v-v2, #s8b-v-x2", {opacity:0}, 0);
enter("#s8b-k1", T("같은 보증금에서")); tl.fromTo("#s8b-v-b2", {opacity:1, scaleY:0}, {scaleY:1, duration:1.0, ease:"power2.inOut"}, T("월세 가구의 순자산은 약")); fade("#s8b-v-v2, #s8b-v-x2", T("월세 가구의 순자산은 약",0.9));
fade("#s8b-ln", T("전세의 약 6억5천900만원보다")); dim("#s8b-v-b1, #s8b-v-v1", T("전세의 약 6억5천900만원보다"), 0.35);
enter("#s8b-k2", T("실제 같은 집에서"));""",
                   at="월세 수준만 바꿔도", src=f"{MODEL} · 월세만 120만원으로 바꾼 재계산 · 다른 조건 기본값"))

    def rc(id, x, head, vals):
        labs = [f"약 {v}" for v in vals[1]]
        return (tx(f"{id}-h", x, 24, head, 25, 700, "var(--ink)", w=560, align="center") +
                vbars(id, x + 60, 430, [(n, v, c, ink, l) for (n, c, ink), v, l in zip(HH, vals[0], labs)], 45, barw=120, gap=60))
    h = rc("s8c-a", 120, "전세대출 연 2% · 매매대출 연 6%", ([5.253, 7.129, 6.886], ["5억2,500만원", "7억1,300만원", "6억8,900만원"]))
    h += rc("s8c-b", 960, "전세대출 연 6% · 매매대출 연 2%", ([6.98, 6.046, 6.886], ["6억9,800만원", "6억500만원", "6억8,900만원"]))
    h += '<div id="s8c-p" class="pill" style="left:690px;top:484px;color:var(--wolse)">월세 보증금대출은 계속 연 4%</div>'
    s.append(scene("s8c", "대출 금리", panel("s8c-p0", h, wide=True),
                   """tl.set("[id^=s8c-a-], [id^=s8c-b-], #s8c-a-h, #s8c-b-h", {opacity:0}, 0);
const a=T("전세대출은 연 2%"); fade("#s8c-a-h", a); [0,1,2].forEach(i=>{ tl.fromTo("#s8c-a-b"+i,{opacity:1,scaleY:0},{scaleY:1,duration:1.0,ease:"power2.inOut"}, a+0.3+i*0.3); fade("#s8c-a-v"+i+", #s8c-a-x"+i, a+1.1+i*0.3); });
dim("#s8c-a-b2, #s8c-a-v2", a+2.6, 0.35);
const b=T("반대로 전세대출은"); fade("#s8c-b-h", b); [0,1,2].forEach(i=>{ tl.fromTo("#s8c-b-b"+i,{opacity:1,scaleY:0},{scaleY:1,duration:1.0,ease:"power2.inOut"}, b+0.3+i*0.3); fade("#s8c-b-v"+i+", #s8c-b-x"+i, b+1.1+i*0.3); });
dim("#s8c-b-b1, #s8c-b-v1, #s8c-b-b2, #s8c-b-v2", b+2.6, 0.35);
enter("#s8c-p", T("월세 보증금대출 금리는"));""",
                   at="금리도 경계를", src=f"{MODEL} · 대출금리만 바꾼 별도 고정금리 조건 · 집값 연 2% · 투자 연 6%"))
    

    h = tx("s8d-lt", 80, 30, "이번 비교 · 처음부터 고정", 26, 700) + tx("s8d-rt", 960, 30, "실제 변동금리 대출", 26, 700)
    h += f'<svg class="abs" style="left:0;top:0" width="1740" height="540">'
    h += f'<path id="s8d-f0" d="M80,170 L760,170" pathLength="1" stroke="{JEONSE}" stroke-width="6" fill="none" stroke-dasharray="1" stroke-dashoffset="1"/>'
    h += f'<path id="s8d-f1" d="M80,320 L760,320" pathLength="1" stroke="{BUY}" stroke-width="6" fill="none" stroke-dasharray="1" stroke-dashoffset="1"/>'
    h += (f'<path id="s8d-v" d="M960,300 L1100,300 L1100,230 L1270,230 L1270,180 L1420,180 L1420,260 L1640,260" pathLength="1" stroke="{INK}" stroke-width="6" '
          f'fill="none" stroke-dasharray="1" stroke-dashoffset="1"/></svg>')
    h += tx("s8d-l0", 80, 120, "조건 A: 연 2% 고정", 22, 700, JEONSE_INK) + tx("s8d-l1", 80, 270, "조건 B: 연 6% 고정", 22, 700, BUY)
    for i, (x, y) in enumerate([(1100, 230), (1270, 180), (1420, 260)]):
        h += f'<div id="s8d-d{i}" class="dot" style="left:{x - 9}px;top:{y - 9}px;background:{INK}"></div>'
    h += tx("s8d-vl", 960, 350, "금리가 바뀌는 시점마다 이자와 남은 투자금이 달라짐", 22, 600, "var(--ink)")
    h += tx("s8d-vn", 960, 390, "선 모양은 설명용 예시", 19, 400, "var(--muted)")
    h += '<div id="s8d-p" class="pill" style="left:80px;top:430px;color:var(--primary)">확인할 것: 언제, 어떤 잔액에 적용됐는지</div>'
    s.append(scene("s8d", "고정금리 조건", panel("s8d-p0", h, wide=True),
                   """fade("#s8d-lt", S0("s8d",0.3)); tl.fromTo("#s8d-f0", {strokeDashoffset:1}, {strokeDashoffset:0, duration:1.2}, S0("s8d",0.6)); fade("#s8d-l0", S0("s8d",0.8));
tl.fromTo("#s8d-f1", {strokeDashoffset:1}, {strokeDashoffset:0, duration:1.2}, S0("s8d",1.2)); fade("#s8d-l1", S0("s8d",1.4));
const v=T("실제 변동금리 대출은"); fade("#s8d-rt", v); tl.fromTo("#s8d-v", {strokeDashoffset:1}, {strokeDashoffset:0, duration:2.4, ease:"none"}, v+0.2);
stagger(["#s8d-d0","#s8d-d1","#s8d-d2"], v+0.6, 0.7, fade); fade("#s8d-vl, #s8d-vn", T("이자와 남은 투자금이"));
enter("#s8d-p", T("어떤 잔액에"));""",
                   at="각 화면은", src=f"{MODEL} · 앞 화면의 금리 조건은 처음부터 고정한 별도 계산"))

    h = grid("s8e")
    for hg, inv in [(4, 6), (2, 2), (2, 8), (0, 6)]:
        x, y = 300 + [2, 6, 8].index(inv) * 420, 60 + [4, 2, 0].index(hg) * 155
        h += f'<div id="s8e-o{hg}{inv}" class="dash" style="left:{x - 6}px;top:{y - 6}px;width:402px;height:152px;border-color:#286cda;border-width:3px"></div>'
    s.append(scene("s8e", "판단 범위", panel("s8e-p", h, wide=True),
                   """tl.set("#s8e-c46, #s8e-c22, #s8e-c28, #s8e-c06", {opacity:0.55}, 0);
stagger(["#s8e-o46","#s8e-o22","#s8e-o28","#s8e-o06"], T("경계 주변을"), 0.3, fade);""",
                   at="이 표에서 유용한", src=f"{MODEL} · 점선 칸은 추가 계산이 필요한 조합 · 손익분기선은 계산하지 않음"))
    return s


# ======================================================================= 9. 실행
def ch9():
    s = []
    h = box("s9a-a", 60, 60, 560, 90, "매달 남는 돈", size=30)
    h += arrow("s9a-a0", 195, 160, 60, "d") + arrow("s9a-a1", 485, 160, 60, "d", GREY)
    h += box("s9a-e", 60, 240, 270, 120, f"ETF 50%{sub('투자', 21)}", size=28, border=BUY, color=BUY)
    h += box("s9a-c", 350, 240, 270, 120, f"현금 50%{sub('수익 없음', 21)}", size=28, bg="#e4e2d9")
    h += tx("s9a-lg", 760, 20, "옅은 막대: 전부 투자(기본) · 진한 막대: 절반만 투자", 21, 400, "var(--muted)")
    base_items = [(n, v, c, ink, "") for (n, c, ink), v in zip(HH, [6.144, 6.587, 6.886])]
    h += vbars("s9a-o", 800, 470, base_items, 50, barw=80, gap=220, lab=False).replace('class="bar"', 'class="bar" data-o="1"')
    half = [(n, v, c, ink, f"약 {l}") for (n, c, ink), v, l in zip(HH, [5.935, 6.102, 6.486], ["5억9,400만원", "6억1,000만원", "6억4,900만원"])]
    h += vbars("s9a-v", 890, 470, half, 50, barw=80, gap=220)
    s.append(scene("s9a", "차액 투자 50%", panel("s9a-p", h, wide=True),
                   """tl.set("[id^=s9a-o-b]", {opacity:0.25}, 0); enter("#s9a-a", S0("s9a",0.4)); fade("#s9a-lg", S0("s9a",0.8));
[0,1,2].forEach(i=>grow("#s9a-o-b"+i, S0("s9a",0.8+i*0.2), 1.0));
const h=T("절반만 넣고"); grow("#s9a-a0, #s9a-a1", h, 0.5); enter("#s9a-e", h+0.4); enter("#s9a-c", h+0.9);
tl.set("[id^=s9a-v-]", {opacity:0}, 0);
const z=[T("매매 약 5억9천400만원"), T("전세 약 6억1천만원"), T("월세 약 6억4천900만원")];
z.forEach((t,i)=>{ tl.fromTo("#s9a-v-b"+i, {opacity:1, scaleY:0}, {scaleY:1, duration:1.0, ease:"power2.inOut"}, t); fade("#s9a-v-v"+i+", #s9a-v-x"+i, t+0.8); });""",
                   src=f"{SRC_BASE} · 차액 투자 실행률 50% · 미투자분은 무수익 현금"))

    h = tx("s9b-l", 40, 30, "10년 후 금융자산 구성 (절반만 투자)", 25, 700)
    stacks = [(0.869, 0.589), (2.732, 1.37), (4.556, 1.13)]
    base, sc = 440, 60
    for i, ((n, c, ink), (e, cs)) in enumerate(zip(HH, stacks)):
        x = 140 + i * 300
        h += f'<div id="s9b-e{i}" class="bar" style="left:{x}px;top:{base - e * sc:.0f}px;width:130px;height:{e * sc:.0f}px;background:{c};border-radius:0"></div>'
        h += f'<div id="s9b-c{i}" class="bar hatch" style="left:{x}px;top:{base - (e + cs) * sc:.0f}px;width:130px;height:{cs * sc:.0f}px;border:1px solid #c9c5b8"></div>'
        h += tx(f"s9b-t{i}", x - 60, base - (e + cs) * sc - 58, f"ETF {e:.2f}억<br>현금 {cs:.2f}억", 20, 700, ink, w=250, align="center")
        h += tx(f"s9b-x{i}", x - 40, base + 10, n, 24, 700, ink, w=210, align="center")
    h += f'<div class="gl" style="left:120px;top:{base}px;width:900px;background:#9aa4a8"></div>'
    h += '<div id="s9b-p" class="pill" style="left:40px;top:488px;background:#f3f2ec">매달 남는 돈을 소비하면 저축 원금도 줄어드는 별도 계산</div>'
    s.append(scene("s9b", "현금으로 남는 돈", panel("s9b-p0", h) +
                   card("s9b-k1", 240, "투자하지 않은 돈", "현금으로 남음", vsize=36) +
                   card("s9b-k2", 420, "구분할 것", None, "수익률 차이 · 저축 실행의 차이"),
                   """fade("#s9b-l", S0("s9b",0.3)); [0,1,2].forEach(i=>{ grow("#s9b-e"+i, S0("s9b",0.5+i*0.2), 0.9); grow("#s9b-c"+i, S0("s9b",1.6+i*0.2), 0.6); fade("#s9b-t"+i+", #s9b-x"+i, S0("s9b",2.0+i*0.2)); });
enter("#s9b-k1", S0("s9b",1.8)); enter("#s9b-p", T("매달 남는 돈을 소비하면")); enter("#s9b-k2", T("임차의 차액투자와"));""",
                   at="여기서 투자하지 않은", src=f"{SRC_BASE} · 차액 투자 실행률 50%"))
    s[-1]["html"] = s[-1]["html"].replace("<br>", " · ")

    h = '<div id="s9c-bl" class="dash" style="left:120px;top:150px;width:880px;height:0;border-width:3px 0 0 0;border-radius:0;border-color:#286cda"></div>'
    h += tx("s9c-bt", 120, 108, "월 예산 300만원", 23, 700, BUY)
    h += '<div id="s9c-a" class="bar" style="left:260px;top:220px;width:180px;height:250px;background:#8fb2ec"></div>'
    h += '<div id="s9c-b" class="bar" style="left:640px;top:90px;width:180px;height:380px;background:#c9c5b8"></div>'
    h += '<div id="s9c-bo" class="bar hatch" style="left:640px;top:90px;width:180px;height:60px;border:2px solid #b4472f;border-radius:6px 6px 0 0"></div>'
    h += tx("s9c-al", 200, 482, "예산 안 · 계속", 22, 700, "var(--ink)", w=300, align="center")
    h += tx("s9c-blb", 580, 482, "예산 초과 · 경로 중단", 22, 700, "var(--no)", w=300, align="center")
    h += tx("s9c-n", 120, 30, "지출 막대는 설명용 예시", 19, 400, "var(--muted)")
    h += mark("s9c-m0", 1100, 70, False, "기존 ETF 매도 없음") + mark("s9c-m1", 1100, 130, False, "추가 대출 없음")
    h += box("s9c-r", 1100, 220, 560, 230, f'현실의 대응{sub("비상자금 · 자산 매각", 23, "var(--ink)", 600)}<span id="s9c-r2" style="display:block;font-size:21px;color:var(--muted);font-weight:400">세금 · 매각 시점 · 추가 대출금리 별도 계산</span>', size=28)
    s.append(scene("s9c", "예산 한도", panel("s9c-p", h, wide=True),
                   """fade("#s9c-bl, #s9c-bt, #s9c-n", S0("s9c",0.3)); grow("#s9c-a", S0("s9c",0.6), 1.0); fade("#s9c-al", S0("s9c",1.4));
const o=T("현금지출이 예산을 넘으면"); grow("#s9c-b", o, 1.2); fade("#s9c-bo", o+1.2);
enter("#s9c-m0", T("팔거나 추가로")); enter("#s9c-m1", T("팔거나 추가로",0.6)); fade("#s9c-blb", T("팔거나 추가로",1.6));
tl.set("#s9c-r2", {opacity:0}, 0); enter("#s9c-r", T("현실에서는 비상자금")); fade("#s9c-r2", T("세금과 매각 시점"));""",
                   at="기본 모형은 매달", src=f"{MODEL} · 월 주거 현금지출이 예산을 넘으면 그 경로는 계산을 멈춤"))

    h = '<div class="gl" style="left:120px;top:150px;width:1500px;height:4px;background:#9aa4a8"></div>'
    h += tx("s9d-t0", 100, 166, "0년", 20, 600, "var(--muted)") + tx("s9d-t1", 1590, 166, "10년", 20, 600, "var(--muted)")
    h += tx("s9d-n", 1300, 40, "사건 위치는 설명용 예시", 19, 400, "var(--muted)")
    for i, (x, t) in enumerate([(420, "전세 갱신 · 보증금 인상"), (820, "월세 인상"), (1220, "시장 하락기 이사")]):
        h += f'<div id="s9d-e{i}" class="dot big" style="left:{x - 14}px;top:138px;background:#b4472f"></div>'
        h += tx(f"s9d-l{i}", x - 160, 186, t, 22, 700, "var(--ink)", w=320, align="center")
    h += box("s9d-a", 120, 300, 700, 170, f'<span style="color:var(--buy)">매매</span>{sub("집 한 채에 자금이 집중", 24, "var(--ink)")}', size=32)
    h += box("s9d-b", 920, 300, 700, 170, f'투자계좌{sub("시장가격이 매일 움직임", 24, "var(--ink)")}', size=32)
    s.append(scene("s9d", "다른 형태의 위험", panel("s9d-p", h, wide=True),
                   """fade("#s9d-t0, #s9d-t1, #s9d-n", S0("s9d",0.3));
const e=T("전세 갱신 때"); enter("#s9d-e0, #s9d-l0", e+0.5); enter("#s9d-e1, #s9d-l1", e+2.4); enter("#s9d-e2, #s9d-l2", T("투자시장이 하락한"));
enter("#s9d-a", T("집 한 채에")); enter("#s9d-b", T("매일 움직이는"));""",
                   at="전세 갱신 때", src=f"{MODEL} · 사건별 확률·금액은 계산하지 않음"))
    return s


# ======================================================================= 10. 다음 선택
def ch10():
    s = []
    h = box("s10a-c", 620, 30, 500, 90, "같은 단지 · 같은 전용면적", border=BUY, size=30, color=BUY)
    h += '<div id="s10a-hl" class="gl" style="left:350px;top:150px;width:1040px;height:3px;background:#286cda"></div>'
    h += '<div id="s10a-vl" class="gl" style="left:869px;top:120px;width:3px;height:30px;background:#286cda"></div>'
    for i, x in enumerate([350, 870, 1390]):
        h += arrow(f"s10a-a{i}", x, 150, 40, "d")
    br = [("s10a-b0", "매매가격", ""), ("s10a-b1", "전세보증금", ""), ("s10a-b2", "월세 계약", "보증금 + 월세 짝 유지")]
    h += "".join(box(id, 130 + i * 520, 200, 440, 110, f"{t}{sub(sv, 21) if sv else ''}", size=30) for i, (id, t, sv) in enumerate(br))
    h += '<div id="s10a-g0" class="pill" style="left:650px;top:330px;background:#f3f2ec">신규 계약</div>'
    h += '<div id="s10a-g1" class="pill" style="left:810px;top:330px;background:#f3f2ec">갱신 계약 구분</div>'
    btm = [("s10a-d0", "당시 금리"), ("s10a-d1", "세금"), ("s10a-d2", "실제 상품의 원화 수익 · 월별")]
    h += "".join(box(id, 130 + i * 520, 410, 440, 90, t, bg="#f3f2ec", size=26) for i, (id, t) in enumerate(btm))
    s.append(scene("s10a", "실제 사례에 필요한 자료", panel("s10a-p", h, wide=True),
                   """enter("#s10a-c", S0("s10a",0.4));
const b=T("전용면적에서 매매가격"); fade("#s10a-hl, #s10a-vl", b); grow("#s10a-a0", b+0.2, 0.4); enter("#s10a-b0", b+0.4);
grow("#s10a-a1", T("전세보증금, 월세"), 0.4); enter("#s10a-b1", T("전세보증금, 월세",0.2)); grow("#s10a-a2", T("전세보증금, 월세",1.2), 0.4); enter("#s10a-b2", T("전세보증금, 월세",1.4));
enter("#s10a-g0, #s10a-g1", T("신규 계약과 갱신"));
const d=T("당시 금리와 세금"); stagger(["#s10a-d0","#s10a-d1","#s10a-d2"], d, 0.7);""",
                   src="국토교통부 실거래가 공개시스템(매매·전월세) 자료 구조 · 실제 사례 계산은 이번 편에서 하지 않음"))

    rows = [("원금", "남은 빚"), ("보증금", "돌려받을 자산"), ("남는 월예산", "금융자산")]
    h = ""
    for i, (a, b) in enumerate(rows):
        y = 60 + i * 150
        h += box(f"s10b-l{i}", 40, y, 320, 110, a, size=30)
        h += arrow(f"s10b-a{i}", 380, y + 55, 150)
        h += box(f"s10b-r{i}", 560, y, 480, 110, b, size=30, border=BUY, color=BUY)
    s.append(scene("s10b", "정리", panel("s10b-p", h) +
                   card("s10b-k1", 240, "함께 볼 결과", None, "기본 조건 + 조건을 바꾼 결과") +
                   card("s10b-k2", 420, "보이는 것", None, "어느 가정이 순자산을 움직였는지"),
                   """tl.set("[id^=s10b-l], [id^=s10b-r]", {opacity:0.3}, 0); fade("[id^=s10b-l]", S0("s10b",0.4)); tl.set("[id^=s10b-l]", {opacity:0.3}, S0("s10b",0.9));
const r=T("원금은 남은"); [0,1].forEach(i=>{ lit("#s10b-l"+i, r+i*1.8); growX("#s10b-a"+i, r+0.4+i*1.8, 0.5); lit("#s10b-r"+i, r+0.8+i*1.8); });
const m=T("남는 월예산은"); lit("#s10b-l2", m); growX("#s10b-a2", m+0.4, 0.5); lit("#s10b-r2", m+0.8);
enter("#s10b-k1", T("기본 조건의 결과와")); enter("#s10b-k2", T("어느 가정이"));""",
                   at="이번에 확인한", src=f"{MODEL} · 이번 편 계산 구조 요약"))

    form = [("초기자금", "f0"), ("소득", "f1"), ("대출한도", "f2"), ("월 상환액", "f3"), ("집값 외에 필요한 돈", "f4")]
    h = '<div id="s10c-fm" class="box" style="left:80px;top:30px;width:880px;height:470px;background:#fff;justify-content:flex-start;padding-top:24px;gap:14px">'
    h += '<div style="font-size:26px;font-weight:700;color:var(--muted)">주거 예산 입력</div>'
    for t, k in form:
        h += f'<div id="s10c-{k}" class="frow"><span>{t}</span><span class="blank"></span></div>'
    h += "</div>"
    h += arrow("s10c-a", 980, 230, 100)
    h += box("s10c-o", 1100, 160, 560, 150, f'주거 예산{sub("다음 편에서 계산", 23, "var(--primary)", 700)}', border=BUY, size=34)
    h += arrow("s10c-a2", 1380, 320, 50, "d")
    h += (f'<div id="s10c-n" class="dash" style="left:1100px;top:390px;width:560px;height:110px;display:flex;flex-direction:column;align-items:center;'
          f'justify-content:center;font-size:30px;font-weight:700;color:var(--ink)">지역 · 단지 후보{sub("예산을 정한 뒤", 21)}</div>')
    s.append(scene("s10c", "다음 편 · 주거 예산", panel("s10c-p", h, wide=True),
                   """enter("#s10c-fm", S0("s10c",0.3)); tl.set("[id^=s10c-f]:not(#s10c-fm)", {opacity:0.3}, 0);
lit("#s10c-f0", T("초기자금이 같아도")); lit("#s10c-f1", T("소득과 대출 조건에"));
const n=T("대출한도와 월 상환액"); lit("#s10c-f2", n+0.3); lit("#s10c-f3", n+1.4); lit("#s10c-f4", T("집값 외에 필요한"));
growX("#s10c-a", T("주거 예산을 계산"), 0.5); enter("#s10c-o", T("주거 예산을 계산",0.4));
grow("#s10c-a2", T("지역과 단지 후보를"), 0.4); enter("#s10c-n", T("지역과 단지 후보를",0.3));""",
                   at="다음 단계는", src="다음 편 예고 · 대출한도·월 상환액은 아직 계산하지 않음"))
    return s
