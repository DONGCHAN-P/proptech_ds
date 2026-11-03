"""Freeze accepted narration and a shared Shorts CTA; no synthesis requests."""
from pathlib import Path
import copy,hashlib,json,shutil
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2];N=E/'narration/top20-split-v4/jun-and-shorts-v1'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).resolve().relative_to(R).as_posix()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    N.mkdir(parents=True,exist_ok=True);s=read(E/'state.json');current=E/s['active_video']
    assert sha(current)=='a8d7771668848fe406d76e429db85026f1b300e634d6096b0a780390a9a2a064'
    t=read(E/'director/top20-split-v4/part1-map-clean-v1/locked_timing.json');intro=read(E/'director/top20-split-v4/part1-intro-v3/locked_timing.json')['intro_sentences']
    body=t['body_scenes'];main_rows=intro[:6]+t['criteria_sentences']+intro[6:]+[x for sc in body for x in sc['sentences']]
    assert len(main_rows)==90 and len({x['sentence_id']for x in main_rows})==90
    rows=[{'sentence_id':x['sentence_id'],'text':x['text'],'reading_text':x['reading_text'],'kind':'accepted_main','main_order':i}for i,x in enumerate(main_rows)]
    cta=[{'sentence_id':'SHORTS-CTA-01','text':'나머지 순위도 궁금하시다면 다른 순위 영상을 확인해 주세요.'},
         {'sentence_id':'SHORTS-CTA-02','text':'지역별 자세한 가격과 생활권 비교는 본편에서 이어집니다.'}]
    for x in cta:x.update(reading_text=x['text'],kind='new_user_requested_shorts_link_CTA')
    reader=R/s['active_reader_script'];text=reader.read_text(encoding='utf-8');cursor=0
    for row in rows:
        i=text.find(row['text'],cursor);assert i>=0,row['sentence_id'];cursor=i+len(row['text'])
    groups=[('INTRO-HOOK',rows[:1]),('INTRO-PURPOSE',rows[1:6]),('INTRO-CRITERIA',rows[6:8]),('INTRO-METHOD',rows[8:10])]
    groups +=[(sc['scene_id'],[x for x in rows if x['sentence_id']in {y['sentence_id']for y in sc['sentences']}])for sc in body]
    groups +=[('SHORTS-CTA',cta)]
    chunks=[]
    for label,selected in groups:
        assert selected;payload='\n\n'.join(x['reading_text']for x in selected);p=N/'inputs'/f'{label}.txt';p.parent.mkdir(exist_ok=True);p.write_text(payload,encoding='utf-8')
        chunks.append({'asset_id':label,'sentence_ids':[x['sentence_id']for x in selected],'characters':len(payload),'path':rel(p),'sha256':sha(p)})
    total=sum(x['characters']for x in chunks)
    source={'revision':'jun-and-shorts-v1','main_sentence_count':90,'additional_shared_CTA_sentences':2,'main_reader_script':rel(reader),'main_reader_script_sha256':sha(reader),
            'source_video':rel(current),'source_video_sha256':sha(current),'sentences':rows+cta,'chunks':chunks,
            'input_characters_to_send':total,'first_pass_estimated_credits_at_1x':total,'shorts_count':3,
            'shorts_split':{'promo':1,'content_rank_groups':[[20,19,18,17,16],[15,14,13,12,11]]},
            'shorts_voice_reuse':'Main Jun assets reused; shared CTA generated once for3shorts',
            'generation_authorized':False,'tts_post_calls':0,'cash_cap_krw':0,'top_up_authorized':False,'automatic_retry':False}
    save(N/'narration_manifest.json',source);save(D/'baseline_state.json',s)
    reference=R/'video-agent-studio/episodes/housing-choice-networth-20261020/narration/jun-replacement-v1/account_readonly.mjs'
    (N/'account_readonly.mjs').write_text(reference.read_text(encoding='utf-8').replace("path.resolve(own, '../../../../../')", "path.resolve(own, '../../../../../../')"),encoding='utf-8')
    (N/'reading_text.txt').write_text('\n\n'.join(x['reading_text']for x in rows+cta)+'\n',encoding='utf-8')
    save(D/'request_scope.json',{'accepted_main_video_sha256':sha(current),'completion_accepted_by_user':True,'user_request':'현재 수정본에 ElevenLabs Jun 적용. 홍보용1편과 내용20~16위/15~11위2편,끝에다른순위영상유도.',
        'part':1,'paid_budget_cap_pending':True,'upload_authorized':False,'part2_authorized':False,'shorts_count':3})
    print(json.dumps({'status':'inputs_prepared_no_generation','main_sentences':90,'CTA_sentences':2,'chunks':len(chunks),'billed_characters':total,'shorts':3,'tts_post_calls':0}))
if __name__=='__main__':main()
