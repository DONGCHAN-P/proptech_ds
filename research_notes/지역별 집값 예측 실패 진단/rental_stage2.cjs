const {get}=require('./rental_fetch.cjs');
Promise.all([
get('https://www.reb.or.kr/r-one/js/soportal/bbs/board/searchBoard.js','rental_reb_searchBoard.js'),
get('https://data.kbland.kr/app~748942c6.7c22ab6481181795a467.js','rental_kb_app.js'),
get('https://kosis.kr/serviceInfo/newContrainDataDetail.do?boardIdx=1985011&boardOrgId=408','rental_kosis_updates.html')]);
