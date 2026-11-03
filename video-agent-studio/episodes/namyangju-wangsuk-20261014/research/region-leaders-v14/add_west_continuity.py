import json,pathlib
p=pathlib.Path(__file__).parent;d=json.loads((p/'w1_middle_geometry.json').read_text(encoding='utf-8'))
green=[[240,470],[240,670],[219,780],[196,830],[157,872],[132,903],[80,932],[59,982],[55,1040],[16,1040],[26,980],[46,930],[85,900],[93,853],[120,817],[141,780],[161,743],[166,705],[177,660],[195,610],[207,567],[211,535],[220,510]]
water=[[239,470],[229,506],[224,550],[217,595],[203,641],[189,689],[187,735],[170,786],[156,831],[130,873],[99,901],[59,936],[39,978],[32,1040],[22,1040],[29,976],[49,932],[91,895],[121,867],[145,826],[160,782],[177,733],[179,687],[193,637],[207,591],[213,546],[218,502],[231,470]]
for name,kind,xy in [('west_riverbank_continuity','park',green),('west_river_continuity','water',water)]:d['features'].insert(0,dict(id='middle_'+name,type=kind,kind=kind,label='',polygon=[[790+x/4,300+y/4]for x,y in xy],source='LH W1 A1 pamphlet p5 west strip crop[790300850560]4x',status='qualified_hand_digitized_plan_not_survey'))
d['west_reference']='w1_middle_west_reference.png';d['notes'].append('서측하천/수변녹지croppedcontinuity보완;동일PDF좌표이며미세지정경계추정X')
(p/'w1_middle_geometry.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
h=json.loads((p/'handoff.json').read_text(encoding='utf-8'));h['outputs']+=['w1_middle_geometry.json','w1_middle_reference.png','w1_middle_west_reference.png'];h['validation'].append('중앙연속성sourcePDF좌표75개큰면/도로/경계추가');(p/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8');print('middle features',len(d['features']))
