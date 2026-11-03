import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {Page} from '../Cards';
import {MapBase, Pin, Arc, mixC} from './MapBase';

const MW = 1080;
const MH = 548;
const GANGNAM: [number, number] = [37.4979, 127.0276];

const Head: React.FC<{kick: string; title: string}> = ({kick, title}) => (
  <div style={{position: 'absolute', left: 92, top: 68, right: 92}}>
    <div style={{fontSize: 28, fontWeight: 700, color: C.sub}}>{kick}</div>
    <div
      style={{fontSize: 52, fontWeight: 800, letterSpacing: '-.03em', marginTop: 6}}
      dangerouslySetInnerHTML={{
        __html: title
          .replace(/<b>/g, `<b style="color:${C.win}">`)
          .replace(/<em>/g, `<em style="color:${C.lose}">`),
      }}
    />
  </div>
);

const Side: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{position: 'absolute', right: 96, top: 252, width: 430}}>{children}</div>
);

/** 장면 전체에 걸쳐 0→n 으로 가는 진행도. 점이 하나씩 찍히게 한다. */
const useStep = (n: number, dur: number, span = 0.86) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, durationInFrames: Math.max(2, Math.round(dur * fps * span)),
    config: {damping: 200, mass: 1.4}});
  return s * n;
};

export const Gen1Map: React.FC<{data: any; dur: number}> = ({data, dur}) => {
  const pos = useStep(data.gen1.length, dur);
  const hl: Record<string, string> = {};
  const pins: Pin[] = [];
  const rows: [string, string, number][] = [];
  data.gen1.forEach((g: any[], k: number) => {
    const [nm, sgg, lat, lng] = g;
    const on = Math.min(1, Math.max(0, pos - k));
    if (on <= 0) return rows.push([nm, C.neutral, 0.22]);
    hl[sgg] = mixC(C.bg, C.win, 0.26 + 0.52 * on);
    if (on > 0.35) pins.push({label: nm, lat, lng});
    rows.push([nm, C.win, 0.25 + 0.75 * on]);
  });
  return (
    <Page pad={false}>
      <Head kick="1989년 발표 · 1991~1996년 입주" title="1기는 <b>이 다섯 곳</b>입니다" />
      <div style={{position: 'absolute', left: 62, top: 212}}>
        <MapBase width={MW} height={MH} highlight={hl} pins={pins} />
      </div>
      <Side>
        <div style={{fontSize: 30, fontWeight: 700, color: C.sub, marginBottom: 14}}>
          1기 신도시 다섯 곳
        </div>
        {rows.map(([nm, col, op], i) => (
          <div key={i} style={{opacity: op, fontSize: 36, fontWeight: 800, color: col, lineHeight: 1.9,
            transform: `translateX(${(1 - op) * 18}px)`}}>{nm}</div>
        ))}
        <div style={{fontSize: 26, color: C.sub, lineHeight: 1.6, marginTop: 16}}>
          영통은 여기 들어가지 않습니다.
        </div>
      </Side>
    </Page>
  );
};

export const YeongtongMap: React.FC<{dur: number}> = ({dur}) => {
  const e = Math.min(1, useStep(1, dur, 0.7));
  return (
    <Page pad={false}>
      <Head kick="01 · 제가 살던 동네" title="여기가 <b>영통</b>입니다" />
      <div style={{position: 'absolute', left: 62, top: 212, opacity: e}}>
        <MapBase width={MW} height={MH}
          highlight={{수원영통구: mixC(C.bg, C.win, 0.25 + 0.35 * e)}}
          pins={[{label: '영통', lat: 37.252, lng: 127.071},
                 {label: '강남', lat: GANGNAM[0], lng: GANGNAM[1], primary: true}]} />
      </div>
      <Side>
        <div style={{fontSize: 30, fontWeight: 700, color: C.sub}}>수원시 영통구</div>
        <div style={{fontSize: 56, fontWeight: 800, color: C.win, letterSpacing: '-.03em', marginTop: 10}}>
          90년대 후반<br />택지지구
        </div>
        <div style={{fontSize: 28, color: C.sub, lineHeight: 1.6, marginTop: 24}}>
          강남에서 남쪽으로 약 30km.<br />광교와 동탄 사이에 있습니다.
        </div>
      </Side>
    </Page>
  );
};

