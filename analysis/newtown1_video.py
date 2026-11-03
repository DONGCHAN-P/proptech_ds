"""신도시 1편 — 대본을 영상으로.

대본(docs/longform/2026-10-10-newtown-1.md)의 내레이션을 그대로 가져와,
각 토막에 화면을 붙였다. **길이는 내레이션 글자 수가 정한다.** 그래서
사장님이 녹음하면 그림이 저절로 맞는다.

화면이 없는 대목은 글자 카드로 채운다. 10분짜리에서 제일 길게 느껴지는 건
빈 화면이다.

실행:
  python analysis/newtown1_video.py            # 카드 + 영상 + 자막
  python analysis/newtown1_video.py --cards    # 카드만 다시
  python analysis/newtown1_video.py --plan     # 길이만 계산
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis import newtown_charts as NC  # noqa: E402
LOSE_C = "#E5484D"
from analysis import newtown_scenes as SC  # noqa: E402
from content import frame as FR  # noqa: E402
from content import longvideo as LV  # noqa: E402

# GPT 와 함께 다듬은 내레이션. 숫자가 바뀐 줄은 자동으로 되돌려 놨다.
POLISH = {}
_pf = ROOT / "config" / "narration.json"
if _pf.exists():
    import json as _json
    POLISH = _json.loads(_pf.read_text(encoding="utf-8")).get("map", {})
MUSIC = ROOT / "assets" / "music" / "thinking_music.mp3"
VOICE_DIR = ROOT / "output" / "longform" / "voice"

ART = ROOT / "output" / "longform" / "newtown1"
CARDS = ART / "cards"
FRAMES = ART / "frames"
SUBS = ART / "subs"
OUT = ROOT / "output" / "longform" / "newtown1_full.mp4"

# 장(章). 테두리 오른쪽 위에 뜨고 진행 점이 여기 맞춰 움직인다.
# 너무 잘게 나누면 점이 기어가는 것처럼 보이고, 뭉치면 어디쯤인지 모른다.
CHAPTERS = ["여는 말", "영통", "광교", "동탄", "반례", "착시",
            "원인", "다시 재기", "시점", "같은 동탄", "결론",
            "한계", "질문", "후보", "예고"]

# 움직이는 장면이 쓰는 데이터. 장면 함수가 아니라 여기서 한 번만
# 읽는다 — 프레임마다 DuckDB 를 때리면 렌더가 끝나지 않는다.
FLAGS = SC.load_flags()
ALLFLAGS = SC.load_all_flags()
CMP = SC.load_compare()
SPLIT = SC.load_split()
MIX = SC.load_mix()
MOVEIN = SC.load_movein()
# 막대 차트는 PNG 와 **같은 행**을 쓴다. 두 군데서 따로 계산하면
# 언젠가 영상과 그림이 다른 숫자를 말한다.
_C = NC.con()
ROWS = {"level": NC.rows_level(_C), "naive": NC.rows_naive(_C),
        "same": NC.rows_same(_C), "peak": NC.rows_peak(_C)}


# 막대 차트마다 붙는 머리말 · 제목 · 단서. 호출부에 늘어놓으면 대본이
# 안 읽힌다.
SPEC = {
    "level": dict(
        kick="2026년 · 30평대 중위 평당가",
        title="지금은 <b>세 배</b> 가까이 벌어져 있습니다",
        legend=SC.LEGEND_WL),
    "naive": dict(
        kick="2015 → 2026 · 동네별 중위 평당가 상승률",
        title="이대로 보면 <em>옥정·검단이 광교보다 위</em>입니다",
        note="그런데 이 그림은 틀렸습니다. 2026년에 거래된 집이 "
             "2015년과 같은 집이 아니기 때문입니다."),
    "same": dict(
        kick="2019 → 2026 · 두 해 모두 거래된 '같은 단지'만",
        title="다시 재면 <b>순서가 뒤집힙니다</b>",
        note="같은 단지의 30평대 상승률 중앙값. 새로 지은 집이 섞이는 "
             "문제를 없앴습니다."),
    "peak": dict(
        kick="2021년 고점 대비 2026년 · 같은 단지",
        title="지키느냐 빠지느냐가 <em>여기서</em> 갈립니다",
        zero=True,
        note="가운데가 0%. 오른쪽이 고점보다 오른 곳, 왼쪽이 내린 곳입니다."),
}


def grow(key: str, *, name: str, static: bool = False) -> str:
    """막대가 0 에서 자라는 차트. 같은 그림을 두 토막에 걸쳐 쓸 때
    뒤쪽은 static — 다시 자라면 화면이 되감긴 것처럼 보인다."""
    return card("custom", name=name, anim=not static,
                scene=f"bars:{key}" + (":static" if static else ""),
                html=SC.bars_anim(ROWS[key], static=static, **SPEC[key]))

_cards: dict[str, str] = {}
_n = 0
_chap = CHAPTERS[0]


SCENE_OF: dict[str, str] = {}


def card(kind: str, *, name: str | None = None, scene: str | None = None,
         **kw) -> str:
    """카드를 하나 등록하고 참조 이름을 돌려준다.

    HTML 을 바로 만들지 않고 (종류, 인자) 로 들고 있는다. 등장 장면을
    프레임마다 다시 그려야 해서, 완성된 HTML 한 장으로는 안 된다.
    """
    global _n
    # 이름을 직접 주면 번호를 쓰지 않는다. 뒤에 카드를 끼워 넣어도
    # c0NN 순번이 밀리지 않아 이모지 매핑이 안전하다.
    if name is None:
        _n += 1
        name = f"c{_n:03d}"
    _cards[name] = (kind, kw)
    if scene:
        SCENE_OF[name] = scene
    return f"cards/{name}"


def B(visual: str, text: str = "", motion: str = "in",
      section: bool = False, hold: float = 0.0) -> LV.Beat:
    return LV.Beat(visual=visual, text=POLISH.get(text, text), motion=motion,
                   section=section, hold=hold, chapter=_chap)


def CH(name: str) -> None:
    """여기부터 새 장. 뒤따르는 B() 들이 이 이름을 단다."""
    global _chap
    assert name in CHAPTERS, name
    _chap = name


# (카드, 이모지, 새 제목, 새 설명, 바뀌기 전 제목 앞부분)
EMOJI_MAP = [
    ('c001', '생각', '"거기 누가 사냐"', None, '분양할 때'),
    ('c013', '공장', '둘째, <b>일자리</b>', '2019 수원지법·지검 · 2021 경기도청', '둘째, 일자리'),
    ('c016', '생각', '"거기를 왜 가냐"', None, '이번에도'),
    ('c019', '저울', '아직 "흔하다"는 <em>이르다</em>', '10년 전을 생각하면 놀라운 숫자', '"흔하다"고'),
    ('c023', '기차', '늦게, 대신 <b>빠르게</b>', '2016 SRT · 2024 GTX-A · 수서 20분대', '교통은 늦게'),
    ('c025', '물음표', '"결국 오른다"?', None, '"신도시는 결국'),
    ('c026', '돋보기', '<em>오른 곳만</em> 봤다', None, '이건 오른 곳만'),
    ('c029', '상승', '얼마나 올랐나', '2015 → 2026 · 중위 평당가 상승률', '"얼마나 올랐나"로'),
    ('c030', '경고', '<em>틀린 이야기</em>를 할 뻔했습니다', None, '여기서 끝냈다면'),
    ('c032', '엑스', '<em>같은 집이 아니다</em>', '2015년에 있던 그 집이 아니다', '2026년에 거래된 집이'),
    ('c035', '체크', '광교는 <b>0%</b>', '새로 지을 땅이 없다', '광교는'),
    ('c036', '자', '<em>같은 자</em>가 아니었다', None, '같은 자로 잰 게'),
    ('c039', '체크', '이제야 <b>섭니다</b>', None, '처음 세웠던 기준이'),
    ('c042', '모래시계', '진짜 차이는 <em>2021년 이후</em>', None, '진짜 차이는'),
    ('c043', '하락', '<em>두 번</em> 벌어졌다', '오를 때 덜 오르고, 내릴 때 더 내렸다', '두 번 벌어졌습니다'),
    ('c045', '돋보기', '<b>같은 동탄</b> 안에서', None, '동네끼리가 아니라'),
    ('c046', '기차', '교통도 일자리도 <b>같다</b>', '같은 삼성권 · 같은 SRT · 같은 GTX', '교통도 일자리도'),
    ('c049', '공사', '남은 변수는 <b>공급</b>', None, '남은 변수는'),
    ('c050', '체크', '가장 <b>깨끗한 증거</b>', '다른 조건이 같은 두 곳', '가장 깨끗한 증거'),
    ('c054', '나침반', '강남으로 <b>가는 길</b>', '거리가 아니라 방향', '그 방향에'),
    ('c055', '모래시계', '<em>한 시간 +</em>', '검단 · 옥정 → 강남', '검단과 옥정은'),
    ('c056', '공장', 'LG디스플레이 파주', '큰 일자리가 바로 옆에 있다', '운정 옆에는'),
    ('c057', '경고', '일자리만으로는 <em>부족</em>', None, '일자리 하나만으로는'),
    ('c060', '물음표', '인과는 <em>아니다</em>', '사례가 여섯이면 우연일 수 있다', '인과로 검증된 게'),
    ('c061', '눈', '반대 시각', '운정은 개통 뒤 인구가 늘고 있다', '반대 시각도'),
    ('c062', '모래시계', '종류가 아니라 <b>시점</b>?', '2028년 삼성역 정차 이후라면', '교통의 종류가 아니라'),
    ('c063', '저울', '오늘 세운 건 <em>가설</em>', '시간이 지나봐야 안다', '오늘 세운 기준은'),
    ('c065', '돋보기', '못 보고 있는 곳은?', None, '지금 내가'),
    ('c066', '나침반', '<b>미리</b> 골라보자', '돌아보는 대신', '돌아보는 대신'),
    ('c068', '빌딩', '③ 남양주 왕숙', 'GTX-B · 9호선 연장 · 약 8만 가구', '③ 남양주 왕숙'),
    ('c070', '메모', '한 곳씩', '완성된 모습 · 일자리 · 강남 교통', '한 곳씩'),
    ('c071', '체크', '틀렸으면 <em>틀렸다고</em>', '시간이 지난 뒤 다시 채점합니다', '틀렸으면'),
    ('c072', '메모', '국토교통부 실거래가', '계산 방법은 영상 설명란에', '국토교통부'),
    ('c073', '경고', '매수 권유가 <em>아닙니다</em>', '판단은 각자의 몫입니다', '특정 지역 매수를'),
]

def to_emoji() -> None:
    """글자만 있던 카드를 **그림이 주인공인 카드**로 바꾼다.

    자막 띠가 내레이션을 이미 다 보여 주는데 카드가 같은 문장을 또 적고
    있었다 (54개 중 17개). 같은 말이 화면에 두 번 떠 있으면 "글자가 많다"
    고 느낀다. 카드는 핵심어만 들고, 설명은 자막에 맡긴다.

    카드 번호는 만들어진 순서라 대본을 고치면 밀린다. 바뀌기 전 제목의
    앞부분을 같이 적어 두고, 어긋나면 세운다.
    """
    for name, icon, big, cap, was in EMOJI_MAP:
        kind, kw = _cards[name]
        cur = re.sub(r"<[^>]+>", "", str(kw.get("big", "")))
        cur = cur.replace("<br>", "")
        assert cur.startswith(was), f"{name}: 카드가 밀렸다 — 지금 「{cur}」"
        new = {"icon": icon, "big": big}
        if cap:
            new["cap"] = cap
        if kw.get("dark"):
            new["dark"] = True
        _cards[name] = ("emoji", new)


def beats() -> list[LV.Beat]:
    b: list[LV.Beat] = []

    # ── 훅 ───────────────────────────────────────────────────────────────
    b.append(B(card("plain", dark=True,
                    big='분양할 때<br><em>"거기 누가 사냐"</em>는<br>'
                        '말을 듣던 동네'),
               "분양할 때 \"거기 누가 사냐\"는 말을 듣던 동네가 있습니다.",
               "still", section=True, hold=1.2))
    _g, _d = FLAGS[0], FLAGS[1]
    b.append(B(card("custom", scene="flags", html=SC.flags_card(FLAGS)),
               f"지금 그 동네 대장 단지는 {_g['peak']:.0f}억이 넘습니다. "
               f"광교 {_g['name']}, {_g['first_y']}년 입주 첫해에 "
               f"{_g['first']:.1f}억이던 집입니다. 동탄2 {_d['name']}도 "
               f"{_d['first_y']}년 {_d['first']:.0f}억에서 "
               f"{_d['peak']:.1f}억이 됐습니다.", "still"))
    b.append(B(card("custom", scene="line", html=SC.line_anim(ALLFLAGS), anim=True),
               "같은 말을 듣고 출발했는데, 저는 그 갈림길을 두 번 "
               "바로 옆에서 지켜봤습니다.", "still"))
    b.append(B(card("title", sec="데이터로보는부동산 · 신도시 시리즈 1편",
                    big="지나간 신도시로<br><b>다음을 고르는 법</b>"),
               "안녕하세요. 오늘은 지나간 신도시를 데이터로 되짚어서, "
               "앞으로 어디가 오를지 판단하는 기준을 세워보겠습니다.",
               "still"))

    # ── 영통 ─────────────────────────────────────────────────────────────
    CH("영통")
    b.append(B(card("title", sec="01", big="영통에서 본<br>두 번의 변화"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("custom", scene="yeongtong", html=SC.yeongtong_map(), anim=True),
               "저는 수원 영통에서 오래 살았습니다. 영통은 90년대 후반에 "
               "조성된 택지지구입니다."))
    b.append(B(card("custom", scene="gen1", html=SC.gen1_map(), anim=True),
               "1기 신도시는 아니고요, 분당·일산·평촌·산본·중동 다섯 곳이 "
               "1기입니다."))
    b.append(B(card("custom", scene="surge", html=SC.surge_card(), anim=True),
               "학군과 상권이 일찍 자리 잡은 동네였고, 여기 살면서 큰 "
               "변화를 두 번 겪었습니다."))

    # ── 광교 ─────────────────────────────────────────────────────────────
    CH("광교")
    b.append(B(card("title", sec="02", big="첫 번째,<br><b>광교</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B("A1_woncheon.png",
               "원천유원지가 있던 자리에 신도시가 들어선다고 했을 때, "
               "영통 사람들 반응은 차가웠습니다.", "none"))
    b.append(B("A1_woncheon.png",
               "\"그 땅에 누가 살겠냐\"는 거였죠. 주변에서 청약을 넣는 "
               "사람도 많지 않았습니다.", "none"))
    b.append(B(card("custom", scene="apt:gwanggyo", anim=True,
                    html=SC.apt_card(
                        FLAGS[0], kick="광교 대표 단지 · 30평대 중위 실거래가",
                        title="입주 첫해 <b>4.7억</b>에서 시작했습니다")),
               "광교 대표 단지인 자연앤힐스테이트는 2012년 입주 첫해 "
               "30평대가 4억 7천만원에 거래됐습니다."))
    b.append(B("06_apt.png",
               "지금은 18억 7천만원입니다. 14년 만에 네 배입니다.", "none"))
    b.append(B(card("custom", scene="reason:gwanggyo", anim=True,
                    html=SC.reason_card(
                        "나침반", "광교가 오른 이유",
                        "<b>세 가지</b>로 봅니다",
                        [("강남 접근성", "2016년 신분당선 연장 · 40분 안팎"),
                         ("일자리", "2019년 수원지법·지검 · 2021년 경기도청"),
                         ("생활 인프라", "광교호수공원 중심 상권")])),
               "광교가 오른 이유는 세 가지로 봅니다.", "still"))
    b.append(B("A2_shinbundang.png",
               "첫째, 강남 접근성입니다. 2016년 신분당선이 광교까지 "
               "이어지면서 강남까지 40분 안팎이 됐습니다.", "none"))
    b.append(B(card("custom", scene="inbound", anim=True,
                    html=SC.inbound_map()),
               "강남으로 출퇴근하던 수원 수요가 광교로 옮겨갔습니다.",
               "still"))
    b.append(B(card("plain", big="둘째, <b>일자리</b>",
                    cap="2019년 수원지법·지검 · 2021년 경기도청 신청사"),
               "둘째, 일자리입니다. 2019년 수원지방법원과 검찰청이, "
               "2021년 경기도청 신청사가 광교로 이전했습니다."))
    b.append(B(card("custom", scene="park", anim=True,
                    html=SC.park_card()),
               "경기도청이라는 안정적인 직장 수요가 생겼습니다. 셋째, "
               "생활 인프라입니다. 광교호수공원을 중심으로 상권이 촘촘하게 "
               "짜였습니다.", "still"))

    # ── 동탄 ─────────────────────────────────────────────────────────────
    CH("동탄")
    b.append(B(card("title", sec="03", big="두 번째,<br><b>동탄</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("plain", big='이번에도<br><em>"거기를 왜 가냐"</em>'),
               "영통보다 남쪽, 화성에 신도시가 생긴다고 했을 때도 반응은 "
               "같았습니다.", "still"))
    b.append(B("A4_dongtan_news.png",
               "동탄2신도시는 한동안 미분양이 쌓였고, 교통이 나쁜 곳에 왜 "
               "가냐는 시선이 많았습니다.", "none"))
    b.append(B("A4_dongtan_news.png",
               "지금은 어떨까요. 숫자를 정확히 보겠습니다.", "none"))
    b.append(B(card("custom", scene="cmp:n", anim=True,
                    html=SC.bars_anim(
                        SC.compare_rows(CMP, "n", lambda v: f"{v:,}건"),
                        kick="2026년 · 30평대 거래 건수",
                        title="동탄이 <b>가장 많이</b> 거래됩니다")),
               "2026년 화성 동탄에서 거래된 30평대는 2,779건입니다."))
    b.append(B(card("custom", scene="cmp:hi", anim=True,
                    html=SC.bars_anim(
                        SC.compare_rows(CMP, "hi", lambda v: f"{v:,}건"),
                        kick="2026년 · 30평대에서 10억을 넘은 거래",
                        title="<b>동탄과 광교</b>에서만 나옵니다",
                        note="나머지 네 곳은 30평대 10억 거래가 올해 "
                             "한 건도 없습니다. 동탄 중위값은 7억 6천만원."
                        )),
               "이 중 10억을 넘긴 거래가 600건, 다섯 건에 한 건입니다. "
               "중위값은 7억 6천만원이고요."))
    b.append(B(card("plain", big="\"흔하다\"고 하기엔<br>이르지만",
                    cap="10년 전을 생각하면 놀라운 숫자입니다"),
               "\"흔하다\"고 말하기는 아직 이르지만, 10년 전을 생각하면 "
               "놀라운 숫자입니다.", "still"))
    b.append(B(card("stat", dark=True, sec="동탄역 롯데캐슬 · 2026년 7월",
                    num="26.5억", cap="고층 · 35평대"),
               "그리고 동탄역 바로 앞 롯데캐슬에서는 올해 7월 "
               "26억 5천만원 거래가 나왔습니다."))
    b.append(B(card("custom", scene="reason:dongtan", anim=True,
                    html=SC.reason_card(
                        "나침반", "동탄도 같은 틀로",
                        "<b>세 가지</b>가 설명합니다",
                        [("일자리", "삼성 화성·기흥 · 평택 고덕 · SK 이천"),
                         ("강남 접근성", "2016 SRT · 2024 GTX-A · 수서 20분대"),
                         ("생활 인프라", "동탄호수공원 중심 상권")],
                        color=LOSE_C)),
               "동탄도 같은 세 가지 틀로 설명됩니다.", "still"))
    b.append(B(card("custom", scene="jobs", anim=True,
                    html=SC.jobs_map()),
               "일자리는 광교보다 강합니다. 바로 옆이 삼성전자 화성·기흥 "
               "캠퍼스고, 평택 고덕의 삼성과 이천의 SK하이닉스도 "
               "출퇴근권입니다.", "still"))
    b.append(B(card("plain", big="교통은 <b>늦게</b>,<br>대신 <b>빠르게</b>",
                    cap="2016년 SRT · 2024년 GTX-A · 수서까지 20분대"),
               "강남 접근성은 광교보다 약했지만 빠르게 좋아졌습니다. "
               "2016년 SRT, 2024년 GTX-A가 개통되면서 수서까지 20분대가 "
               "됐습니다."))
    b.append(B("C_GTX.png",
               "2028년 GTX 삼성역이 정식 개통되면 강남 한복판까지 "
               "연결됩니다. 생활 인프라로는 동탄호수공원과 그 주변 상권이 "
               "있습니다.", "none"))

    # ── 반례 ─────────────────────────────────────────────────────────────
    CH("반례")
    b.append(B(card("title", sec="04", dark=True,
                    big="그런데,<br><em>안 오른 신도시</em>도<br>있습니다"),
               "", "still", section=True, hold=1.8))
    b.append(B(card("plain",
                    big='"신도시는 결국<br>오른다"',
                    cap="저도 그렇게 정리하고 싶었습니다"),
               "여기까지 들으면 \"신도시는 처음엔 욕먹어도 결국 오른다\"고 "
               "정리하고 싶어집니다. 저도 그랬습니다.", "still"))
    b.append(B(card("plain", dark=True,
                    big="이건 <em>오른 곳만</em><br>골라 본 결론입니다"),
               "그런데 이건 오른 곳만 골라 본 결론입니다.", "still",
               hold=0.8))
    b.append(B(card("custom", scene="counter", html=SC.counter_map(), anim=True),
               "같은 2기 신도시인데 사정이 다른 곳이 있습니다. 인천 검단, "
               "김포 한강, 파주 운정, 양주 옥정입니다."))
    b.append(B("C_신도시관련.png",
               "이곳들도 초기에 미분양이 쌓였고, 언젠가 오를 거라는 기대가 "
               "있었습니다.", "still"))
    b.append(B(grow("level", name="g_level"),
               "지금은 세 배 가까이 벌어져 있습니다.", "in", hold=1.5))

    # ── 착시 ─────────────────────────────────────────────────────────────
    CH("착시")
    b.append(B(card("title", sec="05", dark=True,
                    big="숫자가<br><em>반대로</em> 나왔습니다"),
               "", "still", section=True, hold=1.8))
    b.append(B(card("plain", big="\"얼마나 올랐나\"로<br>줄을 세워보면",
                    cap="2015 → 2026 · 동네별 중위 평당가 상승률"),
               "자, 그러면 \"얼마나 올랐나\"로 줄을 세워보면 되겠죠. "
               "2015년부터 2026년까지, 동네별로 중위 평당가가 몇 퍼센트 "
               "올랐는지 계산했습니다."))
    b.append(B(grow("naive", name="g_naive"),
               "결과가 제 예상과 반대였습니다.", "in", hold=1.2))
    b.append(B(grow("naive", name="g_naive2", static=True),
               "부진하다고 생각했던 양주 옥정이 플러스 178%, 인천 검단이 "
               "124%입니다. 광교는 123%입니다.", "out"))
    b.append(B(card("plain", dark=True,
                    big="여기서 끝냈다면<br><em>틀린 이야기</em>를<br>"
                        "했을 겁니다"),
               "옥정과 검단이 광교보다 많이 올랐다는 뜻이 됩니다. 여기서 "
               "영상을 끝냈다면, 저는 틀린 이야기를 했을 겁니다.", "still",
               hold=1.0))

    # ── 왜 틀렸나 ────────────────────────────────────────────────────────
    CH("원인")
    b.append(B(card("title", sec="06", big="무엇이<br><b>잘못됐나</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("plain",
                    big="2026년에 거래된 집이<br>2015년과 "
                        "<em>같은 집이 아니다</em>"),
               "이유를 찾는 데 한참 걸렸습니다. 답은 2026년에 거래된 집이 "
               "2015년과 같은 집이 아니라는 것이었습니다.", "still"))
    b.append(B("03_mix.png",
               "검단에서 올해 거래된 30평대의 58%가 2020년 이후에 지은 새 "
               "아파트입니다. 검단 신도시 입주가 그때부터 "
               "본격화됐으니까요.", "none"))
    b.append(B(card("custom", scene="newold", anim=True,
                    html=SC.newold_card(MIX)),
               "새 아파트는 평당 2,341만원, 기존 아파트는 평당 "
               "1,245만원입니다.", "still"))

    b.append(B(card("custom", scene="mix", html=SC.mix_anim(MIX), anim=True),
               "새 집이 절반 넘게 섞이면 동네 중위값은 당연히 올라갑니다. "
               "기존에 살던 분들 집값이 오른 게 아닙니다.", "still"))
    b.append(B(card("plain", big="광교는 <b>0%</b>",
                    cap="옥정 70% · 운정 38% · 광교는 새로 지을 땅이 없습니다"),
               "옥정은 70%, 운정은 38%가 새 집이었습니다. 반대로 광교는 "
               "2026년 거래의 100%가 기존 단지입니다. 새로 지을 땅이 "
               "없으니까요."))
    b.append(B(card("plain", dark=True,
                    big="<em>같은 자</em>로 잰 게<br>아니었던 겁니다"),
               "같은 자로 잰 게 아니었던 겁니다.", "still", hold=1.0))

    # ── 다시 재면 ────────────────────────────────────────────────────────
    CH("다시 재기")
    b.append(B(card("title", sec="07", big="다시<br><b>재면</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("versus", sec="자를 바꿨습니다",
                    left={"tag": "바꾸기 전", "color": "#E5484D",
                          "title": "동네 전체<br>거래의 중위값",
                          "sub": "2026년에 거래된 집이<br>"
                                 "2015년과 같은 집이 아니다"},
                    right={"tag": "바꾼 뒤", "color": "#2F6FED",
                           "title": "두 해 다 거래된<br>같은 단지만",
                           "sub": "2019년과 2026년 둘 다<br>"
                                  "거래가 있었던 단지의 중앙값"}),
               "그래서 계산을 바꿨습니다. 2019년과 2026년, 두 해 모두 거래가 "
               "있었던 같은 단지만 남기고, 그 단지들이 얼마나 올랐는지 "
               "중앙값을 봤습니다."))
    b.append(B(grow("same", name="g_same"),
               "순서가 완전히 뒤집혔습니다.", "in", hold=1.4))
    b.append(B(grow("same", name="g_same2", static=True),
               "광교와 동탄은 수도권 평균 47%를 웃돌았고, 검단·옥정·김포·"
               "운정은 평균의 절반 수준입니다.", "out"))
    b.append(B(card("plain", big="처음 세웠던 기준이<br>"
                                 "<b>이제야 섭니다</b>"),
               "처음에 세웠던 기준이 이제야 데이터로 섭니다.", "still"))

    # ── 언제 갈렸나 ──────────────────────────────────────────────────────
    CH("시점")
    b.append(B(card("title", sec="08", big="언제<br><b>갈렸나</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("custom", scene="slope", anim=True,
                    html=SC.slope_anim(SPLIT)),
               "상승기에는 모두가 올랐습니다. 다만 광교·동탄은 97%에서 "
               "114%, 수도권 평균 88%보다 더 올랐고, 검단·김포·운정은 "
               "52%에서 73%로 덜 올랐습니다.", "still"))
    b.append(B(card("plain", dark=True,
                    big="진짜 차이는<br><em>2021년 이후</em>"),
               "진짜 차이는 2021년 이후입니다.", "still", hold=0.8))
    b.append(B(grow("peak", name="g_peak"),
               "광교와 동탄1은 고점을 지켰고, 동탄2는 6% 빠졌습니다. "
               "수도권 평균이 마이너스 1%니까 거의 제자리입니다.", "in"))
    b.append(B(grow("peak", name="g_peak2", static=True),
               "반면 운정은 마이너스 23%, 김포와 옥정은 마이너스 22%, "
               "검단은 마이너스 13%입니다.", "out"))
    b.append(B(card("plain", dark=True, big="<em>두 번</em> 벌어졌습니다",
                    cap="오를 때 덜 오르고, 내릴 때 더 내렸습니다"),
               "두 번 벌어진 겁니다. 오를 때 덜 오르고, 내릴 때 더 "
               "내렸습니다.", "still", hold=1.0))

    # ── 같은 동탄 ────────────────────────────────────────────────────────
    CH("같은 동탄")
    b.append(B(card("title", sec="09",
                    big="같은 동탄인데도<br><b>갈렸습니다</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("plain", big="동네끼리가 아니라<br>"
                                 "<b>같은 동탄 안에서</b>"),
               "지금까지는 동네끼리 비교했는데, 같은 동탄 안에서도 차이가 "
               "났습니다.", "still"))
    b.append(B(card("plain", big="교통도 일자리도<br>사실상 <b>같습니다</b>",
                    cap="같은 삼성 일자리권 · 같은 SRT · 같은 GTX"),
               "동탄1과 동탄2는 붙어 있습니다. 같은 삼성 일자리권이고, 같은 "
               "SRT·GTX를 씁니다. 교통도 일자리도 사실상 같습니다."))
    b.append(B(grow("peak", name="g_peak3", static=True),
               "그런데 2021년 고점 이후를 보면 동탄1은 플러스 2%, 동탄2는 "
               "마이너스 6%입니다.", "in"))
    b.append(B(card("units", sec="30평대 거래가 있는 단지 수",
                    rows=[("동탄1", 39, "#2F6FED"),
                          ("동탄2", 92, "#E5484D")]),
               "무엇이 달랐을까요. 단지 수입니다. 30평대 거래가 있는 단지를 "
               "세어보면 동탄1은 39개, 동탄2는 92개입니다."))
    b.append(B(card("custom", scene="movein", html=SC.movein_anim(MOVEIN), anim=True),
               "2.4배죠. 그중 81개가 2015년에서 2019년 사이에 한꺼번에 "
               "입주했습니다."))
    b.append(B(card("plain", big="남은 변수는<br><b>공급</b>이었습니다",
                    cap="공급이 많은 쪽이 조정기에 더 빠졌습니다"),
               "교통과 일자리를 똑같이 놓고 보니, 남은 변수는 공급이었습니다. "
               "그리고 공급이 많은 쪽이 조정기에 더 빠졌습니다."))
    b.append(B(card("plain", dark=True,
                    big="가장 <b>깨끗한 증거</b>",
                    cap="다른 조건이 같은 두 곳을 비교할 수 있었으니까요"),
               "이게 아까 말씀드린 세 번째 기준, 주변 공급이 브레이크라는 "
               "이야기의 가장 깨끗한 증거입니다.", "still"))

    # ── 무엇이 갈랐나 ────────────────────────────────────────────────────
    CH("결론")
    b.append(B(card("title", sec="10", big="무엇이<br><b>갈랐나</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("custom", scene="direction", html=SC.direction_map(), anim=True),
               "지도를 보면 눈에 들어오는 게 있습니다. 성공한 쪽은 전부 "
               "서울 남쪽이고, 부진한 쪽은 서쪽과 북쪽입니다.", "still"))
    b.append(B(card("custom", scene="direction:static", html=SC.direction_map(static=True)),
               "거리의 문제가 아닙니다. 광교에서 강남까지와 검단에서 "
               "강남까지는 직선거리로 비슷합니다.", "still"))
    b.append(B(card("plain", dark=True,
                    big="그 방향에<br><b>강남으로 가는 길</b>이<br>"
                        "있느냐"),
               "갈린 건 그 방향에 강남으로 가는 길이 있느냐였습니다.",
               "still", hold=0.8))
    b.append(B("C_GTX2.png",
               "먼저 강남 접근성입니다. 운정에도 GTX-A가 들어왔지만, 이 "
               "노선은 서울역으로 갑니다. 강북 도심이지 강남이 아닙니다.", "none"))
    b.append(B(card("plain", big="검단과 옥정은<br>지금도 <em>한 시간 +</em>",
                    cap="강남까지"),
               "검단과 옥정은 지금도 강남까지 한 시간이 훌쩍 넘습니다.",
               "still"))
    b.append(B(card("plain", big="운정 옆에는<br>"
                                 "<b>LG디스플레이 파주</b>",
                    cap="큰 일자리가 있는데도 가격은 부진했습니다"),
               "다음은 일자리입니다. 흥미로운 곳이 운정입니다. 바로 옆에 "
               "LG디스플레이 파주 사업장이라는 큰 일자리가 있는데도 가격은 "
               "부진했습니다."))
    b.append(B(card("plain", dark=True,
                    big="일자리 하나만으로는<br><em>부족합니다</em>"),
               "일자리 하나만으로는 부족하다는 뜻입니다.", "still",
               hold=0.8))
    b.append(B("C_신도시_결사반대.png",
               "마지막은 주변 공급입니다. 2019년 고양 창릉이 3기 신도시로 "
               "발표되자, 운정·일산·검단 주민들이 집값 하락을 걱정하며 "
               "집회까지 열었습니다.", "none"))
    b.append(B("C_신도시_결사반대.png",
               "운정 행정복지센터 앞에 500여 명이 모였고, 3기 발표 후 첫 "
               "반대 집회였습니다.", "none"))
    b.append(B("C_양주옥정_미달.png",
               "옆에 대규모 공급이 계속 나오면 기다림이 길어집니다.",
               "still"))
    b.append(B(card("steps", sec="정리하면",
                    items=["강남 <b>교통</b>", "<b>일자리</b>",
                           "주변 <em>공급</em>은 브레이크"]),
               "정리하면 이렇습니다. 강남으로 가는 교통이 가장 강하게 "
               "작용했고, 일자리는 그다음, 주변 공급은 브레이크 역할을 "
               "했습니다.", "still", hold=1.2))

    # ── 한계 ─────────────────────────────────────────────────────────────
    CH("한계")
    b.append(B(card("title", sec="11", dark=True,
                    big="다만, 이건<br><em>여섯 사례</em>에서<br>"
                        "뽑은 패턴입니다"),
               "", "still", section=True, hold=1.8))
    b.append(B(card("plain", big="인과로 검증된 게<br><em>아닙니다</em>",
                    cap="사례가 여섯이면 우연일 수 있습니다"),
               "솔직하게 말씀드리면 이 순위는 인과로 검증된 게 아닙니다. "
               "여섯 곳을 놓고 공통점을 찾은 것이고, 사례가 여섯이면 우연일 "
               "수 있습니다."))
    b.append(B(card("plain", big="반대 시각도<br>있습니다",
                    cap="운정은 GTX-A 개통 뒤 인구가 늘고 있다는 분석"),
               "반대 시각도 있습니다. 운정은 GTX-A 개통 뒤 인구가 늘고 "
               "있다는 분석이 있습니다.", "still"))
    b.append(B(card("plain", big="교통의 <b>종류</b>가 아니라<br>"
                                 "<b>시점</b>이었다면",
                    cap="2028년 삼성역 정차 이후 운정이 오른다면"),
               "2028년 삼성역 정차가 시작되고 나서 운정이 오른다면, 부진의 "
               "원인은 교통의 종류가 아니라 시점이었다는 뜻이 됩니다."))
    b.append(B(card("plain", dark=True,
                    big="오늘 세운 기준은<br><em>가설</em>입니다",
                    cap="맞는지는 시간이 지나봐야 압니다"),
               "그래서 오늘 세운 기준은 가설입니다. 맞는지는 시간이 지나봐야 "
               "압니다.", "still", hold=1.0))

    # ── 질문 ─────────────────────────────────────────────────────────────
    CH("질문")
    b.append(B(card("title", sec="12", big="그래서<br>생긴 <b>질문</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("plain", dark=True,
                    big="지금 내가<br><em>못 보고 있는 곳</em>은<br>"
                        "어디일까"),
               "두 번을 겪고 나니 질문이 하나 생겼습니다. 지금 제가 못 보고 "
               "있는 곳은 어디일까.", "still", hold=1.0))
    b.append(B(card("plain", big="돌아보는 대신<br><b>미리 골라보자</b>"),
               "이번에는 오른 곳을 돌아보는 대신, 이 기준에 맞는 곳을 미리 "
               "데이터로 골라보려고 합니다.", "still"))

    # ── 후보 ─────────────────────────────────────────────────────────────
    CH("후보")
    b.append(B(card("title", sec="13", big="후보<br><b>네 곳</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B("A7_gen2_gen3.png",
               "이 기준으로 추린 후보는 네 곳입니다.", "none", hold=1.0))
    b.append(B("C_송파하남선.png",
               "하남 교산. 3호선 연장선이 2032년 개통을 목표로 하고 있고, "
               "강남고속터미널까지 40분대가 예상됩니다. 3기 중 강남에 가장 "
               "가깝습니다.", "none"))
    b.append(B("C_GTX4.png",
               "고양 창릉. GTX-A 창릉역이 생깁니다. 2028년 삼성역 정차가 "
               "시작되면 강남 직결이 됩니다. 다만 오늘 본 운정과 같은 "
               "노선입니다.", "none"))
    b.append(B(card("plain", big="③ <b>남양주 왕숙</b>",
                    cap="GTX-B · 9호선 연장 · 3기 최대 약 8만 가구 · "
                        "자체 물량이 곧 브레이크"),
               "남양주 왕숙. GTX-B와 9호선 연장이 지나갑니다. 3기 최대 규모, "
               "약 8만 가구입니다. 자체 물량이 곧 브레이크일 수 있습니다."))
    b.append(B("C_용인_반도체.png",
               "용인 이동. 삼성전자 반도체 국가산단 바로 옆 배후 "
               "신도시입니다. 2030년 첫 입주가 목표고, 오늘 본 동탄 모델이 "
               "반복될지가 관건입니다.", "none"))
    b.append(B("C_입주_카운트다운.png",
               "다만 한 가지 짚고 가겠습니다. 3기 신도시는 그 자체가 대규모 "
               "공급입니다. 오늘 본 브레이크가 이 도시들에도 걸릴 수 "
               "있습니다.", "none"))

    # ── 예고 ─────────────────────────────────────────────────────────────
    CH("예고")
    b.append(B(card("title", sec="14", big="다음 영상<br><b>예고</b>"),
               "", "still", section=True, hold=1.6))
    b.append(B(card("plain", big="한 곳씩<br>다뤄보겠습니다",
                    cap="완성됐을 때의 모습 · 출퇴근 일자리 · "
                        "강남 교통이 언제 좋아지는지"),
               "다음 영상부터 한 곳씩 다뤄보겠습니다. 완성됐을 때의 모습, "
               "출퇴근 가능한 일자리, 강남 교통이 언제 어떻게 좋아지는지를 "
               "데이터로 확인하겠습니다."))
    b.append(B(card("plain", dark=True,
                    big="틀렸으면<br><em>틀렸다고</em><br>말씀드리겠습니다",
                    cap="오늘 세운 기준은 시간이 지난 뒤 다시 채점합니다"),
               "그리고 오늘 세운 기준이 맞았는지는 시간이 지난 뒤 이 "
               "채널에서 다시 채점하겠습니다. 틀렸으면 틀렸다고 "
               "말씀드리겠습니다."))
    # CC BY 는 상업적 이용이 되지만 **출처 표기가 의무**다. 설명란에만
    # 적고 끝내지 않고 화면에도 남긴다 — 사진·AI 이미지와 같은 규칙이다.
    b.append(B(card("plain", big="국토교통부<br>실거래가 공개시스템",
                    cap="계산 방법은 영상 설명란에 · 경계 통계청 SGIS<br>"
                        "음악 Thinking Music — Kevin MacLeod "
                        "(incompetech.com, CC BY 4.0)"),
               "오늘 쓴 데이터는 국토교통부 실거래가 공개시스템 자료고, "
               "계산 방법은 영상 설명란에 적어두겠습니다."))
    b.append(B(card("plain", big="특정 지역 매수를<br>권하는 내용이 "
                                 "<em>아닙니다</em>",
                    cap="판단은 각자의 몫입니다"),
               "이 영상은 특정 지역 매수를 권하는 내용이 아닙니다. 판단은 "
               "각자의 몫입니다.", "still"))
    b.append(B(card("title", sec="", big="구독하고<br>기다려 주세요",
                    cap=""),
               "다음 편이 궁금하시면 구독하고 기다려 주세요. 감사합니다.",
               "still", hold=2.0))
    to_emoji()
    return b


def main() -> int:
    ap = argparse.ArgumentParser(description="신도시 1편 영상")
    ap.add_argument("--cards", action="store_true", help="카드만 다시 만든다")
    ap.add_argument("--plan", action="store_true", help="길이만 계산")
    ap.add_argument("--no-subs", action="store_true",
                    help="하단 자막 띠 없이 (직접 얹으실 때)")
    ap.add_argument("--voice", action="store_true",
                    help="TTS 음성 초안을 만들고 그 길이로 장면을 맞춘다")
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()

    bs = beats()
    if a.voice:
        from content import voice as VO
        print(f"  음성 만드는 중... ({sum(1 for b in bs if b.text)}토막)")
        got = VO.speak([b.text for b in bs], VOICE_DIR)
        for b, g in zip(bs, got):
            b.audio, b.adur = g["path"], g["dur"]
    total = sum(b.measure() for b in bs)
    mm, ss = divmod(int(total), 60)
    bar = "=" * 62
    print(f"\n{bar}\n  신도시 1편  장면 {len(bs)}개 · "
          f"{mm}분 {ss}초\n{bar}")
    narr = sum(len("".join(b.text.split())) for b in bs)
    print(f"  내레이션 {narr:,}자 · 카드 {len(_cards)}장 · "
          f"그래픽 {sum(1 for b in bs if b.visual.endswith('.png') and not b.visual.startswith('cards/'))}회 인용")
    if a.plan:
        return 0

    # 순차 점등 카드는 48장을 11초에 걸쳐 쓰고 있었다 — 한 장이 7프레임씩
    # 걸려 뚝뚝 끊겼다. 장면 길이에 맞춰 다시 센다.
    LV.fit_anim(bs, _cards)
    print(f"\n  카드 {len(_cards)}장 만드는 중...")
    card_frames = LV.build_cards(_cards, CARDS, css=SC.css())
    print("  테두리 만드는 중...")
    chrome = FR.build(CHAPTERS, FRAMES, ep="신도시 시리즈 · ",
                      source="국토교통부 실거래가 · 해제 건 제외")
    if a.cards:
        return 0

    subs = {}
    if not a.no_subs:
        print("  자막 띠 만드는 중...")
        subs = LV.build_subs(bs, SUBS)
    print("  영상 만드는 중...")
    music = None if (a.no_music or not MUSIC.exists()) else MUSIC
    out = LV.render(bs, ART, OUT, chrome, subs, card_frames, music=music)
    srt = LV.write_srt(bs, OUT.with_suffix(".srt"))
    cue = LV.cue_sheet(bs, ROOT / "docs" / "longform" /
                       "2026-10-10-newtown-1-cue.md")
    print(f"\n  영상  {out}  ({out.stat().st_size / 1e6:.0f}MB)")
    print(f"  자막  {srt}")
    print(f"  큐시트 {cue}")
    print(f"{bar}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
