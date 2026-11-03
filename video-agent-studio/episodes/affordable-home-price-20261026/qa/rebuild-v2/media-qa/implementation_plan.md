# 실제 미디어 독립 검수 준비 Implementation Plan

> **For agentic workers:** 현재 독립 QA가 직접 실행한다. 사용자 지정 소유 범위는 이 media-qa 폴더다.

**Goal:** exact MP4·SRT·EDL에서 모든 필수 프레임을 빠짐없이 추출하고, 원본 DOM 글리프·도형 검사를 독립 기록한다.

**Architecture:** Python 한 개가 입력 SHA·전역 프레임·SRT를 검증하고 계획/추출/디코드 영수증을 만든다. 작은 Node 검사기는 고정된 장면 HTML을 읽어 글꼴 로드 후 글리프 경계를 검사한다. 자동 기술검사는 육안 승인과 별도로 남긴다.

**Tech Stack:** 설치된 Python 3.11·Pillow·FFmpeg 7.1·ffprobe·Node·playwright-core·headless Chrome. 설치·네트워크·ASR 실행 없음.

**Spec:** editor/rebuild-v2/build_contract.json, qa/rebuild-v2/acceptance.json, 현재 사용자 packet.

## Global Constraints

- 최종은 원문 배열의 34장면, 장면별 중간/마지막, 모든 컷 전/직후/다음, 모든 SRT 큐 중간, 3종 실측 앵커 진행, 최대 줌 상태를 포함한다.
- 모든 쓰기는 media-qa 내부. 원본·narration·Tesla 소스는 읽기만 한다.
- sampled frames·연속재생·실제청취·ASR을 구분하고 최종 승인 자동화는 하지 않는다.

## Review Focus

- 짧은 자막도 실제 표시되는 프레임을 배정한다. 표시 프레임이 없는 큐는 오류다.
- 경계는 end exclusive. 마지막 프레임과 다음 장면 첫 프레임을 혼동하지 않는다.
- 컷 목록은 브랜드·챕터·CTA를 포함해 전체 EDL을 빈틈 없이 덮는다.
- 입력 SHA·CFR/PTS·프레임 수가 다르면 수집을 중단한다.
- 의도된 글자 포함 도형의 예외는 명시적 관계만 사용하고 다른 충돌은 기록한다.

## Tasks

- [x] check_media_review.py: 짧은 큐·전구간 컷·순서·누락/손상·쓰기경계 테스트를 먼저 실행해 미구현 실패를 확인했다.
- [x] media_review.py: 순수 SRT/계획 함수와 SHA 고정·decode·select 추출·열람대장 수집기를 구현했다. 대표 MP4 한 개씩도 수집한다.
- [x] geometry_review.cjs: source SHA를 확인하고 실제 문자 Range와 도형 교차를 기록한다. 외부 URL은 차단한다.
- [x] 입력 template과 handoff에 전역 EDL 필드 및 미확인 coverage를 명시했다. Lovelace 필드 질의 packet을 추가했다.
- [x] 단위검사8개와 로컬 합성 AV 실증이 통과했다. 실제 본편 검수는 입력 대기이며 수행했다고 기록하지 않았다.
