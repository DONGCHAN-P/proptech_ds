import React from 'react';
import {continueRender, delayRender, staticFile} from 'remotion';
import {C} from '../theme';
import {Feature, UtmkConf, geoName, makeProjector, mix, toUtmk} from './geo';

type Geo = {features: Feature[]};
type Conf = {utmk: UtmkConf; exact: Record<string, string>;
  reorg: Record<string, string>; splitCities: string[]};

let cacheGeo: Geo | null = null;
let cacheConf: Conf | null = null;

/** 경계 파일은 326KB 다. 장면마다 다시 받으면 렌더가 그만큼 느려진다. */
export const useGeo = (): [Geo | null, Conf | null] => {
  const [geo, setGeo] = React.useState<Geo | null>(cacheGeo);
  const [conf, setConf] = React.useState<Conf | null>(cacheConf);
  const [handle] = React.useState(() =>
    cacheGeo && cacheConf ? null : delayRender('지도 경계 읽는 중'),
  );
  React.useEffect(() => {
    if (handle === null) return;
    Promise.all([
      fetch(staticFile('geo.json')).then((r) => r.json()),
      fetch(staticFile('geoconf.json')).then((r) => r.json()),
    ]).then(([g, c]) => {
      cacheGeo = g;
      cacheConf = c;
      setGeo(g);
      setConf(c);
      continueRender(handle);
    });
  }, [handle]);
  return [geo, conf];
};

export type Pin = {label: string; lat: number; lng: number; primary?: boolean};
export type Arc = {a: [number, number]; b: [number, number]; color: string; t: number};

/**
 * 수도권 지도. 파이썬 `geo.svg()` 가 하던 일을 그대로 한다 —
 * 대상만 색칠하고, 핀을 찍고, 글자가 겹치면 밀어 떼어 놓는다.
 */
export const MapBase: React.FC<{
  width: number;
  height: number;
  highlight?: Record<string, string>;
  pins?: Pin[];
  arcs?: Arc[];
}> = ({width, height, highlight = {}, pins = [], arcs = []}) => {
  const [geo, conf] = useGeo();
  if (!geo || !conf) return null;

  const want: Record<string, string> = {};
  for (const [k, v] of Object.entries(highlight)) {
    want[geoName(k, conf.exact, conf.reorg, conf.splitCities)] = v;
  }
  const P = makeProjector(geo.features, width, height);
  const paths: React.ReactNode[] = [];

  geo.features.forEach((f, i) => {
    const hit = want[f.properties.name];
    const d = f.geometry.coordinates
      .map((poly) =>
        poly
          .map(
            (ring) =>
              'M' + ring.map(([x, y]) => P(x, y).map((v) => v.toFixed(1)).join(',')).join('L') + 'Z',
          )
          .join(''),
      )
      .join('');
    paths.push(
      <path key={i} d={d} fill={hit ?? C.neutral} stroke="#fff" strokeWidth={2} strokeLinejoin="round" />,
    );
  });

  const fillPin = Object.values(highlight)[0] ?? C.ink;
  const marks: React.ReactNode[] = [];
  const placed: {x: number; y: number; half: number}[] = [];
  const dots: [number, number][] = [];

  const put = pins.map((p) => {
    const [x, y] = P(...toUtmk(conf.utmk, p.lng, p.lat));
    dots.push([x, y]);
    return {...p, x, y};
  });

  arcs.forEach((a, i) => {
    const [ax, ay] = P(...toUtmk(conf.utmk, a.a[1], a.a[0]));
    const [bx, by] = P(...toUtmk(conf.utmk, a.b[1], a.b[0]));
    const t = Math.max(0, Math.min(1, a.t));
    if (t <= 0) return;
    marks.push(
      <line key={`arc${i}`} x1={ax} y1={ay} x2={ax + (bx - ax) * t} y2={ay + (by - ay) * t}
        stroke={a.color} strokeWidth={6} strokeLinecap="round" opacity={0.85} />,
    );
    if (t >= 1)
      marks.push(<circle key={`ad${i}`} cx={bx} cy={by} r={8} fill={a.color} stroke="#fff" strokeWidth={3} />);
  });

  put.forEach((p, i) => {
    marks.push(
      p.primary ? (
        <g key={`p${i}`}>
          <circle cx={p.x} cy={p.y} r={22} fill={C.sub} opacity={0.35} />
          <circle cx={p.x} cy={p.y} r={11} fill={fillPin} stroke="#fff" strokeWidth={4} />
        </g>
      ) : (
        <circle key={`p${i}`} cx={p.x} cy={p.y} r={7} fill={C.ink} opacity={0.55} stroke="#fff" strokeWidth={2} />
      ),
    );
  });

  // 글자끼리도, 점 위에도 안 올라가게. 아래위로 번갈아 자리를 찾는다.
  const STEP = 34;
  const tries = [0];
  for (let k = 1; k < 14; k++) tries.push(STEP * k, -STEP * k);
  [...put].sort((a, b) => a.y - b.y || a.x - b.x).forEach((p, i) => {
    const half = p.label.length * 15 + 4;
    const base = p.y - 28;
    let ty = base;
    for (const d of tries) {
      const t = base + d;
      if (t < 26 || t > height - 12) continue;
      if (placed.some((q) => Math.abs(t - q.y) < 34 && Math.abs(p.x - q.x) < half + q.half)) continue;
      if (dots.some(([qx, qy]) => Math.abs(t - qy) < 26 && Math.abs(p.x - qx) < half + 14)) continue;
      ty = t;
      break;
    }
    placed.push({x: p.x, y: ty, half});
    if (Math.abs(ty - base) > 6)
      marks.push(
        <line key={`l${i}`} x1={p.x} y1={p.y} x2={p.x} y2={ty > p.y ? ty - 22 : ty + 10}
          stroke={C.ink} strokeWidth={1.6} opacity={0.45} />,
      );
    marks.push(
      <text key={`t${i}`} x={p.x} y={ty} textAnchor="middle" fontSize={30} fontWeight={800}
        fill={C.ink} stroke="#fff" strokeWidth={6} paintOrder="stroke">
        {p.label}
      </text>,
    );
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {paths}
      {marks}
    </svg>
  );
};

export const mixC = mix;
