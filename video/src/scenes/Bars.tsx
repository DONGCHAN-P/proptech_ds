import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {Page} from '../Cards';

const X0 = 400;
const X1 = 1330;
const TOP = 236;
const ROW = 60;
const TRACK = 20;

type Row = [string, number, string, string];

/** 0 에서 자라는 막대. 줄마다 조금씩 늦게 출발해 순서가 차례로 읽힌다.
 *  숫자는 세지 않는다 — 세는 숫자는 중간에 잘라 가면 틀린 값이 박제된다. */
export const Bars: React.FC<{rows: Row[]; spec: any; still?: boolean}> = ({rows, spec, still}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lim = Math.max(...rows.map((r) => Math.abs(r[1]))) || 1;
  const span = X1 - X0;
  const zero = !!spec.zero;
  return (
    <Page pad={false}>
      <div style={{position: 'absolute', left: 92, top: 68, right: 92}}>
        <div style={{fontSize: 28, fontWeight: 700, color: C.sub}}>{spec.kick}</div>
        <div
          style={{fontSize: 52, fontWeight: 800, letterSpacing: '-.03em', marginTop: 6}}
          dangerouslySetInnerHTML={{__html: spec.title.replace(/<b>/g, `<b style="color:${C.win}">`).replace(/<em>/g, `<em style="color:${C.lose}">`)}}
        />
        {spec.note ? (
          <div style={{fontSize: 25, color: C.sub, marginTop: 12, lineHeight: 1.45, maxWidth: 1300}}>
            {spec.note}
          </div>
        ) : null}
      </div>
      {zero ? (
        <div
          style={{
            position: 'absolute',
            left: X0 + span / 2,
            top: TOP - 12,
            width: 2,
            height: rows.length * ROW + 4,
            background: C.sub,
            opacity: 0.5,
          }}
        />
      ) : null}
      {rows.map(([lab, v, col, txt], i) => {
        const g = still ? 1 : spring({frame: frame - i * 2, fps, config: {damping: 200, mass: 0.8}});
        const t = still ? 1 : spring({frame: frame - i * 2 - 9, fps, config: {damping: 200}});
        const y = TOP + i * ROW;
        const w = zero ? (Math.abs(v) / lim) * (span / 2) * g : Math.max(3, (v / lim) * span * g);
        const x = zero ? X0 + span / 2 - (v < 0 ? w : 0) : X0;
        return (
          <React.Fragment key={i}>
            <div
              style={{position: 'absolute', left: 92, top: y, width: X0 - 116, textAlign: 'right', fontSize: 26, fontWeight: 700}}
              dangerouslySetInnerHTML={{__html: lab.replace(/<small>/g, `<small style="font-size:21px;color:${C.sub};font-weight:600">`)}}
            />
            <div style={{position: 'absolute', left: X0, top: y + 5, width: span, height: TRACK, borderRadius: 999, background: '#E9E6DE'}} />
            <div style={{position: 'absolute', left: x, top: y + 5, width: w, height: TRACK, borderRadius: 999, background: col}} />
            <div style={{position: 'absolute', left: X1 + 22, top: y, fontSize: 28, fontWeight: 800, color: col, opacity: t}}>
              {txt}
            </div>
          </React.Fragment>
        );
      })}
    </Page>
  );
};
