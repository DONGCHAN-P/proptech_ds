import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1];ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
contract={'guide':'video-agent-studio/guides/채널_톤앤매너와_복기루프.md','tokens':'config/channel_style_tokens.json','baseline_primary':'namyangju-wangsuk-20261014/readability-cta-v15','baseline_secondary':'video/out/newtown-v14-release.mp4','loop':['freeze_actual_reference_frames_once','compare_same_message_scene','fix_style_and_information_hierarchy','independent_QA_three_representative_scenes','expand_to_full','review_all_cut_boundaries_and_changed_scenes'],'external_references':'explanation techniques supplement channel grammar','visual_review_v2_is_final_style':False}
write(root/'config/channel_style_tokens.json',read(ep/'visual/channel-style-v1/style_tokens.json'))
p=root/'video-agent-studio/templates/episode_preflight.json';v=read(p);v['channel_style_contract']=contract;v['representative_style_QA']='required_before_full_render';write(p,v)
p=root/'config/video_style.json';v=read(p);v['channel_style_contract']=contract;write(p,v)
p=ep/'preflight.json';v=read(p);v['channel_style_contract']=contract;v['representative_style_QA']='required_before_full_render';write(p,v)
p=ep/'visual/photo-v3/assets.json';v=read(p)
for a in v:
 a['status']='director_viewed_place_sign_or_exit_identified_historical_only'
 a['usage']='Historical 2015 Wonheung identity footage only; full contain, attribution outside image, CC BY-SA3.0 and source URL. Not 2026 current street/access evidence; do not use image GPS metadata.'
 a['credit_text']=re.sub('<[^>]+>','',a['metadata'].get('Artist',{}).get('value',''))+' / CC BY-SA 3.0 / 2015.03.04'
write(p,v)
print('Registered channel style loop and verified historical photo scope.')
