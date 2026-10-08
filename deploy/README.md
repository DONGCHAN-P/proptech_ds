# 배포 (Fly.io · 서울 리전)

`web/` 맞춤 찾기를 공개 서비스로 올린다. 데이터는 이미지에 같이 넣고, 매일 갱신 뒤 다시 배포한다
(저장소를 따로 두지 않는 가장 단순한 구조).

```
deploy/
  bundle.py     서버가 읽는 것만 deploy/build/ 에 모은다 (약 77MB)
  Dockerfile    python:3.11-slim + uvicorn :8080
  fly.toml      icn · 1GB 1대 상시 · /api/health 체크
  deploy.ps1    build_index → bundle → fly deploy
```

## 처음 한 번 (사람이 할 일)

1. **Fly.io 가입 + 카드 등록** — <https://fly.io>
2. **flyctl 설치 · 로그인**
   ```powershell
   iwr https://fly.io/install.ps1 -useb | iex
   fly auth login
   ```
3. **앱 이름 정하기** — `deploy/fly.toml` 의 `app = "CHANGE-ME"` 를 바꾸고
   ```powershell
   fly apps create <앱이름>
   ```
4. **VWorld 지도 키** — <https://www.vworld.kr> 에서 WMTS 키 발급, 서비스 URL 에
   `https://<앱이름>.fly.dev` 와 나중에 쓸 도메인을 등록한 뒤
   ```powershell
   fly secrets set VWORLD_MAP_KEY=<키> --app <앱이름>
   ```
   (선택) `VWORLD_LAYER=gray` 로 회색 지도, `ODSAY_API_KEY` 로 Top5 통근 실측
5. **배포**
   ```powershell
   powershell -ExecutionPolicy Bypass -File deploy\deploy.ps1
   ```
6. **도메인 연결** (정한 뒤)
   ```powershell
   fly certs add <도메인> --app <앱이름>
   ```
   안내대로 DNS 에 A/AAAA 레코드를 넣으면 HTTPS 인증서가 자동 발급된다.

## 알아둘 점

- **OSM 공식 타일은 운영에 쓰지 않는다.** 이용 정책상 서비스 트래픽 금지다. 키 없이 운영 모드로
  뜨면 로그에 `[경고]` 가 찍힌다
- 메모리: 기동 후 약 190MB. 역 근접 계산을 4천 행씩 나눠 1GB 머신에서 여유가 있다
- 운영 모드(`APP_ENV=production`)에서는 `/docs` 를 닫고, 캐시가 없으면 인덱스를 다시 만들지
  않고 바로 실패한다 (원본 `master/` 가 이미지에 없다)
- 비용: shared-cpu-1x 1GB 상시 1대 기준 월 약 6~7달러 + 트래픽
