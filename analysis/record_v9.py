from pathlib import Path
import json,re
root=Path('video/public/asset-pack-v9')
s=Path('video/src/AssetCutsV9.tsx').read_text(encoding='utf-8-sig')
rows=[dict(start=float(a),end=float(b),file=f) for a,b,f in re.findall(r"start:([\d.]+),end:([\d.]+),file:'([^']+)'",s)]
(root/'placements.json').write_text(json.dumps(dict(method='static PNG, no zoom, fade in 0.2 seconds',cuts=rows),ensure_ascii=False,indent=2),encoding='utf8')
src=Path('video/out/newtown-v8-sources.md').read_text(encoding='utf8')
src+='\n\n## v9 사용자가 제공한 소재\n\n원본 폴더: C:/Users/e2ken/Documents/Codex/2026-10-13/referenced-chatgpt-conversation-this-is-an/outputs/newtown_asset_pack_unpacked/newtown_asset_pack\n\n본문 PNG 10장을 사용했다. 폴더 가이드에 따르면 7장은 AI 개념 이미지, 3장은 개념 카드이며 특정 실제 단지·사업장·역의 촬영 자료가 아니다. 실제 장소 확인은 기존 지도와 출처가 있는 사진으로 유지한다. 썸네일은 본편에 삽입하지 않았다.\n\n6초 확대 MP4는 사용하지 않고 PNG를 고정했다. 삽입 위치는 video/public/asset-pack-v9/placements.json에 기록했다. Jun 음성·실거래 데이터·10분 길이를 유지했다.\n'
Path('video/out/newtown-v9-sources.md').write_text(src,encoding='utf8')
for old,new in [('newtown-v8.srt','newtown-v9.srt'),('newtown-v8-timing.json','newtown-v9-timing.json')]:Path('video/out/'+new).write_bytes(Path('video/out/'+old).read_bytes())
