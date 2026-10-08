"""텔레그램 봇 — 아침에 단지 후보를 보내고, 고르면 영상을 만들어 돌려준다.

흐름
    아침     후보 5곳 전송 (단지·금액·표본)
    사람     "3" 한 글자
    봇       프로필 생성 → 덱 재료 → 검증 → 렌더 → mp4 + 캡션 전송

왜 롱폴링인가
    웹훅은 공개 URL 이 있어야 한다. 집 데스크톱에 포트를 열 이유가 없다.
    텔레그램은 getUpdates 를 길게 붙잡아 주는 방식을 지원하므로, 상주
    프로세스 하나로 끝난다.

**allowlist 를 반드시 건다.** 봇 이름만 알면 누구나 말을 걸 수 있다.
/build 는 이 PC 에서 파이썬을 돌리는 명령이라, 모르는 사람이 부를 수 있으면
안 된다. 허용된 chat_id 가 아니면 조용히 버린다 — 답을 주면 봇이 살아 있다는
것만 알려 주는 꼴이다.

영상 한 편은 1~2분 걸린다. 그동안 들어온 메시지를 잃지 않으려고 offset 을
파일에 남기고, 만드는 중에는 새 작업을 받지 않는다.

실행:
  .venv\\Scripts\\python.exe -m notify.bot
  .venv\\Scripts\\python.exe -m notify.bot --morning   # 후보만 보내고 끝
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import ledger as LD  # noqa: E402
from content import reels as R  # noqa: E402
from notify import telegram as TG  # noqa: E402

POLL_TIMEOUT = 50          # getUpdates 를 붙잡아 두는 시간 (초)
STATE = ROOT / "output" / "bot_state.json"
LOG = ROOT / "logs" / "bot.log"
NL = chr(10)


def to_log() -> None:
    """작업 스케줄러로 뜨면 콘솔이 없다.

    pythonw 에 콘솔이 붙지 않으면 sys.stdout 이 None 이 되고, print 한 줄에
    AttributeError 로 죽는다. 상주 프로세스가 첫 메시지에서 조용히 사라지는
    셈이다. 어차피 로그 없이는 왜 죽었는지도 알 수 없으니 파일로 돌린다.
    """
    LOG.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None or not sys.stdout.isatty():
        sys.stdout = sys.stderr = fh
    print(f"{NL}--- {datetime.now():%Y-%m-%d %H:%M:%S} 시작 ---")

HELP = """쓸 수 있는 것
/today   오늘 단지 후보 5곳
1~5      그 번호로 영상 만들기
/again   마지막에 만든 영상 다시 보내기
/carousel 캐러셀 6장 (피드용)
/thread  스레드 본문
/all     영상+캐러셀+스레드 한 번에

/단지 래미안   이름으로 찾기 (오늘 신고가 목록 안에서)
/예산 6       "6억이면 어디 살 수 있나" 지도
/평형        같은 단지 다른 평형으로

/done    올렸다고 기록 (다음 회차에 그 지역을 피합니다)
/skip    안 올렸다고 기록 (다시 권해도 됩니다)
/log     최근 발행 기록

/help    이 안내

