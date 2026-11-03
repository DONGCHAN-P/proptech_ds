"""Adapt proven release tools for the newly approved, bounded Jun revision."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
OLD=EP/'director/two-episode-production-v1'

def create(name, replacements):
    text=(OLD/name).read_text(encoding='utf8')
    for before,after in replacements:
        assert text.count(before)==1,(name,before,text.count(before))
        text=text.replace(before,after)
    target=HERE/name
    assert not target.exists(),target
    target.write_text(text,encoding='utf8')

create('claude_review.py',[
    ("out=EP/'director/two-episode-production-v1/claude'/args.round", "out=EP/'director/launch-and-jun-v1/claude'/args.round"),
    ("사용자2026-10-26직접지시:Claude검수및무료TTS후YouTube비공개업로드. 개인거래/자격증명전달금지.",
     "사용자2026-10-26직접승인:동일대본v6의Jun음성포함10739크레딧상한·추가결제0·Claude검수후YouTube비공개업로드및기존비공개exEGpjcqdF0교체. 개인거래/자격증명전달금지.")
])
create('claude_transport.py',[])
create('prepare_final_release.py',[
    ("assert authorization['paid_voice_generation_authorized'] is False", "assert authorization['paid_voice_generation_authorized'] is True\nassert authorization['included_credit_cap']==10739 and authorization['additional_cash_usd_cap']==0\nledger=read(EP/'narration/jun-production-v1/generation_ledger.json')\nassert ledger['status']=='completed' and ledger['actual_credits']<=authorization['included_credit_cap']\nassert ledger['topup_calls']==0 and ledger['overage_calls']==0 and ledger['automatic_retries']==0"),
    ("default='outputs/private-release-v2'", "default='outputs/jun-release-v1'"),
    ("default='v6'", "default='jun-v1'")
])
create('private_release.py',[
    ("assert authorization['paid_voice_generation_authorized'] is False", "assert authorization['paid_voice_generation_authorized'] is True\n        assert authorization['included_credit_cap']==10739 and authorization['additional_cash_usd_cap']==0\n        ledger=read(episode/'narration/jun-production-v1/generation_ledger.json')\n        assert ledger['status']=='completed' and ledger['actual_credits']<=authorization['included_credit_cap']\n        assert ledger['topup_calls']==0 and ledger['overage_calls']==0 and ledger['automatic_retries']==0")
])
lock=json.loads((OLD/'locked_script.json').read_text(encoding='utf8'))
(HERE/'locked_script.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'adapted':['claude_review.py','claude_transport.py','prepare_final_release.py','private_release.py'],
                  'generation_executed':False,'upload_executed':False,'delete_executed':False}))
