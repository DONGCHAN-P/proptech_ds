---

## name: 부동산 데이터 분석 채널 — 통합 DESIGN.md base-systems: Linear (dark data surfaces) \+ PostHog (light document surfaces) brand-accent: teal \#0d9488  \# 단일 브랜드색. 교체 시 이 값만 변경. font: Inter (sans) \+ JetBrains Mono (수치/코드) modes: dark(data) · light(doc)

## Overview

이 시스템은 성격이 다른 두 표면을 한 채널 정체성으로 묶는다.

- **Dark mode (데이터 표면)** — Linear 기반. 영상 속 차트·대시보드·예측 알고리즘 웹툴. 배경을 거의 비워 데이터가 주인공이 되게 한다.  
- **Light mode (문서 표면)** — PostHog 기반. 블로그·이북·리포트. 따뜻한 크림 캔버스로 읽기 피로를 줄이고, 4색 콜아웃으로 "확실/추정/경고/참고"를 시각 언어화한다.

두 모드를 하나의 채널로 묶는 끈은 **세 가지**다: ① 폰트 통일(Inter), ② 단일 브랜드색(teal), ③ 데이터 의미색 3종(예측=파랑 · 이상치=빨강 · 검증=초록)을 양 모드에서 동일하게 적용.

**Key Characteristics:**

- 두 모드는 캔버스만 다르고, 브랜드색·의미색·폰트는 완전히 공유한다.  
- 브랜드 teal은 CTA·포커스·링크 강조에만 쓰는 희소 액센트. 데이터 의미색과 절대 섞지 않는다.  
- 의미색 3종(파랑/빨강/초록)은 차트에서만 쓰고 UI 장식으로 쓰지 않는다 → 그래야 "빨강=이상치"가 학습된다.  
- 깊이는 그림자가 아니라 surface 단차 \+ 1px 헤어라인으로 만든다(양 모드 공통).  
- 정체성 핵심 \= "감이 아니라 확률, 정직한 검증". 화려함·자극 금지, 절제가 신뢰다.

---

## Colors

### 0\. 브랜드 & 의미색 (양 모드 공통 — 이 시스템의 정체성)

| Token | Value | Use |
| :---- | :---- | :---- |
| `{brand.accent}` | \#0d9488 (teal) | 단일 브랜드색. 1차 CTA, 포커스 링, 링크 강조, 로고 마크. 한 화면에 희소하게. |
| `{brand.accent-hover}` | \#14b8a6 | CTA hover |
| `{brand.accent-pressed}` | \#0f766e | CTA pressed |
| `{data.predict}` | \#3b82f6 (blue) | **예측값·예측 밴드.** 차트 전용. |
| `{data.predict-band}` | rgba(59,130,246,0.15) | 예측 구간(불확실성) 음영. |
| `{data.anomaly}` | \#ef4444 (red) | **이상치·급등락 거래.** 차트의 튀는 점·강조. |
| `{data.verified}` | \#22c55e (green) | **검증 성공·구간 적중.** 회고에서 맞은 예측. |
| `{data.actual}` | 모드별 ink색 | 실제 실거래가 점·선(중립색, 의미색 아님). |

원칙: 브랜드 teal과 의미색 3종은 **용도가 절대 겹치지 않는다.** teal은 UI(버튼·링크), 의미색은 데이터(차트)에만. 이 분리가 깨지면 "빨강을 보면 이상치"라는 학습이 무너진다.

### 1\. Dark mode surfaces (데이터 표면 — Linear 기반)

