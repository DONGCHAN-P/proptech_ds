import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {C, FONT, Plan, BeatT, fontCss} from './theme';
import {Frame} from './Frame';
import {EmojiCard, PlainCard, StatCard, TitleCard, Page} from './Cards';
import {Scene} from './scenes/Scene';

const CW = 1650;
const CH = 928;

/** 자막 띠 — 참고한 포맷(오그랩)처럼 두 겹 테두리. 밝은 차트 위에서도
 *  어두운 카드 위에서도 뜬다. */
const Sub: React.FC<{text: string}> = ({text}) => {
  if (!text.trim()) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        transform: 'translateX(-50%)',
        bottom: 26,
        maxWidth: CW - 180,
        padding: '15px 34px',
        borderRadius: 11,
        background: '#fff',
        border: `3px solid ${C.accent}`,
        boxShadow: '0 0 0 1.5px rgba(17,17,17,.82), 0 14px 34px rgba(0,0,0,.30)',
        fontSize: 37,
        fontWeight: 700,
        lineHeight: 1.42,
        color: C.ink,
        textAlign: 'center',
        letterSpacing: '-.02em',
      }}
    >
      {text}
    </div>
  );
};

/** 켄번즈. 파이썬에서는 ffmpeg zoompan 이 정수 프레임에 걸리는 문제로
 *  재생이 끊겼다. 여기서는 프레임마다 CSS transform 이라 그 문제가 없다. */
const Motion: React.FC<{motion: string; dur: number; children: React.ReactNode}> = ({
  motion,
  dur,
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame, [0, Math.max(1, dur * fps)], [0, 1], {
    extrapolateRight: 'clamp',
  });
  let scale = 1;
  let x = 0;
  if (motion === 'in') scale = 1 + 0.09 * p;
  else if (motion === 'out') scale = 1.09 - 0.09 * p;
  else if (motion === 'panL' || motion === 'panR') {
    scale = 1.045;
    x = (motion === 'panL' ? 1 - p : p) * CW * 0.045 - CW * 0.0225;
  } else scale = 1 + 0.025 * p; // still — 알아챌 수 없을 만큼만
  return (
    <div
      style={{
        width: CW,
        height: CH,
        transform: `scale(${scale}) translateX(${x}px)`,
        // 위를 붙박아 당긴다. 가운데 기준으로 키우면 맨 위 눈표·제목이
        // 먼저 잘려 나간다.
        transformOrigin: 'top center',
      }}
    >
      {children}
    </div>
  );
};

const Body: React.FC<{b: BeatT; data: any}> = ({b, data}) => {
  if (b.asset) {
    return <Img src={staticFile(`assets/${b.asset.split('/').pop()}`)} style={{width: CW, height: CH}} />;
  }
  const c = b.card!;
  const p = c.props || {};
  if (c.kind === 'title') return <TitleCard sec={String(p.sec ?? '')} big={p.big} dark={p.dark} />;
  if (c.kind === 'stat')
    return <StatCard sec={p.sec} num={p.num} cap={p.cap} dark={p.dark} down={p.down} />;
  if (c.kind === 'emoji') return <EmojiCard icon={p.icon} big={p.big} cap={p.cap} dark={p.dark} />;
  if (c.kind === 'custom') return <Scene name={c.scene || c.name} data={data} dur={b.dur} />;
  if (c.kind === 'plain') return <PlainCard big={p.big} cap={p.cap} dark={p.dark} />;
  // steps · versus · units 는 Scene 안에서 처리한다
  return <Scene name={c.kind} data={{...data, props: p}} dur={b.dur} />;
};

export const Main: React.FC<{plan: Plan}> = ({plan}) => {
  const {fps} = useVideoConfig();
  let at = 0;
  const rows = plan.beats.map((b) => {
    const from = Math.round(at * fps);
    const len = Math.max(1, Math.round(b.dur * fps));
    at += b.dur;
    return {b, from, len};
  });
  const chIdx = (name: string) => plan.chapters.indexOf(name) + 1;

  return (
    <AbsoluteFill style={{background: C.shell, fontFamily: FONT}}>
      <style>{fontCss(staticFile)}</style>
      {plan.music ? (
        <Audio src={staticFile('music/thinking_music.mp3')} volume={0.2} loop />
      ) : null}
      {rows.map(({b, from, len}) => (
        <Sequence key={b.i} from={from} durationInFrames={len} name={`${b.i} ${b.chapter}`}>
          <Frame
            channel={plan.channel}
            series={plan.series}
            chapter={b.chapter}
            source={plan.source}
            total={plan.chapters.length}
            idx={chIdx(b.chapter)}
          >
            <Motion motion={b.motion} dur={b.dur}>
              <Body b={b} data={plan.data} />
            </Motion>
            <Sub text={b.text} />
          </Frame>
          {b.audio ? (
            <Audio
              src={staticFile(`voice/${b.audio.split('/').pop()}`)}
              startFrom={0}
              volume={1}
            />
          ) : null}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
