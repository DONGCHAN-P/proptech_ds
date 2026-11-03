from pathlib import Path
import json,hashlib,subprocess
from PIL import Image
E=Path('video-agent-studio/episodes/capital-10eok-map-20261017');O=E/'outputs/monthly-5eok-permanent-v2';B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');v=O/'capital_5eok_permanent_monthly_2006-2026_v2.mp4'
for i,f in enumerate([0,965,966,967,968,969,970,971,1709]):
 p=O/f'encoded_f{f:04d}.png';subprocess.run([str(B/'ffmpeg.exe'),'-v','error','-y','-i',str(v),'-vf',f'select=eq(n\,{f})','-frames:v','1',str(p)],check=True)
 im=Image.open(p);im.resize((375,667)).save(O/f'phone375_f{f:04d}.png')
contact=Image.new('RGB',(375*6,667))
for i,f in enumerate(range(966,972)):contact.paste(Image.open(O/f'phone375_f{f:04d}.png'),(375*i,0))
contact.save(O/'motion_contact_phone375.png')
r=json.loads((O/'technical_receipt.json').read_text(encoding='utf8'));h={'status':'render_complete_independent_qa_pending','video':str(v),'sha256':r['sha256'],'full_decode_exit_code':0,'frames':1710,'duration_s':57,'audio_streams':0,'rule':'first strictly-over-50000 month immediately and permanently off; no_trade stays lit until breach; no reappearance','final_lit':2524,'final_cumulative_observed':8288,'unlinked_excluded':884,'partial_month':'2026.10 maximum contract date2026.10.10','qa_path':'qa/monthly-5eok-permanent-v2/final_review.json','actual_continuous_playback':False,'actual_listening':False,'new_api_calls':0,'paid_calls':0,'upload':False};(O/'handoff.json').write_text(json.dumps(h,indent=2),encoding='utf8');print(json.dumps(h))
