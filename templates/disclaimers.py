"""고정 문구 — 변경 금지.

Phase 6 점검 항목이다. 이 파일의 문구는 손대지 않는다. 바꿔야 할 일이
생기면 로드맵과 함께 고치고, 테스트가 그 사실을 알도록 한다.
"""
from __future__ import annotations

# 스레드 · 인스타 하단 고정
DISCLAIMER_SOCIAL = (
    "본 콘텐츠는 국토교통부 실거래가 공개시스템의 공공데이터를 기반으로 "
    "자동 생성된 단순 정보 제공용 자료입니다. 매수·매도를 추천하거나 "
    "가격 상승/하락을 보장하지 않으며, 투자에 대한 모든 책임은 본인에게 "
    "있습니다."
)

# 유튜브 영상 고정 자막 + 설명란
DISCLAIMER_YOUTUBE = (
    "※ 안내: 본 영상은 공공데이터 API 기반으로 분석된 주간 거래 지표이며, "
    "특정 아파트 단지에 대한 투자 권유가 아닙니다. 실거래가 등록 및 취소 "
    "시점에 따라 실제 시세와 차이가 발생할 수 있습니다."
)

# Phase 7 M0 — Day 1부터 모든 콘텐츠에 가입 동선을 넣는다.
# 링크는 뉴스레터 도구 선정(HUMAN) 후 .env 의 NEWSLETTER_URL 로 주입한다.
CTA_NEWSLETTER = "매주 수도권 거래 지표를 메일로 받아보기 → {url}"
CTA_PLACEHOLDER_URL = "(뉴스레터 링크 준비 중)"

# 출처 표기 — 차트 하단과 본문에 공통으로 쓴다
SOURCE_NOTE = "국토교통부 실거래가 공개시스템 · 해제(취소) 건 제외"

ALL_DISCLAIMERS = {
    "social": DISCLAIMER_SOCIAL,
    "youtube": DISCLAIMER_YOUTUBE,
}
