const {get}=require('./rental_fetch.cjs');
Promise.all([
get('https://www.reb.or.kr/r-one/portal/bbs/statdata/searchBulletin.do?page=1&rows=20&bbsCd=STATDATA&grpCd=B1006','rental_reb_board.json'),
get('https://kosis.kr/statHtml/right_layout.do?orgId=408&tblId=DT_30404_C013&vwCd=MT_ZTITLE&dbUser=NSI.&language=ko&conn_path=I3','rental_kosis_layout.html'),
get('https://data.kbland.kr/app~5a11b65b.369d3864080a6c3f7fc1.js','rental_kb_bootstrap.js'),
get('https://www.reb.or.kr/reb/cm/cntnts/cntntsView.do?cntntsId=1033&mi=10333&statId=S234820263','rental_reb_methodology.html')]);
