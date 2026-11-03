from pathlib import Path
p=Path(__file__).resolve().parent
s=(p.parent/'series-hook-v6/generate.mjs').read_text(encoding='utf-8')
for a,b in [("from './preflight.mjs'","from '../series-hook-v6/preflight.mjs'"),('outputs/story-review-v6/M000_series_hook.txt','outputs/story-review-v8/M010_cta.txt'),('fea5b5541864404a1867408186876cbcdbbcc65ede1a931f47c43876df3f047e','d67f35c05d75736239d631a8afab1c9f6d84a1523ed0b03f5dc653651ba18d11'),('236','59'),('284','71'),('M000','M010')]:s=s.replace(a,b)
s=s.replace("assert.equal(auth.root_execution_authorized,true);", "assert.equal(auth.root_execution_authorized,true);assert.equal(auth.actual_credit_hard_cap,71);assert.equal(auth.submitted_character_hard_cap,71);assert.equal(auth.additional_cash_usd_cap,0);")
(p/'generate.mjs').write_text(s,encoding='utf-8')