export const DirectionMap: React.FC<{data: any; dur: number; still?: boolean}> = ({data, dur, still}) => {
  const raw = useStep(data.dirs.length, dur, 0.88);
  const pos = still ? data.dirs.length : raw;
  const arcs: Arc[] = [];
  const pins: Pin[] = [{label: '강남', lat: GANGNAM[0], lng: GANGNAM[1], primary: true}];
  data.dirs.forEach((d: any[], k: number) => {
    const [nm, lat, lng, win] = d;
    const t = Math.max(0, Math.min(1, pos - k));
    if (t <= 0) return;
    arcs.push({a: GANGNAM, b: [lat, lng], color: win ? C.win : C.lose, t});
    if (t > 0.8) pins.push({label: nm, lat, lng});
  });
  const done = still ? 1 : Math.max(0, Math.min(1, (pos - data.dirs.length + 0.6) / 0.6));
  return (
    <Page pad={false}>
      <Head kick="2기 신도시 여섯 곳 · 강남 기준" title="거리가 아니라 <em>방향</em>이었습니다" />
      <div style={{position: 'absolute', left: 62, top: 212}}>
        <MapBase width={MW} height={MH} highlight={{강남구: '#111111'}} pins={pins} arcs={arcs} />
      </div>
      <Side>
        <div style={{fontSize: 34, fontWeight: 800, color: C.win, lineHeight: 1.6}}>
          남쪽으로 간 길<br />광교 · 동탄
        </div>
        <div style={{fontSize: 34, fontWeight: 800, color: C.lose, lineHeight: 1.6, marginTop: 26}}>
          서쪽 · 북쪽으로 간 길<br />검단 · 김포한강<br />운정 · 옥정
        </div>
        <div style={{fontSize: 28, color: C.sub, lineHeight: 1.6, marginTop: 30, opacity: done}}>
          직선거리는 비슷합니다.<br />갈린 건 <b style={{color: C.ink}}>방향</b>입니다.
        </div>
      </Side>
    </Page>
  );
};

export const CounterMap: React.FC<{data: any; dur: number}> = ({data, dur}) => {
  const pos = useStep(data.counter.length, dur);
  const hl: Record<string, string> = {};
  const pins: Pin[] = [];
  const rows: [string, string, number][] = [];
  const SHORT: Record<string, string> = {
    '인천 검단': '검단', '김포 한강': '김포', '파주 운정': '운정', '양주 옥정': '옥정',
  };
  data.won.forEach((w: any[]) => {
    const [nm, sgg, lat, lng] = w;
    hl[sgg] = mixC(C.bg, C.win, 0.3);
    pins.push({label: nm, lat, lng});
  });
  data.counter.forEach((cg: any[], k: number) => {
    const [nm, sgg, lat, lng] = cg;
    const on = Math.min(1, Math.max(0, pos - k));
    if (on <= 0) return rows.push([nm, C.neutral, 0.22]);
    hl[sgg] = mixC(C.bg, C.lose, 0.22 + 0.48 * on);
    if (on > 0.35) pins.push({label: SHORT[nm] ?? nm, lat, lng});
    rows.push([nm, C.lose, 0.25 + 0.75 * on]);
  });
  pins.push({label: '강남', lat: GANGNAM[0], lng: GANGNAM[1], primary: true});
  return (
    <Page pad={false}>
      <Head kick="2기 신도시 · 같은 시기에 출발" title="<em>사정이 다른 곳</em>이 있습니다" />
      <div style={{position: 'absolute', left: 62, top: 212}}>
        <MapBase width={MW} height={MH} highlight={hl} pins={pins} />
      </div>
      <Side>
        <div style={{fontSize: 30, fontWeight: 700, color: C.sub, marginBottom: 14}}>
          같은 2기, 사정이 다른 곳
        </div>
        {rows.map(([nm, col, op], i) => (
          <div key={i} style={{opacity: op, fontSize: 36, fontWeight: 800, color: col, lineHeight: 1.9}}>{nm}</div>
        ))}
        <div style={{fontSize: 26, color: C.sub, lineHeight: 1.6, marginTop: 26}}>
          파란 곳이 지금까지 본 광교·동탄입니다.
        </div>
      </Side>
    </Page>
  );
};
