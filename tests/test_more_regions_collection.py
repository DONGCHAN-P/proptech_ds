import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collector import collect_more_regions as job

class MoreRegionsTests(unittest.TestCase):
    def test_current_gwangju_and_ulsan_codes(self):
        groups=job.groups()
        self.assertEqual(set(groups['gwangju']),{'12210','12240','12270','12300','12330'})
        self.assertEqual(set(groups['ulsan']),{'31110','31140','31170','31200','31710'})
        self.assertFalse(set(groups['gwangju']) & set(job.OLD_GWANGJU.values()))

    def test_city_parent_exclusion_keeps_all_wards_and_unrelated_counties(self):
        groups=job.groups()
        self.assertTrue({'43111','43112','43113','43114','43740','43745','43710'} <= set(groups['chungbuk']))
        self.assertNotIn('43110',groups['chungbuk'])
        self.assertTrue({'44131','44133','44130'} <= set(groups['chungnam']))
        for codes in groups.values():
            self.assertEqual(len(codes),len(set(codes)))

    def test_call_reserved_before_request_and_cap_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(job,'LEDGER',Path(tmp)):
                job.reserve_call(1)
                p=next(Path(tmp).glob('calls-*.json'))
                self.assertEqual(json.loads(p.read_text())['calls'],1)
                with self.assertRaisesRegex(RuntimeError,'LOCAL_CALL_CAP_REACHED'):
                    job.reserve_call(1)
                self.assertEqual(json.loads(p.read_text())['calls'],1)

    def test_atomic_status_write_retries_transient_windows_reader_lock(self):
        real_replace=job.worker.os.replace
        attempts=[]
        def transient_lock(src,dst):
            attempts.append(1)
            if len(attempts)<3:
                raise PermissionError('simulated Windows reader sharing lock')
            return real_replace(src,dst)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'status.json'
            target.write_text('{"state":"before"}',encoding='utf8')
            with patch.object(job.worker.os,'replace',side_effect=transient_lock), patch.object(job.worker.time,'sleep'):
                job.worker.save(target,{'state':'after'})
            self.assertEqual(json.loads(target.read_text())['state'],'after')
            self.assertEqual(len(attempts),3)

if __name__=='__main__':
    unittest.main()
