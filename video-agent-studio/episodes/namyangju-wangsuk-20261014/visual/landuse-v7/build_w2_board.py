"""LH W2 A3 pamphlet p5 factual spatial transcription, not cadastral geometry."""
import json, pathlib, html
from PIL import Image, ImageDraw, ImageFont
P=pathlib.Path(__file__).parent
colors={'housing':'#F5C96D','school':'#8ECFDB','park':'#A8CE8C','commercial':'#E97E7B','mixed':'#EDA36E','public':'#9B94C2','work':'#728CB8','water':'#85C6E1'}
features=[]
def f(i,t,xy,label='',anchor=None):
 features.append(dict(id=i,type=t,polygon=xy,label=label,anchor=anchor))
# Pixel positions transcribed against the verified north-up source plan.
f('a11','housing',[(82,326),(126,273),(223,237),(271,289),(217,365),(210,420),(171,418),(131,368)],'A-11',(185,320))
f('b2','housing',[(226,444),(224,384),(278,307),(345,382),(288,443)],'B-2',(279,388))
f('a2','housing',[(290,444),(351,385),(438,477),(383,514),(347,472)],'A-2',(373,454))
f('a1','housing',[(123,470),(211,470),(211,605),(170,605),(124,581),(105,546)],'왕숙2 A-1',(162,539))
f('school_e','school',[(227,460),(305,460),(305,521),(227,521)],'초',(267,491))
f('school_m','school',[(229,527),(305,527),(305,573),(229,573)],'중',(267,550))
f('school_k','school',[(232,579),(276,579),(276,604),(235,604)],'',None)
f('park_w','park',[(311,462),(347,478),(381,520),(401,591),(345,619),(260,663),(232,609),(280,608),(311,576)],'공원',(337,560))
f('a3','housing',[(398,535),(454,499),(528,603),(454,650)],'왕숙2 A-3',(461,577))
f('a10','housing',[(261,677),(404,600),(427,654),(402,695),(334,712),(286,703)],'A-10',(354,661))
f('a4','housing',[(484,474),(535,450),(572,452),(637,515),(558,590)],'A-4',(559,509))
f('b5','housing',[(485,316),(524,277),(551,254),(598,274),(567,344)],'B-5',(546,301))
f('b4','housing',[(628,249),(680,214),(686,193),(758,184),(783,273),(674,287)],'B-4',(721,244))
f('a7','housing',[(770,147),(786,113),(822,86),(840,85),(846,270),(799,270)],'A-7',(813,191))
f('park_n','park',[(550,438),(571,349),(610,279),(630,260),(669,292),(782,292),(782,327),(754,358),(730,333),(686,387),(655,420),(622,456),(589,452)],'공원',(626,359))
f('school_n','school',[(688,389),(730,339),(773,360),(737,416)],'초',(732,378))
f('b1','housing',[(622,464),(682,406),(723,431),(657,506)],'B-1',(669,456))
f('c3','mixed',[(667,518),(739,443),(774,468),(718,542),(697,557)],'주상복합',(720,501))
f('c4','mixed',[(729,556),(784,491),(814,506),(793,573),(774,611)],'주상복합',(773,552))
f('c2','mixed',[(565,602),(645,535),(688,575),(616,670)],'주상복합',(626,607))
f('c1','mixed',[(459,659),(538,622),(593,690),(520,755)],'주상복합',(526,687))
f('c5','mixed',[(632,693),(701,606),(752,640),(695,735)],'주상복합',(695,678))
f('public_w','public',[(409,676),(440,675),(482,745),(443,760),(388,713)],'공공',(437,714))
f('work_w','work',[(426,783),(485,753),(505,780),(454,805)],'',None)
f('b3','housing',[(897,438),(976,485),(917,622),(852,580)],'B-3',(914,527))
f('a6','housing',[(851,586),(917,625),(905,686),(813,646)],'A-6',(864,642))
f('park_e','park',[(985,492),(1050,536),(1100,606),(1048,673),(1081,701),(1032,739),(935,689),(920,620)],'공원',(1012,612))
f('a5','housing',[(1052,675),(1106,615),(1146,711),(1105,733)],'A-5',(1106,681))
f('school_e2','school',[(1032,745),(1083,707),(1115,742),(1080,779)],'초',(1072,745))
f('school_e3','school',[(976,753),(1026,794),(1064,830),(1097,787),(1030,746)],'중',(1026,793))
f('a9','housing',[(887,783),(1004,839),(958,898),(826,834)],'A-9',(915,831))
f('a8','housing',[(1048,840),(1116,754),(1206,845),(1134,906)],'A-8',(1131,837))
f('a12','housing',[(1007,847),(1073,899),(1040,935),(960,906)],'A-12',(1017,896))
f('commerce1','commercial',[(547,798),(606,748),(605,795),(578,815)],'상업',(577,789))
f('commerce2','commercial',[(618,750),(664,791),(637,820),(618,793)],'',None)
f('commerce3','commercial',[(650,826),(673,806),(702,826),(681,855)],'',None)
f('public_s','public',[(614,920),(672,905),(710,1013),(670,1047)],'공공',(663,968))
f('park_s','park',[(744,901),(886,948),(980,1010),(898,1045),(805,1053),(747,999)],'공원',(836,995))
f('work_s','work',[(784,849),(871,890),(955,931),(934,965),(849,923),(765,885)],'업무',(858,907))
f('water','water',[(856,171),(872,319),(859,403),(875,444),(865,497),(846,548),(830,608),(797,675),(774,741),(748,800),(726,881),(741,935),(756,1003),(730,1041),(746,1068),(792,1087),(816,1074),(802,1043),(782,1027),(775,1003),(779,973),(799,946),(810,931),(802,916),(782,938),(760,932),(749,898),(751,858),(767,815),(796,775),(818,718),(834,661),(850,602),(872,550),(889,491),(890,440),(878,396),(881,320),(869,168)],'',None)
roads=[[(246,224),(284,295),(363,382),(451,467),(540,607),(613,702),(712,771),(814,817),(929,876),(1037,967),(1100,1103)],[(216,428),(286,447),(353,465),(393,511),(437,625),(477,689),(513,776)],[(464,466),(499,447),(546,443),(590,456),(651,520),(718,577),(806,651),(902,716),(1027,799),(1127,918)],[(842,76),(782,110),(769,169),(786,251),(792,326),(777,374),(739,429),(650,520),(538,615),(446,658)],[(906,367),(864,407),(805,465),(718,577),(613,703),(535,779),(446,820),(364,840)],[(981,488),(958,518),(932,570),(913,643),(900,718),(926,767),(1008,841),(1080,906),(1140,926)],[(721,1045),(689,1087),(720,1142),(828,1191),(945,1197),(1042,1153),(1120,1100)]]
data=dict(revision='landuse-w2-board-v7',dimensions=[1392,1305],coordinate_system='source-plan-local-pixel; north-up; NOT cadastral/WGS84',source=dict(file='research/map-led-v5/w2_a3_pamphlet.pdf',page=5,source_crop_pixels=[839,245,1303,680],source_render_scale=1,trace_scale=3,url='https://apply.lh.or.kr/lhapply/lhFile.do?fileid=66836710'),features=features,roads=roads,cameras={'whole':[40,50,1300,1240],'a1_a3_school':[60,355,665,485],'station_commerce':[375,645,675,410],'east_park':[760,400,500,540]},notes=['공식 토지이용계획의 주요 용도와 상대 배치를 직접 정리한 도해. 측량·분양경계 자료 아님.','왕숙2 A-1/A-3은 서로 다른 블록이며 같은 A번호의 왕숙1과 구별.','계획 시설의 개교·개통·운영을 보장하지 않음.','원본 일부 작은 필지·공급처리시설 등 생략. 도로 폭·보행시간 측정 금지.'])
P.joinpath('w2_board.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
im=Image.new('RGB',(1392,1305),'#F5F3EB');d=ImageDraw.Draw(im);svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1392" height="1305" viewBox="0 0 1392 1305"><rect width="1392" height="1305" fill="#F5F3EB"/>']
font='C:/Windows/Fonts/malgunbd.ttf'
for o in features:
 col=colors[o['type']];d.polygon(o['polygon'],fill=col,outline='#FFFFFF',width=3)
 svg.append(f'<polygon id="{o["id"]}" points="'+ ' '.join(f'{x},{y}' for x,y in o['polygon'])+f'" fill="{col}" stroke="white" stroke-width="3"/>')
for road in roads:
 d.line(road,fill='#FFFFFF',width=13,joint='curve');svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in road)+'" fill="none" stroke="white" stroke-width="13" stroke-linejoin="round"/>')
im.save(P/'w2_board_unlabelled.png')
P.joinpath('w2_board_unlabelled.svg').write_text(''.join(svg)+ '</svg>',encoding='utf-8')
for o in features:
 if not o['label']:continue
 x,y=o['anchor'];size=25 if len(o['label'])<5 else 25
 d.text((x,y),o['label'],font=ImageFont.truetype(font,size),fill='#203345',anchor='mm',stroke_width=0)
 svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" font-family="Malgun Gothic" font-weight="700" font-size="{size}" fill="#203345">{html.escape(o["label"])}</text>')
svg.append('</svg>');P.joinpath('w2_board.svg').write_text(''.join(svg),encoding='utf-8');im.save(P/'w2_board.png')
for key,(x,y,w,h) in data['cameras'].items():
 im.crop((x,y,x+w,y+h)).resize((round(w*1.5),round(h*1.5))).save(P/f'w2_preview_{key}.png')
print('Created',len(features),'source-verified simplified spatial areas; 4 camera previews')
