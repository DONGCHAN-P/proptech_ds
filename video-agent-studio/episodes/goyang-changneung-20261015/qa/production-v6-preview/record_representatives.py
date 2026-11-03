from pathlib import Path
import json,hashlib
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v6-preview');ep=q.parent.parent;o=ep/'outputs/production-v6-preview'
r=[]
for name,checks in [('commute',['15 exact times match report','MBC focus and caption align','current transit and representative-point caveat shown','5 selected destinations visible']),('price',['three exact prices and types','basic plus balcony sums match','no bar-number overlap']),('calendar',['2030 unknown month is year range','2031.12 and three move-in months correct','all five rows readable']),('decision',['S4/S5/S1 conditions and cautions readable','no title or caption clipping']),('detail',['S4 locator/detail/school6/kindergarten6 match','scheduled move-in vs target opening distinguished','QAV6-004 cropped unspoken high-school parcel'])]:
 p=o/f'proof_{name}.png';r.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'inspection':'actual view_image full-resolution source image','media_type':'Remotion still; not final MP4','confirmed':checks})
(q/'representative_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print('5 actual visual inspections recorded with hashes')