| Token | Value | Use |
| :---- | :---- | :---- |
| `{dark.canvas}` | \#010102 | 데이터 화면 기본 배경(faint blue tint, 순흑 아님). |
| `{dark.surface-1}` | 한 단계 위 | 차트 카드, 패널, KPI 타일. |
| `{dark.surface-2}` | 두 단계 위 | 강조 카드, hover 카드. |
| `{dark.surface-3}` | 세 단계 위 | 서브내비, 드롭다운. |
| `{dark.hairline}` | \#23252a | 카드·디바이더 1px 보더. |
| `{dark.hairline-strong}` | 강한 1px | 입력 포커스 링. |
| `{dark.ink}` | \#f7f8f8 | 헤드라인·본문(밝은 회색). |
| `{dark.ink-muted}` | \#d0d6e0 | 보조 텍스트. |
| `{dark.ink-subtle}` | \#8a8f98 | 3차 텍스트, 축 라벨, 범례. |
| `{dark.ink-tertiary}` | \#62666d | 비활성·각주. |

Dark mode 깊이: surface ladder(canvas→1→2→3) \+ 헤어라인. 드롭섀도·분위기 그라데이션 금지. 패널 상단에 미세한 흰색 엣지 하이라이트만 허용.

### 2\. Light mode surfaces (문서 표면 — PostHog 기반)

| Token | Value | Use |
| :---- | :---- | :---- |
| `{light.canvas}` | \#eeefe9 | 문서/블로그 기본 배경(따뜻한 크림, 순백 아님). 위→아래 끊김 없이. |
| `{light.surface-soft}` | \#e5e7e0 | 2차 버튼 fill, 인라인코드 칩, 서브내비. |
| `{light.surface-card}` | \#ffffff | 카드·타일(크림 위 흰 카드). 주력 카드 표면. |
| `{light.surface-doc}` | \#fcfcfa | 문서 본문 카드(살짝 크림 섞인 흰색). |
| `{light.surface-code}` | \#23251d | 코드블록 배경(짙은 올리브차콜, 반전). |
| `{light.hairline}` | \#bfc1b7 | 카드 1px 보더, 표 괘선, 푸터 구분. |
| `{light.hairline-soft}` | \#dcdfd2 | 카드 내부 행 구분. |
| `{light.ink}` | \#23251d | 헤드라인·강조(올리브차콜, 거의 검정). |
| `{light.body}` | \#4d4f46 | 기본 본문(올리브그레이). 가장 많이 쓰는 텍스트색. |
| `{light.mute}` | \#6c6e63 | 메타·푸터·2차 주석. |
| `{light.ash}` | \#9b9c92 | 비활성. |

### 3\. 콜아웃 색 (Light mode 문서 전용 — 불확실성 표기 체계)

PostHog의 4색 파스텔을 그대로 가져오되, **채널 원칙("확실/추정 구분")에 맞게 의미를 재정의**한다.

| Token | 배경 / 강조 | 재정의된 의미 | 라벨 |
| :---- | :---- | :---- | :---- |
| `{callout.verified}` | \#d9eddf / \#2c8c66 | **확실·검증됨** (데이터로 확인) | ✅ 검증됨 |
| `{callout.estimate}` | \#dceaf6 / \#2c84e0 | **추정·가설** (확인 안 된 추론) | 💡 추정 |
| `{callout.caution}` | \#f7d6d3 / \#cd4239 | **주의·리스크** (틀릴 수 있음) | ⚠️ 주의 |
| `{callout.note}` | \#e7d8ee / \#7c44a6 | **참고·맥락** (배경 정보) | 📘 참고 |

이 4색은 **문서 본문 안에서만** 쓴다. 마케팅 카드 배경이나 차트에 쓰지 않는다. 이게 당신 채널의 "확실한 것/추정인 것 구분" 원칙을 시각 언어로 만든 핵심 자산이다.

---

## Typography

### Font Family (양 모드 통일)

