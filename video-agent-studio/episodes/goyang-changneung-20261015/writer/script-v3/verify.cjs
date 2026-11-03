const fs=require('fs'),crypto=require('crypto'),path=require('path');
const w=__dirname,ep=path.resolve(w,'../..'),m=JSON.parse(fs.readFileSync(path.join(w,'manifest.json'),'utf8'));
const source=fs.readFileSync(path.join(ep,'outputs/script-review-v2/script_v2.md'),'utf8').replace(/\r\n/g,'\n');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
let sum=0;
for(const c of m.chapters){
  const p=path.join(w,c.path),t=fs.readFileSync(p,'utf8');
  const expected=source.split('## '+c.scene_id+' · ')[1].split('### 낭독\n\n')[1].split('\n\n### 화면 지시')[0].trim();
  if(t!==expected||sha(p)!==c.sha256||[...t].length!==c.characters)throw Error(c.scene_id);
  sum+=[...t].length;
}
const s=JSON.parse(fs.readFileSync(path.join(w,'scene_proposals.json'),'utf8'));
if(sum!==m.total_characters||sum>7661||s.scenes.length!==10)throw Error('total');
for(let i=0;i<10;i++)if(s.scenes[i].narration_text!==fs.readFileSync(path.join(w,m.chapters[i].path),'utf8'))throw Error('scene');
if(sha(path.join(w,'script_v3.md'))!==sha(path.join(ep,'outputs/script-review-v3/script_v3.md')))throw Error('review copy');
console.log(JSON.stringify({chapters:10,sum,exact_match:true,hashes_match:true,scene_narration_match:true,review_copy_match:true,script_sha:sha(path.join(w,'script_v3.md')),manifest_sha:sha(path.join(w,'manifest.json'))}));
