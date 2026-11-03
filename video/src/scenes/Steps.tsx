import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {Page} from '../Cards';

/** 순차 점등 — 내레이션이 짚는 항목만 밝히고 나머지는 어둡게.
 *  파이썬에서는 장면 길이를 몰라 48장을 11초에 펴 쓰다 5fps 로 끊겼다.
 *  여기서는 프레임을 그대로 쓰므로 그 문제가 없다. */
export const Steps: React.FC<{sec?: string; items: string[]; dark?: boolean}> = ({
  sec, items, dark,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = items.length;
  const [fs, dia, pad, gap] = n <= 3 ? [62, 76, 22, 26] : [52, 64, 16, 18];
  // 전체 길이의 8할에 걸쳐 차례로 켜지고, 마지막은 끝까지 남는다.
  const per = fps * 1.5;
  return (
    <Page dark={dark}>
      {sec ? (
        <div style={{fontSize: 34, fontWeight: 700, color: dark ? 'rgba(255,255,255,.55)' : C.sub, marginBottom: 26}}>
          {sec}
        </div>
      ) : null}
      {items.map((it, k) => {
        const on = spring({frame: frame - k * per, fps, config: {damping: 200}});
        const off = k === n - 1 ? 0 : spring({frame: frame - (k + 1) * per, fps, config: {damping: 200}});
        const op = 0.14 + 0.86 * on - 0.3 * off;
        const ring = on - off;
        return (
          <div
            key={k}
            style={{
              display: 'flex', alignItems: 'center', borderRadius: 18,
              border: `3px solid rgba(255,228,92,${ring})`,
              padding: `${pad}px 30px`, marginBottom: gap, opacity: op,
            }}
          >
            <div style={{
              flex: 'none', width: dia, height: dia, borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 800, fontSize: dia * 0.5, marginRight: 28,
              background: dark ? '#fff' : C.ink, color: dark ? C.ink : '#fff',
            }}>{k + 1}</div>
            <div
              style={{fontWeight: 800, letterSpacing: '-.03em', lineHeight: 1.25, fontSize: fs}}
              dangerouslySetInnerHTML={{__html: it
                .replace(/<b>/g, `<b style="color:${dark ? '#8FB6FF' : C.win}">`)
                .replace(/<em>/g, `<em style="color:${dark ? '#FF8A8F' : C.lose}">`)}}
            />
          </div>
        );
      })}
    </Page>
  );
};
