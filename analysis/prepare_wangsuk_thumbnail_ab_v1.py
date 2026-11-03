"""Package generated thumbnail without changing its artwork; preserve current control."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
root=Path(__file__).resolve().parents[1]
o=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/thumbnail-ab-v1';o.mkdir(exist_ok=True)
original=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15/thumbnail.jpg'
generated=Path('C:/Users/e2ken/.codex/generated_images/01a13a00-2b87-7460-b2c7-1ac1332bacf9/exec-48d6736c-1fd4-49c9-abea-f2c2f88561ca.png')
shutil.copy2(original,o/'A_plan_control.jpg');shutil.copy2(generated,o/'B_ai_city_original.png')
# Delivery encoding only: keep generated artwork, dimensions and typography unchanged.
with Image.open(generated) as im:
 im.convert('RGB').save(o/'B_ai_city_test.jpg',quality=95,optimize=True)
records=[]
for name in ['A_plan_control.jpg','B_ai_city_original.png','B_ai_city_test.jpg']:
 p=o/name
 with Image.open(p) as im:size=list(im.size)
 records.append({'file':name,'bytes':p.stat().st_size,'size':size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert (o/'B_ai_city_test.jpg').stat().st_size<2*1024*1024
d={'video_id':'T_GBxTRgRSc','video_url':'https://youtu.be/T_GBxTRgRSc','experiment':'thumbnail_only_control_vs_ai_series','status':'assets_ready_browser_connection_required','test_started':False,'title_change_authorized_or_performed':False,'video_reupload_performed':False,'thumbnail_replaced_without_test':False,'A':'A_plan_control.jpg','B':'B_ai_city_test.jpg','B_original':'B_ai_city_original.png','generation':'built-in image_gen; one generation, reference previous newtown-thumbnail-release.jpg; no separate CLI/API call','image_type':'AI concept city, not actual Wangsuk photo or official planned view','layout':'Left: series label and large district name; right: cinematic generic Korean new-town residential stream/park at sunset; bottom: AI concept label','copy':['신도시 분석 시리즈','남양주','왕숙','기다릴 만할까?'],'hypothesis':'Cinematic series thumbnail may communicate place and choice more clearly at mobile size than two dense planning maps; result not measured','test_metric':'YouTube native watch-time-based test outcome; CTR supplementary, no predicted lift','scope':'Keep current title/video/description unchanged, compare original A and generated B concurrently in native Studio test','official_instructions':'https://support.google.com/youtube/answer/16391400?hl=ko','browser_observation':'cua.getState returned browsers=[]; createBrowserTab iab unavailable','artifacts':records}
(o/'experiment.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
