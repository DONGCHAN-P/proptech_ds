import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_shorts import *
import shutil
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
for s in manifest:
 if len(sys.argv)>1 and s['id']!=sys.argv[1]: continue
 p=Path(s['file']);probe=json.loads(subprocess.check_output([str(FF/'ffprobe.exe'),'-v','error','-show_format','-show_streams','-of','json',str(p)],text=True,encoding='utf-8'))
 subprocess.run([str(FF/'ffmpeg.exe'),'-v','error','-i',str(p),'-f','null','-'],check=True,stderr=open(OUT/f"{s['id']}_decode.log",'w'))
 frames=[0,60,s['duration_frames']//2,s['duration_frames']-2]
 if s['id']=='01_rail':frames += [1193,1194,1195]
 if s['id']=='02_price':frames += [826]
 for f in sorted(set(frames)):
  subprocess.run([str(FF/'ffmpeg.exe'),'-y','-v','error','-i',str(p),'-vf',f'select=eq(n\\,{f})','-vsync','0','-frames:v','1',str(OUT/f"{s['id']}_actual_{f}.png")],check=True)
 s['technical']={'probe':probe,'whole_decode_exit':0,'sample_frames':sorted(set(frames)),'actual_listening':False,'continuous_playback':False,'audio_source':'v15 original continuous narration segment, AAC encoded; no new synthesis','layout':'1080x1920 purpose-composed portrait panels; semantic captions reflow only'}
 s['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 (OUT/f"{s['id']}_technical.json").write_text(json.dumps(s['technical'],ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/f"{s['id']}_metadata.json").write_text(json.dumps({k:s[k] for k in ['title','description','start','end','cue_count','sha256']},ensure_ascii=False,indent=2),encoding='utf-8')
 print(s['id'],s['sha256'],flush=True)
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
handoff={'revision':'shorts-release-v1','source':str(SRC),'source_sha256':manifest[0]['source_sha256'],'outputs':manifest,'paid_generation':False,'upload_by':'root only','actual_listening':False,'continuous_playback':False,'next':'fact_review actual QA, then root publication','unresolved':['independent actual QA pending']}
(WORK/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(WORK/'build_shorts.py',OUT/'build_shorts.py');shutil.copy2(WORK/'check_delivery.py',OUT/'check_delivery.py')
(OUT/'README.md').write_text('''# 남양주 왕숙 쇼츠 3편

기존 v15 Jun 음성의 연속된 완결 문장만 사용했습니다. 지도는 원본 검증 도해/현황에서 필요한 판을 세로 화면에 재배치했습니다. 새 유료 생성은 없습니다.

| 파일 | 원본 범위 | 길이 |
|---|---|---|
| 01_rail.mp4 | 03:30.800–04:33.000 | 62.200초 |
| 02_price.mp4 | 09:04.767–09:56.167 | 51.400초 |
| 03_choice.mp4 | 13:36.233–14:24.500 | 48.267초 |

각 동명 SRT/ASS, metadata JSON(제목·설명), technical JSON, manifest에 실제 파일 해시와 검수 자료가 있습니다. 1080×1920 / 30fps. 원본 전체 지도 무작정 세로 크롭 없이 의미있는 지도판과 큰 자막으로 구성했습니다.

가격은 2026.7~9, 83≤전용<85㎡, 5층+, 취소표시 제외 수집 표본의 중위값입니다. 호가가 아닙니다. B17/A1/A3는 서로 다른 공고의 기본형 가격이며 확장·옵션·세금 별도입니다. 후보는 현재 접수/자유매매 안내나 미래 시세 순위가 아닙니다.

출처: 기존 v15의 LH 공고·팸플릿 기반 자체 도해, 국토교통부 실거래 표본, © OpenStreetMap 기여자. 실제 음성 청취 및 연속 재생은 미검증입니다. 전체 디코드/기술 검사와 실제 대표 프레임 검수는 별도로 구분합니다.

재현: 프로젝트 루트에서 tools/python311/python.exe video-agent-studio/episodes/namyangju-wangsuk-20261014/editor/shorts-release-v1/build_shorts.py 실행 후 check_delivery.py 실행. 원본 full MP4/기존 지도판 및 editor 폴더의 source PNG 입력을 보존해야 합니다. 공개 업로드는 총괄 담당입니다.
''',encoding='utf-8')
(WORK/'placement_guide.md').write_text('3개 MP4는 독립 쇼츠입니다. 원본 시간/길이는 outputs/shorts-release-v1/README.md 참조. 상단 제목·중앙 실제 지도판·하단 큰 의미자막. 철도만 39.8초에 기존 운영노선 판으로 직접 전환하며 줌은 없습니다. 자료 유형은 실제 공개지도/공식 계획 기반 자체 도해입니다. 업로드는 총괄 담당.',encoding='utf-8')