- **Inter** — 전 텍스트 역할. Linear 독자 폰트와 PostHog의 IBM Plex 양쪽의 최근접 무료 대체. 하나로 두 베이스를 자연 통일한다. weight 400/500/600/700/800.  
- **JetBrains Mono** — 수치·ID·코드. 데이터 화면의 숫자(가격·확률·날짜)와 문서의 코드블록에 사용. 데이터 채널에서 모노는 "정밀함"의 신호다.

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
| :---- | :---- | :---- | :---- | :---- | :---- |
| `{type.display-xl}` | 56–80px | 700 | 1.05–1.10 | \-2.0 \~ \-3.0px | 최상위 히어로(다크 데이터 랜딩). 모바일 36px로 축소. |
| `{type.display-lg}` | 40px | 700 | 1.15 | \-1.0px | 섹션 오프너. |
| `{type.display-md}` | 28px | 700 | 1.20 | \-0.6px | 서브섹션, 카드 그룹 타이틀. |
| `{type.card-title}` | 22px | 600 | 1.25 | \-0.4px | 차트 카드·피처 카드 제목. |
| `{type.subhead}` | 20px | 400 | 1.40 | \-0.2px | 리드 문단. |
| `{type.body-lg}` | 18px | 400 | 1.50 | \-0.1px | 히어로 서브헤드. |
| `{type.body}` | 16px | 400 | 1.50 | 0 | 기본 본문. |
| `{type.body-sm}` | 14–15px | 400 | 1.50–1.71 | 0 | 카드 본문, 문서 본문, 푸터. |
| `{type.caption}` | 12–13px | 400–500 | 1.40 | 0 | 캡션·메타·차트 축 라벨. |
| `{type.button}` | 14px | 600 | 1.20 | 0 | 버튼 라벨. |
| `{type.eyebrow}` | 13px | 600 | 1.30 | \+0.4px (대문자) | 섹션 아이브로(양수 자간·대문자로 구분). |
| `{type.mono}` | 13–14px | 400–500 | 1.45 | 0 | JetBrains Mono. 수치·ID·코드. |

### Principles

- **위계는 굵기+크기로.** 색으로 위계를 만들지 않는다(PostHog식). 색은 브랜드·의미 전용.  
- **Display는 음수 자간 공격적으로**(Linear식). 큰 헤드라인일수록 \-2.0\~-3.0px.  
- **아이브로만 양수 자간+대문자.** 나머지 대문자 변환 금지.  
- **모노는 수치 컨텍스트에만.** 가격·확률·날짜·ID. 일반 본문에 모노 쓰지 않는다.  
- Display 700 ↔ body 400\. 같은 Inter 패밀리로 굵기만 좁힌다.

---

## Layout

### Spacing System

- **Base unit:** 4px(다크) / 8px(라이트) 혼용 — 토큰으로 통일.  
- **Tokens:** `{space.xxs}` 4px · `{space.xs}` 8px · `{space.sm}` 12px · `{space.md}` 16px · `{space.lg}` 24px · `{space.xl}` 32px · `{space.xxl}` 48px · `{space.section}` 80–96px.  
- 카드 내부 패딩: 표준 카드 24px(`{space.lg}`), 가격/플랜 카드 32px(`{space.xl}`), CTA 배너 48px(`{space.xxl}`).  
- 버튼 패딩: 8px 16px. 입력 패딩: 8px 12px.

### Grid & Container

- 최대 콘텐츠 폭 \~1280px. 문서 본문은 \~720px(가독성).  
- 카드 그리드: desktop 3\~4-up → tablet 2-up → mobile 1-up.  
- **데이터 화면:** 차트 패널이 전체 폭을 차지하는 주인공. 주변 chrome은 최소화.  
- **문서 화면:** 240px 스티키 좌측 사이드바(섹션 내비) \+ 720px 본문 옵션.

### Whitespace Philosophy

- **Dark:** 캔버스가 곧 여백. surface-1 패널로 lift해서 섹션을 구분(흰 여백 아님).  
- **Light:** 크림 캔버스가 끊김 없이 흐른다. 장식 구분선 없음. 1px 헤어라인만으로 분리.  
- 섹션 간 `{space.section}` 80\~96px.

---

## Elevation & Depth (양 모드 공통 철학: 그림자 없음)

