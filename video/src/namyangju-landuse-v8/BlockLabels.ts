import dictionary from '../../public/namyangju-landuse-v8/block_dictionary.json';
export const entries=dictionary.entries;
export function entry(board:string,id:string){return entries.find(e=>e.board_id===board&&e.feature_id===id)}
const short:Record<string,string>={w1_a1:'A1',w1_a2:'A2',w1_a24:'A24',w1_b17:'B17',w1_s1:'S1',w1_s2:'S2',w1_a17:'A17',a1:'A1',a3:'A3',a4:'A4'};
export function labelsFor(board:string,ids:string[]){const labelOverrides:Record<string,string>={},meaningLabels:Record<string,string>={};for(const id of ids){const e=entry(board,id);if(!e)continue;if(short[id])labelOverrides[id]=short[id];if(e.supply_program){meaningLabels[id]=e.developer_brand?'아테라 · 공공분양':e.supply_program.includes('신혼희망')?'신혼희망타운':'공공분양'}else if(e.land_use.includes('공동주택'))meaningLabels[id]='공동주택용지'}return {labelOverrides,meaningLabels}}
