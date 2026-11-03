import pathlib,json,shutil
EP=pathlib.Path(__file__).resolve().parents[1];ROOT=EP.parents[2];ed=EP/'editor-v2';out=EP/'outputs/v2';out.mkdir(exist_ok=True)
d=json.loads((ROOT/'video/src/data-insight-v2/data.json').read_text(encoding='utf8'));manifest=json.loads((EP/'inputs/manifest.json').read_text(encoding='utf8'))
def tc(t):return f'{int(t)//3600:02}:{int(t)//60%60:02}:{int(t)%60:02},000'
(out/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{tc(s['start'])} --> {tc(s['end'])}\n{s['caption']}" for i,s in enumerate(d['scenes']))+'\n',encoding='utf8')
(out/'captions.json').write_text(json.dumps([{'text':s['caption'],'startMs':s['start']*1000,'endMs':s['end']*1000,'timestampMs':None,'confidence':None} for s in d['scenes']],ensure_ascii=False,indent=2),encoding='utf8')
uses={'A01':[(6,9,'monitor'),(19,24,'phone mobile adaptation; original two alert messages and graph crops')],'A03':[(9,10.5,'laptop')],'A05':[(13,15.3,'monitor; all7 GIF frames compressed23.1s into2.3s with fast-playback label')],'A06':[(24,25.5,'laptop'),(27,30,'monitor')],'A07':[(3,5,'monitor')],'A08':[(25.5,27,'laptop')],'A09':[(10.5,13,'laptop')],'A10':[(16,17.5,'laptop full timeline document'),(17.5,19,'laptop original dashboard crop')],'A12':[(15.3,16,'monitor')],'A13':[(0,3,'monitor'),(5,6,'monitor')]}
refs={'A02':'visual-v2/monitor_keyframe.png','A04':'visual-v2/phone_keyframe.png','A11':'visual-v2/laptop_keyframe.png'}
usage=[]
for a in manifest:
 if a['id'] in uses:usage.append({'asset_id':a['id'],'source_sha256':a['sha256'],'role':'ui_inside_physical_display','uses':[{'start':x,'end':y,'display':z} for x,y,z in uses[a['id']]]})
 else:usage.append({'asset_id':a['id'],'source_sha256':a['sha256'],'role':'office_background_reference_only','reference_output':refs[a['id']],'original_photo_insert_visible':False})
(ed/'asset_usage.json').write_text(json.dumps(usage,ensure_ascii=False,indent=2),encoding='utf8');shutil.copy2(ed/'asset_usage.json',out/'asset_usage.json');shutil.copy2(ROOT/'video/src/data-insight-v2/tracking.json',ed/'tracking.json')
inputs=list((ROOT/'video/src/data-insight-v2').glob('*'))+list((ROOT/'video/public/data-insight-v2').glob('*'))+[ed/'verify_v2.py',ed/'on_screen_text_v2.md',ed/'mobile_text_inventory.md',EP/'script_v2.md',EP/'scenes_v2.json',ROOT/'video/package-lock.json',ROOT/'video/remotion.config.ts']
job={'task_id':'data-insight-v2-final','inputs':[str(x) for x in inputs],'outputs':[str(out/'data_insight_30s_v2.mp4'),str(ed/'technical_verification.json')],'steps':[{'argv':['C:/Program Files/nodejs/node.exe',str(ROOT/'video/node_modules/@remotion/cli/remotion-cli.js'),'render',str(ROOT/'video/src/data-insight-v2/entry.tsx'),'DataInsightV2',str(out/'data_insight_30s_v2.mp4'),'--codec=h264','--crf=18','--concurrency=4','--log=error'],'cwd':str(ROOT/'video')},{'argv':[str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(ed/'verify_v2.py')]}]}
(ed/'render_job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf8');print('V2 final job ready; ten device UI assets + three background references; 900 frames.')
