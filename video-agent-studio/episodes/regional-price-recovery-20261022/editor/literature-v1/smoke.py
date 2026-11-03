from pathlib import Path
import json,shutil,html
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/literature-visual-v1';P=OUT/'project';S=OUT/'checks/smoke'
T=json.loads((P/'timing.json').read_text(encoding='utf8'));s=T['scenes'][0]
for d in ['assets/fonts','compositions']:(S/d).mkdir(parents=True,exist_ok=True)
for name in ['common.css','gsap.min.js']:shutil.copy2(P/'assets'/name,S/'assets'/name)
for f in (P/'assets/fonts').glob('*'):shutil.copy2(f,S/'assets/fonts'/f.name)
shutil.copy2(P/'compositions/L001.html',S/'compositions/L001.html')
caps=''.join(f'<div class="caption-cue clip" data-start="{c["start"]}" data-duration="{c["end"]-c["start"]}" data-track-index="2">{html.escape(c["text"])}</div>' for c in T['captions'] if c['scene_id']=='L001')
(S/'index.html').write_text(f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><link rel="stylesheet" href="assets/common.css"><style>@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2')}}@font-face{{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}}</style><script src="assets/gsap.min.js"></script></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{s['duration']}" data-fps="30"><div class="brand">│ 데이터로 보는 부동산</div><h1 class="scene-title">같은 수도권, 다른 가격 흐름</h1><div data-composition-id="L001" data-composition-src="compositions/L001.html" data-start="0" data-duration="{s['duration']}" data-width="1920" data-height="1080" data-track-index="1"></div><div class="caption-box">{caps}</div><div class="source">보유 실거래 · 동일 단지·전용면적군 연결 · 2006Q1–2026Q2</div></div><script>window.__timelines['main']=gsap.timeline({{paused:true}})</script></body></html>''',encoding='utf8')
(S/'hyperframes.json').write_text(json.dumps({'authoringSkill':'general-video'}),encoding='utf8')
print(str(S))
