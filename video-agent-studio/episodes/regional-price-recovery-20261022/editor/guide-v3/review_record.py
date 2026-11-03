from pathlib import Path
import json,hashlib
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/guide-v3';D=EP/'director/guide-v3'
a=json.loads((O/'assets.json').read_text('utf-8'))
for c in a['chapters']:
    if c.get('generator')=='built_in_image_gen':c['source_manifest']=str(EP/'visual/guide-v3/generated_assets.json')
(O/'assets.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),'utf-8')
r={'revision':'guide-v3','reviewer':'main_director','video_sha256':hashlib.sha256((O/'regional_guide_v3.mp4').read_bytes()).hexdigest(),
   'contact_sheets_viewed':[str(O/f'checks/contact-{i}.jpg') for i in range(1,15)],'encoded_sample_count':125,
   'contact_sheet_scope':'All 125 extracted samples viewed at reduced contact-sheet resolution; not every caption read at native resolution.',
   'additional_native_resolution_frames':[str(O/f'checks/encoded/frame-{n}.png') for n in ['118','093','077']],
   'native_resolution_scope':'Three longest display captions checked for clipping, wrapping and correspondence.',
   'observations':['Eight different image chapter cards visible.','Five body photos precede topic-specific diagrams.','Household example stays in L002; actual floorplan stays in L003.','Chapter/body entry boundaries sampled before, at and one frame after; no unintended black flash found.','Final caption box disappears for three-second CTA hold then existing outro.','Native-resolution long captions fit white box.'],
   'required_open_issues':0,'actual_listening':False,'continuous_playback':False,
   'metadata_correction':'Four newly generated chapter source_manifest references corrected to actual generated_assets.json. Images, composition and encoded video unchanged.'}
if (O/'checks/before_unit_fix/main_encoded_review.json').exists():
    r={'revision':'guide-v3-unit-fix','reviewer':'main_director','video_sha256':r['video_sha256'],
       'prior_full_sample_review':str(O/'checks/before_unit_fix/main_encoded_review.json'),
       'prior_full_sample_review_scope':'125 reduced-resolution encoded samples and three native long-caption frames before the isolated label correction.',
       'contact_sheets_viewed':[str(O/f'checks/contact-{i}.jpg') for i in [8,9,10]],
       'additional_native_resolution_frames':[str(O/f'checks/encoded/frame-{n}.png') for n in ['073','074']],
       'scope':'Changed L005 chapter, its splice entry/exit and two actual native-resolution calculation frames. Other source composition files and all timing remain unchanged.',
       'observations':['Both net-stock result labels use 채 and match narration.','Chapter entry and exit remain aligned.','Caption and scene duration unchanged.'],
       'required_open_issues':0,'actual_listening':False,'continuous_playback':False}
(D/'main_encoded_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'review_record':str(D/'main_encoded_review.json'),'required_open_issues':0}))
