import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SIDE=Path(__file__).resolve().parent


class RepairV6Contracts(unittest.TestCase):
    def module(self):
        source=SIDE/'repair_v6.py'
        self.assertTrue(source.is_file(),'v6 최소 변경 재사용 생성기 구현 전')
        spec=importlib.util.spec_from_file_location('repair_v6',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def inputs(self):
        old=json.loads((SIDE/'prepare-v5/prepared.json').read_text(encoding='utf8'))
        new=json.loads((SIDE/'prepare-v6/prepared.json').read_text(encoding='utf8'))
        changes=json.loads((SIDE.parents[1]/'outputs/script-final-v6/changes.json').read_text(encoding='utf8'))
        return old,new,changes

    def test_only_declared_two_paragraphs_can_be_synthesized(self):
        r=self.module();old,new,changes=self.inputs()
        result=r.compare_plans(old,new,changes)
        self.assertEqual(result['changed_ids'],['C05P03','C06P02'])
        self.assertEqual(result['reused_count'],52)
        bad=copy.deepcopy(new);bad['chapters'][0]['paragraphs'][0]['text']+=' 변경'
        with self.assertRaises(ValueError):r.compare_plans(old,bad,changes)

    def test_reuse_rejects_reading_voice_or_original_text_drift(self):
        r=self.module();old,new,_=self.inputs()
        paragraph=new['chapters'][0]['paragraphs'][0]
        folder=SIDE/'production-injoon-v5/paragraphs/C01P01'
        request=r.p.load(folder/'request.json');measured=r.p.load(folder/'measured.json')
        r.assert_reusable(paragraph,request,measured,new['voice'])
        for key in ('text','spoken_text'):
            bad=copy.deepcopy(request);bad[key]+=' 변경'
            with self.assertRaises(ValueError):r.assert_reusable(paragraph,bad,measured,new['voice'])
        bad=copy.deepcopy(request);bad['voice']['rate']='-10%'
        with self.assertRaises(ValueError):r.assert_reusable(paragraph,bad,measured,new['voice'])

    def test_versioned_publication_keeps_v5_and_rejects_root_drift(self):
        r=self.module()
        with tempfile.TemporaryDirectory(dir=SIDE) as temp:
            root=Path(temp);original=b'{"revision":"v5"}\n';(root/'final_timing.json').write_bytes(original)
            expected=r.p.digest(root/'final_timing.json')
            r.publish_versioned(root,expected,{'revision':'v6'})
            self.assertEqual((root/'final_timing.v5.json').read_bytes(),original)
            self.assertEqual((root/'final_timing.v6.json').read_bytes(),(root/'final_timing.json').read_bytes())
            with self.assertRaises(ValueError):r.publish_versioned(root,expected,{'revision':'v6-again'})


if __name__=='__main__':unittest.main(verbosity=2)
