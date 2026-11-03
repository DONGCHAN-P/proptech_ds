"""Record the current explicit map-cleanup/photo-transition revision scope."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
D=Path(__file__).resolve().parent; E=D.parents[2]; R=E.parents[2]
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).resolve().relative_to(R).as_posix()
def main():
    if (D/'production_authorization.json').exists():
        print('existing authorization retained');return
    state=read(E/'state.json'); baseline=E/state['active_video']
    assert sha(baseline)=='158a92ca8e8354620b36affeffa7a69dd637edf7c4a1fd48f515e70d38c89997'
    w=E/'writer/top20-split-v4/map-clean-v1';w.mkdir(parents=True,exist_ok=True)
    sentences=[{'sentence_id':'P01-CRITERIA-01','text':'가격은 2026년 5월부터 10월까지 계약된 전용 83~85제곱미터 아파트 실거래를 기준으로 합니다.'},
               {'sentence_id':'P01-CRITERIA-02','text':'11월 3일 확인한 거래에서 취소 건을 빼고, 단지별로 가운데 값인 중위가격을 구했습니다.'}]
    script={'revision':'map-clean-v1','scene_id':'P01-CRITERIA','part':1,'sentences':sentences,
            'basis':'Existing displayed map conditions, moved to an opening explanation at the user’s explicit request.',
            'unchanged_body_sentences':80,'cash_cap_krw':0}
    write(w/'criteria_script.json',script)
    prior_md=R/'영상/신혼부부_지역별아파트/2부작_수정안/1편_20-11위_대본_v3_도입수정안.md'
    reader=prior_md.with_name('1편_20-11위_대본_v4_지도기준과사진전환.md')
    text=prior_md.read_text(encoding='utf-8').replace('대본v3 도입 수정안','대본v4 지도 기준·사진 전환')
    text=text.replace('검토용 초안입니다. 도입을 채널의 집 찾기 취지와 후속 지역·예산별 단지 소개에 맞춰 고쳤습니다. 지역 본문과 결말은 승인된 v2 원문입니다.',
                      '지도 하단의 거래 기준을 도입 설명으로 옮기고, 지역별 진입은 대표 사진으로 전환합니다. 기존 지역 본문과 결말은 유지합니다.')
    marker='지도의 점 하나는 아파트 한 단지이고'
    assert marker in text
    text=text.replace(marker,'\n\n'.join(x['text'] for x in sentences)+'\n\n'+marker)
    reader.write_text(text,encoding='utf-8')
    gate=create(E.name,'script','지도 하단 거래 조건을 도입 설명으로 이동하고 순위 변경 시 지역 대표 사진으로 전환하는 사용자 명시 수정 요청. 기존 지역 본문·결론·무료 InJoon을 유지하는 편집 범위.')
    gate.update(status='approved',approval_basis='direct_user_scoped_revision_instruction',
                exact_generated_wording_user_approval=False,
                user_request='지도 하단의 2026.05~10 계약·OpenStreetMap contributors 문구를 정리하고 초반에 기준 설명. 순위가 바뀔 때 지역 대표 이미지로 전환.',
                artifacts=[{'path':rel(w/'criteria_script.json'),'sha256':sha(w/'criteria_script.json')},{'path':rel(reader),'sha256':sha(reader)}],
                part=1,paid_generation_authorized=False,upload_authorized=False,cash_cap_krw=0)
    write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(D/'script_decision.json',gate)
    auth={'status':'approved','decision_id':gate['id'],'scope':{'part':1,'revision':'map-clean-v1','free_InJoon_criteria_voice_generation':True,
          'cash_cap_krw':0,'paid_generation_authorized':False,'upload_authorized':False,'external_file_export_authorized':False,'part2_production_authorized':False},
          'script':rel(w/'criteria_script.json'),'script_sha256':sha(w/'criteria_script.json'),'reader_script':rel(reader),
          'baseline_video':rel(baseline),'baseline_sha256':sha(baseline),'baseline_timing':rel(E/state['active_timing']),
          'baseline_audio':rel(E/state['active_audio']),'baseline_audio_sha256':state['active_audio_sha256'],
          'approval_basis':gate['approval_basis'],'exact_generated_wording_user_approval':False}
    write(D/'production_authorization.json',auth);write(D/'baseline_state.json',state)
    old=R/'output/video_decisions/decisions'/f"{state['pending_decision_id']}.json"
    if old.exists():
        g=read(old);g.update(status='revision_requested',revision_request=gate['user_request'],superseded_by_revision='map-clean-v1');write(old,g)
    state.update(phase='part1_map_clean_photo_transition_production',pending_decision_id=None,
                 active_production_revision='map-clean-v1',production_authorization=(D/'production_authorization.json').relative_to(E).as_posix(),
                 updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(script='scoped_user_revision:'+gate['id'],budget='free_only_cash_0',completed='not_reached_map_clean_v1',pre_upload='not_reached_part1')
    write(E/'state.json',state)
    plan=['# 1편 지도 하단 정리와 순위 전환', '',
          '사용자 명시 요청: 지도 하단 반복 기준을 도입으로 이동, 지역 순위 진입마다 대표 사진으로 전환.', '',
          '1. 기존 기준을 풀어 쓴 2문장만 무료 InJoon으로 만들고 실제 단어 경계로 새 삽입 길이를 고정한다.',
          '2. 기존 도입 39.7초의 발화 사이에 기준 화면을 삽입한다. 나머지 내레이션은 재사용한다.',
          '3. 지역마다 순위를 읽는 첫 문장에 새로운 대표 사진·큰 순위·지역명을 배치하고 지도로 넘긴다. 기존 사진과 다른 실제 장소 사진을 우선한다.',
          '4. 지도 반복 하단 문구만 정리한다. 가격 범례·지도·학교/역/상권·자막·단지 표시는 보존한다. 출처는 상단 작은 표기와 상세 출처 문서에 정리한다.',
          '5. HyperFrames에서 기준 화면과 사진 전환을 렌더링하고 기존 본편에 합성한다. 전체 재제작 대신 영향받은 시각 요소만 교체한다.',
          '6. 모든 순위 전환 전후·지도 하단·새 기준 문장·긴 자막·최종 프레임과 전체 디코드 검수 후 새 로컬 completed 결정을 만든다.', '',
          '허용: 1편 편집·추가 기준 문장·무료 음성, 현금0원. 업로드·2편·유료 생성·외부 검수 전송은 별도 상태를 유지한다.', '',
          '이전 완성 gate는 수정 요청으로 전환하며 이전 파일·원천 자료·승인/검수 기록을 보존한다.']
    (D/'제작계획.md').write_text('\n'.join(plan)+'\n',encoding='utf-8')
    print(json.dumps({'status':'scoped_revision_recorded','script_decision_id':gate['id'],'new_sentences':2,'cash_cap_krw':0},ensure_ascii=False))
if __name__=='__main__':main()
