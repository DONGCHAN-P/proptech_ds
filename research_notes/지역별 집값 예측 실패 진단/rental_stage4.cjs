const {get}=require('./rental_fetch.cjs');
Promise.all([
get('https://www.reb.or.kr/r-one/portal/bbs/statdata/selectBulletinPage.do?bbsCd=STATDATA&seq=1011','rental_reb_monthly_attachment.html'),
get('https://kosis.kr/statHtml/statHtmlContent.do?orgId=408&tblId=DT_30404_C013&vwCd=MT_ZTITLE&dbUser=NSI.&language=ko&conn_path=I3','rental_kosis_content.html')]);
