from pathlib import Path
import json
p=Path('video/src/PilotV6.tsx').read_text(encoding='utf-8-sig')
p=p.replace("import {Apartment,Continuation} from './ContinuationV6';","import {Apartment} from './ContinuationV6';\nimport {ContinuationV7 as Continuation,MapPanel} from './MediaV7';")
old="if(index===3)return <AbsoluteFill style={{background:cream}}><Img src={staticFile('pilot-v2/map-v3.png')} style={{width:1920,height:1080}}/></AbsoluteFill>;"
assert old in p;p=p.replace(old,"if(index===3)return <MapPanel id=\"dongtan-core\"/>;")
p=p.replace('id="NewtownV6"','id="NewtownV7"')
Path('video/src/PilotV7.tsx').write_text(p,encoding='utf8')
Path('video/out/newtown-v7.srt').write_bytes(Path('video/out/newtown-v6.srt').read_bytes())
Path('video/out/newtown-v7-timing.json').write_bytes(Path('video/out/newtown-v6-timing.json').read_bytes())
report={"base":"v6","duration_seconds":285.2,"narration":"same Jun audio files and timings as v6","changed_intervals":[{"start":22.333,"end":26.867,"visual":"동탄역·롯데캐슬·백화점 실제 상세지도"},{"start":113.367,"end":118.367,"visual":"광교 생활권·일자리 지도"},{"start":130.9,"end":135.9,"visual":"광교 역·행정 중심 지도"},{"start":135.9,"end":140.9,"visual":"경기도청 공개 사진"},{"start":140.9,"end":148.967,"visual":"광교호수공원 실제 사진"},{"start":148.967,"end":152.967,"visual":"동탄 반도체 사업장 지도"},{"start":152.967,"end":165.967,"visual":"동탄역 복합단지 지도"},{"start":170.967,"end":185.9,"visual":"SRT·GTX-A 실제 역 사진"}],"unused_reference_assets":"Lotte construction photos lack confirmed reuse permission; not included","photo_ids":["gnews-gwanggyo-history-0","commons-3","commons-1","commons-0"]}
Path('video/out/newtown-v7-changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
