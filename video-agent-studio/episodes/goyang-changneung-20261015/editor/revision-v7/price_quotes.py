from pathlib import Path
import sys,json,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];sys.path.insert(0,str(EP.parent/'namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps'));import pymupdf
O=EP/'outputs/visual-review-v7';PUB=E/'cache/public/review-v7';PUB.mkdir(parents=True,exist_ok=True);d=pymupdf.open(EP/'outputs/source-review-v7/S4_official.pdf');rows=[]
for name,page,rect in [('S4_basic_header',5,[50,75,800,182]),('S4_basic_84AH',6,[50,328,800,412]),('S4_balcony_header',7,[50,418,800,470]),('S4_balcony_84AH',7,[50,745,800,803])]:
 f=PUB/(name+'.png');d[page-1].get_pixmap(matrix=pymupdf.Matrix(3,3),clip=pymupdf.Rect(rect)).save(f);rows.append({'file':name+'.png','pdf_page':page,'crop_pdf_points':rect,'scale':3,'source_sha256':hashlib.sha256((EP/'outputs/source-review-v7/S4_official.pdf').read_bytes()).hexdigest(),'usage':'원문 헤더/단위와 선택 타입행을 분리 발췌하고 동일 폭으로 배치; 전체 페이지 축소 아님'})
(O/'price_quote_manifest.json').write_text(json.dumps({'source':'outputs/source-review-v7/S4_official.pdf','quotes':rows,'rights':'공고 공개 원문·사실 확인용 최소 표 인용. 명시 재사용 라이선스 미확인; 포괄 복제 허가 확정으로 표시하지 않음. 출처/공고명/일자/페이지/단위 표시.'},ensure_ascii=False,indent=2),encoding='utf-8');print('4 actual PDF header/type-row quotes rendered')
