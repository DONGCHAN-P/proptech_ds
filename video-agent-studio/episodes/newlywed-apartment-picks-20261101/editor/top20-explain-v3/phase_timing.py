"""원발화 단어로 특징 종료와 가격 시작을 구분합니다. 추정값은 시안에만 씁니다."""
import math


def price_phase(scene, word_groups, locked=False):
    price_ids = {sid for b in scene.get('screen_beats', [])
                 if b.get('purpose') in ['regional_and_complex_price','regional_price','complex_price','representative_complex_price']
                 for sid in b.get('sentence_ids', [])}
    price_ids.update(t['sentence_id'] for t in scene.get('sentences',[]) if t.get('price_role'))
    order = [t['sentence_id'] for t in scene.get('sentences', [])]
    price_order = [sid for sid in order if sid in price_ids]
    if not price_order:
        raise ValueError(f"{scene['scene_id']}: 가격 발화 sentence_id가 없습니다.")
    first = order.index(price_order[0])
    feature_ids = order[:first]
    if locked:
        required = feature_ids + price_order
        missing = [sid for sid in required if not word_groups.get(sid)]
        if missing:
            raise ValueError('원발화 단어 메타데이터 누락: ' + ','.join(missing))
        for sid in required:
            for w in word_groups[sid]:
                if w.get('scene_id') != scene['scene_id']:
                    raise ValueError('다른 장면의 단어 메타데이터: ' + sid)
                if not all(k in w for k in ['local_start_s', 'local_end_s', 'text']):
                    raise ValueError('scene local 단어 시작/종료/원문 필수: ' + sid)
        end = max(float(w['local_end_s']) for sid in feature_ids for w in word_groups[sid])
        start = min(float(w['local_start_s']) for w in word_groups[price_order[0]])
        if start < end - .001:
            raise ValueError('특징 낭독이 끝나기 전에 가격 발화가 시작됩니다.')
        basis = 'actual_original_word_boundaries_scene_local'
    else:
        times = {t['sentence_id']: t for t in scene['sentence_times']}
        start = float(times[price_order[0]]['start_s'])
        end = max(float(times[sid]['end_s']) for sid in feature_ids)
        basis = 'provisional_sentence_budget_NOT_actual_audio'
    if not all(math.isfinite(v) for v in [start, end]) or not 0 <= end <= start < scene['duration_s']:
        raise ValueError('특징 종료/가격 시작 앵커 범위 오류')
    return {'scene_id': scene['scene_id'], 'feature_last_word_end_s': end,
            'price_first_word_start_s': start, 'switch_s': start,
            'price_sentence_ids': price_order, 'timing_basis': basis,
            'timing_locked': locked, 'transition': '의미 단위 하드 컷; 사진은 switch_s 직전까지 유지'}
