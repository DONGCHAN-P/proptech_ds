"""One-time, idempotent source patch; preserve the pre-education standalone map."""
from pathlib import Path
import shutil,json
HERE=Path(__file__).resolve().parent.parent
backup=HERE/'versions/v1-before-education'
if not backup.exists():
    backup.mkdir(parents=True)
    for name in ['index.html','build.py']:
        shutil.copy2(HERE/name,backup/name)
    shutil.copytree(HERE/'src',backup/'src')
app=HERE/'src/app.js';text=app.read_text(encoding='utf8')
if 'drawEducation();' not in text:
    text=text.replace("ctx.globalAlpha=1;ctx.restore();if(el('boundary').checked)","ctx.globalAlpha=1;ctx.restore();drawEducation();if(el('boundary').checked)",1)
    text=text.replace("let [x,y]=world(e.clientX,e.clientY);for(const i", "let [x,y]=world(e.clientX,e.clientY);if(hitEducation(x,y)){drag=null;return}for(const i",1)
    text=text.replace('select,filter,fit};resize();','select,filter,fit,educationStats:()=>({...eduStats}),showSchool};initEducation();resize();',1)
    text=text.replace('source:DATA.meta};let a=', 'layers:educationState(),source:DATA.meta};let a=',1)
    assert 'drawEducation();' in text and 'initEducation();' in text and 'if(hitEducation' in text
    app.write_text(text,encoding='utf8')
template=HERE/'src/index.template.html';text=template.read_text(encoding='utf8')
if 'id="education-schools"' not in text:
    controls='''<fieldset style="border:1px solid #dedbd0;border-radius:8px;margin:14px 0;padding:10px"><legend>학교·교통 레이어</legend><label class="toggle"><input style="width:auto" type="checkbox" id="education-schools" checked> 학교 위치 · 확대 시 표시</label><select id="education-grade" aria-label="학교급"><option value="">초·중·고 전체</option><option>초등학교</option><option>중학교</option><option>고등학교</option></select><label class="toggle"><input style="width:auto" type="checkbox" id="education-zones"> 통학구역·학군 경계</label><select id="education-zone-kind" aria-label="학교 구역 종류"><option value="elementary_zones">초등 통학구역·공동통학구역</option><option value="middle_zones">중학교 학구·학군</option><option value="high_zones">고등학교 학교군</option></select><small id="education-status"></small><p class="muted">학교: 2026.10.01 · 구역: 2026.09.20<br>보라: 초등 · 초록: 중등 · 주황: 고등<br>지하철 역·노선: 원자료 준비 중</p></fieldset>'''
    text=text.replace('<p class="muted" id="found">',controls+'<p class="muted" id="found">',1)
    text=text.replace('도로·역·개별 학원 위치를 생성하지 않습니다.','학교는 공식 좌표를 표시합니다. 도로·역·개별 학원 위치는 아직 수록하지 않았습니다.')
    text=text.replace('도형 1m 반올림</div>','도형 1m 반올림 · 학교·학구도: 한국교육시설안전원</div>')
    template.write_text(text,encoding='utf8')
build=HERE/'build.py';text=build.read_text(encoding='utf8')
if "data['education']" not in text:
    text=text.replace("raw=json.dumps(data,", "education=HERE/'layers/processed/education.json'\nif education.exists():\n data['education']=json.loads(education.read_text(encoding='utf8'));data['meta']['education']=data['education']['meta']\nraw=json.dumps(data,",1)
    text=text.replace("revision=hashlib.sha256(compressed+js.encode()", "js=(HERE/'src/education.js').read_text(encoding='utf8')+'\\n'+js\nrevision=hashlib.sha256(compressed+js.encode()",1)
    build.write_text(text,encoding='utf8')
schema=HERE/'data/schema.json';d=json.loads(schema.read_text(encoding='utf8'))
d['properties']['education']={'type':'object','required':['meta','schools','zones','links'],'description':'Optional school points and school-zone rings in native EPSG:5179; separate source dates.'}
schema.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print('Education source integration ready; baseline preserved')
