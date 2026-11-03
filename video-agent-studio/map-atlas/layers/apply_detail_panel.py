from pathlib import Path
H=Path(__file__).resolve().parents[1]
p=H/'src/index.template.html';s=p.read_text(encoding='utf8').replace('<aside id="right">','<aside id="right"><button id="back-to-list">← 단지 목록으로</button>');p.write_text(s,encoding='utf8')
p=H/'src/app.js';s=p.read_text(encoding='utf8').replace('function select(i,fly=false){selected=i;','function select(i,fly=false){document.body.classList.toggle(\'detail-open\',i!==null);selected=i;');p.write_text(s,encoding='utf8')
for name,mark in [('education.js','function showSchool(id){'),('transit.js','function showStation(id){')]:
 p=H/'src'/name;s=p.read_text(encoding='utf8').replace(mark,mark+"\n document.body.classList.add('detail-open');");p.write_text(s,encoding='utf8')
p=H/'src/explorer.js';s=p.read_text(encoding='utf8').replace('function initExplorer(){',"function initExplorer(){\n el('back-to-list').onclick=()=>{document.body.classList.remove('detail-open','show-detail');if(innerWidth<=850)document.body.classList.add('show-search')};\n el('reset').addEventListener('click',()=>document.body.classList.remove('detail-open')); ");p.write_text(s,encoding='utf8')
p=H/'src/styles.css';s=p.read_text(encoding='utf8')+'''\n/* One persistent discovery rail: results -> detail -> back. */
#right{display:none;left:12px;right:auto;top:12px;bottom:70px;width:320px;border-radius:10px;background:#fffffff5}.detail-open #right{display:block}.detail-open #left{display:none}#back-to-list{width:100%;text-align:left;margin-bottom:16px;color:#6655d9}#zoom-tools{right:20px}#scale{left:350px}.capture #right{display:none}@media(max-width:850px){.detail-open #right{display:none}.detail-open.show-detail #right{display:block}.show-search #left{display:block}#scale{left:15px}}
''';p.write_text(s,encoding='utf8')
