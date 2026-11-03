import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {Page} from '../Cards';

const W = 1650;
const H = 928;
const SUB = 196;

export const Head: React.FC<{kick: string; title: string; note?: string}> = ({
  kick,
  title,
  note,
}) => (
  <div style={{position: 'absolute', left: 92, top: 68, right: 92}}>
    <div style={{fontSize: 28, fontWeight: 700, color: C.sub}}>{kick}</div>
    <div
      style={{fontSize: 52, fontWeight: 800, letterSpacing: '-.03em', marginTop: 6}}
      dangerouslySetInnerHTML={{
        __html: title
          .replace(/<b>/g, '<b style="color:' + C.win + '">')
          .replace(/<em>/g, '<em style="color:' + C.lose + '">'),
      }}
    />
    {note ? (
      <div style={{fontSize: 25, color: C.sub, marginTop: 12, lineHeight: 1.45, maxWidth: 1300}}>
        {note}
      </div>
    ) : null}
  </div>
);

/** 장면 전체에 걸친 진행도. 0 → 1. 파이썬의 ease(p) 자리를 스프링이 맡는다. */
export const useProgress = (dur: number, span = 0.86) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({
    frame,
    fps,
    durationInFrames: Math.max(2, Math.round(dur * fps * span)),
    config: {damping: 200, mass: 1.4},
  });
};

// ── 대장 단지 꺾은선 ────────────────────────────────────────────────────
const PX0 = 182;
const PX1 = 1180;
const PY0 = 206;
const PY1 = 604;
const Y0 = 2010;
const Y1 = 2026;
const VMAX = 24;

export const Line: React.FC<{flags: any[]; dur: number}> = ({flags, dur}) => {
  const e = useProgress(dur, 0.88);
  const yc = Y0 + (Y1 - Y0) * e;
  const X = (y: number) => PX0 + ((y - Y0) / (Y1 - Y0)) * (PX1 - PX0);
  const Y = (v: number) => PY1 - (Math.min(v, VMAX) / VMAX) * (PY1 - PY0);

  const grid: React.ReactNode[] = [];
  for (let v = 0; v <= VMAX; v += 5) {
    grid.push(<line key={'g' + v} x1={PX0} y1={Y(v)} x2={PX1} y2={Y(v)} stroke={C.line} strokeWidth={1.5} />);
    grid.push(
      <text key={'gt' + v} x={PX0 - 22} y={Y(v) + 10} textAnchor="end" fontSize={26} fill={C.sub}>
        {v}억
      </text>,
    );
  }
  for (let y = Y0; y <= Y1; y += 4) {
    grid.push(
      <text key={'x' + y} x={X(y)} y={PY1 + 48} textAnchor="middle" fontSize={26} fill={C.sub}>
        {y}
      </text>,
    );
  }

  const areas: React.ReactNode[] = [];
  const lines: React.ReactNode[] = [];
  const tips: {f: any; x: number; y: number; v: number}[] = [];
  flags.forEach((f, i) => {
    // 그림판은 2010년부터다. 2006년부터 있는 단지는 잘라 쓴다.
    const ser = (f.series as [number, number][]).filter((s) => s[0] >= Y0);
    const pts = ser.filter((s) => s[0] <= yc).map((s) => [s[0], s[1]] as [number, number]);
    const nxt = ser.find((s) => s[0] > yc);
    if (pts.length && nxt) {
      const last = pts[pts.length - 1];
      const t = (yc - last[0]) / (nxt[0] - last[0]);
      pts.push([yc, last[1] + (nxt[1] - last[1]) * t]);
    }
    if (pts.length < 2) return;
    const d = pts.map((q, k) => (k ? 'L' : 'M') + X(q[0]).toFixed(1) + ',' + Y(q[1]).toFixed(1)).join(' ');
    areas.push(
      <path key={'a' + i}
        d={d + ' L' + X(pts[pts.length - 1][0]) + ',' + PY1 + ' L' + X(pts[0][0]) + ',' + PY1 + ' Z'}
        fill={f.color} opacity={0.085} />,
    );
    lines.push(
      <path key={'l' + i} d={d} fill="none" stroke={f.color} strokeWidth={6}
        strokeLinecap="round" strokeLinejoin="round" />,
    );
    const last = pts[pts.length - 1];
    tips.push({f, x: X(last[0]), y: Y(last[1]), v: last[1]});
  });

  // 여섯 줄이면 끝값이 바닥에 뭉친다. 최소 간격을 지켜 밀어 둔다.
  tips.sort((a, b) => a.y - b.y);
  const GAP = 44;
  const FLOOR = H - SUB - 14;
  let used = tips.length ? Math.min(tips[0].y + 10, FLOOR - tips.length * GAP) - GAP : 0;
  const labels = tips.map((t, i) => {
    const ly = Math.max(t.y + 10, used + GAP);
    used = ly;
    return (
      <g key={i}>
        <circle cx={t.x} cy={t.y} r={9} fill={t.f.color} stroke="#fff" strokeWidth={3} />
        {Math.abs(ly - t.y) > 14 ? (
          <line x1={t.x + 10} y1={t.y} x2={t.x + 22} y2={ly - 10} stroke={t.f.color} strokeWidth={2} opacity={0.5} />
        ) : null}
        <text x={t.x + 26} y={ly} fontSize={25} fontWeight={800} fill={t.f.color}>
          {t.f.town} {t.v.toFixed(1)}억
        </text>
      </g>
    );
  });

  return (
    <Page pad={false}>
      <Head kick="대장 단지 30평대 · 연도별 중위 실거래가" title="같은 출발선에서 <b>이렇게</b> 벌어졌습니다" />
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        {grid}
        <text x={PX0 + 10} y={PY0 + 132} fontSize={176} fontWeight={800} fill="rgba(17,17,17,.07)" letterSpacing={-8}>
          {Math.round(yc)}
        </text>
        <line x1={X(yc)} y1={PY0 - 14} x2={X(yc)} y2={PY1} stroke={C.sub} strokeWidth={2} opacity={0.22} />
        {areas}
        {lines}
        {labels}
      </svg>
    </Page>
  );
};

