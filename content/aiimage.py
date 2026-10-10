"""AI 생성 이미지 — 만들되, **어디서 왔는지 반드시 남긴다**.

이 레포는 생성 이미지를 오래 막아 왔다 (ROADMAP H7 · 5-0항). 이유는 하나다.
**존재하지 않는 건물을 실거래가 옆에 두면 보는 사람이 그걸 실제 단지로
믿는다.** 그 판단은 지금도 유효하다.

그래서 이 모듈은 "써도 된다"가 아니라 "쓰기로 했다면 흔적을 남긴다"는
쪽이다. 사진과 똑같이 `.license.json` 을 짝으로 적는다 — 모델, 프롬프트
원문, 만든 날짜, 위험 등급. 나중에 "이 그림 어디서 났지"를 되짚을 수
있어야 한다.

위험 등급
    abstract   장소도 숫자도 글자도 없는 질감·은유. 오인할 대상이 없다
    depictive  건물·지도·차트처럼 **실재를 흉내 내는** 그림. 실거래가
               옆에 두면 오인을 부른다. 쓸 거면 화면에 고지를 넣는다

실행:
  python -m content.aiimage --prompt "..." --name hero --risk depictive
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODEL = "gpt-image-1.5"
SIZE = "1536x1024"          # 16:9 에 가장 가까운 지원 크기
RISKS = ("abstract", "depictive")
NOTICE = "이미지 일부는 AI로 생성했습니다"


def generate(prompt: str, name: str, outdir: Path, *,
             risk: str = "depictive", model: str = MODEL,
             size: str = SIZE, quality: str = "high") -> Path:
    """한 장 만들고 출처를 짝으로 남긴다."""
    if risk not in RISKS:
        raise ValueError(f"risk 는 {RISKS} 중 하나")
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv(ROOT / ".env")
    client = OpenAI()
    r = client.images.generate(model=model, prompt=prompt, size=size,
                               quality=quality, n=1)
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f"{name}.png"
    png.write_bytes(base64.b64decode(r.data[0].b64_json))

    # 사진과 같은 자리에 같은 모양으로. 출처 없는 그림은 쓰지 않는다.
    (outdir / f"{name}.license.json").write_text(json.dumps({
        "source": f"AI 생성 ({model})",
        "type": "ai-generated",
        "risk": risk,
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "acquired": date.today().isoformat(),
        "credit": NOTICE,
        "note": ("실재를 흉내 내는 그림이다. 화면에 고지를 넣는다."
                 if risk == "depictive" else
                 "장소·숫자·글자가 없는 추상 질감이다."),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return png


def main() -> int:
    ap = argparse.ArgumentParser(description="AI 이미지 생성 (출처 기록 포함)")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--risk", default="depictive", choices=RISKS)
    ap.add_argument("--out", default="output/longform/ai")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--quality", default="high")
    a = ap.parse_args()
    p = generate(a.prompt, a.name, ROOT / a.out, risk=a.risk,
                 model=a.model, quality=a.quality)
    print(f"  저장: {p}  ({p.stat().st_size / 1024:.0f}KB)")
    print(f"  출처: {p.with_suffix('.license.json').name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
