import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('video_task_runner', ROOT/'analysis/video_task_runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class VideoTaskRunnerTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'output').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT/'output')
        self.folder = Path(self.tmp.name)
        self.source = self.folder/'input.txt'
        self.target = self.folder/'output.txt'
        self.source.write_text('first', encoding='utf8')
        command = "from pathlib import Path; import sys; p=Path(sys.argv[2]); p.write_text(Path(sys.argv[1]).read_text()); print('x'*20000)"
        self.job = {'task_id':'unit-render', 'inputs':[str(self.source)], 'outputs':[str(self.target)],
                    'steps':[{'argv':[sys.executable,'-c',command,str(self.source),str(self.target)]}]}
        self.jobs = self.folder/'jobs'

    def tearDown(self):
        self.tmp.cleanup()

    def test_same_inputs_reuse_but_changed_input_and_output_rebuild(self):
        self.assertFalse(runner.run_job(self.job,self.jobs)['reused'])
        self.assertTrue(runner.run_job(self.job,self.jobs)['reused'])
        self.source.write_text('second',encoding='utf8')
        self.assertFalse(runner.run_job(self.job,self.jobs)['reused'])
        self.assertEqual(self.target.read_text(),'second')
        self.target.write_text('corrupted',encoding='utf8')
        self.assertFalse(runner.run_job(self.job,self.jobs)['reused'])
        self.assertEqual(self.target.read_text(),'second')

    def test_changed_command_invalidates_cache(self):
        runner.run_job(self.job,self.jobs)
        self.job['steps'][0]['argv'][-3] += '; print(42)'
        self.assertFalse(runner.run_job(self.job,self.jobs)['reused'])

    def test_failure_is_not_success_or_retried(self):
        self.job['steps']=[{'argv':[sys.executable,'-c','raise SystemExit(7)']}]
        with self.assertRaises(runner.JobFailed):
            runner.run_job(self.job,self.jobs)
        receipt=json.loads((self.jobs/'unit-render/receipt.json').read_text())
        self.assertEqual(receipt['status'],'failed')
        self.assertEqual(receipt['exit_code'],7)
        self.assertFalse(self.target.exists())

    def test_missing_output_is_failure(self):
        self.job['steps']=[{'argv':[sys.executable,'-c','print(1)']}]
        with self.assertRaises(runner.JobFailed):runner.run_job(self.job,self.jobs)

    def test_stdout_stays_in_log_not_summary(self):
        result=runner.run_job(self.job,self.jobs)
        self.assertLess(len(json.dumps(result)),2000)
        self.assertNotIn('x'*100,result.__repr__())
        self.assertGreater((self.jobs/'unit-render/step-01.log').stat().st_size,19000)

    def test_paths_cannot_escape_workspace(self):
        self.job['outputs']=[str(ROOT.parent/'outside.txt')]
        with self.assertRaises(ValueError):runner.run_job(self.job,self.jobs)


if __name__=='__main__':unittest.main()
