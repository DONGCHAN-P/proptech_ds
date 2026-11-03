"""Explicit user-authorized delivery of the completed channel report only."""
import datetime,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from notify import telegram as TG

def main():
 report=ROOT/'reports/유튜브_채널분석_20261029/보고서.html'
 receipt=ROOT/'output/telegram_deliveries/youtube_channel_review_20261029.json'
 digest=hashlib.sha256(report.read_bytes()).hexdigest()
 if receipt.exists():
  old=json.loads(receipt.read_text(encoding='utf-8'))
  if old.get('ok') and old.get('report_sha256')==digest:
   print(json.dumps({'status':'already_sent','message_id':old['message_id']}));return
 bridge=json.loads((ROOT/'config/video_telegram_bridge.json').read_text(encoding='utf-8'))
 assert bridge['private_chat_only'] is True
 token,cid=TG.creds();assert token and cid,'Configured Telegram connection unavailable'
 expected=os.getenv(bridge.get('sender_user_id_env','TELEGRAM_USER_ID'),'').strip()
 assert not expected or expected==cid,'Private recipient mismatch'
 chat=TG._post('getChat',token,data={'chat_id':cid})
 assert chat.get('ok') and chat['result']['type']=='private','Private recipient verification failed'
 caption='유튜브 채널 분석 보고서 · 2026-10-29\n\n영상별 성과·유입 경로·유지율과 8가지 인사이트, 다음 개선 순서를 정리했습니다.\nAnalytics 처리 데이터: 2026-10-02~10-25\n기간 조회수 8,439회 · 시청시간 110.4시간\n본편 검색 유입이 본편 시청시간의 75.5%를 차지했습니다.\n\nHTML을 다운로드해 브라우저로 열면 차트와 표를 볼 수 있습니다.'
 with report.open('rb') as f:
  response=TG._post('sendDocument',token,data={'chat_id':cid,'caption':caption},files={'document':('유튜브_채널분석_20261029.html',f,'text/html')},timeout=60)
 receipt.parent.mkdir(parents=True,exist_ok=True)
 if not response.get('ok'):
  fail={'ok':False,'error_code':response.get('code'),'error':TG.mask(response.get('error','send_failed'),token),'report_sha256':digest}
  receipt.write_text(json.dumps(fail,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(fail,ensure_ascii=False));raise SystemExit(1)
 msg=response['result'];doc=msg.get('document',{})
 result={'ok':True,'message_id':msg['message_id'],'file_name':doc.get('file_name'),'sent_bytes':doc.get('file_size'),'local_bytes':report.stat().st_size,'report_sha256':digest,'report':str(report.relative_to(ROOT)),'private_recipient_verified':True,'sent_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':'Direct user request: 유튜브 채널 분석 보고서는 텔레그램으로 보내줘'}
 receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:result[k] for k in ['ok','message_id','file_name','sent_bytes']},ensure_ascii=False))
if __name__=='__main__':main()
