const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname,ep=path.resolve(root,'../..');
const old=JSON.parse(fs.readFileSync(path.join(root,'../script-v1/scene_proposals.json'),'utf8'));
const py=fs.readFileSync(path.join(root,'build.py'),'utf8');
const overrides=Object.fromEntries([...py.matchAll(/'(M\d+)':'''([\s\S]*?)'''/g)].map(m=>[m[1],m[2]]));
for(const s of old.scenes)if(overrides[s.scene_id])s.narration_text=overrides[s.scene_id];
old.revision='script-v2';old.status='working_draft_research_pending';
fs.writeFileSync(path.join(root,'working_scenes.json'),JSON.stringify(old,null,2));
