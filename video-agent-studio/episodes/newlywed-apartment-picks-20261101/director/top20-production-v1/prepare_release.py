"""Freeze exact independently checked artifacts for the three authorized private uploads."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
H=EP/'editor/top20-production-v1'
OUT=EP/'outputs/top20-production-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()

def main():
    rows=[]
    for kind,version in [('main','v5'),('promo','v3'),('analysis','v3')]:
        receipt=H/f'render_receipt_{kind}_{version}.json';r=read(receipt)
        video=Path(r['output']);assert sha(video)==r['output_sha256'] and r['full_decode_passed']
        qa=EP/'qa/top20-production-v1'/f'{kind}_final.json';q=read(qa)
        assert q['video_sha256']==sha(video) and q['critical_open']==0 and q['required_open']==0 and q['whole_decode']=='pass'
        srt=OUT/'subtitles'/(kind+'.srt');assert srt.is_file()
        meta=OUT/'metadata'/(kind+'.json');m=read(meta)
        assert m['privacy']=='private' and len(m['description'].encode('utf-8'))<=5000
        item={'id':kind,'video':rel(video),'sha256':sha(video),'subtitles':rel(srt),'subtitles_sha256':sha(srt),
          'metadata':rel(meta),'metadata_sha256':sha(meta),'qa':rel(qa),'qa_sha256':sha(qa),
          'renderer_receipt':rel(receipt),'duration_s':float(r['probe']['format']['duration']),
          'actual_listening':q.get('actual_listening',False),'continuous_playback':q.get('continuous_playback',False)}
        if kind=='main':
            thumb=OUT/'thumbnail/TH001_신혼부부_수도권TOP20_v2_1280x720.png'
            assert sha(thumb)=='d669526af8537c36aeade8a35f79731fd5158b78dad723bad6d86c416c4a85bd'
            item.update(thumbnail=rel(thumb),thumbnail_sha256=sha(thumb))
        rows.append(item)
    manifest={'status':'exact_local_media_verified_for_private_review_upload','label':'비공개 검토본',
      'created_at':datetime.now(timezone(timedelta(hours=9))).isoformat(),'episode_id':EP.name,
      'privacy':'private','channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','items':rows,
      'authorization':rel(HERE/'authorization.json'),'script':rel(HERE/'script_v4.md'),'script_sha256':sha(HERE/'script_v4.md'),
      'new_paid_generation':False,'cash_cost_krw':0,'voice':'free ko-KR-InJoonNeural',
      'Claude_Opus_Max_review':'not_performed_current_connection_unavailable',
      'actual_listening':False,'continuous_playback':False,'native_shorts_related_video_applied':False,
      'source_and_rights':'Per-photo credits, original metadata, map license and music credit preserved',
      'public_release_authorized':False,'delete_existing_videos':False}
    save(OUT/'release_manifest.json',manifest)
    state=read(EP/'state.json')
    state.update(phase='local_media_verified_for_private_review_upload',render_created=True,
      release_manifest=rel(OUT/'release_manifest.json'),render_revision='main-v5-shorts-v3',
      artifact_quality_scope='independent encoded frame/technical review; actual listening and Claude unavailable',
      video=rows[0]['video'],video_sha256=rows[0]['sha256'],shorts=[r for r in rows if r['id']!='main'])
    save(EP/'state.json',state)
    print(json.dumps({'local_release':'verified','privacy':'private','items':[(x['id'],x['duration_s']) for x in rows],'cash_cost_krw':0},ensure_ascii=False))

if __name__=='__main__':main()
