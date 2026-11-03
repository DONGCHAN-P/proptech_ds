const fs=require('fs'),path=require('path');
const E=__dirname,EP=path.resolve(E,'../..'),O=path.join(EP,'outputs/production-v6-ui-r5'),old=path.join(EP,'outputs/production-v6-preview');
const p=JSON.parse(fs.readFileSync(path.join(old,'project_r4.json'))),rendered=JSON.parse(fs.readFileSync(path.join(old,'rendered_project_r4.json')));
function mapping(x){let b=x.props,n=Number(x.unit?.match(/_(\d+)/)?.[1]),s=x.scene_id,mode='baseline',focus=b.focus||'all',phase='';
 if(b.board==='commute')mode='commute';
 if(s==='M001'&&n>=3){mode='plan';phase=({3:'layout',5:'station',6:'agenda'})[n]||'';}
 if(s==='M003'){
  if(n===1)mode='photo';if(n===2||n===3)mode='transit';
  if(n>=7&&n<=12){mode='rail';focus=({7:'all',8:'GTX',9:'S5',10:'waiting',11:'sameyear',12:'waiting'})[n];phase=n===12?'twostep':'';}
 }
 if(b.board==='price'){mode='price';phase=n>=6?'delta':'';}
 if(s==='M005'&&[4,5,6,7,8,9,10,11,12].includes(n)){mode='school';focus=n<=6?'S5':n<=9?'S1':'S4';phase=/공원|하천|녹지/.test(b.caption)?'park':'education';}
 if(b.board==='supply'){mode='supply';focus=({1:'overview',2:'overview',3:'S5',4:'total',5:'S6',6:'S5',7:'effects',8:'total'})[n]||'overview';phase=n>=4?'complete':'';if(n===7)phase='effects';if(n===3){focus=/S4/.test(b.caption)?'S4':/S1/.test(b.caption)?'S1':/S5/.test(b.caption)?'S5':'overview';}}
 if(b.board==='family'){mode='family';focus='all';phase=({3:'cost',4:'commute',5:'usecase',6:'updates'})[n]||'';}
 if(b.board==='decision'){mode='decision';phase=({9:'series',10:'access',11:'criteria'})[n]||'';}
 return {mode,focus,phase,caption:b.caption||'',baseProps:b};
}
// Internal clause timing is proportional to text length, not acoustic forced alignment.
const splitRules={
 'M005_010.wav':[['S4는 가칭 6유치원과 6초등학교의 공고상 목표가','S4'],['입주 예정월과 같은 2030년 3월입니다.','S4']],
 'M001_004.wav':[['오늘 비교할 S5는 세 후보 중 입주 예정이 빠른 곳,','S5'],['S4는 원흥 기존 생활권과의 접점을 살펴볼 곳,','S4'],['S1은 학교·공원 배치와 별도 입주 일정을 함께 볼 곳입니다.','S1']],
 'M003_002.wav':[['현재 주변에서 서울로 나가는 길은 원흥역 3호선 축과,','원흥'],['도래울에서 새절역 6호선으로 연결하는 축을 먼저 보겠습니다.','새절']],
 'M003_008.wav':[['2026년 9월 말 발표 기준 GTX-A 창릉역은 2030년 개통 예정,','GTX'],['고양은평선은 2031년 12월 목표입니다.','EP']],
 'M003_009.wav':[['S5는 2028년 1월,','S5'],['S1은 2029년 5월,','S1'],['S4는 2030년 3월 입주 예정입니다.','S4']],
 'M008_002.wav':[['현재 집의 계약 종료,','contract'],['아이의 입학,','school'],['희망 이사 시점을 적고','move'],['후보의 입주·학교·철도 일정을 나란히 놓습니다.','all']]
};
let intervals=[];
for(let i=0;i<p.intervals.length;){let x=p.intervals[i],group=p.intervals.filter(y=>y.unit===x.unit),rule=splitRules[x.unit];if(rule){let start=group[0].start_frame,end=group.at(-1).end_frame,total=rule.reduce((a,r)=>a+r[0].length,0),used=0;for(let [j,[text,focus]]of rule.entries()){let stop=j===rule.length-1?end:start+Math.round((end-start)*(used+text.length)/total),begin=start+Math.round((end-start)*used/total);let y={...x,start_frame:begin,end_frame:stop,duration_frames:stop-begin,props:{...x.props,caption:text}},v=mapping(y);v.focus=focus;intervals.push({...y,r5_props:v});used+=text.length;}i+=group.length;}else{intervals.push({...x,r5_props:mapping(x)});i++;}}
for(let x of intervals){let q=x.r5_props;x.semantic_key=JSON.stringify([q.mode,q.focus,q.phase,q.mode==='baseline'||q.mode==='school'?{board:q.baseProps.board,cue:q.baseProps.cue,variant:q.baseProps.variant}:null]);}
let visual=[],lastKey=null,entry=0;
for(let x of intervals){if(x.semantic_key!==lastKey){entry=x.start_frame;lastKey=x.semantic_key;}
 if(x.r5_props.mode==='baseline'){for(let v of rendered.visual_intervals.filter(v=>v.start_frame>=x.start_frame&&v.end_frame<=x.end_frame))visual.push({...v,source_file:path.join(old,v.frame_file),reused_r4:true});continue;}
 let motionEnd=Math.min(x.end_frame,entry+45);for(let f=x.start_frame;f<motionEnd;f++)visual.push({scene_id:x.scene_id,start_frame:f,end_frame:f+1,duration_frames:1,render_props:{...x.r5_props,motionFrame:f-entry},semantic_key:x.semantic_key});if(motionEnd<x.end_frame)visual.push({scene_id:x.scene_id,start_frame:Math.max(x.start_frame,motionEnd),end_frame:x.end_frame,duration_frames:x.end_frame-Math.max(x.start_frame,motionEnd),render_props:{...x.r5_props,motionFrame:44},semantic_key:x.semantic_key});
}
const norm=s=>s.replace(/\s/g,'');if(norm(intervals.map(x=>x.props.caption||'').join(''))!==norm(p.intervals.map(x=>x.props.caption||'').join('')))throw Error('Spoken caption text changed');
for(let [a,b]of [[0,p.intro_at],[p.intro_at+150,p.outro_start]]){let rows=visual.filter(x=>x.start_frame>=a&&x.end_frame<=b);if(rows.reduce((n,x)=>n+x.duration_frames,0)!==b-a)throw Error('Timeline gap');}
fs.mkdirSync(O,{recursive:true});let out={...p,revision:'v6-ui-r5',intervals,visual_intervals:visual,timing_note:'Measured unit boundaries; proportional clause estimates; no forced alignment',unchanged_audio:'../production-v6-preview/full_mix_r2.m4a',r4_source:path.join(old,'changneung_full_v6_preview_r4.mp4')};fs.writeFileSync(path.join(O,'project_r5.json'),JSON.stringify(out,null,2));
function tc(f){let m=Math.round(f/30*1000),h=Math.floor(m/3600000);m%=3600000;let n=Math.floor(m/60000);m%=60000;return `${String(h).padStart(2,'0')}:${String(n).padStart(2,'0')}:${String(Math.floor(m/1000)).padStart(2,'0')},${String(m%1000).padStart(3,'0')}`;}
fs.writeFileSync(path.join(O,'changneung_v6_ui_r5.srt'),intervals.filter(x=>x.props.caption).map((x,i)=>`${i+1}\n${tc(x.start_frame)} --> ${tc(x.end_frame)}\n${x.props.caption}\n`).join('\n'));
console.log(JSON.stringify({intervals:intervals.length,states:visual.length,new_states:visual.filter(x=>!x.reused_r4).length,reused_states:visual.filter(x=>x.reused_r4).length,total_frames:p.duration_frames}));
