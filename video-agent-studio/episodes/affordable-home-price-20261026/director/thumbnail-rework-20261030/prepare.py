from pathlib import Path
from PIL import Image
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
VIS=EP/'visual/thumbnail-rework-20261030';OUT=EP/'outputs/thumbnail-rework-20261030';OUT.mkdir(parents=True,exist_ok=True)
(VIS/'assets').mkdir(parents=True,exist_ok=True)
GEN=Path('C:/Users/e2ken/.codex/generated_images/01a15aba-4458-7903-9e2d-977fb782278f/exec-c4837cd9-8d54-48ab-b9d2-3ee1c52afb46.png')
assert GEN.is_file();dest=VIS/'assets/TH001_background_AI.png';shutil.copyfile(GEN,dest)
prior=EP/'outputs/jun-quality-v2/thumbnail/thumbnail.png';shutil.copyfile(prior,OUT/'previous_thumbnail_local.png')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'task':'thumbnail_only','video_id':'0495J7FMmCk','user_request':'기존 방식으로 썸네일 변경; 낮은 클릭 전환율은 사용자 보고',
 'reference':{'thumbnail':'housing-choice-networth-20261020/outputs/jun-release-v1/thumbnail.png','template':'video-agent-studio/assets/thumbnail-series/v1/style.json'},
 'design':{'white_copy':'현금 1억~5억','yellow_copy':'얼마짜리 집?','kicker':'내 집 마련 계산법','subline':'대출 · 세금 · 월 부담까지','font':'Pretendard ExtraBold','yellow':'#FEDC2C','layout':'fullbleed apartment photo style; large white/yellow type; no cards'},
 'background':{'asset_id':'TH001','type':'ai_generated_concept_background','actual_place':None,'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest),'size':Image.open(dest).size,'generator':'built-in image_gen','reference_is_style_only':True,'specific_complex_claim':False,'on_screen_ai_label':False},
 'previous_local_sha256':sha(prior),'new_paid_api_calls':0,'elevenlabs_credits':0,'content_video_changed':False,'youtube_thumbnail_replace_authorized':'current direct user request','thumbnail_generation_calls':1,
 'ctr_baseline':'user-reported decline; no measured CTR requested from API in this task','expected_effect':'hypothesis; no CTR uplift claim'}
(HERE/'asset_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'prepared':True,'asset_size':manifest['background']['size'],'video_id':manifest['video_id']}))
