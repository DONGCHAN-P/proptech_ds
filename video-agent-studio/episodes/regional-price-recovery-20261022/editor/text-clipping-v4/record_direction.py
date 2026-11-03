from pathlib import Path
import json,datetime
EP=Path(__file__).resolve().parents[2];p=EP/'state.json';s=json.loads(p.read_text('utf-8'))
s['stage']='direction_discussion_requested_common_visual_fixes_pending'
s['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
s['updated_client_date']='2026-10-26'
s['direction_discussion_v4']={'status':'discuss_before_new_script_or_render','request_file':str(EP/'director/direction-discussion-v4/요청정리.md'),'intent':'Use literature-derived insights to investigate causes of regional price differences with our data. Develop questions through dialogue.','hypothesis_agreed':False,'new_script_written':False,'new_render_started':False}
s['common_visual_feedback']={'remove_on_screen_AI_concept_badges':True,'remove_unnecessary_negative_disclaimers':True,'highlight_spoken_quarter_and_peak_reference':True,'text_clipping_report_seconds':44,'reproduced_frame':str(EP/'outputs/text-clipping-v4/checks/before-44s.png'),'current_mp4_replaced':False,'status':'recorded_pending_visual_revision'}
p.write_text(json.dumps(s,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'stage':s['stage'],'current_mp4_replaced':False,'new_script_written':False},ensure_ascii=False))
