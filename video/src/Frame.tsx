import React from 'react';
import {C, FONT} from './theme';

/**
 * 시그니처 테두리 — 어느 한 장을 잘라 가도 우리 영상인 게 보이게.
 *
 * 본문만 움직이고 테두리는 **고정**이다. 켄번즈로 그림을 당길 때 테두리까지
 * 같이 움직이면 멀미가 나고 채널명이 흔들려 읽히지도 않는다.
 *
 * 파이썬에서는 알파가 뚫린 PNG 를 장마다 따로 찍어 얹었다. 여기서는 그냥
 * 본문 위에 테두리를 그리면 되므로 그 과정이 통째로 사라진다.
 */
export const Frame: React.FC<{
  channel: string;
  series: string;
  chapter: string;
  source: string;
  total: number;
  idx: number;
  children?: React.ReactNode;
}> = ({channel, series, chapter, source, total, idx, children}) => {
  const W = 1920;
  const H = 1080;
  const cw = 1650;
  const ch = 928;
  const cx = (W - cw) / 2;
  const cy = 76;
  const r = 22;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: C.shell,
        fontFamily: FONT,
      }}
    >
      {/* 모눈. "데이터를 다룬다"는 신호라 거의 안 보일 만큼만 깐다. */}
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        <defs>
          <pattern id="grid" width={48} height={48} patternUnits="userSpaceOnUse">
            <path d="M48,0 V48 M0,48 H48" stroke={C.shell2} strokeWidth={1} fill="none" />
          </pattern>
        </defs>
        <rect width={W} height={H} fill="url(#grid)" />
      </svg>

      {/* 본문 — 테두리보다 먼저 깔고 둥글게 깎는다 */}
      <div
        style={{
          position: 'absolute',
          left: cx,
          top: cy,
          width: cw,
          height: ch,
          borderRadius: r,
          overflow: 'hidden',
          background: C.bg,
        }}
      >
        {children}
      </div>

      <div
        style={{
          position: 'absolute',
          left: cx - 2,
          top: cy - 2,
          width: cw + 4,
          height: ch + 4,
          border: '2px solid rgba(255,255,255,.12)',
          borderRadius: r + 2,
          pointerEvents: 'none',
        }}
      />

      {/* 머리띠 */}
      <div
        style={{
          position: 'absolute',
          left: cx,
          top: 0,
          width: cw,
          height: cy,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
          <div style={{width: 7, height: 30, background: C.accent, borderRadius: 4}} />
          <div style={{fontSize: 27, fontWeight: 800, color: '#fff', letterSpacing: '-.01em'}}>
            {channel}
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            fontSize: 24,
            fontWeight: 600,
            color: 'rgba(255,255,255,.72)',
          }}
        >
          {series}
          <b style={{color: C.accent, fontWeight: 800}}>{chapter}</b>
        </div>
      </div>

      {/* 꼬리띠 + 진행 표시 */}
      <div
        style={{
          position: 'absolute',
          left: cx,
          top: cy + ch,
          width: cw,
          height: H - cy - ch,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{fontSize: 21, color: 'rgba(255,255,255,.46)'}}>{source}</div>
        <div style={{display: 'flex', gap: 7}}>
          {Array.from({length: total}, (_, k) => (
            <i
              key={k}
              style={{
                width: 26,
                height: 5,
                borderRadius: 3,
                background: k < idx ? C.accent : 'rgba(255,255,255,.28)',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
