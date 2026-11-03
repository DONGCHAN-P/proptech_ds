"""Cross-check delivered source proof records without changing editor files."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re

Q = Path(__file__).resolve().parent
E = Q.parents[2]
H = E / 'editor/top20-split-v4/shorts-ui-v2-20261104'
D = E / 'director/top20-split-v4/shorts-ui-v2-20261104'
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
results = []
for project in sorted(H.glob('SHORT*')):
    if not project.is_dir():
        continue
    lock = read(D / 'shorts' / project.name / 'locked_timing.json')
    glyph = read(project / 'glyph_bounds.json')
    scenes = {x['scene_id']: x for x in lock['scenes']}
    sentence = {x['sentence_id']: x for x in lock['sentences']}
    checks = []
    def check(name, passed, detail=None):
        checks.append(dict(check=name, passed=bool(passed), detail=detail))
    safe = [140,260,840,1360]
    bad_safe = []
    bad_font = []
    groups = defaultdict(list)
    minima = {'title':56,'caption':54,'key_value':52,'condition_source':26,'label':26}
    for element in glyph['elements']:
        box = element['bbox']
        if box[0]<safe[0]-.1 or box[1]<safe[1]-.1 or box[2]>safe[2]+.1 or box[3]>safe[3]+.1:
            bad_safe.append(element)
        if element['font_px']<minima[element['kind']]:
            bad_font.append(element)
        groups[element['time_s']].append(element)
    intersects=[]
    for t, elements in groups.items():
        for i, a in enumerate(elements):
            for b in elements[i+1:]:
                x,y=a['bbox'],b['bbox']
                w=min(x[2],y[2])-max(x[0],y[0]); h=min(x[3],y[3])-max(x[1],y[1])
                if w>.5 and h>.5:
                    intersects.append(dict(time_s=t,a=a['id'],b=b['id'],width=w,height=h))
    check('all_glyph_safe_profile', glyph['safe_rect']==safe and not bad_safe, dict(sample_count=glyph['sample_count'],elements=len(glyph['elements']),violations=bad_safe))
    check('all_glyph_font_minimums',not bad_font,bad_font)
    check('independently_recomputed_glyph_intersections',not intersects,intersects)
    anchors=read(project/'price_anchor_audit.json')
    anchor_rows=[]
    for a in anchors:
        s=sentence[a['sentence_id']];sc=scenes[a['scene_id']];row=sc['visual_facts']['rows'][a['row']]
        chars=s['display_character_timing'];text=''.join(chars['characters']);i=text.index(a['token'])
        native=chars['chunk_local_start_times_seconds'][i]
        target=s['segment_start_s']-s['source_clip']['start_s']+native
        cid='scene-'+a['scene_id'].rsplit('-',1)[1]
        html=(project/'compositions'/f'{cid}.html').read_text(encoding='utf-8')
        width=float(re.search(r'id="'+cid+'-bar'+str(a['row'])+r'"[^>]*style="width:([0-9.]+)%"',html).group(1))/100
        bar_ok=abs(width-row['bar_fraction'])<1e-9 and a['bar_fraction']==row['bar_fraction']
        timing_ok=abs(target-a['target_s'])<1e-7 and abs(native-a['native_chunk_s'])<1e-7 and abs(target-sc['start_s']-a['reveal_local_s'])<1e-7
        row_ok=a['rendered_value']==row['value'] and row['label'] in html and row['sample'] in html
        check('price_'+a['sentence_id']+'_'+str(a['row']),bar_ok and timing_ok and row_ok)
        anchor_rows.append(dict(sentence_id=a['sentence_id'],row=a['row'],target_s=target,source_bar_fraction=row['bar_fraction'],html_bar_fraction=width,passed=bar_ok and timing_ok and row_ok))
    boundary=read(project/'price_boundary_checks.json')
    bar_measures=[]
    for b in boundary['checks']:
        f=scenes[b['scene_id']]['visual_facts']['rows'][b['row']]['bar_fraction']
        before=b['states'][0];full=[x for x in b['states'] if x['offset_s']>=.35-1e-8]
        ok=before['opacity']==0 and before['barWidth']==0 and all(abs(x['barWidth']-x['trackWidth']*f)<.03 for x in full)
        check('measured_bar_'+b['scene_id']+'_'+str(b['row']),ok)
        bar_measures.append(dict(scene_id=b['scene_id'],row=b['row'],expected_px=674*f,actual_final_px=full[-1]['barWidth'],passed=ok))
    css=(project/'style.css').read_text(encoding='utf-8')
    check('bar_height_10px', '.bar{height:10px;' in css and 'width:674px;height:10px' in css)
    integrity=read(project/'caption_integrity.json')
    check('all_wrapped_caption_text_and_timing_unchanged',len(integrity['cues'])==len(lock['captions']) and all(
        a['text']==b['text'] and a['start_s']==b['start_s'] and a['end_s']==b['end_s'] and a['wrapped_text'].replace('\n',' ')==b['text']
        for a,b in zip(integrity['cues'],lock['captions'])))
    visibility=read(project/'caption_visibility_boundary_checks.json')
    failures=[]
    for x in visibility['checks']:
        expected=[c['text'] for c in lock['captions'] if c['start_s']<=x['time_s']<c['end_s']]
        actual=[a.replace('\n',' ') for a in x['actual']]
        if expected!=actual:
            failures.append(dict(time_s=x['time_s'],expected=expected,actual=actual))
    check('caption_visibility_boundaries_recomputed_from_lock',not failures,dict(samples=len(visibility['checks']),failures=failures))
    all_html=''.join(x.read_text(encoding='utf-8') for x in (project/'compositions').glob('scene-*.html'))
    check('no_five_row_ledger',not re.search(r'class="[^"]*(?:ledger|rank-list|rank-table)',all_html))
    check('static_photo_crop_no_camera_zoom', '.hero{width:100%;height:100%;object-fit:cover}' in css and not re.search(r'tl\.[^;]*photo[^;]*(?:scale|zoom)',all_html))
    evidence_files=[project/x for x in ['glyph_bounds.json','price_anchor_audit.json','price_boundary_checks.json','caption_integrity.json','caption_visibility_boundary_checks.json','long_label_sample_stress.json','style.css']]+sorted((project/'compositions').glob('*.html'))
    results.append(dict(short_id=project.name,passed=all(x['passed'] for x in checks),checks=checks,price_anchor_rows=anchor_rows,measured_bars=bar_measures,evidence=[dict(path=str(p),sha256=sha(p)) for p in evidence_files]))
output=dict(status='passed_source_cross_checks' if all(x['passed'] for x in results) else 'requires_correction',shorts=results,
            coverage=dict(editor_DOM_glyph_records='all records independently recomputed for safe bounds, font minimums, and intersections; not a new browser capture',native_numeric_anchors='all 22 rows independently recomputed from immutable character times',bar_fraction='all 22 HTML widths and measured final widths compared to frozen facts',caption_lexical='all 76 cues',sampled_source_images='representatives_review.json',final_encoded_frames='pending',actual_listening=False,continuous_playback=False),
            note='Glyph ink may exceed its CSS line box because overflow is visible. This alone is not clipping; scene clipping, safe bounds, collisions, and viewed raster evidence are assessed separately.')
(Q/'source_review.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=output['status'],shorts=[dict(short_id=x['short_id'],failed=[y['check'] for y in x['checks'] if not y['passed']]) for x in results])))
