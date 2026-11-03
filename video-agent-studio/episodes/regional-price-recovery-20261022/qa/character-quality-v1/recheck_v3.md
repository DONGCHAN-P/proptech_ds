# v3 제한 재검수 — 정지 표본 2장

**판정: SR01–03의 수정은 지정 정지 표본에서 확인된다. 20초 무음 방향 시안의 정지 화면 개선 확인이며, 전체 본편 합격이나 연속 동작 통과가 아니다.**

## 확인한 입력과 버전

episode_root의 `outputs/character-quality-v1/` 아래 다음 입력만 열었다.

- `checks/encoded-v3/01-2s.png`: `view_image`로 00:02 원본 이미지 확인.
- `checks/encoded-v3/12-19.9s.png`: `view_image`로 00:19.9 원본 이미지 확인.
- `checks/verification-v3.json`: v3 식별 정보 읽기. 기록상 영상은 `character_quality_sample_v3.mp4`, 1920×1080·30fps·20초·600프레임·음성 없음이다.

**checked_revision:** `character-quality-v3`

**v3 MP4 SHA256 — verification-v3.json 기재값:**

```text
700f3b5bd1c29bdf171194bc54ae6ce0e3bc507c4a7f69d7b3ef2f66ce41e669
```

이 값으로 대상을 식별했다. MP4 해시를 이번에 재계산하지 않았으며, v2의 메인 최신파일 SHA를 사용하지 않았다. 검증 파일의 전체 디코드 성공 기록도 이번 검사로 재실행하거나 승계한 품질 판정이 아니다.

## SR01–03 결과

공통 scene_id는 `household-scene`, owner는 주 에이전트다. 아래 status는 이 보고서의 정지 표본 범위에만 적용한다.

| issue_id | timecode | severity | evidence와 수정 결과 | status / 남은 확인 |
|---|---|---|---|---|
| SR01 | 00:02 | required | 세 인물이 왼쪽 집 안에 있고 오른쪽 빈 공간에 앞서 보이던 단독 타원 그림자가 없다. 기존 `fixed pending rerender`에서 **2초 표본의 해소 확인**으로 진전했다. | `verified_in_sample` / 0초부터 등장 전까지 전체 구간과 그림자·인물 동시 진입은 unchecked |
| SR02 | 00:02, 00:19.9 | recommended | 대기 중 자녀와 도착한 자녀 모두 다리를 곧게 모은 안정된 서 있는 자세다. 19.9초에는 팔이 몸 옆으로 내려가 있어 기존의 목적 불명확한 양팔 전방 제스처가 사라졌다. 신발과 바닥도 표본상 접촉 관계로 읽힌다. | `verified_in_sample` / 걷기에서 정착으로 넘어가는 전환, 팔 내림의 자연스러움·발 미끄러짐은 unchecked |
| SR03 | 00:19.9 | recommended | 오른쪽 아래 중복 결론 문구가 제거됐다. 두 방과 인구 3명·2가구, 하단 예시 설명이 남아 기존보다 정보 경쟁이 줄었다. 큰 제목은 유지되지만 이번 표본에서 추가 필수 수정으로 판단할 근거는 없다. | `verified_in_sample` / 가구 수 변경 타이밍과 작은 화면 연속 가독성은 unchecked |

## 검수 한계와 전달

**coverage:** 지정 PNG 2/2 실제 열람, v3 검증 JSON 읽기. 연속 재생=`unchecked`, 실제 청취=`unchecked`(무음 시안), 이동 중간·장면 경계·전환 검사=`unchecked`. 두 정지 화면으로 보행 리듬이나 20초 전체 품질을 보장하지 않는다. 기존 CQ 5개 전체를 일괄 통과시키거나 재건축 이주 장면까지 승인하지 않는다.

추가 수정 요구는 이번 두 표본에서 발견하지 않았다. 다음 확인은 필요한 경우 이동·도착 전환의 실제 연속 재생에 한정한다. 기존 보고서와 구현·공통 상태는 보존했고, `qa/character-quality-v1/recheck_v3.md`만 작성했다.
