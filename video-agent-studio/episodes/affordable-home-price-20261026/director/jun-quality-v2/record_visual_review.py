from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import json,hashlib
OWN=Path(__file__).resolve().parent;EP=OWN.parents[1];ROOT=EP.parents[2]
Q=OWN/'encoded_checks';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
d=read(Q/'technical_report.json')
ending=[]
for r in d['frames']:
    if 'ending' not in r['labels']:continue
    with Image.open(ROOT/r['path']) as im:
        band=im.convert('RGB').crop((96,876,1824,1000))
        mae=sum(ImageStat.Stat(ImageChops.difference(band,Image.new('RGB',band.size,(246,244,239)))).mean)/3
    ending.append({'frame_index':r['frame_index'],'time_s':r['time_s'],'ivory_RGB_MAE':mae})
assert all(x['ivory_RGB_MAE']<3 for x in ending if 21054<=x['frame_index']<21144)
(Q/'ending_rail_check.json').write_text(json.dumps({'status':'pass','white_rail_absent_after_final_speech_until_outro':True,'frames':ending},indent=2)+'\n',encoding='utf-8')
selected=[r for r in d['frames'] if any(k.endswith(('_resident','_middle','_end')) or k.endswith('_special') or k=='ending' for k in r['labels'])]
selected=[r for r in selected if not all(k.startswith('CH') for k in r['labels'])]
report={'video_sha256':d['sha256'],'required_open':[],
 'scope':'최종 MP4의 실제 프레임 컨택트시트 관찰. 31개 본문 도입·중간·끝, CTA·영수증 전환·마지막 발화와 아웃트로 경계를 포함한다.',
 'viewed_sheets':[f'encoded_{phase}_{i}.jpg' for phase in ['resident','middle','end'] for i in [1,2,3]]+['encoded_specials.jpg'],
 'scene_samples_viewed':93,'special_sheet_frames':14,'unique_viewed_frame_indices':sorted({r['frame_index'] for r in selected}),
 'all_354_sample_frames_individually_viewed':False,
 'automated_caption_ROI_matches':156,'caption_ROI_note':'자막 중간 시점 실제 인코딩 영역과 기존 승인 레이아웃의 픽셀 비교. 전체 자막의 실제 청취·연속 시청을 뜻하지 않는다.',
 'findings':[],'checked_features':['글자 경계·선/화살촉 정렬','도입 시 설명 대상 유지','계산서→준비금 분할 전환','현재 숫자·비교 결과','구독·좋아요 CTA','S18 이미지 퇴장 후 한도 설명','마지막 발화 뒤 자막 박스 종료'],
 'ending_rail_check':'ending_rail_check.json','actual_listening':False,'continuous_playback':False,
 'chapter_cards_and_brand':'고정된 기존 7개 이미지·승인 브랜드의 소스·레이아웃은 재사용. 새 영상의 배치·디코딩·경계 추출을 확인했고 전체 연속 재생은 하지 않았다.',
 'independent_source_and_shorts':'qa/jun-quality-v2/baseline_findings.json 및 shorts-review/handoff.json',
 'claude_final_approval':False,'new_upload_performed':False}
(Q/'visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'unique_frames_viewed':len(report['unique_viewed_frame_indices']),'scene_samples':93,'specials':14,'required_open':0,'ending':'pass'}))
