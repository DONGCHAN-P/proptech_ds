"""Publish only the two completed Shorts explicitly requested by the user."""
import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
RELEASE = EP / 'outputs/shorts-release-v2'
OUT = RELEASE / 'public-release-v1'
TARGETS = {
    'funnel': ('vNVQHPWeD-I', '8599bb589247e8b6c62b577bee3a5ce5898026dffce8abf13c5033a18b4b5efd'),
    'analysis': ('p1qtIhWKBoE', '3f70117cab7c454257a1cb539d61c85d6efcba3c5a052c843f2f796c973cdbe3'),
}
CHANNEL = 'UCr_mTC0x_Uobv6MrIsOkrXw'
WRITABLE_STATUS = ('embeddable', 'license', 'publicStatsViewable',
                   'selfDeclaredMadeForKids', 'containsSyntheticMedia')


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rel(p):
    return p.relative_to(ROOT).as_posix()


def validate_local():
    previous = read(RELEASE / 'completion.json')
    assert previous['Codex_approved'] and previous['Claude_Opus_max_approved']
    assert len(previous['items']) == 2
    for row in previous['items']:
        vid, digest = TARGETS[row['id']]
        assert row['video_id'] == vid and row['video_sha256'] == digest
        assert sha(ROOT / row['video']) == digest
        assert sha(ROOT / row['subtitles']) == row['subtitles_sha256']
    return previous


def videos(youtube):
    response = youtube.videos().list(
        part='snippet,status,processingDetails',
        id=','.join(v[0] for v in TARGETS.values()),
    ).execute(num_retries=0)
    assert {x['id'] for x in response['items']} == {v[0] for v in TARGETS.values()}
    return {x['id']: x for x in response['items']}


def validate_online(video, row, public=False):
    assert video['id'] == row['video_id']
    assert video['snippet']['channelId'] == CHANNEL
    assert video['snippet']['title'] == row['title']
    assert video['status']['uploadStatus'] == 'processed'
    assert video['processingDetails']['processingStatus'] == 'succeeded'
    assert not video['status'].get('publishAt')
    assert video['status']['privacyStatus'] in (['public'] if public else ['private', 'public'])


def captions(youtube, video_id):
    response = youtube.captions().list(part='snippet', videoId=video_id).execute(num_retries=0)
    assert any(x['snippet']['language'] == 'ko' and x['snippet']['status'] == 'serving'
               for x in response['items'])
    return response


