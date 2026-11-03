import React from 'react';
import { interpolate } from 'remotion';

const INK = '#173348', BLUE = '#286cda', CREAM = '#f6f4ef';
const FF = 'Pretendard, sans-serif';
const CL = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

function lp(frame: number, stage: number, s: number) {
  if (stage > s) return 1;
  if (stage < s) return 0;
  return interpolate(frame, [0, 45], [0, 1], CL);
}

/* ══ SupplyDynamics ══════════════════════════════════════════════════ */
type SR = { id: string; label: string; date: string; count: number; excluded?: boolean };
const STAGE_CARDS = [['입주가', '모임'], ['생활', '수요'], ['매매·임대', '대안']];

export function SupplyDynamics({ frame, stage, rows, active="all" }: { frame: number; stage: number; rows: SR[];active?:string }) {
 const branch=(s:number)=>lp(frame,stage,s);return <div style={{position:'absolute',left:80,top:200,width:1760,height:610,fontFamily:FF,color:INK}}>
 <div style={{display:'flex',gap:20,height:180}}>{rows.slice(0,4).map(r=><div data-zone={`supply-chip-${r.id}`} key={r.id} style={{flex:1,background:r.excluded?'#f0e8da':'#fffdf8',border:(active===r.id?'4px solid '+BLUE:'1px solid #cbd5dc'),borderRadius:10,padding:'14px 18px'}}><div style={{fontSize:28,fontWeight:700}}>{r.label}</div><div style={{fontSize:24,marginTop:5}}>{r.date}</div><div style={{fontSize:48,fontWeight:700,color:BLUE,marginTop:6}}>{r.count.toLocaleString()}<span style={{fontSize:26}}>세대{r.excluded?' · 별도':''}</span></div></div>)}</div>
 <div data-zone="supply-origin" style={{position:'absolute',left:0,top:220,width:480,height:310,background:'#e5edf8',border:'3px solid '+BLUE,borderRadius:14,display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',gap:20}}><div style={{fontSize:40,fontWeight:700}}>입주가 모임</div><div style={{fontSize:27}}>도시에 들어오는 가구 증가</div></div>
 {[{s:1,y:220,title:'생활시설 이용 수요',sub:'상권·서비스를 이용할 가구'},{s:2,y:390,title:'매매·임대 대안',sub:'단기적으로 비교할 선택지'}].map(x=><div data-zone={`supply-effect-${x.s}`} key={x.s} style={{position:'absolute',left:900,top:x.y,width:860,height:140,background:stage===x.s?'#e5edf8':'#fffdf8',border:'3px solid '+(stage>=x.s?BLUE:'#cbd5dc'),borderRadius:14,padding:'23px 32px'}}><div style={{fontSize:36,fontWeight:700,color:stage>=x.s?BLUE:INK}}>{x.title}</div><div style={{fontSize:27,marginTop:13}}>{x.sub}</div></div>)}
 <svg width={1760} height={550} style={{position:'absolute',inset:0,pointerEvents:'none'}}>{[{s:1,y:290},{s:2,y:460}].map(x=><path key={x.s} d={`M480,375 H650 V${x.y} H895`} pathLength={1} stroke={BLUE} strokeWidth={4} fill="none" strokeDasharray={1} strokeDashoffset={1-branch(x.s)}/>)}</svg>
 </div>;
}

/* ══ RestrictionEvents ═══════════════════════════════════════════════ */
type RR = { id: string; label: string; origin: string; duration: string; kind: string };
const KC: Record<string, string> = { resale: '#d45c28', residency: '#1a8a5c', lh: '#6b4faa' };
const CW = [280, 820, 620]; // col widths: name / origin / duration

export function RestrictionEvents({ frame, stage, rows }: { frame: number; stage: number; rows: RR[] }) {
  const lanes = rows.slice(0, 3);
  const HDR = ['이름', '기산 사건', '기간 / 구조'];

  return (
    <div style={{ position: 'absolute', left: 80, top: 200, width: 1760, height: 610, fontFamily: FF, color: INK }}>
      {/* ── header ── */}
      <div style={{ display: 'flex', marginBottom: 16, paddingLeft: 20 }}>
        {HDR.map((h, i) => (
          <div key={i} style={{ width: CW[i], fontSize: 26, color: '#7a8490', fontWeight: 600 }}>{h}</div>
        ))}
      </div>
      {/* ── lanes ── */}
      {lanes.map((r, li) => {
        const p = lp(frame, stage, li);
        const on = stage > li || p > 0.01;
        const kc = KC[r.kind] ?? BLUE;
        const num = r.duration.match(/\d+/)?.[0] ?? '';
        const unit = r.duration.replace(/\d+/, '').trim();
        return (
          <div data-zone={`restriction-${r.id}`} key={r.id} style={{ position: 'relative', height: 140, marginBottom: 18, borderRadius: 12, border: `2px solid ${on ? kc : '#cdc9c2'}`, background: on ? `${kc}12` : CREAM, overflow: 'hidden' }}>
            <svg style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 4 }}>
              <path d="M0,2 L1760,2" pathLength={1} stroke={kc} strokeWidth={4} fill="none"
                strokeDasharray={1} strokeDashoffset={1 - p} />
            </svg>
            <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 20px' }}>
              <div style={{ width: CW[0], fontSize: 28, fontWeight: 700, color: on ? kc : '#637580' }}>{r.label}</div>
              <div style={{ width: CW[1], fontSize: 31, color: on ? INK : '#637580' }}>{r.origin}</div>
              <div style={{ width: CW[2], display: 'flex', alignItems: 'baseline', gap: 6, color: on ? INK : '#637580' }}>
                <span style={{ fontSize: 48, fontWeight: 700, color: on ? kc : '#637580' }}>{num}</span>
                <span style={{ fontSize: 26, fontWeight: on ? 600 : 400 }}>{unit}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
