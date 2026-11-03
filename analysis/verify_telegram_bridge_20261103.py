"""Verify the restored bridge using existing authenticated records, no sends."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from notify.video_decisions import write
O=R/'reports/텔레그램_연결진단_20261103';S=R/'output/telegram_conversation'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
cfg=read(R/'config/video_telegram_bridge.json');h=read(S/'health.json');diag=read(O/'diagnosis.json')
assert cfg['codex_thread']==os.environ['CODEX_THREAD_ID']
assert Path(cfg['codex_executable']).is_file()
assert h.get('mirror')=='running' and 'error_type'not in h
assert (datetime.now(timezone.utc)-datetime.fromisoformat(h['at'])).total_seconds()<20
incoming=read(S/'inbox/718066311.json')
assert incoming['source']=='authenticated_telegram_user' and incoming['thread']==cfg['codex_thread']
assert incoming['status']=='dispatched' and incoming['application_status']=='applied'
matches=[]
for p in (S/'outbox').glob('*.json'):
 j=read(p)
 if j.get('phase')=='commentary' and '일반 답변도 전송되도록' in j.get('text','') and '보냈어' in j.get('text',''):matches.append((p,j))
assert matches,'No current acknowledgement reply has been mirrored yet'
path,outgoing=max(matches,key=lambda row:row[1].get('created_at',''))
assert outgoing['status']=='sent','Current acknowledgement is still pending Telegram delivery'
for row in diag['invalid_records_preserved']:
 p=S/'inbox'/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
diag.update(status='repaired_live_bidirectional_path_verified',verified_at_kst=datetime.now(timezone(timedelta(hours=9))).isoformat(),
 root_causes=['bound_to_old_conversation','extension_update_removed_pinned_CLI','three_malformed_inbox_JSON_records_aborted_worker_iteration','current_Assistant_message_event_shapes_not_recognized'],
 process_correction='The stale PID marker suggested a stopped receiver; a scoped process query found a running receiver, which was restarted with the fixes.',
 test_count=27,tests_passed=True,current_health=h,current_poller_pid=(S/'poller_pid.txt').read_text(encoding='utf-8').strip(),
 incoming_test={'update_id':incoming['update_id'],'authenticated':True,'queued_message_id':incoming.get('queued_message_id'),'dispatched':True,'applied':True},
 outgoing_test={'receipt':str(path.relative_to(R)).replace('\\','/'),'phase':outgoing['phase'],'status':outgoing['status'],'sent_at':outgoing['sent_at']},
 phone_display_or_read_receipt_verified=False,
 source_changes=['notify/conversation_bridge.py','notify/bot.py','tests/test_conversation_bridge.py','config/video_telegram_bridge.json'],
 previous_message_381_edited=False)
write(O/'diagnosis.json',diag)
report='''# 텔레그램 연결 진단·복구

2026-11-03, 한국시간 기준. 자동 답장 경로를 복구하고 실제 인증된 수신과 Telegram API 발송을 확인했습니다.

## 확인된 원인

1. 연결이 현재 대화 대신 10월 14일의 이전 대화를 가리켰습니다.
2. 확장 프로그램 업데이트 뒤 사라진 구버전 실행 파일 경로가 남아 있었습니다.
3. 손상된 수신 JSON 3개 중 하나를 읽다가 처리 반복 전체가 중단됐습니다.
4. 현재 로그의 `item_completed/AgentMessage` 및 `response_item/message` 형식을 읽지 못해 일반 답변이 누락됐습니다. 질문 도구 알림은 별도 경로여서 전송될 수 있었습니다.

## 반영한 수정

현재 대화·로그·설치된 실행 파일로 연결했습니다. 실행 파일 경로가 바뀌면 설치된 CLI를 다시 찾도록 했습니다. 손상된 기록은 원본 그대로 보존하며, 이전 대화의 미처리 요청은 자동 재실행하지 않습니다. 답변의 새 기록 형식을 지원하고 중복 전송·추론/도구 출력 제외 검사를 유지했습니다. 실행 중인 단일 수신기에 수정을 반영했습니다.

수신기가 중지됐다는 초기 판단은 오래된 PID 기록에 따른 오판이었습니다. 실제 프로세스는 실행 중이었으며, 진단 과정에서 확인·정정하고 재시작했습니다.

## 검증

- 관련 테스트 27개 통과
- 정상 상태의 최신 heartbeat 및 현재 대화 바인딩 확인
- 텔레그램의 실제 인증 메시지 ‘보냈어’ 수신 → 현재 대화 큐 전달 → 적용 확인
- 해당 메시지에 대한 현재 답변의 자동 전송 영수증 `sent` 확인
- 손상 기록 3개의 원본 해시 보존 확인, 이전 대화의 요청 3개 자동 재실행 차단

휴대폰 화면 표시·읽음 여부는 API 영수증과 구분합니다. 어제 업로드 알림은 11월 2일 19:40, @proptech_ds_bot의 메시지381로 전송 성공 응답이 기록돼 있으나 휴대폰에서 보이지 않았던 직접 원인은 확정하지 못했습니다.

기존 알림을 같은 내용으로 수정해 존재를 확인하려던 `editMessageText` 요청은 자동 승인 검토에서 ‘진단 요청에 기존 메시지 수정 권한은 포함되지 않는다’는 이유로 거절되어 실행하지 않았습니다. 해당 알림을 수정하거나 삭제하지 않았습니다.
'''
(O/'진단결과.md').write_text(report,encoding='utf-8')
print(json.dumps({'bridge':'running_current_conversation','tests_passed':27,'authenticated_inbound_dispatched':True,'current_reply_mirrored':'sent','original_invalid_records_preserved':3,'phone_read_receipt':'not_verified','existing_message_edited':False},ensure_ascii=False))
