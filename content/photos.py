"""표지 사진 — 출처·라이선스 관리.

`docs/02_CLI_디자인지시사항.md` 5-0항. **라이선스 정보가 없는 사진은 쓰지
않는다.** 예외 없다 — "일단 쓰고 나중에 확인"은 이미 발행된 뒤에야 문제가
드러나고, 그때는 되돌릴 수 없다.

금지 소스가 분명하다. 분양 조감도·광고 이미지, 포털 지도·로드뷰 캡처, 뉴스
사진, **특정 단지처럼 보이는 AI 생성 이미지**, 정부 사이트 화면을 흉내 낸
합성 이미지. AI 생성이 금지인 이유는 T16 의 "실사풍 건물 이미지를 만들지
않는다"와 같다 — 보는 사람이 실제 그 단지로 오인한다.

배치:

    assets/photos/{시군구코드}/
        yongin-01.jpg
        yongin-01.license.json

`license.json` 한 장에 담는 것:

    {
      "source": "직접 촬영 | 공공누리 제1유형 | 스톡 이름",
      "type": "own | kogl-1 | kogl-0 | stock",
      "acquired": "2026-10-06",
      "credit": "출처: ○○○ (공공누리 제1유형)",
      "scene": "region | complex"
    }

`scene: region` 이면 지역 풍경이라는 뜻이고, 카드 우상단에 "이미지는 지역
참고용"을 찍는다 (5-0항).
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTO_DIR = ROOT / "assets" / "photos"

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# 허용 라이선스 유형. 여기 없는 값은 통과시키지 않는다 — 오타 하나로
# 라이선스 불명 사진이 발행되는 길을 열어두지 않는다.
ALLOWED_TYPES = {
    "own": "직접 촬영",
    "kogl-0": "공공누리 제1유형",     # 제0유형(=출처표시 불요)도 포함
    "kogl-1": "공공누리 제1유형",
    "stock": "상업 이용 허락 스톡",
}
REQUIRED = ("source", "type", "acquired", "credit")

MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp"}


@dataclass
class Photo:
    path: Path
    meta: dict

    @property
    def credit(self) -> str:
        return self.meta["credit"]

    @property
    def is_region(self) -> bool:
        """특정 단지가 아니라 지역 풍경인가."""
        return self.meta.get("scene", "region") == "region"

    def data_uri(self) -> str:
        mime = MIME.get(self.path.suffix.lower(), "image/jpeg")
        b64 = base64.b64encode(self.path.read_bytes()).decode()
        return f"data:{mime};base64,{b64}"


def license_path(img: Path) -> Path:
    return img.with_suffix(img.suffix + ".license.json")


def check(img: Path) -> list[str]:
    """한 장에 대한 라이선스 검사. 빈 리스트면 써도 된다."""
    lic = license_path(img)
    if not lic.exists():
        return [f"{img.name}: license.json 없음 — 쓰지 않는다"]
    try:
        meta = json.loads(lic.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{img.name}: license.json 을 읽을 수 없다 ({e})"]

    bad = [f"{img.name}: '{k}' 누락" for k in REQUIRED if not meta.get(k)]
    if meta.get("type") not in ALLOWED_TYPES:
        bad.append(f"{img.name}: 허용되지 않는 라이선스 '{meta.get('type')}' "
                   f"(가능: {sorted(ALLOWED_TYPES)})")
    try:
        date.fromisoformat(str(meta.get("acquired", "")))
    except ValueError:
        bad.append(f"{img.name}: acquired 가 YYYY-MM-DD 가 아니다")
    return bad


def find(sigungu_code: str) -> tuple[Photo | None, list[str]]:
    """그 지역 사진 한 장을 고른다. 라이선스를 통과한 것만 돌려준다.

    사진이 없으면 `(None, [])` 이다 — 그건 실패가 아니라 폴백 신호다
    (지시사항 5항: 사진을 못 구하면 map 또는 오프화이트 표지).
    라이선스가 **잘못된** 경우에만 사유를 함께 돌려준다.
    """
    d = PHOTO_DIR / str(sigungu_code)
    if not d.is_dir():
        return None, []
    imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
    problems: list[str] = []
    for img in imgs:
        bad = check(img)
        if bad:
            problems += bad
            continue
        meta = json.loads(license_path(img).read_text(encoding="utf-8"))
        return Photo(img, meta), problems
    return None, problems


def audit() -> list[str]:
    """보유 사진 전수 검사. 발행 전 점검과 테스트가 같이 쓴다."""
    if not PHOTO_DIR.is_dir():
        return []
    bad = []
    for img in sorted(PHOTO_DIR.rglob("*")):
        if img.suffix.lower() in IMG_EXT:
            bad += check(img)
    return bad
