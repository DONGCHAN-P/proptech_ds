import fs from 'node:fs';let s=fs.readFileSync('video/src/PilotV2.tsx','utf8');s=s.replace("const navy='#132B39',cream='#F4F1E9',amber='#E9AD52',muted='#81939B';","const navy='#111111',cream='#F6F4EF',amber='#FFE45C',muted='#6E6E6E';");
s=s.replaceAll('#A97226','#2F6FED').replaceAll('#C27C22','#2F6FED').replaceAll('#237F85','#E5484D').replaceAll('#2E7380','#E5484D').replaceAll('#60747b','#6E6E6E').replaceAll('#64767d','#6E6E6E');
s=s.replace("const colors=['#2F6FED','#E5484D','#80949D','#8D7EAF','#A2926E'];","const colors=['#E5484D','#2F6FED','#9AA0A6','#777E87','#B4A8A0'];");
s=s.replace('<Buildings/>',"<div style={{borderLeft:'6px solid #2F6FED',padding:'25px 0 25px 45px'}}><div style={{fontSize:30,color:'#6E6E6E'}}>동탄2신도시 · 전용 84㎡</div><div style={{fontSize:68,fontWeight:800,lineHeight:1.2,marginTop:20}}>동탄역<br/>롯데캐슬</div><div style={{fontSize:28,color:'#6E6E6E',marginTop:28}}>2017 분양 → 2026 거래</div></div>");
s=s.replace('<div style={{position:\'absolute\',left:96,right:96,bottom:126','<div className="caption" style={{position:\'absolute\',left:96,right:96,bottom:126');
s=s.replace("<div style={{position:'absolute',bottom:88,left:90,right:90",'<div className="caption" style={{position:\'absolute\',bottom:88,left:90,right:90');
s=s.replace('function Pilot(){let cursor=0;return <AbsoluteFill>',"function Pilot(){let cursor=0;return <AbsoluteFill style={{background:'#15161A'}}><div style={{position:'absolute',top:16,left:98,right:98,display:'flex',justifyContent:'space-between',color:'#F6F4EF',fontFamily:'Pretendard',fontSize:22}}><b><span style={{color:'#FFE45C'}}>▏</span>데이터로 보는 부동산</b><span>신도시 시리즈 · <b style={{color:'#FFE45C'}}>광교·동탄</b></span></div><div style={{position:'absolute',left:96,top:60,width:1728,height:972,borderRadius:18,overflow:'hidden'}}><div style={{width:1920,height:1080,position:'relative',transform:'scale(.9)',transformOrigin:'top left'}}>");
s=s.replace("})}</AbsoluteFill>}","})}</div></div></AbsoluteFill>}");
s=s.replace("id=\"NewtownV2\"","id=\"NewtownV3\"");
s=s.replace("font-weight:700 900}","font-weight:700 900} .caption{background:#fff;border:2px solid #e3dfb0;border-radius:10px;padding:18px 28px;box-shadow:0 4px 12px #0002;font-size:32px!important;left:300px!important;right:300px!important} ");
fs.writeFileSync('video/src/PilotV3.tsx',s);console.log('V3 restyle created, audio reused');

