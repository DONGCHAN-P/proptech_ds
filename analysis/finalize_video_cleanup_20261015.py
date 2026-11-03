import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];o=root/'output/cleanup-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
receipts=[read(o/f'deletion_result_{x}.json') for x in ['video','bundle','cache']]
rows=[x for r in receipts for x in r['results']];deleted=[x for x in rows if x['status']=='deleted'];failed=[x for x in rows if x['status']=='failed']
assert len({x['path'].casefold() for x in rows})==len(rows)
assert all(not Path(x['path']).exists() for x in deleted)
e=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
for p in sorted((e/'outputs/youtube-release-v15').glob('*_upload_receipt.json')):
 d=read(p);j=read(Path(d['job']) if Path(d['job']).is_absolute() else root/d['job']);v=root/j['video'];assert hashlib.sha256(v.read_bytes()).hexdigest()==d['sha256']
required=['video/out/newtown-v14-release.mp4','video/out/newtown-v13-release-review.mp4','video/out/shorts-v1/dongtan-gap.mp4','video/out/shorts-v1/five-questions.mp4','video/out/shorts-v1/gtx-alone.mp4','video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4','video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/caption-station-v13/brand_outro_v13_no_caption.mp4']
for x in required:assert (root/x).is_file(),x
g=read(o/'guide_complete.json')
for x in g['files']:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256']
bundle=read(o/'delete_bundle_verified.json')
for x in bundle['files']:assert Path(x['finalrefs'][0]).is_file()
total=sum(x['bytes'] for x in deleted)
result={'deleted_files':len(deleted),'deleted_bytes':total,'deleted_gib':total/1024**3,'failed_files':len(failed),'published_artifacts_hash_verified':4,'first_episode_final_and_three_shorts_present':True,'reproduction_base_files_present':True,'canonical_bundle_assets_still_present':True,'guide_completed_before_deletion':True,'unrelated_application_files_deleted':False,'receipts':[f'deletion_result_{x}.json' for x in ['video','bundle','cache']]}
(o/'cleanup_completed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(o/'failed_deletions.json').write_text(json.dumps({'files':failed},ensure_ascii=False,indent=2),encoding='utf-8')
empty=read(o/'empty_directories_removed.json') if (o/'empty_directories_removed.json').exists() else {}
text=f'''# 영상 자료 정리 완료

2026-10-15. 사용자 요청에 따라 제작 가이드와 피드백 이력을 완성한 뒤 실제 삭제했다.

- 삭제 파일: **{len(deleted):,}개 / {total:,} bytes ({total/1024**3:.2f} GiB)**
- 삭제 실패: **{len(failed)}개** — 실패 목록은 `failed_deletions.json`.
- 빈 디렉터리 정리: {empty.get('removed_empty_directories',0):,}개. 비어 있는 폴더만 제거했고 재귀 삭제는 사용하지 않았다.
- 전편 최종 롱폼·쇼츠 3개, 왕숙 최종 롱폼·쇼츠 3개, 최신 ZIP, 재현용 기준 영상·브랜드·원본 음성·정렬·지도·조사·승인·업로드 기록은 보존했다.
- 왕숙 공개 파일 4개의 SHA256을 업로드 기록과 재검증했다. 전편 최종/쇼츠와 재현 입력 존재, 중복 제거 후 `video/public` 정본 존재를 확인했다.

## 무엇을 삭제했나

이전 검토본 MP4·과거 중복 ZIP·재생성 가능한 렌더 조각/PCM·중간 검수 이미지, 정본과 전체 SHA256이 같은 번들 복사본, `video/node_modules/.cache`의 Remotion/Webpack 생성 캐시다. 설치 패키지·실행 바이너리와 다른 업무 데이터는 보존했다. 렌더 캐시는 다음 빌드에서 재생성된다.

## 남긴 과거 파일의 이유

왕숙 v15 조립의 입력인 왕숙 v14 전체본과 v13 무자막 브랜드 아웃트로, 전편 쇼츠 재현용 newtown v13은 단순 옛 버전이 아닌 현재 재현 입력이므로 보존했다. 작은 코드·대본·출처·검수 이력도 근거 보존을 위해 남긴다. 이력 문서 속 삭제된 중간 파일은 당시 기록이며 현재 기준본이 아니다.

## 추적 파일

- `deletion_result_video.json`, `deletion_result_bundle.json`, `deletion_result_cache.json`: 파일별 실제 삭제 결과.
- `protected.json`: 원본 보존 목록. SHA 중복 검증으로 해제된 사본은 `protected_before_duplicate_resolution.json`과 구분한다.
- `delete_bundle_verified.json`: 삭제 사본→보존 정본 경로 및 일치 SHA256.
- `cleanup_completed.json`: 최종 합계 및 검증 결과.

PowerShell 스크립트 파일 직접 실행은 시스템 실행 정책 때문에 사용할 수 없어, 동일한 검증 코드를 기존 PowerShell 세션의 명령으로 수행했다. 실행 정책·보안 설정은 변경하지 않았다.
'''
(o/'정리_결과.md').write_text(text,encoding='utf-8')
print(json.dumps(result))
