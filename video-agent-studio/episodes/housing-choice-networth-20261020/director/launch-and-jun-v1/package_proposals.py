"""Package proposal artifacts; retain all existing delivery and approval records."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
EP = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020'
OUT = EP / 'outputs/launch-proposal-v1'
DIRECTOR = Path(__file__).resolve().parent

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rel(p):
    return p.relative_to(ROOT).as_posix()

script = EP / 'outputs/script-final-v6/script_v6.md'
assert sha(script) == '0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7'
prompts = {
    'TH001_same_money_different_ten_years.png': "Create ONE polished 16:9 Korean YouTube thumbnail proposal for a Korean real estate data explainer channel, premium editorial financial documentary style, a finished full canvas with flawlessly readable Hangul. This film compares buying, jeonse and monthly rent for the same 600 million won apartment over 10 years starting from identical capital, without guaranteeing any winner. Layout: left 58% deep navy almost black gradient for typography, right 42% a highly natural photographic Korean high-rise apartment complex at blue hour, warm lit windows, elegant cinematic light, realistic architecture, no specific identifiable actual location, no people, no dollar bills, no coins flying, no arrows or fabricated charts. Typography on left in heavy clean Korean sans serif, exact text only: small top line '매매 · 전세 · 월세', huge two-line headline '같은 돈' (white) and '다른 10년' (warm bright yellow #FEDC2C). Headline has very strong mobile readability and generous left/top/bottom margin; no text crossing buildings. Small understated footer text on left '2억5천만원으로 시작한 세 가구'. Keep that footer legible and above bottom 15% timestamp area; lower-right stays free of important text. A single understated photographic house key in near foreground on lower right can link the real estate theme; no cheesy 3D house icons. Refined controlled palette navy, offwhite, warm yellow. Match Korean channel cover grammar with large white and yellow text on architectural photographic background. Professional clean composition, subtle natural contrast, no clutter, no logo, no watermark, no technical AI labels. Output the completed thumbnail, not a mockup sheet or device view.",
    'TH002_rent_and_invest.png': "Generate ONE completed professional 16:9 YouTube thumbnail for a Korean real estate data channel. Alternative B focused on the question whether paying monthly rent while investing the difference can leave more wealth after ten years. Photographic, premium, credible Korean financial editorial aesthetic. Left 60% uncluttered dark navy space, right 40% natural close-up of a neat contemporary Korean apartment living room window looking out at realistic apartment towers at dusk, on the windowsill a simple house key and a closed neutral folder, no fake currency, no person, no plotted data, no tablet UI. Strong very large Pretendard-like extra-bold Korean typography. EXACT only text: top smaller '매매 · 전세 · 월세 10년 비교', huge line1 white '월세 내고도', huge line2 yellow #FEDC2C '더 남는다?', one modest line near lower left, comfortably above bottom15%, '집값 2% · 투자 6% 가정'. This is a question thumbnail; do not make categorical winner graphics. Typography occupies left two thirds with 5% margin at all edges; right lower corner reserved for YouTube duration stamp, no text there. High clean white/yellow/navy contrast consistent with Korean apartment data documentary covers. Finished thumbnail, not a device mockup or sheet. Natural photographic architecture, no glossy 3D icons, no arrows, no watermark, no logo, no AI process labels."
}
assets = []
for index, (name, prompt) in enumerate(prompts.items(), start=1):
    p = OUT / name
    with Image.open(p) as im:
        dims, mode = im.size, im.mode
        im.verify()
    assert dims == (1672, 941)
    assets.append({
        'asset_id': f'TH00{index}', 'file': rel(p), 'sha256': sha(p),
        'bytes': p.stat().st_size, 'width': dims[0], 'height': dims[1], 'mode': mode,
        'type': 'generated_thumbnail_proposal', 'provider': 'built-in image_gen',
        'transparent_background': False, 'actual_place': False, 'ai_generated': True,
        'upscaled': False, 'prompt': prompt,
        'review': 'actual generated image inspected: Korean headline and digits match, no clipped letters, generous margins, lower-right free of text',
        'release_status': 'proposal; final upload-size normalization pending selection'
    })
write(OUT / 'assets.json', {
    'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_script_sha256': sha(script), 'assets': assets,
    'api_key_billed_image_generation_calls': 0,
    'generator': 'built-in imagegen; no CLI/API-key fallback',
    'view_scope': 'generated image proposals visually inspected; existing video not changed'
})
budget_path = EP / 'narration/jun-replacement-v1/budget_proposal.json'
budget = read(budget_path)
assert budget['input_characters'] == 8715
assert budget['proposed_cap'] == 10739
assert budget['included_remaining'] == 22558
assert budget['additional_cash_usd_cap'] == 0 and budget['generation_started'] is False
request_path = DIRECTOR / 'request.json'
request = read(request_path)
request.update(scoped_credit_budget_status='awaiting_10739_included_credit_confirmation',
               budget_proposal=rel(budget_path), budget_proposal_sha256=sha(budget_path),
               marketing_proposals=rel(OUT / '쇼츠_제목_썸네일_제안.md'),
               proposal_assets=rel(OUT / 'assets.json'),
               private_target_readonly=rel(DIRECTOR / 'old_private_target_readonly.json'))
write(request_path, request)
state_path = EP / 'state.json'
state = read(state_path)
state['jun_replacement_v1'] = {
    'status': 'proposals_delivered_budget_confirmation_pending',
    'request': rel(request_path), 'budget': rel(budget_path),
    'marketing_proposals': rel(OUT / '쇼츠_제목_썸네일_제안.md'),
    'script_sha256': sha(script), 'visibility': 'private',
    'old_video_id': 'exEGpjcqdF0', 'delete_after_verified_replacement': True,
    'deletion_executed': False, 'new_synthesis_calls': 0,
    'additional_cash_usd_cap': 0, 'proposed_credit_cap': 10739,
    'updated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat()
}
write(state_path, state)
shelf_path = ROOT / 'config/video_shelf.json'
shelf = read(shelf_path)
entry = next(e for e in shelf['entries'] if e['name'] == '매매전월세')
entry['files'].update({
    '유입제안.md': rel(OUT / '쇼츠_제목_썸네일_제안.md'),
    '썸네일_시안A.png': rel(OUT / 'TH001_same_money_different_ten_years.png'),
    '썸네일_시안B.png': rel(OUT / 'TH002_rent_and_invest.png'),
    'Jun_음성예산.json': rel(budget_path)
})
write(shelf_path, shelf)
report = {'status': 'proposal_packaged', 'assets': len(assets),
          'script_sha256': sha(script), 'included_credit_cap_proposed': 10739,
          'new_tts_calls': 0, 'uploads': 0, 'deletions': 0,
          'current_delivery_unchanged': True, 'full_prompt_record': rel(OUT / 'assets.json')}
write(OUT / 'proposal_verification.json', report)
print(json.dumps(report, ensure_ascii=False))
