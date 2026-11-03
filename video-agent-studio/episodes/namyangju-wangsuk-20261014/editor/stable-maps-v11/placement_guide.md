실제 배포 파일은 `outputs/stable-maps-v11/stable-maps_v11_front.mp4`이며 원본 00:00~08:45의 검토본이다. 525초 뒤 본편에는 자동 연결하지 않는다.

철도 부분 파일 `stable-maps_v11_rail.mp4`는 원본 02:45~04:33, 108초다. 한 장의 정적 지도이며 레이어 전환·줌·팬·펄스·노선 그리기가 없다. 실제 운영선형과 신설역 계획 구간은 구분한다. 작은 왕숙역 배치판은 LH B17 원도의 사실 상대배치를 자체 도해로 만든 것이며 GIS와 별도 축척이다.

전체 판은 y0..919에 합성한다. 원본 y922 이하 자막·흰바를 유지하며, AAC 음성은 재인코딩 없이 복사한다. 새 렌더는 H.264 1080p30 CRF18이며 기존 MP4와 원본 데이터는 보존한다. 지도 파일은 현재 프레임을 읽지 않는 정적 Remotion 컴포넌트에서 PNG로 렌더했다.

재현: `node editor/stable-maps-v11/render_plates.cjs`, `python editor/stable-maps-v11/render_static.py rail`, `python editor/stable-maps-v11/render_static.py front`. 실제 실행은 저장소 루트에서 에피소드 경로를 포함한다. 전체 명령은 배포 폴더 render_command JSON에 기록한다.

검수는 실제 MP4 디코드·매 프레임 지도 ROI 비교·독립 시각 검수다. 실제 청취나 연속 재생을 했다고 주장하지 않는다.
