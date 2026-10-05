# Pretendard

SNS 이미지 렌더에 쓰는 본문 글꼴. `content/design.py` 가 base64 `@font-face` 로
심는다.

**시스템 설치에 기대지 않고 파일을 레포에 넣는 이유** — 렌더 환경(개발 PC, CI,
다른 사람 기기)이 바뀌면 설치된 글꼴이 조용히 맑은 고딕으로 떨어진다. 에러가 안
나고 글자 모양만 바뀌어서, PNG 를 눈으로 보기 전에는 알 수 없다.

- 출처: https://github.com/orioncactus/pretendard
- 라이선스: SIL Open Font License 1.1 (`OFL.txt`)
- 굵기: Regular 400 / Medium 500 / SemiBold 600 / Bold 700 / ExtraBold 800

굵기를 추가하면 `design.font_face_css()` 의 목록에도 넣어야 한다.
