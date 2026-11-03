export type Point = [number, number];
export type Quad = [Point, Point, Point, Point]; // TL, TR, BR, BL; composition pixels
export type TrackKey = {time: number; quad: Quad}; // source seconds

export function homography(width: number, height: number, quad: Quad): number[] {
  const from: Quad = [[0, 0], [width, 0], [width, height], [0, height]];
  const rows: number[][] = [];
  from.forEach(([x, y], i) => {
    const [u, v] = quad[i];
    rows.push([x, y, 1, 0, 0, 0, -u*x, -u*y, u]);
    rows.push([0, 0, 0, x, y, 1, -v*x, -v*y, v]);
  });
  for (let c = 0; c < 8; c++) {
    let pivot = c;
    for (let r = c+1; r < 8; r++) if (Math.abs(rows[r][c]) > Math.abs(rows[pivot][c])) pivot = r;
    if (Math.abs(rows[pivot][c]) < 1e-10) throw new Error('Screen quadrilateral is degenerate');
    [rows[c], rows[pivot]] = [rows[pivot], rows[c]];
    const divisor = rows[c][c];
    for (let j = c; j <= 8; j++) rows[c][j] /= divisor;
    for (let r = 0; r < 8; r++) if (r !== c) {
      const factor = rows[r][c];
      for (let j = c; j <= 8; j++) rows[r][j] -= factor*rows[c][j];
    }
  }
  return rows.map(row => row[8]);
}

export function project(h: number[], [x, y]: Point): Point {
  const divisor = h[6]*x+h[7]*y+1;
  return [(h[0]*x+h[1]*y+h[2])/divisor, (h[3]*x+h[4]*y+h[5])/divisor];
}

export function cssMatrix(h: number[]): string {
  return `matrix3d(${[h[0],h[3],0,h[6],h[1],h[4],0,h[7],0,0,1,0,h[2],h[5],0,1].join(',')})`;
}

export function trackedQuad(keys: TrackKey[], time: number): Quad {
  if (!keys.length) throw new Error('Actual measured screen track required');
  if (time <= keys[0].time) return keys[0].quad;
  const end = keys.findIndex(k => k.time >= time);
  if (end < 0) return keys[keys.length-1].quad;
  const a = keys[end-1], b = keys[end], mix = (time-a.time)/(b.time-a.time);
  return a.quad.map((p, i) => [p[0]+(b.quad[i][0]-p[0])*mix, p[1]+(b.quad[i][1]-p[1])*mix]) as Quad;
}
