## 논의 (4줄)

1. **SupplyDynamics**: 칩 4개는 항상 표시, stage마다 45f 안에 SVG pathLength=1 선 draw → hold 후 다음 카드 강조, 가격인과 단정 없음.
2. **RestrictionEvents**: 최대 3레인 고정 그리드, 각 lane은 이름·기산사건·기간 세 열을 고정 폭으로 배치해 겹침 차단, kind별 색상 구분.
3. 두 컴포넌트 모두 `pathLength={1}+strokeDashoffset+interpolate clamp`로 진행선 제어, 카메라 줌·pulse·점멸 없음.
4. 날짜·법규 하드코딩 없이 전부 외부 props만 표시, 숫자 48px·본문 26px 이상 유지.

```tsx
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

export function SupplyDynamics({ frame, stage, rows }: { frame: number; stage: number; rows: SR[] }) {
  const chips = rows.slice(0, 4);
  // card width=480, gap=160 → 3*480+2*160=1760
  const cx = (i: number) => i * 640 + 240; // card center-x

  return (
    <div style={{ position: 'absolute', left: 80, top: 200, width: 1760, height: 610, fontFamily: FF, color: INK }}>
      {/* ── chips ── */}
      <div style={{ display: 'flex', gap: 20, height: 140 }}>
        {chips.map(r => (
          <div key={r.id} style={{ flex: 1, background: r.excluded ? '#d8d4cd' : INK, color: r.excluded ? '#888' : CREAM, borderRadius: 10, padding: '14px 18px', opacity: r.excluded ? 0.5 : 1 }}>
            <div style={{ fontSize: 26 }}>{r.label}</div>
            <div style={{ fontSize: 20, opacity: 0.6, marginTop: 4 }}>{r.date}</div>
            <div style={{ fontSize: 48, fontWeight: 700, marginTop: 6 }}>{r.excluded ? '제외' : r.count.toLocaleString()}</div>
          </div>
        ))}
      </div>
      {/* ── connector lines (pathLength=1) ── */}
      <svg style={{ position: 'absolute', top: 340, left: 0, width: 1760, height: 20 }} overflow="visible">
        {[0, 1].map(i => {
          const p = lp(frame, stage, i + 1);
          const x1 = cx(i) + 240, x2 = cx(i + 1) - 240;
          return (
            <path key={i} d={`M${x1},10 L${x2},10`} pathLength={1}
              stroke={BLUE} strokeWidth={3} fill="none" markerEnd="url(#arr)"
              strokeDasharray={1} strokeDashoffset={1 - p} />
          );
        })}
        <defs>
          <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill={BLUE} />
          </marker>
        </defs>
      </svg>
      {/* ── stage cards ── */}
      <div style={{ position: 'absolute', top: 190, left: 0, display: 'flex', gap: 160 }}>
        {STAGE_CARDS.map(([l1, l2], i) => {
          const p = lp(frame, stage, i);
          const on = stage > i || p > 0.01;
          return (
            <div key={i} style={{ width: 480, height: 220, borderRadius: 14, border: `3px solid ${on ? BLUE : '#c0bcb5'}`, background: on ? `${BLUE}1a` : CREAM, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, opacity: on ? 1 : 0.45 }}>
              <div style={{ fontSize: 36, fontWeight: 700 }}>{l1}</div>
              <div style={{ fontSize: 36, fontWeight: 700 }}>{l2}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
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
          <div key={i} style={{ width: CW[i], fontSize: 22, color: '#7a8490', fontWeight: 600 }}>{h}</div>
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
          <div key={r.id} style={{ position: 'relative', height: 140, marginBottom: 18, borderRadius: 12, border: `2px solid ${on ? kc : '#cdc9c2'}`, background: on ? `${kc}12` : CREAM, overflow: 'hidden' }}>
            <svg style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 4 }}>
              <path d="M0,2 L1760,2" pathLength={1} stroke={kc} strokeWidth={4} fill="none"
                strokeDasharray={1} strokeDashoffset={1 - p} />
            </svg>
            <div style={{ display: 'flex', alignItems: 'center', height: '100%', padding: '0 20px' }}>
              <div style={{ width: CW[0], fontSize: 28, fontWeight: 700, color: on ? kc : '#b0aaa3' }}>{r.label}</div>
              <div style={{ width: CW[1], fontSize: 26, color: on ? INK : '#b8b2ab' }}>{r.origin}</div>
              <div style={{ width: CW[2], display: 'flex', alignItems: 'baseline', gap: 6, color: on ? INK : '#b8b2ab' }}>
                <span style={{ fontSize: 48, fontWeight: 700, color: on ? kc : '#c0bbb3' }}>{num}</span>
                <span style={{ fontSize: 26, fontWeight: on ? 600 : 400 }}>{unit}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

**사용 예시** (부모가 제목/자막/출처 분리):
```tsx
<SupplyDynamics frame={f} stage={2} rows={[
  { id:'s4', label:'S4 당첨', date:'2026-03', count:780 },
  { id:'s6', label:'S6', date:'2026-06', count:430 },
  { id:'nb1', label:'인근 A', date:'2026-09', count:620 },
  { id:'nb2', label:'인근 B', date:'2026-12', count:447 },
]} />

<RestrictionEvents frame={f} stage={1} rows={[
  { id:'resale', label:'전매제한', origin:'당첨자 발표일', duration:'3년', kind:'resale' },
  { id:'reside', label:'거주의무',  origin:'거주의무 개시일', duration:'3년', kind:'residency' },
  { id:'lh',     label:'LH 환매',  origin:'입주지정일',    duration:'5년', kind:'lh' },
]} />
```