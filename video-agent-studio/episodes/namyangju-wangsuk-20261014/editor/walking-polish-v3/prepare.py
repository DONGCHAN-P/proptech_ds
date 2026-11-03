from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[5]
source=ROOT/'video/src/NamyangjuRailRouteProofV2.tsx'
out=ROOT/'video/src/NamyangjuRailRouteProofV3.tsx'
s=source.read_text(encoding='utf-8').replace('NamyangjuRailRouteProofV2','NamyangjuRailRouteProofV3')
a=s.index('function Walker(')
b=s.index('function Bus(',a)
s=s[:a]+'''function walkFacing(points:number[][],progress:number,pr:any){const a=pointAlong(points,Math.max(0,progress-.025),pr),b=pointAlong(points,Math.min(1,progress+.025),pr);return b[0]-a[0]<-2?-1:1}
function Walker({x,y,moving=false,color=amber,facing=1}:any){
 const f=useCurrentFrame(),cycle=moving?f*.26:0,stride=moving?Math.sin(cycle):0;
 const bounce=moving?Math.abs(Math.sin(cycle))*.8:0;
 const jacket=color===amber?'#b77e15':'#0786b4',pants='#2b3d47';
 const leg=(side:number)=>{const swing=stride*side*23,knee=Math.max(0,-stride*side)*24;return <g key={side} transform={`translate(${side*1.3} -19) rotate(${swing})`}><path d="M-2.6 0L2.5 0L2.8 10L-2.6 10Z" fill={pants}/><g transform={`translate(0 10) rotate(${knee})`}><path d="M-2.6 -1L2.8 -1L2.6 8L-2.1 8Z" fill={pants}/><path d="M-2.2 6.5L2.8 6.5L7.4 8.5L7.4 10L-2.8 10Z" fill="#17262e"/></g></g>};
 const arm=(side:number)=>{const swing=-stride*side*22;return <g key={side} transform={`translate(${side*4} -36) rotate(${swing})`}><path d="M-2.2 0L2.2 0L2.4 10L-1.8 11Z" fill={jacket}/><path d="M-1.8 9L2.4 9L4.2 16L.7 17Z" fill={jacket}/><ellipse cx={2.1} cy={17.2} rx={2} ry={2.4} fill="#e5b891"/></g>};
 return <g transform={`translate(${x} ${y})`}><circle cx={0} cy={-12} r={16} fill="#fffdf5" stroke={color} strokeWidth={1.25}/><g transform={`translate(0 ${-bounce*.48}) scale(${facing*.48} .48)`}>
 {leg(-1)}{arm(-1)}
 <path d="M-7 -36Q-12 -35 -11 -25L-7 -24Z" fill="#43535c"/>
 <path d="M-5.2 -38Q0 -41 5.7 -37L6.3 -26L4.8 -19L-5 -19L-6.4 -29Z" fill={jacket}/>
 <path d="M-1.5 -42L2.8 -42L3.3 -37L-1.9 -37Z" fill="#e5b891"/>
 <ellipse cx={1.3} cy={-47} rx={4.9} ry={5.5} fill="#e5b891"/>
 <path d="M-3.6 -47Q-4 -53 1.4 -53Q6.4 -53 6.2 -48L2.4 -49L-2 -46Z" fill="#263740"/>
 <path d="M5 -48L7.1 -46L5 -45Z" fill="#e5b891"/>
 {leg(1)}{arm(1)}
 </g></g>;
}
''' +s[b:]
s=s.replace('<Walker x={wp[0]} y={wp[1]}/>','<Walker x={wp[0]} y={wp[1]} moving={walk>0&&walk<1} facing={walkFacing(c.walkPoints,walk,pr)}/>')
s=s.replace('<Place p={c.station} pr={pr} color={pink}/>','<Place p={c.station} pr={pr} color={pink} align="left"/>')
a=s.index('{busActive?<Bus')
b=s.index('</g></g>}',a)+len('</g></g>}')
s=s[:a]+'''{busActive?<Bus x={bp[0]} y={bp[1]}/>:<Walker x={lp[0]} y={lp[1]} color={blue} moving={(accessActive&&access>0&&access<1)||(!accessActive&&!waiting&&egress>0&&egress<1)} facing={walkFacing(legPoints,accessActive||waiting?access:egress,pr)}/>}'''+s[b:]
out.write_text(s,encoding='utf-8')
manifest={'input_source':str(source),'input_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source':str(out),'source_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'data_reused_readonly':'video/public/namyangju-rail-route-proof-v2/proof_data.json','audio_reused_readonly':'video/public/namyangju-rail-route-proof-v1/original_audio_94_174.wav','change_scope':'walking marker SVG geometry and stride only','old_figure_height_px':59,'new_nominal_figure_height_px':25.44,'badge_diameter_px':32,'badge_bounce':False,'foot_anchor':True,'heading':'horizontal facing from smoothed route tangent, never body rotation','moving_states':'walk/access/egress progress strictly >0 and <1; wait and arrival idle','paid_generation':False,'full_master_modified':False}
(Path(__file__).parent/'input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('walking v3 source prepared')
