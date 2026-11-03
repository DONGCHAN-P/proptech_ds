import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from notify import video_decisions as vd


class VideoDecisionCommands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = self.root / 'output/video_decisions'
        (self.root / 'config').mkdir()
        (self.root / 'config/video_telegram_bridge.json').write_text(
            json.dumps({'enabled': True, 'dispatch_enabled': False}), encoding='utf-8')
        self.d = vd.create('test-episode', 'script', 'script-v1', store=self.store)

    def update(self, text, sender=123):
        return {'update_id': 1, 'message': {'text': text, 'from': {'id': sender},
                'chat': {'id': 123, 'type': 'private'}}}

    def test_bot_suffix_and_whitespace(self):
        result = vd.ingest(self.update('/approve@proptech_ds_bot\n' + self.d['id']), '123', '123', self.store)
        self.assertTrue(result['accepted'])

    def test_plain_explicit_command(self):
        result = vd.ingest(self.update('approve ' + self.d['id']), '123', '123', self.store)
        self.assertTrue(result['accepted'])

    def test_revision_requires_feedback(self):
        result = vd.ingest(self.update('/revise ' + self.d['id']), '123', '123', self.store)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['reason'], 'missing_revision_note')
        self.assertEqual(json.loads((self.store / 'decisions' / (self.d['id'] + '.json')).read_text())['status'], 'pending')

    def test_bare_command_is_handled_with_guidance_without_approval(self):
        from notify import telegram
        with patch.object(vd, 'ROOT', self.root), patch.object(vd, 'STORE', self.store), \
             patch.object(telegram, 'creds', return_value=('unused', '123')), \
             patch.object(telegram, 'send', return_value=True) as send, \
             patch.dict('os.environ', {'TELEGRAM_USER_ID': '123'}):
            result = vd.handle_update(self.update('/approve'))
        self.assertIsNotNone(result)
        self.assertFalse(result['accepted'])
        self.assertIn(self.d['id'], send.call_args.args[0])
        self.assertFalse((self.store / 'inbox').exists())

    def test_sender_and_edited_messages_remain_rejected(self):
        text = '/approve ' + self.d['id']
        self.assertEqual(vd.ingest(self.update(text, sender=999), '123', '123', self.store)['reason'], 'unauthorized')
        up = self.update(text)
        up['edited_message'] = up.pop('message')
        self.assertFalse(vd.ingest(up, '123', '123', self.store)['accepted'])

    def test_valid_command_records_processing_without_feedback_text(self):
        from notify import telegram
        with patch.object(vd, 'ROOT', self.root), patch.object(vd, 'STORE', self.store), \
             patch.object(telegram, 'creds', return_value=('unused', '123')), \
             patch.object(telegram, 'send', return_value=True), \
             patch.dict('os.environ', {'TELEGRAM_USER_ID': '123'}):
            result = vd.handle_update(self.update('/revise ' + self.d['id'] + ' private feedback'))
        self.assertTrue(result['accepted'])
        record = (self.root / 'logs/video_decisions.jsonl').read_text(encoding='utf-8')
        self.assertNotIn('private feedback', record)
        data = json.loads(record)
        self.assertEqual(data['stage'], 'ingest')
        self.assertTrue(data['accepted'])
        self.assertEqual(data['decision_id'], self.d['id'])

    def test_revision_content_is_data_and_replay_rejected(self):
        up = self.update('/revise ' + self.d['id'] + ' echo unsafe; $HOME')
        result = vd.ingest(up, '123', '123', self.store)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['event']['note'], 'echo unsafe; $HOME')
        self.assertFalse(vd.ingest(up, '123', '123', self.store)['accepted'])


if __name__ == '__main__':
    unittest.main()
