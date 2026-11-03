export interface Asset {
  id: string; name: string; class: string; availableFrom: string | null;
  listedDate: string; lotUnits: bigint; requiresKnowledge: number; feeBps: bigint;
}
export interface Price {
  assetId: string; date: string; priceKRW: bigint; volumeUnits: bigint | null;
  kind: 'VISIBLE' | 'EXECUTION' | 'CLOSE'; quality: 'MOCK';
}
export interface Dataset { version: string; quality: 'MOCK'; assets: Asset[]; prices: Price[] }
export const SCALE = 100_000_000n;

export function quarterDates(index: number) {
  const month = 2006 * 12 + 9 + index * 3;
  const year = Math.floor(month / 12), m = month % 12;
  const date = (d: Date) => d.toISOString().slice(0, 10);
  return {
    quarter: `${year}Q${Math.floor(m / 3) + 1}`,
    start: date(new Date(Date.UTC(year, m, 1))),
    asOf: date(new Date(Date.UTC(year, m, 0))),
    end: date(new Date(Date.UTC(year, m + 3, 0))),
  };
}

// Entirely synthetic test data; independent of personal seed and historical prices.
// Weekdays are synthetic sessions, not a verified exchange holiday calendar.
const assets: Asset[] = [
  { id:'MOCK_A',name:'가상 성장주 A',class:'STOCK',listedDate:'2000-01-01',availableFrom:'2000-01-01',lotUnits:SCALE,requiresKnowledge:0,feeBps:15n },
  { id:'MOCK_B',name:'가상 배당주 B',class:'STOCK',listedDate:'2000-01-01',availableFrom:'2000-01-01',lotUnits:SCALE,requiresKnowledge:0,feeBps:15n },
  { id:'MOCK_GOLD',name:'가상 실물 금',class:'GOLD',listedDate:'2000-01-01',availableFrom:'2000-01-01',lotUnits:1_000_000n,requiresKnowledge:0,feeBps:100n },
  { id:'BTC',name:'비트코인',class:'CRYPTO',listedDate:'2009-01-03',availableFrom:null,lotUnits:1n,requiresKnowledge:40,feeBps:25n },
  { id:'ETH',name:'이더리움',class:'CRYPTO',listedDate:'2015-07-30',availableFrom:null,lotUnits:1n,requiresKnowledge:40,feeBps:25n },
  { id:'KRX_GOLD',name:'KRX 금시장',class:'GOLD',listedDate:'2014-03-24',availableFrom:null,lotUnits:SCALE,requiresKnowledge:0,feeBps:30n },
];
const prices: Price[] = [];
const base = [60_000n, 25_000n, 45_000n];
assets.slice(0,3).forEach((asset, a) => {
  let previous = base[a];
  prices.push({assetId:asset.id,date:'2006-09-29',priceKRW:previous,volumeUnits:100_000n*SCALE,kind:'VISIBLE',quality:'MOCK'});
  for(let t=0;t<80;t++) {
    const d=quarterDates(t), session = new Date(`${d.start}T00:00:00Z`);
    while([0,6].includes(session.getUTCDay())) session.setUTCDate(session.getUTCDate()+1);
    const execution = previous * BigInt(9900 + ((t * 37 + a * 11) % 240)) / 10_000n;
    prices.push({assetId:asset.id,date:session.toISOString().slice(0,10),priceKRW:execution,volumeUnits:100_000n*SCALE,kind:'EXECUTION',quality:'MOCK'});
    // Synthetic oscillations, not imitations of any named historical crisis.
    const bps = 10_000 + [160,95,70][a] + Math.round(Math.sin((t+a*7)/3)*[650,350,200][a]);
    previous=execution*BigInt(bps)/10_000n;
    const closeDate = new Date(`${d.end}T00:00:00Z`);
    while([0,6].includes(closeDate.getUTCDay())) closeDate.setUTCDate(closeDate.getUTCDate()-1);
    prices.push({assetId:asset.id,date:closeDate.toISOString().slice(0,10),priceKRW:previous,volumeUnits:100_000n*SCALE,kind:'CLOSE',quality:'MOCK'});
  }
});
export const MOCK_DATASET: Dataset = { version:'mock-quarterly-1.0.0',quality:'MOCK',assets,prices };

export function lastPrice(data: Dataset, assetId: string, asOf: string): Price | undefined {
  return data.prices.filter(p=>p.assetId===assetId && p.date<=asOf).sort((a,b)=>b.date.localeCompare(a.date))[0];
}
export function executionPrice(data: Dataset, assetId: string, turn: number): Price | undefined {
  const {start,end}=quarterDates(turn);
  return data.prices.filter(p=>p.assetId===assetId && p.date>=start && p.date<=end && p.kind==='EXECUTION').sort((a,b)=>a.date.localeCompare(b.date))[0];
}