후보를 받은 뒤 번호만 보내면 됩니다. 한 편에 1~2분 걸려요."""


# ── 상태 ─────────────────────────────────────────────────────────────────
def load() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2),
                     encoding="utf-8")


def allowed(chat_id) -> bool:
    """허용된 사람인가. 설정된 chat_id 하나만 받는다."""
    want = TG.creds()[1]
    return bool(want) and str(chat_id) == str(want)


# ── 지표·후보 ────────────────────────────────────────────────────────────
def metrics() -> dict | None:
    """지표 JSON. 봇의 모든 길이 여기를 지난다.

    이름 정규화를 여기서 한 번에 한다. carousel.pick() 은 자기 입구에서
    하지만 thread.generate() 는 안 하므로, 영상은 "신트리 4단지"인데
    스레드만 "신트리4" 로 나갔다.
    """
    from content import aptname as AN
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        return None
    return AN.normalize(json.loads(files[-1].read_text(encoding="utf-8")))


def candidates(data: dict) -> list[dict]:
    from content import briefing as B
    return B.apt_candidates(data)


def card(i: int, c: dict) -> str:
    bits = [f'{i}. {c["apt_name"]}  ({c["region"]} {c["dong"]})'.rstrip(),
            f'   {c["pyeong"]} · {c["amount"]} · 종전 최고가 +{c["over"]}%']
    tail = f'   누적 {c["hist"]:,}건'
    if c.get("deals_1y"):
        tail += f' · 1년 {c["deals_1y"]}건'
    bits.append(tail)
    return NL.join(bits)


def morning(quiet: bool = False) -> bool:
    """아침 후보 전송. 보낼 게 없으면 그 사실을 보낸다."""
    data = metrics()
    if not data:
        TG.send("지표 파일이 없습니다. 먼저 수집·지표를 돌려야 합니다.")
        return False
    cands = candidates(data)
    if not cands:
        TG.send(f'[{data["asof"]}] 오늘은 표본을 넘긴 단지 후보가 없습니다.')
        return False

    st = load()
    st["asof"] = data["asof"]
    st["candidates"] = [{k: v for k, v in c.items() if k != "row"}
                        for c in cands]
    st["rows"] = [c["row"] for c in cands]
    st["sent_at"] = datetime.now().isoformat(timespec="seconds")
    save(st)

    head = f'오늘의 단지 후보 ({data["asof"]} 기준)'
    body = (NL + NL).join(card(i, c) for i, c in enumerate(cands, 1))
    tail = "번호를 보내면 그 단지로 영상을 만들어 드립니다. (1~2분)"
    return TG.send(NL.join([head, "", body, "", tail]), quiet=quiet)


# ── 만들기 ───────────────────────────────────────────────────────────────
def make(n: int) -> None:
    """n 번 후보로 영상을 만들어 보낸다. 실패해도 **왜** 인지 보낸다."""
    st = load()
    rows, cands = st.get("rows") or [], st.get("candidates") or []
    if not rows:
        TG.send("후보 목록이 없습니다. /today 를 먼저 보내 주세요.")
        return
    if not 1 <= n <= len(rows):
        TG.send(f"1~{len(rows)} 사이로 보내 주세요.")
        return

    row, info = rows[n - 1], cands[n - 1]
    TG.send(f'{info["apt_name"]} ({info["region"]}) 로 만들겠습니다. '
            f'1~2분 걸려요.', quiet=True)

    try:
        from content import cover as CV
        from content import reels as R
        from metrics.build_metrics import profile_for

        data = metrics()
        if not data or data["asof"] != st.get("asof"):
            TG.send("지표가 그 사이 바뀌었습니다. /today 로 후보를 다시 받아 주세요.")
            return

        # 프로필은 매주 8개만 미리 만든다. 고른 단지가 그 밖이면 여기서 뽑는다.
        if not profile_for(data, row):
            TG.send(f'{info["apt_name"]} 는 소개 재료가 모자랍니다 '
                    f'(월별 기록·이웃 단지). 다른 번호를 골라 주세요.')
            return

        key = f'{row["apt_id"]}:{row["pyeong_bucket"]}'
        cand = next((c for c in CV.build(data)
                     if f'{c.data.get("apt_id")}:'
                        f'{c.data.get("pyeong_bucket")}' == key), None)
        if cand is None:
            TG.send(f'{info["apt_name"]} 는 표지 기준(표본·재료)을 넘지 '
                    f'못했습니다. 다른 번호를 골라 주세요.')
            return

        outdir = ROOT / "output" / data["asof"]
        outdir.mkdir(parents=True, exist_ok=True)
        out = R.build(data, outdir, force=cand)
        if out is None:
            TG.send("만들 재료가 모자랐습니다.")
            return

        st["last"] = str(out)
        st["last_label"] = f'{info["apt_name"]} ({info["region"]})'
        # /done 이 무엇을 기록할지 알아야 한다. 라벨만으로는 모자라다.
        st["last_info"] = {k: info.get(k) for k in
                           ("key", "apt_name", "region", "pyeong")}
        st["last_asof"] = data["asof"]
        save(st)

        cap = caption(data, cand)
        TG.send_file(out, f'{info["apt_name"]} · {info["region"]} · '
                          f'{info["pyeong"]} {info["amount"]}', quiet=True)
        if cap:
            TG.send(cap, quiet=True)
        TG.send("올리실 때 캡션은 위 문구를 그대로 쓰시면 됩니다.", quiet=True)
    except Exception as e:
        # 검증에 걸린 것과 터진 것을 가른다. 앞은 내용 문제, 뒤는 코드 문제다.
        TG.send(f"만들다 막혔습니다 — {TG.mask(str(e) or type(e).__name__)}")
        traceback.print_exc()


def caption(data: dict, cand) -> str:
    try:
        from content.caption import reels_caption
        from content.carousel import pick
        return reels_caption(pick(data, force=cand))
    except Exception as e:
        print(f"  캡션 생성 실패 ({type(e).__name__})")
        return ""


# ── 예산 지도 ────────────────────────────────────────────────────────────
def budget_map(cap: float) -> None:
    """"N억이면 어디 살 수 있나" 한 편.

    단지 덱과 **다른 아젠다**다. 단지 소개는 그 단지를 아는 사람에게만 뜻이
    통하는데, 릴스는 모르는 사람에게 노출되는 매체다. 예산은 설명이 필요
    없고 보는 사람 모두가 자기 숫자를 갖고 있다.
    """
    from content import budget as BG
    if not 1 <= cap <= 50:
        TG.send("예산은 1~50억 사이로 보내 주세요. 예: /예산 6", quiet=True)
        return
    TG.send(f"{cap:g}억 기준으로 지도를 그리겠습니다. 1~2분 걸려요.",
            quiet=True)
    try:
        b = BG.compute(int(round(cap * 10000)))
        if not b["rows"]:
            TG.send("표본을 넘긴 시군구가 없습니다.", quiet=True)
            return
        scs = BG.scenes(b)
        outdir = ROOT / "output" / b["asof"]
        outdir.mkdir(parents=True, exist_ok=True)
        out = R.render(scs, outdir)
        final = outdir / f'budget_{b["cap_label"]}.mp4'
        out.replace(final)

        st = load()
        st["last"] = str(final)
        st["last_label"] = f'예산 지도 {b["cap_label"]}'
        # 예산 지도는 단지가 없다. 발행 기록은 단지 기준이라 비워 둔다 —
        # 안 비우면 직전에 만든 단지가 올린 것으로 잘못 기록된다.
        st.pop("last_info", None)
        st.pop("last_asof", None)
        save(st)

        none_n, all_n = len(b["none"]), len(b["all_"])
        head = (f'{b["cap_label"]} 기준 · {b["pyeong_label"]} · '
                f'최근 {b["months"]}개월')
        lines = [head, "",
                 f'거의 전부 살 수 있는 곳 {all_n}곳',
                 f'한 건도 없는 곳 {none_n}곳']
        for r in b["none"][:3]:
            lines.append(f'  · {r["sigungu_name"]} '
                         f'(0/{r["deals"]:,}건)')
        TG.send_file(final, head, quiet=True)
        TG.send(NL.join(lines), quiet=True)
    except Exception as e:
        TG.send(f"예산 지도에서 막혔습니다 — "
                f"{TG.mask(str(e) or type(e).__name__)}")
        traceback.print_exc()


# ── 후보 밖 찾기 ─────────────────────────────────────────────────────────
def offer(cands: list[dict], head: str) -> None:
    """찾은 것을 번호와 묶어 내놓는다. 상태를 덮어써야 번호가 통한다."""
    st = load()
    data = metrics()
    st["asof"] = data["asof"]
    st["candidates"] = [{k: v for k, v in c.items() if k != "row"}
                        for c in cands]
    st["rows"] = [c["row"] for c in cands]
    save(st)
    body = (NL + NL).join(card(i, c) for i, c in enumerate(cands, 1))
    TG.send(NL.join([head, "", body, "", "번호를 보내면 만들어 드립니다."]),
            quiet=True)


def find(term: str) -> None:
    from content import briefing as B
    data = metrics()
    if not data:
        TG.send("지표 파일이 없습니다.", quiet=True)
        return
    got = B.search_apts(data, term)
    if not got:
        TG.send(f'"{term}" 로 찾은 단지가 없습니다.{NL}'
                f'오늘 신고가 목록 안에서만 찾습니다 — 덱 첫 장이 '
                f'"종전 최고가"라서, 신고가가 아닌 단지로 만들면 그 문구가 '
                f'거짓이 됩니다.', quiet=True)
        return
    offer(got, f'"{term}" 로 찾은 단지 {len(got)}곳')


def other_pyeongs() -> None:
    """같은 단지 다른 평형. 둘이 같은 날 신고가를 치는 일이 있다."""
    from content import briefing as B
    st = load()
    info = st.get("last_info")
    data = metrics()
    if not (info and data):
        TG.send("먼저 번호를 보내 주세요.", quiet=True)
        return
    apt_id = str(info.get("key", "")).split(":")[0]
    got = B.pyeongs_of(data, apt_id)
    if len(got) < 2:
        TG.send(f'{info.get("apt_name")} 는 오늘 신고가가 '
                f'{len(got)}개 평형뿐입니다.', quiet=True)
        return
    offer(got, f'{got[0]["apt_name"]} 의 평형 {len(got)}개')


# ── 발행 패키지 (T17) ────────────────────────────────────────────────────
def resolve(st: dict):
    """마지막에 고른 단지로 (지표, Candidate, info) 를 되살린다.

    캐러셀·스레드도 **같은 단지**로 나와야 한다. 각자 자동 선정을 돌리면
    영상은 양천구인데 캐러셀은 다른 구가 되는 일이 생긴다.
    """
    from content import cover as CV
    from metrics.build_metrics import profile_for

    info, asof = st.get("last_info"), st.get("last_asof")
    rows_, cands = st.get("rows") or [], st.get("candidates") or []
    if not (info and asof):
        return None, None, None
    data = metrics()
    if not data or data["asof"] != asof:
        return None, None, None
    # 이름이 아니라 **키**로 찾는다. 한 단지가 평형 둘로 올라오는 날이
    # 있고(병점역아이파크캐슬 20·30평대), 이름으로 맞추면 엉뚱한 평형의
    # 캐러셀이 영상과 다른 숫자를 들고 나간다.
    row = next((r for i, r in enumerate(rows_)
                if i < len(cands)
                and cands[i].get("key") == info.get("key")), None)
    if row is None or not profile_for(data, row):
        return None, None, None
    cand = next((c for c in CV.build(data)
                 if f'{c.data.get("apt_id")}:{c.data.get("pyeong_bucket")}'
                 == info.get("key")), None)
    return data, cand, info


def send_carousel() -> None:
    """캐러셀 6장. 피드에도 올리실 수 있게."""
    from content import carousel as C
    st = load()
    data, cand, info = resolve(st)
    if cand is None:
        TG.send("먼저 번호를 보내 영상을 만들어 주세요.", quiet=True)
        return
    TG.send("캐러셀 6장을 만들겠습니다. 1분쯤 걸려요.", quiet=True)
    try:
        outdir = ROOT / "output" / data["asof"]
        cards = C.build_cards(data, outdir, force=cand)
        if not cards:
            TG.send("캐러셀 재료가 모자랐습니다.", quiet=True)
            return
        made, problems = C.render(cards, outdir, cand.data.get("params") or {})
        for p in made:
            TG.send_file(p, "", quiet=True)
        msg = f'{info["apt_name"]} 캐러셀 {len(made)}장'
        if problems:
            msg += f'{NL}넘침 경고 {len(problems)}건 — PC 에서 확인하세요'
        TG.send(msg, quiet=True)
    except Exception as e:
        TG.send(f"캐러셀에서 막혔습니다 — {TG.mask(str(e) or type(e).__name__)}")
        traceback.print_exc()


def send_thread() -> None:
    """스레드 본문. 검증을 통과한 것만 보낸다."""
    from content import thread as TH
    st = load()
    data, cand, info = resolve(st)
    if cand is None:
        TG.send("먼저 번호를 보내 영상을 만들어 주세요.", quiet=True)
        return
    try:
        items = TH.generate("new_high", data, 1, force=cand)
        ok = [r for r in items if r.get("ok")]
        if not ok:
            why = NL.join(f'· {w}' for r in items for w in r.get("reasons", []))
            TG.send(f'스레드가 검증에 걸렸습니다.{NL}{why}', quiet=True)
            return
        for r in ok:
            TG.send(r["text"], quiet=True)
    except Exception as e:
        TG.send(f"스레드에서 막혔습니다 — {TG.mask(str(e) or type(e).__name__)}")
        traceback.print_exc()


def send_all() -> None:
    """영상 + 캐러셀 + 캡션 + 스레드. 폰에서 그대로 올리실 수 있게."""
    st = load()
    last = st.get("last")
    if last and Path(last).exists():
        TG.send_file(last, st.get("last_label", ""), quiet=True)
    send_carousel()
    send_thread()
    TG.send("다 보냈습니다. 올리신 뒤 /done 을 보내 주세요.", quiet=True)


# ── 발행 기록 ────────────────────────────────────────────────────────────
def mark(status: str) -> None:
    """마지막에 만든 것을 올렸는지 기록한다.

    수동 업로드라서 올렸다는 사실은 사람만 안다. 이 한 줄이 없으면 다음 주
    중복 방지가 아무 일도 못 한다 — 같은 지역을 연달아 권하게 된다.
    """
    st = load()
    info, asof = st.get("last_info"), st.get("last_asof")
    if not (info and asof):
        TG.send("아직 만든 게 없습니다. 번호를 먼저 보내 주세요.", quiet=True)
        return
    LD.record(asof, info, status)
    if status == LD.PUBLISHED:
        TG.send(f'기록했습니다 — {info["apt_name"]} ({info["region"]}).{NL}'
                f'다음 회차 표지에서 {info["region"]} 는 빼겠습니다.', quiet=True)
    else:
        TG.send(f'건너뜀으로 기록했습니다 — {info["apt_name"]}. '
                f'다시 권해도 됩니다.', quiet=True)


def show_log(n: int = 8) -> None:
    rs = LD.recent(n)
    if not rs:
        TG.send("아직 발행 기록이 없습니다.", quiet=True)
        return
    lines = []
    for r in rs:
        mk = "올림" if r.get("status") == LD.PUBLISHED else "건너뜀"
        lines.append(f'{r.get("asof")}  {r.get("apt_name")} '
                     f'({r.get("region")}) — {mk}')
    blocked = LD.regions(2)
    tail = (f'{NL}다음 회차에 피할 지역: {", ".join(sorted(blocked))}'
            if blocked else "")
    TG.send("최근 발행 기록" + NL + NL.join(lines) + tail, quiet=True)


# ── 받기 ─────────────────────────────────────────────────────────────────
def handle(text: str) -> None:
    t = (text or "").strip()
    low = t.lower()
    if low in ("/start", "/help", "도움말"):
        TG.send(HELP, quiet=True)
    elif low in ("/today", "/후보", "후보"):
        morning(quiet=True)
    elif low == "/again":
        st = load()
        last = st.get("last")
        if last and Path(last).exists():
            TG.send_file(last, st.get("last_label", ""), quiet=True)
        else:
            TG.send("아직 만든 영상이 없습니다.", quiet=True)
    elif low.startswith(("/예산", "/budget")):
        part = t.split(maxsplit=1)
        if len(part) < 2:
            TG.send("예: /예산 6  (6억으로 어디 살 수 있나)", quiet=True)
        else:
            try:
                budget_map(float(part[1].replace("억", "").strip()))
            except ValueError:
                TG.send("숫자로 보내 주세요. 예: /예산 6", quiet=True)
    elif low.startswith(("/단지", "/find", "/찾기")):
        term = t.split(maxsplit=1)
        if len(term) < 2:
            TG.send("예: /단지 래미안", quiet=True)
        else:
            find(term[1])
    elif low in ("/평형", "/pyeong"):
        other_pyeongs()
    elif low in ("/carousel", "/캐러셀"):
        send_carousel()
    elif low in ("/thread", "/스레드"):
        send_thread()
    elif low in ("/all", "/전부"):
        send_all()
    elif low in ("/done", "/올림", "올림"):
        mark(LD.PUBLISHED)
    elif low in ("/skip", "/건너뜀"):
        mark(LD.SKIPPED)
    elif low == "/log":
        show_log()
    elif t.isdigit():
        make(int(t))
    else:
        TG.send(f"무슨 뜻인지 몰랐습니다.{NL}{NL}{HELP}", quiet=True)


def serve() -> int:
    """롱폴링 루프. Ctrl-C 로 멈춘다."""
    tok, cid = TG.creds()
    if not (tok and cid):
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 필요하다")
        return 1
    info = TG.me(tok)
    if not info.get("ok"):
        return 1
    print(f"봇 @{info['result'].get('username')} 대기 중 "
          f"(허용 chat_id {cid}) — Ctrl-C 로 종료")

    st = load()
    offset = st.get("offset", 0)
    while True:
        res = TG._post("getUpdates", tok, data={
            "offset": offset, "timeout": POLL_TIMEOUT})
        if not res.get("ok"):
            print(f"  수신 실패 — {TG.explain(res)}")
            continue
        for up in res.get("result") or []:
            offset = max(offset, up["update_id"] + 1)
            st = load()
            st["offset"] = offset
            save(st)
            msg = up.get("message") or up.get("edited_message") or {}
            chat = (msg.get("chat") or {}).get("id")
            if not allowed(chat):
                # 답하지 않는다. 답하면 봇이 살아 있다는 것만 알려 준다.
                print(f"  허용되지 않은 chat_id {chat} — 무시")
                continue
            text = msg.get("text") or ""
            print(f"  받음: {text[:40]}")
            try:
                handle(text)
            except Exception:
                traceback.print_exc()


def main() -> int:
    ap = argparse.ArgumentParser(description="텔레그램 봇")
    ap.add_argument("--morning", action="store_true",
                    help="후보만 한 번 보내고 끝 (작업 스케줄러용)")
    a = ap.parse_args()
    try:
        to_log()
    except Exception:
        pass
    if a.morning:
        return 0 if morning() else 1
    try:
        return serve()
    except KeyboardInterrupt:
        print("\n종료")
        return 0


if __name__ == "__main__":
    sys.exit(main())
