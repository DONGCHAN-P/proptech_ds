import fs from 'node:fs/promises';
import {account} from '../namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs';
// Read-only account queries; does not generate or upload any narration text.
const {safe}=await account();
await fs.mkdir(new URL('narration/',import.meta.url),{recursive:true});
await fs.writeFile(new URL('narration/account_preflight.json',import.meta.url),JSON.stringify(safe,null,2));
console.log(JSON.stringify({included_remaining:safe.included_remaining,voice_rate:safe.voice_rate,model_rates:safe.model_rates,overage_enabled:safe.overage_enabled,paid_api_called:false}));
