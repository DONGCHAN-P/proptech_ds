exec(open(__file__.replace('crop.py','build.py'),encoding='utf-8').read().split('manifest=[]')[0])
for block,page_no,target in [('S1',6,'783,400'),('S4',6,'867,190'),('S5',5,'769,980')]:
 d=pymupdf.open(O/f'{block}_official.pdf');p=d[page_no-1];hits=p.search_for(target)
 h=hits[0];r=pymupdf.Rect(10,max(0,h.y0-85),p.rect.width-10,min(p.rect.height,h.y1+25));p.get_pixmap(matrix=pymupdf.Matrix(3,3),clip=r).save(O/f'{block}_84_price_crop.png')
for block,page_no,target in [('S1',7,'6,980'),('S4',7,'6,139'),('S5',8,'6,618')]:
 d=pymupdf.open(O/f'{block}_official.pdf');p=d[page_no-1];h=p.search_for(target)[-1];r=pymupdf.Rect(10,max(0,h.y0-65),p.rect.width-10,min(p.rect.height,h.y1+45));p.get_pixmap(matrix=pymupdf.Matrix(3,3),clip=r).save(O/f'{block}_84_balcony_crop.png')
print('6 crops saved')
