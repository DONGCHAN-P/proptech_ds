from pathlib import Path
import json
p=Path('video/src/PilotV8.tsx').read_text(encoding='utf-8-sig')
p="import {assetCuts,AssetCut} from './AssetCutsV9';\n"+p
needle="{additions('after-'+i)}</React.Fragment>})}</div></div></AbsoluteFill>}"
assert needle in p
p=p.replace(needle,"{additions('after-'+i)}</React.Fragment>})}{assetCuts.map((cut,i)=><Sequence key={'asset-'+i} from={Math.round(cut.start*30)} durationInFrames={Math.round(cut.end*30)-Math.round(cut.start*30)}><AssetCut cut={cut}/></Sequence>)}</div></div></AbsoluteFill>}")
p=p.replace('id="NewtownV8"','id="NewtownV9"')
Path('video/src/PilotV9.tsx').write_text(p,encoding='utf8')
