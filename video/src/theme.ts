// 색과 치수는 한 곳에서만 정한다. 파이썬 쪽 design.py 와 같은 값이어야
// 하므로 바꿀 때는 둘 다 바꾼다 — 갈라지면 같은 영상이 두 얼굴을 한다.
export const C = {
  bg: '#F6F4EF',
  ink: '#111111',
  sub: '#6E6E6E',
  line: '#E3E0D8',
  neutral: '#C9C6BE',
  accent: '#FFE45C',
  win: '#2F6FED',
  lose: '#E5484D',
  grey: '#9AA0A6',
  gold: '#E8A33D',
  shell: '#15161A',
  shell2: '#1E2026',
} as const;

export const FONT = 'Pretendard, system-ui, sans-serif';

// 자막 띠가 쓰는 아래쪽. 본문은 여기 들어오면 안 된다.
export const SUB_ZONE = 196;

// Remotion 은 public/ 을 번들 루트가 아니라 staticFile() 로 준다.
// 절대 경로(/fonts/...)로 적었다가 전부 404 가 났다.
export const fontCss = (f: (p: string) => string) => `
@font-face{font-family:Pretendard;font-weight:400;font-display:block;
  src:url(${f('fonts/Pretendard-Regular.woff2')}) format('woff2');}
@font-face{font-family:Pretendard;font-weight:500;font-display:block;
  src:url(${f('fonts/Pretendard-Medium.woff2')}) format('woff2');}
@font-face{font-family:Pretendard;font-weight:600;font-display:block;
  src:url(${f('fonts/Pretendard-SemiBold.woff2')}) format('woff2');}
@font-face{font-family:Pretendard;font-weight:700;font-display:block;
  src:url(${f('fonts/Pretendard-Bold.woff2')}) format('woff2');}
@font-face{font-family:Pretendard;font-weight:800;font-display:block;
  src:url(${f('fonts/Pretendard-ExtraBold.woff2')}) format('woff2');}
*{margin:0;padding:0;box-sizing:border-box;}
body{-webkit-font-smoothing:antialiased;}
em{font-style:normal;}
`;

export type Plan = {
  fps: number;
  width: number;
  height: number;
  content: {w: number; h: number; x: number; y: number};
  subZone: number;
  pad: number;
  fade: number;
  channel: string;
  series: string;
  source: string;
  chapters: string[];
  music: string | null;
  beats: BeatT[];
  data: any;
};

export type BeatT = {
  i: number;
  dur: number;
  chapter: string;
  text: string;
  motion: string;
  section: boolean;
  hold: number;
  audio: string | null;
  adur: number;
  asset?: string;
  card?: {name: string; kind: string; scene?: string; props: any};
};