| Level | Dark 처리 | Light 처리 | Use |
| :---- | :---- | :---- | :---- |
| 0 flat | 보더·섀도 없음 | 보더·섀도 없음 | 본문·히어로 텍스트 |
| 1 | `{dark.surface-1}` \+ 1px `{dark.hairline}` | white 카드 \+ 1px `{light.hairline}` | 기본 카드, 차트 패널 |
| 2 | `{dark.surface-2}` \+ hairline-strong | `{light.surface-soft}` 행 구분 | 강조 카드 |
| 3 | `{dark.surface-3}` | `{light.surface-code}` 반전 코드블록 | 서브내비 / 코드 |
| focus | 2px `{brand.accent}` 50% | 2px `{brand.accent}` \+ focus ring | 포커스 입력·버튼 |

양 모드 공통: **드롭섀도 금지.** 깊이는 surface 단차 \+ 1px 헤어라인 \+ (라이트는) 반전 코드블록으로만.

### Decorative Depth

- **Dark:** 차트·대시보드 스크린샷이 곧 장식. 분위기 그라데이션·스포트라이트 카드 금지.  
- **Light:** 데이터 일러스트(차트 아이콘, 작은 도식)가 마진 장식. PostHog식 마스코트를 쓰고 싶다면 채널 마스코트 1종으로 통일(선택). 단, 신뢰 포지셔닝상 과하지 않게.

---

## Shapes

### Border Radius Scale (양 모드 공통)

| Token | Value | Use |
| :---- | :---- | :---- |
| `{rounded.xs}` | 4px | 상태 칩, 인라인 코드, 배지 |
| `{rounded.sm}` | 6px | 인라인 태그, 작은 칩 |
| `{rounded.md}` | 8px | **모든 버튼·입력·표준 CTA** |
| `{rounded.lg}` | 12px | 카드(피처·가격·차트 카드) |
| `{rounded.xl}` | 16px | 대형 차트/대시보드 패널 |
| `{rounded.pill}` | 9999px | 토글 탭, 상태 필 |
| `{rounded.full}` | 9999px | 아바타 |

CTA는 `{rounded.md}` 8px. 필 라운드 금지(Linear식 절제). 필은 토글·상태 칩에만.

---

## Components

### Buttons

**`button-primary`** — 단일 브랜드 CTA (양 모드)

- 배경 `{brand.accent}`, 텍스트 white, `{type.button}`, padding 8px 16px, height 40px, `{rounded.md}`.  
- hover → `{brand.accent-hover}`, pressed → `{brand.accent-pressed}`.  
- 한 fold(화면 한 단위)에 teal 버튼은 가급적 1개.

**`button-secondary`**

- Dark: 배경 `{dark.surface-1}` \+ 1px `{dark.hairline}`, 텍스트 `{dark.ink}`.  
- Light: 배경 `{light.surface-soft}`, 텍스트 `{light.ink}`.  
- padding 8px 16px, height 40px, `{rounded.md}`.

**`button-tertiary`** — 고스트

- 배경 투명, 텍스트 모드별 ink, `{type.button}`, `{rounded.md}`. "전체 보기 →" 등 최저 강조.

### Cards & Containers

**`chart-card`** (Dark 주력) — 차트/대시보드 패널

- 배경 `{dark.surface-1}`, 1px `{dark.hairline}`, `{rounded.xl}` 16px, padding 24px.  
- 차트가 주인공. 카드 chrome은 어둡고 조용하게. 예측 밴드·이상치 점이 surface 위에서 튀게.

**`kpi-card`** (Dark) — 단일 지표 타일

- 배경 `{dark.surface-1}`, `{rounded.lg}` 12px, padding 24px.  
- 큰 수치는 `{type.display-md}` \+ JetBrains Mono. 라벨은 `{type.caption}` `{dark.ink-subtle}`.

**`doc-card`** (Light 주력) — 문서 본문 카드

