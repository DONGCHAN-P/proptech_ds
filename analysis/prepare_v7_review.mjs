import fs from 'node:fs';
let p=fs.readFileSync('analysis/review_v6.mjs','utf8').replaceAll('v6','v7');
p=p.replace('[2,7,10,17,24,29,39,45,51.4,52,53,54,55,65,78,88,93,100,118,135,154,172,192,212,230,251,273]','[2,10,17,24,29,39,45,53,55,65,78,93,100,115,120,133,137,144,150,155,163,168,175,182,192,212,230,251,273]');
fs.mkdirSync('video/out/qa-v7',{recursive:true});fs.writeFileSync('analysis/review_v7.mjs',p);
const manifest=JSON.parse(fs.readFileSync('video/public/real-assets/manifest.json','utf8')),ids=['gnews-gwanggyo-history-0','commons-3','commons-1','commons-0'];
let credits='# 광교·동탄 v7 영상 출처\n\n사진은 실제 촬영 자료이며, 2026년 현재 모습이라고 주장하지 않습니다. 영상은 원본 사진의 비율을 유지해 배치했습니다.\n\n';
for(const id of ids){const a=manifest.find(p=>p.id===id);credits+=`- ${a.title}\n  - 저작자: ${a.author.split('\n')[0]}\n  - 출처: ${a.source_url}\n  - 이용 조건: ${a.license} (${a.license_url})\n  - 촬영/게시: ${a.photographed||a.published}\n  - 원본 파일: video/public/real-assets/${a.file}\n\n`;}
credits+='지도: © OpenStreetMap contributors\nhttps://www.openstreetmap.org/copyright\n실제 지도 타일과 시설·사업장 대표 좌표 사용. 개별 출입구·통근 경로·도시 경계와 구분합니다.\n\n가격·청약 사례: 첨부 리서치 대본의 파이낸셜뉴스 기사\nhttps://www.fnnews.com/news/202609060901255554\n\n차트: 국토교통부 실거래 수집 표본, 해제 제외. 대표 단지는 전용83~85㎡, 지역 비교는30평대. 2026년은10월6일까지 수집된 부분 연도 표본입니다.\n';
fs.writeFileSync('video/out/newtown-v7-sources.md',credits);
