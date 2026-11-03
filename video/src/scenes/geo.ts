// 위경도 → EPSG:5179 (UTM-K). 파이썬 `content/geo.py` 와 **같은 식**이어야
// 한다. 둘이 갈라지면 같은 좌표가 두 자리에 찍힌다. 상수는 geoconf.json
// 으로 받아 와서 양쪽이 한 값을 쓰게 했다.
export type UtmkConf = {
  _A: number; _F: number; _K0: number;
  _LAT0: number; _LON0: number; _X0: number; _Y0: number;
};

export const toUtmk = (c: UtmkConf, lng: number, lat: number): [number, number] => {
  const rad = Math.PI / 180;
  const e2 = c._F * (2 - c._F);
  const ep2 = e2 / (1 - e2);
  const p = lat * rad;
  const l = lng * rad;
  const p0 = c._LAT0 * rad;
  const l0 = c._LON0 * rad;
  const M = (phi: number) =>
    c._A *
    ((1 - e2 / 4 - (3 * e2 ** 2) / 64 - (5 * e2 ** 3) / 256) * phi -
      ((3 * e2) / 8 + (3 * e2 ** 2) / 32 + (45 * e2 ** 3) / 1024) * Math.sin(2 * phi) +
      ((15 * e2 ** 2) / 256 + (45 * e2 ** 3) / 1024) * Math.sin(4 * phi) -
      ((35 * e2 ** 3) / 3072) * Math.sin(6 * phi));
  const N = c._A / Math.sqrt(1 - e2 * Math.sin(p) ** 2);
  const T = Math.tan(p) ** 2;
  const C = ep2 * Math.cos(p) ** 2;
  const A = (l - l0) * Math.cos(p);
  const x =
    c._X0 +
    c._K0 * N * (A + ((1 - T + C) * A ** 3) / 6 +
      ((5 - 18 * T + T ** 2 + 72 * C - 58 * ep2) * A ** 5) / 120);
  const y =
    c._Y0 +
    c._K0 *
      (M(p) - M(p0) +
        N * Math.tan(p) *
          (A ** 2 / 2 + ((5 - T + 9 * C + 4 * C ** 2) * A ** 4) / 24 +
            ((61 - 58 * T + T ** 2 + 600 * C - 330 * ep2) * A ** 6) / 720));
  return [x, y];
};

export type Feature = {properties: {name: string}; geometry: {coordinates: number[][][][]}};

/** 우리 시군구명 → 경계 파일 이름. `geo.py geo_name()` 과 **같은 규칙**.
 *  어림짐작으로 쪼개면 안 된다 — 쪼갤 시 목록까지 파이썬에서 받아 쓴다.
 *  (추측으로 정규식을 짰다가 강조색이 하나도 안 칠해졌다.) */
export const geoName = (
  name: string,
  exact: Record<string, string>,
  reorg: Record<string, string>,
  splitCities: string[] = [],
): string => {
  if (reorg[name]) return reorg[name];
  if (exact[name]) return exact[name];
  for (const city of splitCities) {
    if (name.startsWith(city) && name.endsWith('구') && name.length > city.length)
      return `${city}시 ${name.slice(city.length)}`;
  }
  return name;
};

/** 경계를 화면에 맞춰 놓는 투영기. 한 번 만들어 재사용한다. */
export const makeProjector = (feats: Feature[], w: number, h: number) => {
  const xs: number[] = [];
  const ys: number[] = [];
  for (const f of feats)
    for (const poly of f.geometry.coordinates)
      for (const [x, y] of poly[0]) {
        xs.push(x);
        ys.push(y);
      }
  const x0 = Math.min(...xs);
  const x1 = Math.max(...xs);
  const y0 = Math.min(...ys);
  const y1 = Math.max(...ys);
  const scale = Math.min(w / (x1 - x0 || 1), h / (y1 - y0 || 1)) * 0.96;
  const ox = (w - (x1 - x0) * scale) / 2;
  const oy = (h - (y1 - y0) * scale) / 2;
  // SVG 는 y 가 아래로 증가한다.
  return (x: number, y: number): [number, number] => [
    ox + (x - x0) * scale,
    oy + (y1 - y) * scale,
  ];
};

export const mix = (a: string, b: string, t: number): string => {
  const hx = (s: string) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
  const [r1, g1, b1] = hx(a);
  const [r2, g2, b2] = hx(b);
  const c = (u: number, v: number) => Math.round(u + (v - u) * t).toString(16).padStart(2, '0');
  return `#${c(r1, r2)}${c(g1, g2)}${c(b1, b2)}`;
};