- 배경 `{light.surface-doc}` \#fcfcfa, 1px `{light.hairline}`, `{rounded.lg}`, padding 24px.  
- 본문 섹션·표·콜아웃·코드블록을 담는다.

**`feature-tile`** (Light) — 마케팅 피처 타일

- 배경 `{light.surface-card}` white, 1px `{light.hairline}`, `{rounded.lg}`, padding 20px.  
- 3\~4-up 그리드. 작은 데이터 아이콘 \+ 1줄 설명.

### Callout Banners (Light 문서 전용 — 불확실성 표기)

**`callout-verified`** / **`-estimate`** / **`-caution`** / **`-note`**

- 배경 `{callout.*}` 파스텔, 텍스트 `{light.ink}`, `{type.body}`, padding 16px 20px, `{rounded.md}`.  
- 각 앞에 이모지+라벨: ✅ 검증됨 / 💡 추정 / ⚠️ 주의 / 📘 참고.  
- **문서 본문 안에서만.** 차트·마케팅 카드 배경 금지.  
- 용례: "이 단지 6개월 예측 12억±1.5억 💡 추정" / "구간 적중 ✅ 검증됨" / "금리 급변 시 빗나갈 수 있음 ⚠️ 주의".

### Code & Numbers

**`code-block`** (Light) — 문서 코드 샘플

- 배경 `{light.surface-code}` \#23251d, 텍스트 white, JetBrains Mono `{type.mono}`, padding 16px 20px, `{rounded.md}`.  
- 신택스 하이라이트는 muted 톤. 콜아웃 파스텔 4색을 코드에 쓰지 않는다.

**`inline-code`** — 인라인 칩

- Light: 배경 `{light.surface-soft}`, 텍스트 `{light.ink}`, `{rounded.xs}`, padding 2px 6px.  
- Dark: 배경 `{dark.surface-2}`, 텍스트 `{dark.ink}`.

**`metric-value`** — 수치 강조 (양 모드)

- JetBrains Mono, `{type.display-md}`\~`{type.card-title}`. 가격·확률·증감률.  
- 증감 방향은 의미색: 상승 맥락이라도 **이상치면 `{data.anomaly}`**, 일반 예측이면 `{data.predict}`. 색 규칙을 데이터 의미에 종속시킨다.

### Inputs & Forms

**`text-input`** \+ **`-focused`**

- Dark: 배경 `{dark.surface-1}`, 텍스트 `{dark.ink}`, `{rounded.md}`, padding 8px 12px. focus \= 2px `{brand.accent}` 50%.  
- Light: 배경 white, 1px `{light.hairline}`, focus \= 2px `{brand.accent}`.

### Navigation

**`top-nav`**

- Dark: 배경 `{dark.canvas}`, height 56px, 로고 좌 \+ 링크 \+ `button-secondary`/`button-primary` 우.  
- Light: 배경 `{light.canvas}` 크림(페이지와 동일), height 56px.  
- 양 모드 모두 우측 끝에 단일 teal `button-primary`.

### Charts (데이터 채널 핵심 — 의미색 규칙)

**`chart-line`** — 시계열(실거래가·예측)

- 실제값: 중립 ink색 선/점. 예측선: `{data.predict}`. 예측 구간: `{data.predict-band}` 음영.  
- 과거 예측 밴드 위에 실제값 점을 올려 "구간 적중" 여부를 한눈에. 적중 점은 `{data.verified}`.

**`chart-anomaly`** — 이상치 강조

- 정상 점: `{dark.ink-subtle}` 회색. 이상 점: `{data.anomaly}` 빨강 \+ 화살표 1개.  
- 쇼츠용은 세로·굵게·메시지 1개(욕심 금지).

**`probability-gauge`** — 확률 게이지

- 상승/보합/하락 3분할 막대 또는 게이지. 색은 데이터 의미색 사용, teal 사용 금지.

