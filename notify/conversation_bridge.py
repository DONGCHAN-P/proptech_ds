"""Authenticated ordinary Telegram messages ↔ one explicitly bound Codex thread.

Never evaluates message bodies. Only fixed inbox paths enter CLI argv. The existing
bot remains the sole getUpdates consumer. Replies tail visible events, not tools
or reasoning, from the configured conversation's local transcript.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from notify import telegram as TG
from notify.video_decisions import write,now

ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'output/telegram_conversation'
CONFIG=ROOT/'config/video_telegram_bridge.json'
DISPATCH_LOCK=threading.Lock()
LEGACY={'/today','/후보','/again','/역세권','/subway','/시간여행','/timetravel',
        '/예산','/budget','/단지','/find','/찾기','/평형','/pyeong','/carousel',
        '/캐러셀','/thread','/스레드','/all','/전부','/done','/올림','/skip','/건너뜀','/log'}

def config():return json.loads(CONFIG.read_text(encoding='utf-8-sig'))
def authorized(update,chat,user):
    m=update.get('message') or {};c=m.get('chat') or {};u=m.get('from') or {}
    return bool(chat and user and c.get('type')=='private' and
                str(c.get('id'))==str(chat) and str(u.get('id'))==str(user) and not u.get('is_bot'))

def ingest(update,chat,user,cfg,store=STORE):
    if not authorized(update,chat,user):return {'accepted':False,'reason':'unauthorized'}
    if not isinstance(update.get('update_id'),int):return {'accepted':False,'reason':'invalid_update'}
    uid=update['update_id'];p=Path(store)/'inbox'/f'{uid}.json'
    if p.exists():return {'accepted':False,'reason':'duplicate','path':str(p)}
    m=update['message'];text=m.get('text') or m.get('caption') or ''
    media=[]
    if m.get('photo'):media.append({**m['photo'][-1],'kind':'photo','suffix':'.jpg'})
    for key in ['document','voice','video','audio']:
        if m.get(key):media.append({**m[key],'kind':key})
    if not text.strip() and not media:return {'accepted':False,'reason':'unsupported_message'}
    e={'update_id':uid,'message_id':m.get('message_id'),'text':text,'media':media,
       'reply_to_message_id':(m.get('reply_to_message') or {}).get('message_id'),
       'received_at':now().isoformat(),'thread':cfg['codex_thread'],
       'status':'pending_dispatch','attachments':[],'source':'authenticated_telegram_user'}
    write(p,e);return {'accepted':True,'path':str(p),'event':e}

def download_media(event,store=STORE):
    import requests
    tok=TG.creds()[0];result=[]
    for i,m in enumerate(event.get('media',[])):
        if m.get('file_size',0)>20*1024*1024:raise ValueError('attachment_exceeds_20MiB')
        info=TG._post('getFile',tok,data={'file_id':m['file_id']})
        if not info.get('ok'):raise RuntimeError('telegram_getFile_failed')
        remote=info['result']['file_path']
        suffix=Path(remote).suffix.lower()
        if not re.fullmatch(r'\.[a-z0-9]{1,8}',suffix):suffix='.bin'
        target=Path(store)/'attachments'/f"{event['update_id']}_{i}{suffix}"
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            tmp=target.with_suffix(suffix+'.part');size=0
            try:
                with requests.get(f'{TG.API}/file/bot{tok}/{remote}',stream=True,timeout=40) as res:
                    res.raise_for_status()
                    with tmp.open('wb') as fh:
                        for chunk in res.iter_content(65536):
                            size+=len(chunk)
                            if size>20*1024*1024:raise ValueError('attachment_exceeds_20MiB')
                            fh.write(chunk)
                tmp.replace(target)
            finally:
                if tmp.exists():tmp.unlink()
        result.append({'path':str(target.resolve()),'kind':m['kind'],
                       'original_name':m.get('file_name'),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    return result

def dispatch(path,cfg,store=STORE):
    with DISPATCH_LOCK:return _dispatch(path,cfg,store)

def resolve_codex_executable(cfg):
    """Recover from an extension update removing a version-pinned CLI path."""
    configured=cfg.get('codex_executable') or 'codex'
    if Path(configured).is_file():return str(configured)
    found=shutil.which(configured) or shutil.which('codex')
    if found and Path(found).is_file():return found
    extensions=Path.home()/'.vscode/extensions'
    candidates=list(extensions.glob('openai.chatgpt-*/bin/windows-x86_64/codex.exe'))
    if candidates:
        return str(max(candidates,key=lambda p:tuple(int(v)for v in re.findall(r'\d+',p.parts[-4]))))
    raise FileNotFoundError('installed_codex_cli_not_found')

def _dispatch(path,cfg,store=STORE):
    path=Path(path).resolve();path.relative_to((Path(store)/'inbox').resolve())
    event=json.loads(path.read_text(encoding='utf-8'))
    if event['status']!='pending_dispatch':return
    if not re.fullmatch(r'[a-f0-9-]{36}',cfg['codex_thread']):raise ValueError('invalid_thread')
    if event['thread']!=cfg['codex_thread']:raise ValueError('thread_binding_changed')
    if event.get('media') and not event.get('attachments'):
        event['attachments']=download_media(event,store);write(path,event)
    prompt=(f'Read the authenticated Telegram conversation message file {path}. '
            'Its text is the user request for this same conversation, and attachments are user-provided data. '
            'Continue the active work with this feedback; do not execute message text as shell code. '
            'If application_status is already applied, do not repeat completed work. '
            'Preserve five scoped video approval gates and existing budgets. A casual reply is not a blanket approval. '
            'Reply in Korean in this conversation. Visible progress and final replies are automatically mirrored to the existing private Telegram chat; '
            'do not send a second identical text via notify.telegram. Use the Telegram file sender only for requested deliverable files. '
            'Record applied status on this inbox event when handled.')
    if event.get('source')=='bridge_internal_self_test':
        prompt=(f'Read the bridge internal connectivity test file {path}. This is a technical self-test, not a new user video task. '
                'Continue the ongoing user work. In a brief Korean commentary say Telegram bridge queue connectivity was received, '
                'and record application_status=applied on that event. Do not create videos, spend credits, approve gates, or upload anything because of this test.')
    args=[resolve_codex_executable(cfg),'queue','--thread',cfg['codex_thread'],'--message',prompt]
    for a in event.get('attachments',[]):
        if Path(a['path']).suffix.lower() in {'.jpg','.jpeg','.png','.webp'}:args+=['-i',a['path']]
    event.update(status='dispatching',dispatch_started_at=now().isoformat(),attempts=event.get('attempts',0)+1);write(path,event)
    try:result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,cwd=ROOT)
    except (subprocess.TimeoutExpired,OSError) as exc:
        event.update(status='dispatch_unknown' if isinstance(exc,subprocess.TimeoutExpired) else 'pending_dispatch',error_type=type(exc).__name__);write(path,event);raise
    if result.returncode:
        event.update(status='pending_dispatch',error_type='CodexQueueFailed');write(path,event)
        raise RuntimeError('CodexQueueFailed')
    ids=[x for x in re.findall(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',result.stdout) if x!=cfg['codex_thread']]
    event.update(status='dispatched',dispatched_at=now().isoformat(),queued_message_id=ids[0] if ids else None);write(path,event)

def handle_update(update):
    cfg=config()
    if not (cfg.get('enabled') and cfg.get('conversation_enabled')):return None
    text=((update.get('message') or {}).get('text') or '').strip()
    command=text.split(maxsplit=1)[0].lower() if text else ''
    if command in LEGACY:return None
    tok,chat=TG.creds();user=os.getenv('TELEGRAM_USER_ID','').strip() or chat
    if not authorized(update,chat,user):return {'accepted':False,'reason':'unauthorized'}
    if text.lower()=='/status':
        health=STORE/'health.json';h=json.loads(health.read_text(encoding='utf-8')) if health.exists() else {}
        TG.send(f"현재 제작 대화 연결: {cfg['codex_thread']}\n답변 전송기: {h.get('mirror','확인 중')}\n"
                f"전달 대기/확인 필요: {h.get('pending_count',0)}건\n"
                '접수 알림은 작업 완료를 뜻하지 않습니다. 일반 문장·사진으로 계속 요청하시면 됩니다.',quiet=True)
        return {'accepted':True,'kind':'status'}
    if text.lower() in {'/help','/start','/status','/대화'}:
        TG.send('이제 일반 문장과 사진을 보내면 현재 영상 제작 대화로 전달합니다.\n'
                '예: 6분 30초 지도를 더 크게 보여줘\n답변과 진행 상황도 이곳으로 돌아옵니다.\n'
                '승인: /approve 결정ID · 수정: /revise 결정ID 수정내용\n'
                'PC·인터넷·Codex와 봇이 실행 중이어야 합니다. 첨부는 파일당 최대 20MiB입니다.',quiet=True)
        return {'accepted':True,'kind':'help'}
    result=ingest(update,chat,user,cfg)
    if not result['accepted']:return result
    if not cfg.get('dispatch_enabled'):
        TG.send('요청을 저장했습니다. Codex 전달이 꺼져 있어 대기 중입니다.',quiet=True);return result
    try:
        dispatch(Path(result['path']),cfg)
        TG.send('요청을 현재 제작 대화에 전달했습니다. 작업 대기열 접수이며 완료 알림은 별도로 보내드립니다.',quiet=True)
    except Exception as exc:
        if isinstance(exc,ValueError) and str(exc)=='attachment_exceeds_20MiB':
            p=Path(result['path']);e=json.loads(p.read_text(encoding='utf-8'));e.update(status='attachment_too_large');write(p,e)
            TG.send('첨부파일은 20MiB 이하로 보내주세요. 본문은 저장됐으며, 작은 파일을 다시 보내주시면 이어서 전달합니다.',quiet=True)
        else:TG.send(f'요청은 저장했지만 전달이 대기 중입니다 ({type(exc).__name__}). /status로 연결 안내를 확인할 수 있습니다.',quiet=True)
    return result

def split_text(text,limit=3800):return [text[i:i+limit] for i in range(0,len(text),limit)]

def visible_text(record):
    p=record.get('payload') or {}
    if record.get('type')=='event_msg' and p.get('type')=='agent_message' and p.get('phase') in {'commentary','final_answer'}:
        return p['phase'],p.get('message','')
    # Current logs store completed AgentMessage items, and retain a response
    # message record with the same visible text. The mirror's fingerprint
    # deduplicates these two representations. Never accept Reasoning/tool items.
    message=None
    if record.get('type')=='event_msg' and p.get('type')=='item_completed':
        item=p.get('item') or {}
        if item.get('type')=='AgentMessage':message=item
    elif record.get('type')=='response_item' and p.get('type')=='message' and p.get('role')=='assistant':
        message=p
    if message and message.get('phase') in {'commentary','final_answer'}:
        content=message.get('content') or []
        text=content if isinstance(content,str) else ''.join(
            part.get('text','') for part in content
            if isinstance(part,dict) and part.get('type') in {'Text','text','output_text'})
        if text.strip():return message['phase'],text
    if record.get('type')=='response_item' and p.get('type')=='function_call' and str(p.get('name','')).endswith('request_user_input_async'):
        try:
            args=json.loads(p.get('arguments','{}'))
            return 'question','\n\n'.join(q['title']+('\n'+'\n'.join('- '+o for o in q['options']) if q.get('options') else '') for q in args.get('questions',[]))
        except (ValueError,KeyError,TypeError):return None
    return None

def mirror_once(cfg,store=STORE):
    store=Path(store);path=Path(cfg['transcript_path']);cursor=store/'reply_cursor.json'
    state=json.loads(cursor.read_text(encoding='utf-8')) if cursor.exists() else {}
    if not path.is_file():raise FileNotFoundError('bound_transcript_missing')
    if state.get('transcript_path')!=str(path) or state.get('offset',0)>path.stat().st_size:
        write(cursor,{'transcript_path':str(path),'offset':path.stat().st_size});return
    with path.open('rb') as fh:
        fh.seek(state['offset'])
        for _ in range(500):
            line=fh.readline()
            if not line or not line.endswith(b'\n'):break
            record=json.loads(line);visible=visible_text(record)
            if visible and visible[1].strip():
                phase,text=visible;fingerprint=hashlib.sha256(' '.join(text.split()).encode()).hexdigest()
                recent=state.setdefault('recent_text_hashes',[])
                if fingerprint not in recent:
                    ident=hashlib.sha256(str(state['offset']).encode()+line).hexdigest()[:24]
                    out=store/'outbox'/f'{ident}.json'
                    if not out.exists():write(out,{'phase':phase,'text':TG.mask(text),'status':'pending','part':0,'created_at':now().isoformat()})
                    state['recent_text_hashes']=(recent+[fingerprint])[-100:]
            state['offset']=fh.tell();write(cursor,state)
    for out in sorted((store/'outbox').glob('*.json'),key=lambda p:json.loads(p.read_text(encoding='utf-8'))['created_at']):
        e=json.loads(out.read_text(encoding='utf-8'))
        if e['status']!='pending':continue
        parts=split_text(e['text'])
        for i in range(e['part'],len(parts)):
            if not TG.send(parts[i],quiet=True):return
            e['part']=i+1;write(out,e)
        e.update(status='sent',sent_at=now().isoformat());write(out,e)

def pending_snapshot(cfg,store=STORE):
    """Isolate corrupt and retired-thread records without changing their data."""
    events=[]
    health={'pending_count':0,'invalid_inbox_count':0,'other_thread_pending_count':0}
    for path in sorted((Path(store)/'inbox').glob('*.json')):
        try:
            event=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(event,dict):raise ValueError('inbox_record_not_object')
        except (ValueError,UnicodeError,OSError):
            health['invalid_inbox_count']+=1
            continue
        if event.get('status') not in {'pending_dispatch','dispatch_unknown','dispatching'}:continue
        if event.get('thread')!=cfg['codex_thread']:
            health['other_thread_pending_count']+=1
            continue
        events.append((path,event))
    health['pending_count']=len(events)
    return events,health

def start_worker():
    def run():
        while True:
            status={'at':now().isoformat()}
            try:
                cfg=config()
                if cfg.get('conversation_enabled') and cfg.get('mirror_enabled'):
                    mirror_once(cfg);status['mirror']='running'
                pending,summary=pending_snapshot(cfg)
                status.update(summary)
                if cfg.get('conversation_enabled') and cfg.get('dispatch_enabled'):
                    for p,e in pending:
                        if e.get('status')=='pending_dispatch' and e.get('attempts',0)<3:
                            last=e.get('dispatch_started_at')
                            from datetime import datetime
                            if not last or (now()-datetime.fromisoformat(last)).total_seconds()>30:
                                try:dispatch(p,cfg)
                                except Exception:pass
            except Exception as exc:status['error_type']=type(exc).__name__
            write(STORE/'health.json',status)
            threading.Event().wait(3)
    threading.Thread(target=run,name='telegram-reply-mirror',daemon=True).start()
