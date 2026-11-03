import json,pathlib,html
from PIL import Image,ImageDraw,ImageFont
P=pathlib.Path(__file__).parent
# Source p6 displayed at 1888x1333 for manual factual transcription. Crop contains the left schematic only.
X,Y=103,270;W,H=763,610
features=[]
def f(i,t,pts,label,anchor):
 features.append(dict(id=i,type=t,polygon=[[x-X,y-Y] for x,y in pts],label=label,anchor=[anchor[0]-X,anchor[1]-Y]))
f('jinjeop2','neighbor',[(411,356),(420,329),(430,314),(449,305),(478,284),(502,278),(513,282),(502,293),(498,309),(490,326),(474,337),(455,346)],'진접2',(463,317))
f('wangsuk1','housing',[(412,363),(454,358),(491,357),(482,374),(474,388),(476,407),(469,430),(475,453),(471,470),(473,487),(485,501),(488,515),(495,520),(491,531),(488,543),(487,553),(480,553),(479,565),(488,581),(482,589),(491,601),(482,603),(465,596),(455,581),(447,573),(430,574),(418,584),(405,589),(414,597),(400,604),(390,613),(369,610),(343,611),(332,603),(330,589),(326,580),(333,566),(339,551),(339,535),(330,522),(317,514),(321,496),(326,480),(346,469),(349,428),(369,411),(389,390)],'왕숙1',(414,466))
f('industry','jobs',[(326,576),(339,565),(353,563),(360,539),(383,532),(410,527),(436,519),(465,526),(482,530),(488,541),(468,542),(457,544),(431,542),(406,546),(383,549),(375,556),(384,564),(413,568),(413,578),(392,580),(369,579),(350,587),(327,587)],'남부 산업·자족용지',(402,561))
f('wangsuk2','housing',[(473,635),(488,630),(501,631),(510,639),(524,638),(536,633),(546,634),(553,628),(561,640),(573,645),(586,646),(596,654),(601,663),(619,668),(600,676),(590,687),(591,695),(576,703),(564,697),(544,699),(528,695),(512,689),(505,682),(491,676),(480,664),(468,659),(478,652),(471,645),(484,647)],'왕숙2',(544,662))
f('yangjeong','neighbor',[(641,681),(657,673),(683,668),(706,658),(720,665),(747,674),(743,689),(749,700),(734,706),(730,714),(744,721),(743,728),(718,730),(694,725),(675,724),(672,714),(659,709),(648,698)],'양정역세권',(697,697))
roads=[[[104-X,318-Y],[250-X,421-Y],[397-X,378-Y],[509-X,355-Y],[568-X,378-Y],[866-X,324-Y]],[[103-X,612-Y],[247-X,561-Y],[427-X,512-Y],[543-X,542-Y],[866-X,596-Y]],[[147-X,657-Y],[387-X,592-Y],[593-X,674-Y],[866-X,719-Y]]]
data=dict(revision='macro-regions-v7',dimensions=[W,H],coordinate_system='source native schematic local pixels; NOT WGS84; no distance measurement',source=dict(file='research/landuse-v7/source_assets/city_business_p6.png',pdf='research/landuse-v7/source_assets/city_business_pdf.pdf',page=6,display_reference_dimensions=[1888,1333],display_crop=[X,Y,X+W,Y+H],actual_image_dimensions=[2064,1458],rights='Original reuse permission unverified; this is a newly styled factual relationship reconstruction.'),features=features,roads=roads,anchors=[dict(id=o['id'],label=o['label'],x=o['anchor'][0],y=o['anchor'][1],kind=o['type']) for o in features],cameras=dict(whole=[0,0,W,H],wangsuk_pair=[185,65,360,405],wangsuk1=[180,55,280,315],wangsuk2=[330,325,320,170]),notes=['남양주시 공개 개략도의 권역 위치관계를 바탕으로 직접 재구성. 법정·지적 경계 아님.','산단은 왕숙1 남부의 광역 용지관계이며 기업별 필지는 확정하지 않음.','별내·다산·왕숙천은 이 원도에서 정확히 특정할 근거가 없어 임의 점·선으로 추가하지 않음.','도로는 위치 인식용 배경 흐름이며 노선·완공 상태 안내 아님.'])
P.joinpath('macro_board.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
im=Image.new('RGB',(W*2,H*2),'#F5F3EB');d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#F5F3EB"/>']
for road in roads:
 d.line([(x*2,y*2) for x,y in road],fill='#D8DDDA',width=5);svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in road)+'" fill="none" stroke="#D8DDDA" stroke-width="2.5"/>')
for o in features:
 col={'housing':'#F5C96D','neighbor':'#D1D9D0','jobs':'#728CB8'}[o['type']];d.polygon([(x*2,y*2) for x,y in o['polygon']],fill=col,outline='#FFFFFF',width=3);svg.append('<polygon id="'+o['id']+'" points="'+' '.join(f'{x},{y}' for x,y in o['polygon'])+f'" fill="{col}" stroke="white" stroke-width="1.5"/>')
im.save(P/'macro_board_unlabelled.png');P.joinpath('macro_board_unlabelled.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')
for o in features:
 x,y=o['anchor'];label=o['label'];size=17 if o['type']=='housing' else 12
 d.text((x*2,y*2),label,font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',size*2),fill='#203345',anchor='mm')
 svg.append(f'<text x="{x}" y="{y}" font-family="Malgun Gothic" font-size="{size}" font-weight="700" fill="#203345" text-anchor="middle" dominant-baseline="middle">{html.escape(label)}</text>')
im.save(P/'macro_board.png');P.joinpath('macro_board.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')
print('Macro region faces',len(features))
