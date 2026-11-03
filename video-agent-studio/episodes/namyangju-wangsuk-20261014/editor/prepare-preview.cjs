// Local preparation only. Never renders final video or calls paid APIs.
const fs = require('fs');
const path = require('path');
const {spawnSync} = require('child_process');
const root = path.resolve(__dirname, '..');
const repo = path.resolve(root, '../../..');
const scenes = JSON.parse(fs.readFileSync(path.join(root,'scenes.json'),'utf8'));
const assetFile=fs.existsSync(path.join(root,'visual/assets_v2.json'))?'visual/assets_v2.json':'visual/assets_v1.json';
const assets = JSON.parse(fs.readFileSync(path.join(root,assetFile),'utf8'));
const font = fs.readFileSync(path.join(repo,'video/public/fonts/Pretendard-Regular.woff2')).toString('base64');
let cursor = 0;
const assembly = scenes.scenes.map(s => {
  const start = cursor; cursor += s.estimated_duration_seconds;
  return {scene_id:s.scene_id,provisional_start_s:start,provisional_end_s:cursor,timing_basis:s.timing_basis,
    sources:assets.assets.filter(a=>a.scene_ids.includes(s.scene_id)).map(a=>a.actual_file),
    needs:s.scene_id==='S008'?['S008 distinct evidence-status recap card']:['actual geography and photo where specified'],
    audio:null,final_edit_allowed:false};
});
fs.writeFileSync(path.join(__dirname,'assembly_provisional_v1.json'), JSON.stringify({revision:'editor-prep-v1',script_revision:'script-v2',scenes_revision:'scenes-v2',visual_revision:assets.revision,framework:'existing video Remotion + PilotV11 / v14 assembly style',fps:30,width:1920,height:1080,timing_locked:false,total_estimate_s:cursor,content_box:{x:100,y:30,width:1720,height:820},caption_box:{x:100,y:910,width:1720,height:125},scenes:assembly},null,2));
const chrome=path.join(repo,'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe');
const results=[];
for(const id of ['S001','S007','S008']){
  const a=assets.assets.find(a=>a.scene_ids.includes(id)&&a.actual_file.endsWith('.svg')&&(id!=='S008'||a.actual_file.includes('S008')));
  if(!a)continue;
  let svg=fs.readFileSync(path.join(root,a.actual_file),'utf8').replace('Noto Sans KR, Malgun Gothic, sans-serif','PreviewPretendard, Malgun Gothic, sans-serif');
  const caption=id==='S001'?'전편의 다섯 질문으로 남양주를 읽습니다.':id==='S008'?'내 생활에 중요한 질문부터 확인합니다.':'LH 표시가격과 실거래가격의 조건을 구분합니다.';
  const html=`<!doctype html><meta charset="utf-8"><style>@font-face{font-family:PreviewPretendard;src:url(data:font/woff2;base64,${font})}body{margin:0;background:#F6F4EF;font-family:PreviewPretendard}svg{position:absolute;left:100px;top:30px;width:1720px;height:820px}.caption{position:absolute;left:100px;top:910px;width:1720px;height:125px;background:white;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:42px;color:#111}.label{position:absolute;left:100px;top:870px;color:#6E6E6E;font-size:24px}</style>${svg}<div class="label">편집 기술 시안 · 잠정 시간 · 음성 없음</div><div class="caption">${caption}</div>`;
  const hp=path.join(__dirname,`${id}_preview_v1.html`), png=path.join(__dirname,`${id}_preview_v1.png`);
  fs.writeFileSync(hp,html);
  const r=spawnSync(chrome,['--headless','--no-sandbox','--disable-gpu','--hide-scrollbars','--allow-file-access-from-files','--window-size=1920,1080','--virtual-time-budget=3000',`--screenshot=${png}`,`file:///${hp.replace(/\\/g,'/')}`],{encoding:'utf8',timeout:20000});
  results.push({scene_id:id,exit_code:r.status,png_exists:fs.existsSync(png),png_bytes:fs.existsSync(png)?fs.statSync(png).size:0,font:'embedded existing Pretendard-Regular.woff2',error:r.error?.message??null});
}
fs.writeFileSync(path.join(__dirname,'preview_technical_v1.json'),JSON.stringify(results,null,2));
console.log(JSON.stringify(results));
