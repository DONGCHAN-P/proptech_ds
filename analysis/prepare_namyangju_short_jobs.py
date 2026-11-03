import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
e=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014';o=e/'outputs/youtube-release-v15'
items=json.loads((e/'outputs/shorts-release-v1/manifest.json').read_text(encoding='utf-8'))
for x in items:
 ident=x['id'];p=Path(x['file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 desc=x['description']+'\n\n전체 지도 분석 본편: https://youtu.be/T_GBxTRgRSc\n전편 광교·동탄: https://youtu.be/a9pYQ9iSCBo\n\n자료·계획 확인 기준 2026.10.15. 계획·목표와 실제 완성은 다릅니다. 출처·모집공고·지도 및 상세 비교 조건은 본편 설명을 확인하세요. 내레이션은 ElevenLabs Jun 합성음성입니다. 지도 © OpenStreetMap contributors https://www.openstreetmap.org/copyright\n\n#남양주왕숙 #왕숙신도시 #Shorts'
 j={'title':x['title'],'description':desc,'tags':['남양주 왕숙','왕숙신도시','3기 신도시','왕숙 분양가','왕숙역','Shorts'],'version':'shorts-release-v1-'+ident,'video':p.relative_to(root).as_posix(),'sha256':x['sha256'],'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','privacy':'public','publication_authorized':True,'notify_subscribers':False,'receipt':(o/f'short_{ident}_upload_receipt.json').relative_to(root).as_posix(),'approval_file':(o/f'short_{ident}_pre_upload.json').relative_to(root).as_posix(),'qa_file':(e/f'qa/shorts-release-v1/{ident}/final_review.json').relative_to(root).as_posix()}
 (o/f'short_{ident}_job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print('Three exact short jobs ready; QA and scoped authorization still required')
