from pathlib import Path
import json,hashlib,subprocess
E=Path(__file__).resolve().parent;EP=E.parents[1];ROOT=EP.parents[2];O=EP/'outputs/shorts-leader-v1'
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
s=(ROOT/'video-agent-studio/episodes/goyang-changneung-20261015/editor/shorts-leader-v2/verify.py').read_text(encoding='utf8').replace('goyang-changneung-20261015','hanam-gyosan-20261019').replace('shorts-leader-v2','shorts-leader-v1').replace('changneung_leader_short_v2.mp4','gyosan_leader_short_v1.mp4').replace('3기 신도시 창릉의','3기 신도시 하남 교산의').replace('production-v8-jun/audio/M009.wav','production-v5-jun/audio/M008.wav').replace("plan['units']","plan['clips']").replace('round(.15*sr)','round(.12*sr)').replace('[1,7,13,18,24,29,34,39,43]','[1,7,11,17,22,28,33,38,44,49]')
(E/'verify.py').write_text(s,encoding='utf8')
subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(E/'verify.py')],check=True)
d=json.loads((E/'layout_bounds.json').read_text());els=d['elements'];bad=[x for x in els if x['bbox'][0]<140 or x['bbox'][1]<260 or x['bbox'][2]>840.1 or x['bbox'][3]>1360];over=[]
for i,a in enumerate(els):
 for b in els[i+1:]:
  if a['frame']!=b['frame']:continue
  x=a['bbox'];y=b['bbox']
  if min(x[2],y[2])-max(x[0],y[0])>1 and min(x[3],y[3])-max(x[1],y[1])>1:over.append([a,b])
save(E/'layout_validation.json',dict(profile='youtube_portrait_full_frame_v2',critical_bounds_violations=bad,critical_text_overlaps=over,measured_elements=len(els),method='Chrome DOM Range rendered text glyphs; modeled YouTube9:16 native UI, not universal device guarantee'))
r=json.loads((O/'render_receipt.json').read_text());save(E/'handoff.json',dict(status='editor_rendered_pending_independent_qa',output=str(O/'gyosan_leader_short_v1.mp4'),sha256=r['sha256'],duration=r['duration'],script=str(O/'script_excerpt.md'),source_plan=str(E/'clip_plan.json'),technical=str(O/'technical.json'),layout=str(E/'layout_validation.json'),encoded_samples=[str(x) for x in O.glob('encoded-*.png')],paid_api_calls=0,upload_performed=False,actual_listening=False,continuous_playback=False,unresolved=['Independent viewer/layout QA and upload gates by root'],next_owner='root/independent QA'))
(E/'placement_guide.md').write_text('# 교산 대장 후보 쇼츠 v1\n\n- 배포 파일: gyosan_leader_short_v1.mp4 / 1080×1920·30fps·약50.43초\n- 기존 Jun M008 의미 단위10개 PCM 원문 발췌. 120ms 구간 사이 쉼, 마지막 무음 본편 유도3초. 속도 변경 없음.\n- 기존 공식 토지이용계획 필지 지도 재사용. C2/B2 실제 필지 채색, 상세 장면에 전체 지구 위치도. 장면간 정직한 컷, 필지 강조0.8초.\n- 자막54px·핵심수치52px·출처26px, 출처는 자막 아래. 기존 영상 축소 카드 아님.\n- 신규 AI 이미지/음성/유료 생성 없음. 기존 Jun 합성음성 재사용이며 청취 품질의 재심사는 미실시.\n- 재현: prepare.py → optimize.py → raster.cjs → measure.cjs → render_command.json argv → finalize.py. prepare는 entry최적화를 되돌리지 않으므로 수정본 보존.\n- 실제 청취·연속 재생은 실시하지 않음. root 독립QA 후 업로드.\n',encoding='utf8')
print(json.dumps(dict(bounds=len(bad),overlaps=len(over),sha256=r['sha256'])))