---

## Do's and Don'ts

### Do

- 데이터 화면은 dark(`{dark.canvas}`), 문서는 light(`{light.canvas}` 크림)로 표면을 분리한다.  
- 브랜드 teal은 CTA·포커스·링크·로고에만. 한 fold에 희소하게.  
- 의미색 3종(파랑/빨강/초록)은 차트에만. 양 모드에서 동일 의미로.  
- 폰트는 Inter로 통일, 수치·코드는 JetBrains Mono.  
- 콜아웃 4색으로 "확실/추정/주의/참고"를 일관되게 표기한다.  
- 깊이는 surface 단차 \+ 1px 헤어라인으로. 그림자 없이.  
- 예측은 항상 구간+확률로 시각화(밴드·게이지). 단일 점 강조 지양.

### Don't

- 브랜드 teal을 차트 데이터 색으로 쓰지 마라(의미색과 충돌).  
- 의미색(빨강·파랑·초록)을 버튼·링크·UI 장식에 쓰지 마라(학습 붕괴).  
- 두 번째 브랜드 채도색을 추가하지 마라. teal 하나.  
- 드롭섀도·분위기 그라데이션·스포트라이트 카드 금지.  
- CTA를 필로 라운드하지 마라(`{rounded.md}` 8px 고정).  
- 콜아웃 파스텔을 마케팅 카드·차트 배경으로 쓰지 마라(문서 본문 전용).  
- 화려한 핀테크/크립토 톤으로 흐르지 마라 — 신뢰 포지셔닝과 충돌.  
- 다크에 순흑(\#000000), 라이트에 순백(\#ffffff 캔버스)을 쓰지 마라(faint tint 유지).

---

## Responsive Behavior

| Name | Width | Key Changes |
| :---- | :---- | :---- |
| Desktop | 1280px+ | 카드 3\~4-up, 문서 사이드바 노출 |
| Tablet | 1024px | 4-up→3-up, 768px에서 3-up→2-up, 사이드바 아코디언 |
| Mobile | 480px | 1-up 단일 컬럼, display-xl 80→36px |

- CTA ≥40px 탭 높이. 입력 ≥44px(터치). 필 탭 ≥44px(터치).  
- 차트 패널은 종횡비 유지, 크롭 금지. 모바일에서 세로 우선(쇼츠와 동일 원칙).  
- 문서 사이드바: desktop 240px → tablet 상단 아코디언 → mobile 접힘.

---

## Iteration Guide

1. 컴포넌트 하나씩, 토큰명으로 직접 참조(`{brand.accent}`, `{data.anomaly}`, `{rounded.md}`).  
2. 새 섹션은 먼저 **어느 모드(dark/light)** 표면에 올릴지 정한다.  
3. 본문 기본은 `{type.body}` 16/400. 강조는 굵기로(색 아님).  
4. 브랜드 teal과 의미색의 용도 분리를 매번 검증한다(UI vs 데이터).  
5. 새 변형은 별도 컴포넌트 엔트리(`-hover`/`-pressed`/`-focused`)로.  
6. 차트 추가 시 의미색 규칙(파랑=예측·빨강=이상·초록=검증) 먼저 적용.  
7. 브랜드색 교체가 필요하면 front-matter의 `brand-accent` 한 줄과 `{brand.accent*}` 토큰만 바꾼다.

## Known Gaps

- 채널 마스코트/일러스트 자산은 미정(선택 사항). 도입 시 1종으로 통일, 신뢰 톤 유지.  
- 다크 모드 차트의 세부 신택스/축 스타일은 실제 데이터로 캘리브레이션 필요.  
- teal(\#0d9488)은 의미색과 비충돌 중립 액센트로 선정한 기본값 — 브랜드 확정 시 교체 가능.  
- 폼 검증/에러 상태는 두 베이스 모두 미문서화 → 구현 시 `{callout.caution}` 톤 차용 권장.

