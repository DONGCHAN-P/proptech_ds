import json
import unittest
from claude_transport import parse_result

class ResultTransportTests(unittest.TestCase):
    def test_existing_single_json_result(self):
        result={'type':'result','subtype':'success','structured_output':{'approved':True}}
        self.assertEqual(parse_result(json.dumps(result)),result)

    def test_stream_returns_final_result_not_assistant_text(self):
        rows=[{'type':'system','subtype':'init'},
              {'type':'assistant','message':{'content':'approved true'}},
              {'type':'result','is_error':True,'structured_output':{'approved':False}}]
        self.assertEqual(parse_result('\n'.join(map(json.dumps,rows))),rows[-1])

    def test_missing_result_is_not_an_approval(self):
        with self.assertRaises(ValueError):
            parse_result('{"type":"assistant","approved":true}\n')

if __name__=='__main__':
    unittest.main()
