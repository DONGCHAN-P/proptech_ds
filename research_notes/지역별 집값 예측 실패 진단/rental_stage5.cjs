const {get}=require('./rental_fetch.cjs');
Promise.all([
get('https://www.reb.or.kr/r-one/js/soportal/bbs/board/selectBoard.js','rental_reb_selectBoard.js'),
get('https://www.reb.or.kr/r-one/portal/bbs/statdata/selectBulletin.do?bbsCd=STATDATA&seq=1011','rental_reb_attachment.json'),
get('https://kosis.kr/statHtml/statHtmlContent.do?orgId=408&tblId=DT_40803_N0002&vwCd=MT_ZTITLE&dbUser=NSI.&language=ko&conn_path=I3','rental_kosis_legacy_content.html')]);
