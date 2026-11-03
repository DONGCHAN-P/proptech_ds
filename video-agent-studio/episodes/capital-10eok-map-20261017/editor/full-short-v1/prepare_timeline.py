from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;E=P.parent.parent;O=E/'outputs/full-short-v1';pktpath=E/'research/annual-map-v2/map_packet_v2.json';pkt=json.loads(pktpath.read_text(encoding='utf8'));receipt=json.loads((O/'render_receipt.json').read_text(encoding='utf8'));stats={s['year']:s for s in pkt['coverage']};frames={x['year']:x for x in receipt['actual_data_frames']};assert set(frames)==set(range(2006,2027));exact=0;reappearance=0;checks=[]
for year in range(2006,2027):
 counts={s:0 for s in ['under','over','no_trade','not_yet_observed']};n=0
 for c in pkt['complexes']:
  r=c['years'][str(year)];counts[r['status']]+=1;n+=r['n']
  if r['n']>0:
   assert r['status']==('under' if r['median_manwon']<=100000 else 'over')
   if r['median_manwon']==100000:exact+=1;assert r['status']=='under'
  else:assert r['status'] in ['no_trade','not_yet_observed']
  if year<c['first_valid_trade_year']:assert r['status']=='not_yet_observed'
 s=stats[year];f=frames[year];assert counts['under']==f['drawn']['under']==s['map_under'];assert counts['no_trade']==f['drawn']['no_trade']==s['map_no_trade'];assert counts['over']==f['over_hidden']==s['map_over'];assert sum(counts.values())==8288;assert counts['under']+counts['over']==s['map_observed'];assert n==s['map_n'];checks.append({'year':year,'counts':counts,'n':n,'passed':True})
for c in pkt['complexes']:
 last=None
 for y in range(2006,2027):
  s=c['years'][str(y)]['status']
  if s in ['under','over']:
   if last=='over' and s=='under':reappearance+=1
   last=s
assert reappearance==528 and exact==174
same=[]
for y in [2006,2025,2026]:
 a=(O/f'year_{y}.png').read_bytes();b=(E/f'outputs/map-preview-v3/year_{y}.png').read_bytes();assert a==b;same.append(y)
segments=[];cursor=0
def add(id,year,n):
 global cursor
 segments.append({'id':id,'year':year,'file':f'year_{year}.png','start_frame':cursor,'end_frame_exclusive':cursor+n,'frames':n,'start_s':cursor/30,'end_s':(cursor+n)/30});cursor+=n
add('opening_hold_2006',2006,90)
for y in range(2006,2026):add('annual_'+str(y),y,45)
add('partial_year_2026',2026,120);add('ending_hold_2026',2026,90);assert cursor==1200
rows=['ffconcat version 1.0']
for seg in segments:rows += ["file '"+(O/seg['file']).resolve().as_posix()+"'",'option framerate 30','duration '+format(seg['frames']/30,'.12f')]
rows += ["file '"+(O/'year_2026.png').resolve().as_posix()+"'",'option framerate 30'];(P/'timeline.ffconcat').write_text('\n'.join(rows)+'\n',encoding='utf8');timeline={'fps':30,'frames':1200,'duration_s':40,'segments':segments,'initial_2006_total_frames':135,'final_2026_total_frames':210,'no_interpolated_prices':True,'no_audio':True,'all_annual_map_pngs':[f'year_{y}.png' for y in range(2006,2027)]};(O/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf8');(O/'source_validation.json').write_text(json.dumps({'all_years_passed':True,'years':checks,'exactly_10eok_shown_complex_years':exact,'reappearance_including_no_trade_gaps':reappearance,'approved_v3_representative_pngs_byte_identical':same,'input_packet_sha256':hashlib.sha256(pktpath.read_bytes()).hexdigest(),'full_video_approved_for_production_only':True,'upload_authorized':False,'publication_authorized':False,'new_api_calls':0,'paid_calls':0},ensure_ascii=False,indent=2),encoding='utf8');print({'years':len(checks),'frames':cursor,'duration':40,'exact10':exact,'reappearance':reappearance,'v3_byte_identical':same})
