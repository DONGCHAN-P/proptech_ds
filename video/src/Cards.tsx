import React from 'react';
import {interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT, SUB_ZONE} from './theme';

const W = 1650;
const H = 928;

// 파이썬에서는 ease(t)=1-(1-t)^3 한 가지로 모든 걸 움직였다. 여기서는
// 스프링을 쓴다 — 멈출 때 아주 살짝 지나쳤다 돌아오는 그 맛이 "툭 뜨는"
// 느낌을 없앤다. 단, 글자에 과한 튕김은 싸 보이므로 damping 을 높게 둔다.
export const useRise = (delay = 0, rise = 34) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - delay, fps, config: {damping: 200, mass: 0.6}});
  return {opacity: s, transform: `translateY(${(1 - s) * rise}px)`};
};

export const usePop = (delay = 0) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - delay, fps, config: {damping: 14, mass: 0.5}});
  return {opacity: Math.min(1, s * 1.6), transform: `scale(${0.93 + 0.07 * s})`};
};

const Html: React.FC<{t: string; style?: React.CSSProperties; cls?: string}> = ({
  t,
  style,
  cls,
}) => <div className={cls} style={style} dangerouslySetInnerHTML={{__html: t}} />;

export const Page: React.FC<{dark?: boolean; children: React.ReactNode; pad?: boolean}> = ({
  dark,
  children,
  pad = true,
}) => (
  <div
    style={{
      width: W,
      height: H,
      position: 'relative',
      background: dark ? C.ink : C.bg,
      color: dark ? '#fff' : C.ink,
      fontFamily: FONT,
      display: pad ? 'flex' : undefined,
      flexDirection: 'column',
      justifyContent: 'center',
      // 아래 196px 은 자막 띠 자리다. 패딩으로 떼어 놓으면 세로 가운데
      // 정렬이 남은 자리 기준으로 잡혀서, 카드마다 좌표를 밀어 올리며
      // 때우던 일이 사라진다.
      padding: pad ? `0 150px ${SUB_ZONE}px` : 0,
    }}
  >
    {children}
  </div>
);

const bigCss = (dark?: boolean) => `
.big{font-size:96px;font-weight:800;letter-spacing:-.035em;line-height:1.2;}
.big em{color:${dark ? '#FF8A8F' : '#E5484D'};}
.big b{color:${dark ? '#8FB6FF' : '#2F6FED'};}
`;

export const TitleCard: React.FC<{sec: string; big: string; dark?: boolean}> = ({
  sec,
  big,
  dark,
}) => {
  const num = /^\d+$/.test(sec);
  const rows = big.split('<br>').length;
  const fs = rows <= 2 ? 128 : 98;
  const a = useRise(0);
  const b = useRise(4);
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rule = spring({frame: frame - 10, fps, config: {damping: 200}});
  const ghost = interpolate(frame, [0, fps * 0.7], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <Page dark={dark}>
      <style>{bigCss(dark)}</style>
      {num && (
        <div
          style={{
            position: 'absolute',
            right: 92,
            top: (H - SUB_ZONE) / 2,
            transform: 'translateY(-50%)',
            fontSize: 500,
            fontWeight: 800,
            lineHeight: 0.76,
            letterSpacing: '-.06em',
            color: dark ? 'rgba(255,255,255,.075)' : 'rgba(17,17,17,.06)',
            opacity: ghost,
          }}
        >
          {sec}
        </div>
      )}
      <div
        style={{
          position: 'absolute',
          left: 150,
          top: (H - SUB_ZONE) / 2,
          transform: 'translateY(-50%)',
          width: 10,
          height: 230,
          background: C.accent,
          borderRadius: 6,
        }}
      />
      <div style={{paddingLeft: 40}}>
        {!num && (
          <div style={{...a, fontSize: 38, fontWeight: 700, color: dark ? 'rgba(255,255,255,.55)' : C.sub}}>
            {sec}
          </div>
        )}
        <Html cls="big" t={big} style={{...b, fontSize: fs, marginTop: num ? 0 : 22}} />
        <div
          style={{
            width: 120 * rule,
            height: 9,
            background: C.accent,
            borderRadius: 5,
            marginTop: 40,
          }}
        />
      </div>
    </Page>
  );
};

export const StatCard: React.FC<{sec: string; num: string; cap: string; dark?: boolean; down?: boolean}> =
  ({sec, num, cap, dark, down}) => {
    const a = useRise(0);
    const b = usePop(4);
    const c = useRise(8);
    return (
      <Page dark={dark}>
        <style>{bigCss(dark)}</style>
        <div style={{...a, fontSize: 34, fontWeight: 700, color: dark ? 'rgba(255,255,255,.55)' : C.sub}}>
          {sec}
        </div>
        <div
          style={{
            ...b,
            transformOrigin: 'left center',
            fontSize: 210,
            fontWeight: 800,
            letterSpacing: '-.045em',
            lineHeight: 1,
            color: down ? C.lose : C.win,
          }}
        >
          {num}
        </div>
        <Html
          t={cap}
          style={{...c, fontSize: 40, fontWeight: 600, marginTop: 28, lineHeight: 1.5, color: dark ? 'rgba(255,255,255,.66)' : C.sub}}
        />
      </Page>
    );
  };

export const PlainCard: React.FC<{big: string; cap?: string; dark?: boolean}> = ({big, cap, dark}) => {
  const a = useRise(0);
  const b = useRise(4);
  return (
    <Page dark={dark}>
      <style>{bigCss(dark)}</style>
      <Html cls="big" t={big} style={a} />
      {cap ? (
        <Html
          t={cap}
          style={{...b, fontSize: 40, fontWeight: 600, marginTop: 28, lineHeight: 1.5, color: dark ? 'rgba(255,255,255,.66)' : C.sub}}
        />
      ) : null}
    </Page>
  );
};

export const EmojiCard: React.FC<{icon: string; big: string; cap?: string; dark?: boolean}> = ({
  icon,
  big,
  cap,
  dark,
}) => {
  const mid = !cap;
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 12, mass: 0.7}});
  const t = useRise(5);
  const c = useRise(9);
  const size = mid ? 340 : 300;
  return (
    <Page dark={dark}>
      <style>{bigCss(dark)}</style>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: mid ? 30 : 72,
          flexDirection: mid ? 'column' : 'row',
          textAlign: mid ? 'center' : 'left',
        }}
      >
        <img
          src={staticFile(`emoji/${icon}.png`)}
          width={size}
          height={size}
          style={{
            flex: 'none',
            opacity: Math.min(1, s * 1.4),
            transform: `scale(${0.72 + 0.28 * s}) rotate(${(1 - s) * -9}deg)`,
          }}
        />
        <div style={{flex: mid ? 'none' : 1, minWidth: 0}}>
          <Html cls="big" t={big} style={{...t, fontSize: mid ? 78 : 84}} />
          {cap ? (
            <Html
              t={cap}
              style={{...c, fontSize: 36, marginTop: 20, fontWeight: 600, color: dark ? 'rgba(255,255,255,.66)' : C.sub}}
            />
          ) : null}
        </div>
      </div>
    </Page>
  );
};
