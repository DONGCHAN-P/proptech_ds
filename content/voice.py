"""내레이션 — 대본 다듬기와 음성 초안.

왜 필요한가
    12분짜리에 소리가 없었다. 자막만 뜨는 무음 영상은 그림이 아무리
    좋아도 **초안으로 읽힌다.** 그리고 장면 길이를 글자 수(초당 5.6자)로
    어림잡고 있어서, 실제로 읽으면 그림과 말이 어긋난다.

두 가지를 한다
    polish()  대본을 GPT 와 함께 다듬는다. **숫자와 단지명은 손대지
              않는다** — 말맛을 고치자고 사실을 바꾸면 안 된다.
              고친 뒤 숫자가 그대로인지 기계로 검사한다.
    speak()   토막마다 음성을 만들고 길이를 잰다. 그 길이가 곧 장면
              길이가 된다.

목소리에 대해
    대본은 1인칭이다 — "저는 수원 영통에서 오래 살았습니다". 합성 음성이
    사장님의 개인 경험을 말하면 신뢰 문제가 된다. **이건 타이밍을 잡기
    위한 초안이고, 공개본은 직접 녹음하는 걸 전제로 한다.** 그래서
    만들어진 파일 옆에 그 사실을 적어 둔다.

실행:
  python -m content.voice --polish docs/longform/2026-10-10-newtown-1-cue.md
  python -m content.voice --speak
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TTS_MODEL = "gpt-4o-mini-tts"
TEXT_MODEL = "gpt-5"
VOICE = "alloy"         # 가장 널리 쓰이는 목소리. 과하지 않다
SPEED = 1.12            # 기본 속도는 설명조로 느리다. 조금만 당긴다
OUT = ROOT / "output" / "longform" / "voice"
NOTICE = ("이 음성은 타이밍을 잡기 위한 **초안**입니다. "
          "대본이 1인칭이라 공개본은 직접 녹음해야 합니다.")

# 말투 지시. "자연스럽게"만 시키면 문어체를 더 얹는다.
SYSTEM = """너는 한국어 데이터 저널리즘 영상의 내레이션을 다듬는 편집자다.

고칠 것
  · 읽을 때 걸리는 어순, 숨 쉴 데 없는 긴 문장
  · 문어체 ("~하는 바", "~에 다름 아니다" 같은 것)
  · 같은 말의 반복

절대 건드리지 말 것
  · 숫자, 퍼센트, 연도, 금액 — 하나도 바꾸지 마라
  · 단지명·지명·기관명
  · 주장의 강도. "~일 수 있습니다"를 "~입니다"로 올리지 마라
  · 1인칭 시점과 담담한 톤. 과장하거나 들뜨게 만들지 마라

길이는 원문의 ±15% 안에서. 설명을 덧붙이지 말고 **다듬기만** 해라.
결과는 다듬은 문장 하나만 출력한다. 따옴표나 설명을 붙이지 마라."""

NUM = re.compile(r"\d[\d,.]*")


def _client():
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(ROOT / ".env")
    return OpenAI()


def numbers(s: str) -> list[str]:
    """숫자만 뽑아 비교용으로. 쉼표는 무시한다 (1,352 == 1352)."""
    return [m.group().replace(",", "").rstrip(".") for m in NUM.finditer(s)]


def polish(lines: list[str], *, model: str = TEXT_MODEL) -> list[dict]:
    """토막마다 다듬고, 숫자가 그대로인지 검사해서 결과를 돌려준다.

    숫자가 하나라도 달라지면 **원문을 쓴다.** 말맛보다 사실이 먼저다.
    """
    cl = _client()
    out = []
    for i, src in enumerate(lines, 1):
        if not src.strip():
            out.append({"src": src, "new": src, "kept": True, "why": "빈 줄"})
            continue
        r = cl.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": src}])
        new = (r.choices[0].message.content or "").strip()
        why = ""
        if not new:
            new, why = src, "응답 없음"
        elif numbers(new) != numbers(src):
            why = (f"숫자가 바뀜 {numbers(src)} → {numbers(new)}")
            new = src
        elif not (0.7 <= len(new) / max(1, len(src)) <= 1.35):
            why = f"길이가 {len(new) / len(src):.0%} 로 벗어남"
            new = src
        out.append({"src": src, "new": new, "kept": new == src, "why": why})
        print(f"\r  다듬는 중 {i}/{len(lines)}", end="", flush=True)
    print()
    return out


def dur(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def speak(texts: list[str], outdir: Path = OUT, *, voice: str = VOICE,
          model: str = TTS_MODEL, speed: float = SPEED) -> list[dict]:
    """토막마다 mp3 를 만들고 길이를 잰다.

    같은 문장은 다시 만들지 않는다 — 대본을 한 줄 고칠 때마다 전부
    다시 읽히면 돈과 시간이 그냥 샌다. 파일 이름은 문장의 해시다.
    """
    cl = _client()
    outdir.mkdir(parents=True, exist_ok=True)
    made = []
    for i, t in enumerate(texts, 1):
        if not t.strip():
            made.append({"text": t, "path": None, "dur": 0.0})
            continue
        key = hashlib.sha1(
            f"{model}|{voice}|{speed}|{t}".encode()).hexdigest()[:16]
        f = outdir / f"{key}.mp3"
        if not f.exists():
            with cl.audio.speech.with_streaming_response.create(
                    model=model, voice=voice, input=t, speed=speed,
                    instructions="차분하고 담담하게. 데이터를 설명하는 "
                                 "톤으로, 과장 없이. 숫자는 또렷하게.",
                    response_format="mp3") as r:
                r.stream_to_file(f)
        made.append({"text": t, "path": f, "dur": dur(f)})
        print(f"\r  읽는 중 {i}/{len(texts)}", end="", flush=True)
    print()
    (outdir / "README.md").write_text(
        f"# 내레이션 음성 (초안)\n\n{NOTICE}\n\n"
        f"- 모델: {model} · 목소리: {voice}\n"
        f"- 파일 이름은 문장의 해시다. 문장이 바뀌면 새로 만든다.\n",
        encoding="utf-8")
    return made


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="내레이션 다듬기 · 음성")
    ap.add_argument("--text", help="한 문장만 시험")
    a = ap.parse_args()
    if a.text:
        r = polish([a.text])[0]
        print(f"  원문: {r['src']}")
        print(f"  다듬: {r['new']}")
        if r["why"]:
            print(f"  되돌림: {r['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
