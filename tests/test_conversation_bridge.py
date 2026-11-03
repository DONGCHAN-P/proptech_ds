import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from notify import conversation_bridge as cb

class ConversationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.store=self.root/'output/telegram_conversation'
        self.cfg={'enabled':True,'dispatch_enabled':True,'conversation_enabled':True,
                  'codex_thread':'01a13a00-2b87-7460-b2c7-1ac1332bacf9','codex_executable':'codex'}
    def update(self,uid=1,text='6분30초 지도 수정해줘',sender=123):
        return {'update_id':uid,'message':{'message_id':10,'text':text,'from':{'id':sender},'chat':{'id':123,'type':'private'}}}
    def test_general_request_persisted_without_approving_gate(self):
        r=cb.ingest(self.update(text='좋아; $(echo test)'), '123','123',self.cfg,self.store)
        e=json.loads(Path(r['path']).read_text(encoding='utf-8'))
        self.assertEqual(e['text'],'좋아; $(echo test)');self.assertNotIn('gate',e)
        self.assertEqual(e['status'],'pending_dispatch')
    def test_auth_duplicate_and_edit(self):
        self.assertFalse(cb.ingest(self.update(sender=999),'123','123',self.cfg,self.store)['accepted'])
        u=self.update();u['edited_message']=u.pop('message')
        self.assertFalse(cb.ingest(u,'123','123',self.cfg,self.store)['accepted'])
        self.assertTrue(cb.ingest(self.update(),'123','123',self.cfg,self.store)['accepted'])
        self.assertEqual(cb.ingest(self.update(),'123','123',self.cfg,self.store)['reason'],'duplicate')
    def test_dispatch_uses_fixed_path_prompt_not_shell_or_user_body(self):
        r=cb.ingest(self.update(text='secret feedback; $HOME'),'123','123',self.cfg,self.store)
        with patch.object(cb.subprocess,'run') as run:
            run.return_value.returncode=0;run.return_value.stdout='queued: 11111111-1111-1111-1111-111111111111'
            cb.dispatch(Path(r['path']),self.cfg,self.store)
        args=run.call_args.args[0]
        self.assertNotIn('secret feedback',str(args));self.assertFalse(run.call_args.kwargs.get('shell',False))
        self.assertEqual(json.loads(Path(r['path']).read_text())['status'],'dispatched')
    def test_outside_path_rejected(self):
        p=self.root/'outside.json';p.write_text('{}')
        with self.assertRaises(ValueError):cb.dispatch(p,self.cfg,self.store)
    def test_only_assistant_visible_events_forwarded(self):
        self.assertIsNone(cb.visible_text({'type':'response_item','payload':{'type':'reasoning','text':'private'}}))
        self.assertIsNone(cb.visible_text({'type':'event_msg','payload':{'type':'task_complete','last_agent_message':'duplicate'}}))
        e={'type':'event_msg','payload':{'type':'agent_message','phase':'final_answer','message':'완료'}}
        self.assertEqual(cb.visible_text(e),('final_answer','완료'))
    def test_tail_no_backlog_then_new_final_exactly_once(self):
        p=self.root/'rollout.jsonl';p.write_text(json.dumps({'type':'event_msg','payload':{'type':'agent_message','phase':'final_answer','message':'old'}})+'\n')
        cfg={**self.cfg,'transcript_path':str(p)}
        cb.mirror_once(cfg,self.store)
        with p.open('a') as f:f.write(json.dumps({'type':'event_msg','payload':{'type':'agent_message','phase':'final_answer','message':'new'}})+'\n')
        with patch.object(cb.TG,'send',return_value=True) as send:
            cb.mirror_once(cfg,self.store);cb.mirror_once(cfg,self.store)
        self.assertEqual(send.call_count,1);self.assertIn('new',send.call_args.args[0])
    def test_long_replies_split_without_truncation(self):
        parts=cb.split_text('가'*9000)
        self.assertEqual(''.join(parts),'가'*9000);self.assertTrue(all(len(p)<=3800 for p in parts))
    def test_async_question_forwarded_as_text(self):
        r={'type':'response_item','payload':{'type':'function_call','name':'request_user_input_async',
            'arguments':json.dumps({'questions':[{'title':'지도 어느 부분인가요?','options':['S1','S5']}]})}}
        self.assertEqual(cb.visible_text(r),('question','지도 어느 부분인가요?\n- S1\n- S5'))
    def test_partial_transcript_line_waits_for_newline(self):
        p=self.root/'rollout.jsonl';p.write_bytes(b'');cfg={**self.cfg,'transcript_path':str(p)}
        cb.mirror_once(cfg,self.store)
        payload=json.dumps({'type':'event_msg','payload':{'type':'agent_message','phase':'final_answer','message':'done'}}).encode()
        p.write_bytes(payload)
        with patch.object(cb.TG,'send',return_value=True) as send:
            cb.mirror_once(cfg,self.store);self.assertFalse(send.called)
            with p.open('ab') as f:f.write(b'\n')
            cb.mirror_once(cfg,self.store);self.assertEqual(send.call_count,1)
    def test_failed_reply_kept_and_retried(self):
        p=self.root/'rollout.jsonl';p.write_bytes(b'');cfg={**self.cfg,'transcript_path':str(p)};cb.mirror_once(cfg,self.store)
        p.write_text(json.dumps({'type':'event_msg','payload':{'type':'agent_message','phase':'final_answer','message':'new'}})+'\n')
        with patch.object(cb.TG,'send',return_value=False):cb.mirror_once(cfg,self.store)
        with patch.object(cb.TG,'send',return_value=True) as send:cb.mirror_once(cfg,self.store)
        self.assertEqual(send.call_count,1)
    def test_bot_routes_general_message_before_legacy(self):
        from notify import bot,video_decisions
        with patch.object(cb.TG,'creds',return_value=('unused','123')),patch.dict('os.environ',{'TELEGRAM_USER_ID':'123'}),\
             patch.object(video_decisions,'handle_update',return_value=None),\
             patch.object(cb,'handle_update',return_value={'accepted':True}) as route,patch.object(bot,'handle') as legacy:
            bot.process_update(self.update())
        route.assert_called_once();legacy.assert_not_called()
    def test_question_tool_and_synthetic_visible_final_are_not_sent_twice(self):
        p=self.root/'rollout.jsonl';p.write_bytes(b'');cfg={**self.cfg,'transcript_path':str(p)};cb.mirror_once(cfg,self.store)
        records=[{'type':'response_item','payload':{'type':'function_call','name':'request_user_input_async','arguments':json.dumps({'questions':[{'title':'질문','options':['A','B']}]})}},
                 {'type':'event_msg','payload':{'type':'agent_message','phase':'final_answer','message':'질문\n- A\n- B'}}]
        p.write_text(''.join(json.dumps(r)+'\n' for r in records))
        with patch.object(cb.TG,'send',return_value=True) as send:cb.mirror_once(cfg,self.store)
        self.assertEqual(send.call_count,1)
    def test_corrupt_inbox_does_not_stop_current_thread_events(self):
        inbox=self.store/'inbox';inbox.mkdir(parents=True)
        (inbox/'broken.json').write_text('{"status": "pending_dispatch",',encoding='utf-8')
        event={'status':'pending_dispatch','thread':self.cfg['codex_thread'],'attempts':0}
        (inbox/'current.json').write_text(json.dumps(event),encoding='utf-8')
        events,health=cb.pending_snapshot(self.cfg,self.store)
        self.assertEqual([p.name for p,e in events],['current.json'])
        self.assertEqual(health['invalid_inbox_count'],1)
        self.assertEqual(health['pending_count'],1)
        self.assertEqual((inbox/'broken.json').read_text(encoding='utf-8'),'{"status": "pending_dispatch",')
    def test_pending_old_thread_is_preserved_without_redispatch(self):
        inbox=self.store/'inbox';inbox.mkdir(parents=True)
        old={'status':'pending_dispatch','thread':'different-thread','attempts':1}
        (inbox/'old.json').write_text(json.dumps(old),encoding='utf-8')
        events,health=cb.pending_snapshot(self.cfg,self.store)
        self.assertEqual(events,[])
        self.assertEqual(health['other_thread_pending_count'],1)
        self.assertEqual(health['pending_count'],0)
        self.assertEqual(json.loads((inbox/'old.json').read_text(encoding='utf-8')),old)
    def test_removed_cli_path_falls_back_to_existing_installed_cli(self):
        installed=self.root/'codex.exe';installed.write_bytes(b'fixture')
        cfg={**self.cfg,'codex_executable':str(self.root/'removed-version/codex.exe')}
        with patch.object(cb.shutil,'which',return_value=str(installed)):
            self.assertEqual(cb.resolve_codex_executable(cfg),str(installed))
    def test_existing_cli_setting_is_kept(self):
        installed=self.root/'codex.exe';installed.write_bytes(b'fixture')
        cfg={**self.cfg,'codex_executable':str(installed)}
        self.assertEqual(cb.resolve_codex_executable(cfg),str(installed))
    def test_current_response_message_shape_is_forwarded(self):
        record={'type':'response_item','payload':{'type':'message','role':'assistant','phase':'commentary',
          'content':[{'type':'output_text','text':'연결을 복구했습니다.'}]}}
        self.assertEqual(cb.visible_text(record),('commentary','연결을 복구했습니다.'))
    def test_current_completed_agent_message_shape_is_forwarded(self):
        record={'type':'event_msg','payload':{'type':'item_completed','item':{'type':'AgentMessage','phase':'final_answer',
          'content':[{'type':'Text','text':'연결 확인 완료'}]}}}
        self.assertEqual(cb.visible_text(record),('final_answer','연결 확인 완료'))
    def test_new_event_shape_never_exports_reasoning_or_tools(self):
        for kind in ['Reasoning','CommandExecution','McpToolCall']:
            record={'type':'event_msg','payload':{'type':'item_completed','item':{'type':kind,'phase':'final_answer',
              'content':[{'type':'output_text','text':'private data'}]}}}
            self.assertIsNone(cb.visible_text(record))
    def test_duplicate_visible_event_shapes_are_sent_once(self):
        p=self.root/'rollout.jsonl';p.write_bytes(b'');cfg={**self.cfg,'transcript_path':str(p)}
        cb.mirror_once(cfg,self.store)
        records=[{'type':'response_item','payload':{'type':'message','role':'assistant','phase':'final_answer',
          'content':[{'type':'output_text','text':'연결 확인 완료'}]}},
          {'type':'event_msg','payload':{'type':'item_completed','item':{'type':'AgentMessage','phase':'final_answer',
          'content':[{'type':'Text','text':'연결 확인 완료'}]}}}]
        p.write_text(''.join(json.dumps(r)+'\n'for r in records),encoding='utf-8')
        with patch.object(cb.TG,'send',return_value=True)as send:cb.mirror_once(cfg,self.store)
        self.assertEqual(send.call_count,1)

if __name__=='__main__':unittest.main()
