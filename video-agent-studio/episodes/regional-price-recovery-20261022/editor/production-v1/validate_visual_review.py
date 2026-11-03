import hashlib,importlib.util,json,re
from html.parser import HTMLParser
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;REPO=EP.parents[2];OUT=EP/'outputs/production-v1-jun';P=OUT/'project';C=OUT/'checks/visual-review'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class HTML(HTMLParser):
    def __init__(self,text):super().__init__();self.elements=[];self.feed(text)
    def handle_starttag(self,t,a):self.elements.append((t,dict(a)))
def main():
    plan=read(P/'visual_review_plan.json');src=(P/'visual-review.html').read_text(encoding='utf-8');doc=HTML(src);root=next(a for _,a in doc.elements if a.get('id')=='root');assert root['data-composition-id']=='visual-review' and abs(float(root['data-duration'])-840.7)<.00001
    mounts=[a for _,a in doc.elements if 'data-composition-src'in a];assert len(mounts)==12
    end=0
    for a in mounts:assert abs(float(a['data-start'])-end)<.00001;end=float(a['data-start'])+float(a['data-duration'])
    assert abs(end-840.7)<.00001 and mounts[-1]['data-composition-id']=='review-S012'
    child=HTML((P/mounts[-1]['data-composition-src']).read_text(encoding='utf-8'));cr=next(a for _,a in child.elements if a.get('id')=='root');last=next(a for _,a in child.elements if a.get('id')=='S012-P6');assert cr['data-composition-id']=='review-S012' and abs(float(last['data-start'])+float(last['data-duration'])-float(cr['data-duration']))<.00001
    captions=read(C/'captions.json')['captions'];ledger=read(C/'caption_display_mapping.json')['paragraphs'];assert len(ledger)==39 and len(captions)==113
    for p in ledger:
        joined=' '.join(c['text'] for c in captions if c['beat_id']==p['beat_id']);assert re.sub(r'\s+',' ',joined)==re.sub(r'\s+',' ',p['display_paragraph'])
    assert captions[-1]['end']==837.7 and all(c['end']-c['start']>=2 for c in captions)
    box=next(a for _,a in doc.elements if 'rpr-caption-box' in a.get('class',''));assert float(box['data-duration'])==837.7
    assert not any(t=='audio' for t,_ in doc.elements) and 'word-break:keep-all'in src
    assert sha(P/'index.html')==plan['protected_original_actual_Jun_entry_sha256']
    spec=importlib.util.spec_from_file_location('rpr',ED/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    try:m.make_timing(read(EP/'outputs/script-review-v3/scenes_v3.json')['scenes'],P/'timing_resolved.json')
    except AssertionError:guard=True
    else:guard=False
    assert guard,'Actual-Jun guard no longer rejects provisional lock'
    assert read(C/'caption_bounds.json')['ok']
    report={'ok':True,'mode':'visual-review','provisional':True,'timing_locked':False,'voice':0,'caption_count':113,'paragraphs':39,'story_seconds':837.7,'caption_end_global':842.7,'outro_start_global':845.7,'body_video_seconds_including_CTA_hold':840.7,'final_expected_seconds':855.7,'actual_Jun_entry_unchanged':True,'actual_Jun_function_rejects_provisional_timing':guard,'all_paragraph_words_preserved_after_recorded_display_normalization':True,'caption_background_ends_before_3s_CTA_hold':True,'source_below_caption_inherited':True,'actual_encoded_full_film_review':'director after body/assembly completes'}
    (C/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');manifest={f.relative_to(REPO).as_posix():sha(f) for f in P.rglob('*') if f.is_file() and '.hyperframes'not in f.parts};(C/'input_freeze.json').write_text(json.dumps({'render_session_id':1596,'owner_shell_pid':24020,'files':manifest},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