def publish(previous):
    sys.path.insert(0, str(ROOT / 'analysis'))
    from upload_changneung_scheduled_v8 import service
    youtube = service()
    if not (OUT / 'authorization.json').exists():
        save(OUT / 'authorization.json', {
            'user_request': '공개로 전환해줘', 'scope': 'two_completed_Shorts_only',
            'channel_id': CHANNEL, 'video_ids': [v[0] for v in TARGETS.values()],
            'privacy': 'public', 'new_uploads': 0, 'new_paid_generation': False,
            'source_completion': rel(RELEASE / 'completion.json'),
            'source_completion_sha256': sha(RELEASE / 'completion.json'),
            'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        })
    baseline = videos(youtube)
    caption_before = {}
    for row in previous['items']:
        validate_online(baseline[row['video_id']], row)
        caption_before[row['video_id']] = captions(youtube, row['video_id'])
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    save(OUT / f'preflight_{stamp}.json', {'videos': baseline, 'captions': caption_before})
    for row in previous['items']:
        video_id = row['video_id']
        old = baseline[video_id]
        receipt_path = OUT / (row['id'] + '_receipt.json')
        receipt = read(receipt_path) if receipt_path.exists() else {
            'video_id': video_id, 'video_sha256': row['video_sha256'],
            'before': old, 'authorization': rel(OUT / 'authorization.json'),
        }
        if old['status']['privacyStatus'] != 'public':
            assert not receipt.get('mutation_attempted'), 'Prior mutation requires read-only reconciliation'
            status = {k: old['status'][k] for k in WRITABLE_STATUS if k in old['status']}
            status['privacyStatus'] = 'public'
            body = {'id': video_id, 'status': status}
            receipt.update(mutation_attempted=True, request=body,
                           attempted_at_utc=datetime.now(timezone.utc).isoformat())
            save(receipt_path, receipt)
            receipt['response'] = youtube.videos().update(part='status', body=body).execute(num_retries=0)
            save(receipt_path, receipt)
        final = videos(youtube)[video_id]
        validate_online(final, row, public=True)
        for k in ('title', 'description', 'tags', 'categoryId', 'defaultLanguage', 'defaultAudioLanguage'):
            assert old['snippet'].get(k) == final['snippet'].get(k), k
        for k in WRITABLE_STATUS:
            assert old['status'].get(k) == final['status'].get(k), k
        caption_after = captions(youtube, video_id)
        assert caption_before[video_id]['items'] == caption_after['items'], 'Caption tracks changed'
        receipt.update(public_verified=True, verification=final, captions=caption_after,
                       verified_at_utc=datetime.now(timezone.utc).isoformat())
        save(receipt_path, receipt)
        print(json.dumps({'video_id': video_id, 'privacy': 'public', 'captions': 'serving'}), flush=True)


def finalize(previous):
    result = copy.deepcopy(previous)
    result.update(status='two_Shorts_public_verified_and_caption_serving',
                  private_upload_completion=rel(RELEASE / 'completion.json'),
                  public_authorization=rel(OUT / 'authorization.json'))
    for row in result['items']:
        receipt_path = OUT / (row['id'] + '_receipt.json')
        receipt = read(receipt_path)
        assert receipt['public_verified'] and receipt['video_id'] == row['video_id']
        validate_online(receipt['verification'], row, public=True)
        row.update(privacy='public', public_receipt=rel(receipt_path))
    result['verified_at_utc'] = datetime.now(timezone.utc).isoformat()
    save(OUT / 'completion.json', result)
    lines = ['# 매매·전세·월세 쇼츠 공개 완료', '']
    for row in result['items']:
        label = '유입용' if row['id'] == 'funnel' else '분석 요약용'
        lines.append(f'- {label}: {row["url"]}')
    lines += ['', '두 편 모두 공개 상태·영상 처리 완료·한국어 자막 제공 상태를 YouTube API로 확인했습니다.',
              '제목·설명·자막 및 기존 공개 설정의 나머지 항목은 유지했습니다.',
              '승인 근거: 사용자 요청 “공개로 전환해줘”. 기존 비공개 업로드·검수 기록은 보존했습니다.', '']
    (OUT / 'public_status.md').write_text('\n'.join(lines), encoding='utf-8')
    state_path = EP / 'state.json'
    state = read(state_path)
    short_state = state['shorts_jun_v1']
    short_state.setdefault('private_upload_completion', short_state['completion'])
    short_state.update(status=result['status'], visibility='public', items=result['items'],
                       completion=rel(OUT / 'completion.json'),
                       public_authorization=rel(OUT / 'authorization.json'))
    save(state_path, state)
    shelf_path = ROOT / 'config/video_shelf.json'
    shelf = read(shelf_path)
    entry = next(x for x in shelf['entries'] if x['name'] == '매매전월세')
    entry['status'] = 'Jun 본편 공개 확인·쇼츠2편 공개 전환 완료 / 한국어 자막 확인'
    entry['files']['쇼츠_업로드.md'] = rel(OUT / 'public_status.md')
    entry['files']['쇼츠_검수결과.json'] = rel(OUT / 'completion.json')
    save(shelf_path, shelf)
    queue_path = ROOT / 'config/video_production_queue_20261026.json'
    queue = read(queue_path)
    queue['housing_choice_shorts_v2'] = result
    save(queue_path, queue)
    print(json.dumps({'status': result['status'], 'urls': [x['url'] for x in result['items']]}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['validate', 'publish', 'finalize'])
    args = parser.parse_args()
    previous = validate_local()
    if args.action == 'validate':
        print(json.dumps({'validated': True, 'video_ids': [v[0] for v in TARGETS.values()]}))
        return
    OUT.mkdir(exist_ok=True)
    protected_sha = sha(ROOT / 'config/current_video.json')
    if args.action == 'publish':
        publish(previous)
    else:
        finalize(previous)
    assert sha(ROOT / 'config/current_video.json') == protected_sha


if __name__ == '__main__':
    main()
