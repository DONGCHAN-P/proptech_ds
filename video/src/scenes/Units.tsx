import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {Page} from '../Cards';

const HOUSE =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDIuNiAyLjQgMTAuMmgyLjNWMjFoNS4xdi01LjloNC40VjIxaDUuMVYxMC4yaDIuM3oiLz48L3N2Zz4=";

/** 「39 대 92」는 숫자로 읽으면 2.4배인 줄만 알고, 늘어놓으면 양이 보인다. */
export const Units: React.FC<{sec?: string; rows: [string, number, string][]; dark?: boolean}> =
({sec, rows, dark}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const e = spring({frame, fps, config: {damping: 200, mass: 1.2}});
  const mx = Math.max(...rows.map((r) => r[1]));
  const dim = dark ? 'rgba(255,255,255,.14)' : C.line;
  return (
    <Page dark={dark}>
      {sec ? <div style={{fontSize: 34, fontWeight: 700, color: dark ? 'rgba(255,255,255,.55)' : C.sub, marginBottom: 34}}>{sec}</div> : null}
      <div style={{display: 'flex', flexDirection: 'column', gap: 30}}>
        {rows.map(([nm, cnt, col], i) => {
          const on = Math.round(cnt * e);
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 26}}>
              <div style={{flex: 'none', width: 168, fontSize: 36, fontWeight: 800, textAlign: 'right'}}>{nm}</div>
              <div style={{flex: 1, display: 'flex', flexWrap: 'wrap', gap: 7, alignContent: 'center'}}>
                {Array.from({length: mx}, (_, k) => (
                  <i key={k} style={{
                    display: 'block', width: 30, height: 30,
                    background: k >= cnt ? 'transparent' : k < on ? col : dim,
                    WebkitMaskImage: `url(${HOUSE})`, maskImage: `url(${HOUSE})`,
                    WebkitMaskSize: 'contain', maskSize: 'contain',
                    WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat',
                  }} />
                ))}
              </div>
              <div style={{flex: 'none', width: 150, fontSize: 44, fontWeight: 800, textAlign: 'right', color: col}}>{on}개</div>
            </div>
          );
        })}
      </div>
    </Page>
  );
};