// ── 새 집이 섞이면 ──────────────────────────────────────────────────────
const MLO = 700;
const MHI = 2900;
const MX0 = 210;
const MX1 = 1430;
const MY = 500;
const ROWS = 7;

export const Mix: React.FC<{m: any; dur: number}> = ({m, dur}) => {
  const p = useProgress(dur, 0.9);
  const mx = (v: number) => MX0 + Math.max(0, Math.min(1, (v - MLO) / (MHI - MLO))) * (MX1 - MX0);
  const eOld = Math.min(1, p / 0.22);
  const eNew = Math.max(0, Math.min(1, (p - 0.3) / 0.34));
  const eMed = Math.max(0, Math.min(1, (p - 0.44) / 0.34));
  const mv = m.old_md + (m.all_md - m.old_md) * eMed;
  const TOP = MY - 118;

  const cloud = (vals: number[], col: string, op: number) =>
    vals.map((v, i) => (
      <circle key={col + i} cx={mx(v)} cy={MY + ((i % ROWS) - (ROWS - 1) / 2) * 20} r={8} fill={col} opacity={op} />
    ));

  const grid: React.ReactNode[] = [];
  for (let v = 1000; v < MHI; v += 500) {
    grid.push(<line key={'m' + v} x1={mx(v)} y1={MY - 118} x2={mx(v)} y2={MY + 128} stroke={C.line} strokeWidth={1.5} />);
    grid.push(
      <text key={'mt' + v} x={mx(v)} y={MY + 170} textAnchor="middle" fontSize={25} fill={C.sub}>
        {v.toLocaleString()}
      </text>,
    );
  }

  return (
    <Page pad={false}>
      <Head
        kick={m.town + ' · ' + m.year + '년 30평대 거래 ' + Number(m.n).toLocaleString() + '건을 100채로 줄여 그렸습니다'}
        title="기존 집값은 그대로인데 <em>동네 중위값만</em> 올라갑니다"
      />
      <div style={{position: 'absolute', left: 92, top: 196, display: 'flex', gap: 40, fontSize: 28, fontWeight: 700}}>
        <span style={{color: C.grey, opacity: eOld}}>
          ● 기존 {m.dots_old.length}채 <b style={{color: C.lose}}>그대로</b>
        </span>
        <span style={{color: C.gold, opacity: eNew}}>
          ● 2020년 이후 새 집 {m.dots_new.length}채가 섞임
        </span>
      </div>
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        {grid}
        <text x={MX1} y={MY + 208} textAnchor="end" fontSize={23} fill={C.sub}>평당 만원</text>
        {cloud(m.dots_old, C.grey, eOld * 0.95)}
        {eNew > 0
          ? cloud(m.dots_new.slice(0, Math.max(1, Math.round(m.dots_new.length * eNew))), C.gold, 0.95)
          : null}
        {/* 출발점을 남겨야 "옮겨갔다"가 보인다. 없으면 그냥 선 하나다. */}
        <line x1={mx(m.old_md)} y1={TOP} x2={mx(m.old_md)} y2={MY + 128} stroke={C.grey} strokeWidth={4}
          strokeDasharray="9 8" opacity={eOld} />
        <text x={mx(m.old_md)} y={TOP - 54} textAnchor="middle" fontSize={26} fontWeight={700} fill={C.grey} opacity={eOld}>
          기존만 보면
        </text>
        <text x={mx(m.old_md)} y={TOP - 22} textAnchor="middle" fontSize={30} fontWeight={800} fill={C.grey} opacity={eOld}>
          {Math.round(m.old_md).toLocaleString()}만원
        </text>
        {eMed > 0.02 ? (
          <g>
            <line x1={mx(m.old_md)} y1={TOP - 92} x2={mx(mv) - 14} y2={TOP - 92} stroke={C.ink} strokeWidth={4} />
            <path d={'M' + mx(mv) + ',' + (TOP - 92) + ' l-20,-10 l0,20 Z'} fill={C.ink} />
            <text x={(mx(m.old_md) + mx(mv)) / 2} y={TOP - 110} textAnchor="middle" fontSize={30} fontWeight={800} fill={C.ink}>
              +{Math.round(mv - m.old_md).toLocaleString()}만원
            </text>
          </g>
        ) : null}
        <line x1={mx(mv)} y1={TOP} x2={mx(mv)} y2={MY + 128} stroke={C.ink} strokeWidth={5} />
        <rect x={mx(mv) - 155} y={TOP - 48} width={310} height={54} rx={11} fill={C.ink} />
        <text x={mx(mv)} y={TOP - 12} textAnchor="middle" fontSize={30} fontWeight={800} fill="#fff">
          동네 중위 {Math.round(mv).toLocaleString()}만원
        </text>
      </svg>
    </Page>
  );
};
