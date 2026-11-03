"""Native portrait Shorts from the director's actual Jun timing locks.

Only this shorts folder and its matching output folder are writable. No TTS,
API, main picture, shared state, or source media is changed.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
EP = HERE.parents[3]
ROOT = EP.parents[2]
OUT = EP / 'outputs/top20-split-v4/jun-and-shorts-v1/shorts'
D = EP / 'director/top20-split-v4/part1-jun-and-shorts-v1'
WRITER = EP / 'writer/top20-split-v4/jun-and-shorts-v1'
FACTS = D / 'shorts_visual_facts.json'
PROFILE = ROOT / 'config/vertical_video_safe_area.json'
BASE = EP / 'editor/top20-split-v4/part1-production-v1/final-v3'
FF = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
IDS = ['SHORT01-PROMO', 'SHORT02-R20-R16', 'SHORT03-R15-R11']
FILENAMES = dict(zip(IDS, ['short01_promo_Jun_native_v4.mp4', 'short02_ranks20_16_Jun_native_v4.mp4', 'short03_ranks15_11_Jun_native_v4.mp4']))
PLANFILES = dict(zip(IDS, ['short01_promo.json', 'short02_ranks20_16.json', 'short03_ranks15_11.json']))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def owned(path):
    p = Path(path).resolve()
    if not any(p.is_relative_to(x.resolve()) for x in (HERE, OUT)):
        raise ValueError(f'Write outside Shorts ownership: {p}')
    return p


def write(path, text):
    p = owned(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def save(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def cp(source, dest):
    dest = owned(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)


def env():
    return {**os.environ, 'HYPERFRAMES_TELEMETRY_DISABLED': '1', 'DO_NOT_TRACK': '1',
            'HYPERFRAMES_HOME': str(HERE / '.hf'), 'HF_HOME': str(HERE / '.hf'),
            'HYPERFRAMES_EXTRACT_CACHE_DIR': str(HERE / '.cache/extract'),
            'XDG_CACHE_HOME': str(HERE / '.cache'), 'XDG_STATE_HOME': str(HERE / '.state'),
            'HYPERFRAMES_RUN_ID': '3-native-vertical-shorts-Jun-v1',
            'PRODUCER_MAX_WORKERS': '1'}


def esc(text):
    return html.escape(str(text), quote=True)


def text_el(cid, key, text, cls, kind='label', style=''):
    return f'<div id="{cid}-{key}" class="{cls}" data-critical="{kind}" style="{style}">{esc(text)}</div>'


def price_anchor(sentence, token):
    """Use explicit native display-to-reading character mapping, no proportional timing."""
    text = sentence.get('display_text', sentence['text'])
    pos = text.find(token)
    if pos < 0:
        raise ValueError(f"No literal value {token!r} in {sentence['sentence_id']}")
    timing = sentence['display_character_timing']
    if ''.join(timing['characters']) != text:
        raise ValueError('Native display character map differs from displayed sentence')
    local = timing['chunk_local_start_times_seconds'][pos]
    at = sentence['start_s'] - sentence['chunk_local_start_s'] + local
    return at, {'sentence_id': sentence['sentence_id'], 'token': token, 'display_char_start': pos,
                'display_char_end': pos + len(token), 'native_chunk_s': local, 'target_s': at,
                'basis': 'locked explicit display_character_timing; no old/free timing or interpolation'}


CSS = r"""
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.woff2');font-weight:400}
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.woff2');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#142e42}
body{font-family:Pretendard,sans-serif;color:#f6f4ef}#short{position:relative;width:100%;height:100%;overflow:hidden}
.scene-host{position:absolute;inset:0}.photo-clip{position:absolute;inset:0;overflow:hidden}
.hero{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 45%}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,46,66,.18) 0%,rgba(20,46,66,.82) 13%,rgba(20,46,66,.91) 40%,rgba(20,46,66,.88) 70%,rgba(20,46,66,.30) 88%,rgba(20,46,66,.04) 100%)}
.scope{position:absolute;left:152px;top:270px;width:676px;height:68px;font-size:56px;font-weight:700;line-height:1.18;letter-spacing:-1.6px;white-space:nowrap}
.province{position:absolute;left:154px;top:344px;width:674px;height:38px;font-size:30px;line-height:1.2;color:#e6b868}
.region{position:absolute;left:150px;top:383px;width:682px;height:77px;font-size:64px;font-weight:700;line-height:1.15;letter-spacing:-1.8px;white-space:nowrap}
.couples{position:absolute;left:154px;top:460px;width:674px;height:62px;font-size:52px;font-weight:700;line-height:1.15;font-variant-numeric:tabular-nums}
.ledger{position:absolute;left:140px;top:531px;width:700px;height:205px}
.ledger-row{height:41px;position:relative;color:#f6f4ef;border-bottom:1px solid rgba(246,244,239,.2);font-size:30px;line-height:40px}
.ledger-row.active{background:#f6f4ef;color:#142e42;font-weight:700;border-radius:5px}
.ledger-rank{position:absolute;left:14px;width:66px}.ledger-name{position:absolute;left:100px;width:280px}.ledger-count{position:absolute;right:16px;width:190px;text-align:right;font-variant-numeric:tabular-nums}
.price-note{position:absolute;left:154px;top:741px;width:674px;height:33px;font-size:26px;line-height:1.2;color:#f6f4ef}
.chart-title{position:absolute;left:154px;top:777px;width:674px;height:36px;font-size:30px;line-height:1.14;font-weight:700;color:#e6b868}
.price-band{position:absolute;left:0;width:1080px;height:125px;background:#f6f4ef;color:#142e42;box-shadow:0 2px 12px rgba(0,0,0,.12)}
.price-band.row-0{top:818px}.price-band.row-1{top:956px}
.price-label{position:absolute;left:154px;top:10px;width:320px;height:37px;font-size:30px;line-height:1.16;font-weight:700;white-space:nowrap}
.price-value{position:absolute;left:154px;top:48px;width:670px;height:66px;font-size:56px;font-weight:700;line-height:1.12;letter-spacing:-1px;font-variant-numeric:tabular-nums}
.sample{position:absolute;right:252px;top:14px;max-width:330px;height:32px;font-size:26px;line-height:1.14;text-align:right;white-space:nowrap}
.bar-track{position:absolute;left:154px;bottom:0;width:674px;height:7px;background:#dedfd9}.bar{height:100%;background:#286cda;transform-origin:left center}.row-1 .bar{background:#ad762e}
.credit{position:absolute;left:152px;top:1260px;width:680px;height:98px;color:#f6f4ef;font-size:26px;line-height:30px}
.credit-line{height:30px;white-space:nowrap;letter-spacing:-.2px}
.caption-group{position:absolute;inset:0}
.caption-rail{position:absolute;left:112px;top:1100px;width:776px;height:150px;background:#f6f4ef;border-radius:12px}
.caption{position:absolute;left:152px;top:1108px;width:676px;height:134px;color:#142e42;font-size:54px;line-height:1.14;font-weight:400;display:flex;align-items:center;justify-content:center;text-align:center;white-space:pre-wrap;word-break:keep-all;letter-spacing:-1px}
.promo-title{position:absolute;left:152px;top:355px;width:676px;font-size:64px;line-height:1.2;font-weight:700;letter-spacing:-1.5px;white-space:pre-wrap}
.promo-hero-word{position:absolute;left:152px;top:570px;width:676px;font-size:88px;line-height:1.18;font-weight:700;letter-spacing:-3px;white-space:pre-wrap}
.promo-sub{position:absolute;left:154px;top:837px;width:674px;font-size:44px;line-height:1.3;white-space:pre-wrap}
.promo-number{position:absolute;left:145px;top:480px;width:690px;font-size:190px;line-height:1.1;font-weight:700;letter-spacing:-8px;color:#e6b868;white-space:nowrap}
.promo-units{position:absolute;left:154px;top:712px;width:674px;font-size:56px;line-height:1.2;font-weight:700}
.promo-detail{position:absolute;left:154px;top:880px;width:674px;font-size:32px;line-height:1.4;white-space:pre-wrap}
.takeaway{position:absolute;left:154px;top:554px;width:674px;font-size:56px;line-height:1.28;font-weight:700;white-space:pre-wrap}
.cta-primary{position:absolute;left:154px;top:814px;width:674px;font-size:56px;font-weight:700;line-height:1.22;white-space:pre-wrap;color:#e6b868}
.cta-secondary{position:absolute;left:154px;top:984px;width:674px;font-size:40px;line-height:1.25;white-space:pre-wrap}
.hook-ruler{position:absolute;left:0;top:790px;width:1080px;height:8px;background:#e6b868;transform-origin:left center}
"""


def ledger(cid, regions, active=None):
    h = [f'<div id="{cid}-ledger" class="ledger">']
    for i, r in enumerate(regions):
        h.append(f'<div class="ledger-row {"active" if r["region_id"] == active else ""}">')
        h.append(text_el(cid, f'l{i}-rank', f'{r["rank"]}위', 'ledger-rank'))
        h.append(text_el(cid, f'l{i}-name', r['region'].split()[-1], 'ledger-name'))
        h.append(text_el(cid, f'l{i}-count', f'{r["couples"]:,}쌍', 'ledger-count'))
        h.append('</div>')
    h.append('</div>')
    return ''.join(h)


def photo_credit(photo):
    years = re.findall(r'(?:19|20)\d{2}', photo['photo_date'])
    year = years[0] if years else photo['photo_date'][:10]
    return f'사진: {photo["author"].strip()} · {photo["license_name"]} · {year}'


def credit(cid, photo):
    lines = ['국가데이터처 2024.11.01 거주 · 국토부 83~85㎡',
             '2026.05~10 계약 · 11.03 조회 · 취소 제외', photo_credit(photo)]
    return '<div class="credit">' + ''.join(text_el(cid, f'credit{i}', t, 'credit-line', 'condition_source') for i, t in enumerate(lines)) + '</div>'


def backdrop(cid, rid, facts):
    focal = {'R20': '23% 50%', 'R19': '50% 50%', 'R18': '57% 45%', 'R17': '55% 50%', 'R16': '53% 50%',
             'R15': '46% 45%', 'R14': '50% 50%', 'R13': '50% 46%', 'R12': '50% 50%', 'R11': '50% 50%'}[rid]
    return f'<div class="photo-clip"><img id="{cid}-hero" class="hero" src="assets/{rid}.jpg" alt="" style="object-position:{focal}" data-layout-allow-overflow></div><div class="shade" data-layout-ignore></div>'


def wrap_caption(text, font):
    """Whitespace-only line wrapping. Every lexical character remains unchanged."""
    words = text.split(' ')
    if font.getlength(text) <= 660:
        return text
    choices = []
    for i in range(1, len(words)):
        left, right = ' '.join(words[:i]), ' '.join(words[i:])
        a, b = font.getlength(left), font.getlength(right)
        if max(a, b) <= 660:
            choices.append((abs(a - b), left + '\n' + right))
    if not choices:
        raise ValueError(f'Caption needs more space without lowering font: {text}')
    return min(choices)[1]


def scene_file(cid, body, commands, duration):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template><style>#{cid}{{position:absolute;inset:0;width:100%;height:100%;overflow:hidden}}</style><div id="{cid}" data-composition-id="{cid}" data-duration="{duration:.9f}" data-width="1080" data-height="1920">{body}</div><script>(()=>{{const tl=gsap.timeline({{paused:true}});{commands}window.__timelines["{cid}"]=tl;}})();</script></template></body></html>'


def build(short_id, version):
    lockfile = D / 'shorts' / short_id / 'locked_timing.json'
    lock = read(lockfile)
    planfile = WRITER / PLANFILES[short_id]
    plan = read(planfile)
    facts = {x['region_id']: x for x in read(FACTS)}
    if lock['status'] != 'actual_Jun_reuse_locked' or lock['vertical_profile'] != 'youtube_portrait_full_frame_v2':
        raise ValueError('Actual native lock / profile required')
    for path, expected in [(planfile, lock['source_plan_sha256']), (FACTS, lock['source_visual_facts_sha256']), (lock['master_audio'], lock['master_audio_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Input hash mismatch: {path}')
    normalize = lambda x: re.sub(r'[^a-zA-Z0-9가-힣]', '', x)
    if [normalize(s['text']) for s in lock['sentences']] != [normalize(s['exacttext']) for s in plan['sequence']]:
        raise ValueError('Locked speech differs from approved writer plan')
    project = HERE / version / short_id
    if (project / 'render_receipt.json').exists():
        raise ValueError('Preserve rendered version; choose a new --version')
    project.mkdir(parents=True, exist_ok=True)
    for name in ['gsap.min.js', 'Pretendard-Regular.woff2', 'Pretendard-Bold.woff2']:
        cp(BASE / 'assets' / name, project / 'assets' / name)
    ttf = ROOT / 'video-agent-studio/episodes/capital-10eok-map-20261017/visual/map-preview-v1/Pretendard-Regular.ttf'
    cp(ttf, project / 'assets/Pretendard-Regular.ttf')
    cp(BASE / 'references/animated-bar-chart.html', project / 'references/animated-bar-chart.html')
    used_regions = [r['region_id'] for r in plan['regions']]
    if short_id == IDS[0]:
        used_regions = ['R12', 'R14', 'R15', 'R17']
    for rid in used_regions:
        ph = facts[rid]['photo']
        if sha(ph['file']) != ph['sha256'] or sha(facts[rid]['source_file']) != facts[rid]['source_sha256']:
            raise ValueError(f'Frozen photo/fact source changed: {rid}')
        cp(ph['file'], project / 'assets' / f'{rid}.jpg')
    cp(lock['master_audio'], project / 'assets/master_audio.wav')
    cp(lockfile.parent / 'captions.srt', project / 'captions.srt')
    write(project / 'style.css', CSS)
    hosts, anchors, scenes = [], [], []
    regions = plan['regions']
    scope = '20~11위 · 본편 미리보기' if short_id == IDS[0] else f'{plan["rankrange"]["from"]}~{plan["rankrange"]["to"]}위 · 거주 순위'
    for index, sc in enumerate(lock['scenes']):
        cid = f'scene-{index:02d}'
        start, end = sc['start_s'], sc['end_s']
        dur = end - start
        rid = sc.get('region_id')
        if not rid:
            rid = (['R12', 'R14', 'R15'][min(index, 2)] if sc['kind'] == 'hook' else used_regions[-1])
        photo = facts[rid]['photo']
        body = backdrop(cid, rid, facts)
        commands = f'tl.fromTo("#{cid}-hero",{{scale:1.01}},{{scale:1.045,duration:{dur:.9f},ease:"none"}},0);'
        if sc['kind'] == 'region':
            rr = next(r for r in regions if r['region_id'] == rid)
            f = facts[rid]
            body += text_el(cid, 'scope', scope, 'scope', 'title')
            body += text_el(cid, 'province', rr['province'] + (' ' + ' '.join(rr['region'].split()[:-1]) if len(rr['region'].split()) > 1 else ''), 'province')
            body += text_el(cid, 'region', f'{rr["rank"]}위 {rr["region"].split()[-1]}', 'region', 'title')
            body += text_el(cid, 'couples', f'신혼부부 {rr["couples"]:,}쌍', 'couples', 'key_value')
            if short_id == IDS[0]:
                body += text_el(cid, 'takeaway', '같은 구 안에서도\n생활권에 따라 다른 예산', 'takeaway')
            else:
                body += ledger(cid, regions, rid)
            body += text_el(cid, 'note', '10월은 조회일까지 신고분', 'price-note', 'condition_source')
            body += text_el(cid, 'charttitle', f['title'], 'chart-title')
            sentence = next(s for s in sc['sentences'] if s['sentence_id'] == rr['price_sentence_id'])
            for rowindex, row in enumerate(f['rows']):
                token = ['61곳', '16곳'][rowindex] if rid == 'R16' else row['value']
                at, audit = price_anchor(sentence, token)
                local = at - start
                audit.update(scene_id=sc['scene_id'], row=rowindex, rendered_value=row['value'], reveal_local_s=local)
                anchors.append(audit)
                body += f'<div class="price-band row-{rowindex}">'
                body += text_el(cid, f'label{rowindex}', row['label'], 'price-label')
                body += text_el(cid, f'value{rowindex}', row['value'], 'price-value', 'key_value', 'opacity:0')
                body += text_el(cid, f'sample{rowindex}', row['sample'], 'sample', 'condition_source', 'opacity:0')
                body += f'<div class="bar-track"><div id="{cid}-bar{rowindex}" class="bar" style="width:{row["bar_fraction"]*100:.9f}%;opacity:0"></div></div></div>'
                commands += f'tl.set(["#{cid}-value{rowindex}","#{cid}-sample{rowindex}","#{cid}-bar{rowindex}"],{{opacity:1}},{local:.9f});'
                commands += f'tl.fromTo("#{cid}-bar{rowindex}",{{scaleX:0}},{{scaleX:1,duration:0.42,ease:"power2.out"}},{local:.9f});'
        elif sc['kind'] == 'hook':
            body += text_el(cid, 'scope', '20~11위 · 본편 미리보기', 'scope', 'title')
            if index == 0:
                body += text_el(cid, 'title', '우리 예산으로\n집을 산다면', 'promo-title', 'title')
                body += text_el(cid, 'question', '어느 동네부터?', 'promo-hero-word', 'title')
                body += text_el(cid, 'sub', '신혼부부가 많이 사는 지역,\n그 안의 아파트 가격까지', 'promo-sub')
            elif index == 1:
                body += text_el(cid, 'title', '지역 선택의 출발점', 'promo-title', 'title')
                body += text_el(cid, 'number', '53', 'promo-number', 'key_value')
                body += text_el(cid, 'units', '수도권 53개 구', 'promo-units', 'title')
                body += text_el(cid, 'detail', '신혼부부 거주 수 순위\n2024년 11월 1일 기준', 'promo-detail')
            else:
                body += text_el(cid, 'title', '이번 본편에서 볼 순위', 'promo-title', 'title')
                body += text_el(cid, 'number', '20~11', 'promo-number', 'key_value', 'font-size:160px')
                body += text_el(cid, 'units', '20위부터 11위까지', 'promo-units', 'title')
                body += text_el(cid, 'detail', '지역별 아파트 가격과\n생활권을 함께 비교합니다', 'promo-detail')
            body += f'<div id="{cid}-ruler" class="hook-ruler" data-layout-ignore></div>'
            commands += f'tl.fromTo("#{cid}-ruler",{{scaleX:0}},{{scaleX:1,duration:.65,ease:"power2.out"}},.12);'
            body += text_el(cid, 'note', '10월 계약은 조회일까지 신고분', 'price-note', 'condition_source', 'top:1036px')
        else:
            other = {'SHORT01-PROMO': '다른 순위 영상도 확인', 'SHORT02-R20-R16': '15~11위 영상도 확인', 'SHORT03-R15-R11': '20~16위 영상도 확인'}[short_id]
            body += text_el(cid, 'scope', '다른 순위도 궁금하다면', 'scope', 'title')
            body += text_el(cid, 'next', other, 'region', 'title', 'font-size:56px')
            body += text_el(cid, 'main', '20~11위 전체는 본편', 'couples', 'key_value')
            if short_id != IDS[0]:
                body += ledger(cid, regions)
            else:
                body += text_el(cid, 'takeaway', '20~16위 · 15~11위\n다른 순위 영상도 확인', 'takeaway')
            body += text_el(cid, 'primary', '자세한 가격과\n생활권 비교는 본편', 'cta-primary', 'title')
            body += text_el(cid, 'secondary', '같은 예산, 다른 생활권', 'cta-secondary')
        body += credit(cid, photo)
        write(project / 'compositions' / f'{cid}.html', scene_file(cid, body, commands, dur))
        hosts.append(f'<div id="host-{cid}" class="clip scene-host" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{start:.9f}" data-duration="{dur:.9f}" data-track-index="0" data-track-kind="graphics" data-width="1080" data-height="1920"></div>')
        scenes.append({'scene_id':sc['scene_id'], 'composition_id':cid, 'kind':sc['kind'], 'start_s':start,'end_s':end,'region_id':sc.get('region_id'),'photo_region_id':rid})
    from PIL import ImageFont
    font = ImageFont.truetype(str(project / 'assets/Pretendard-Regular.ttf'), 54)
    capbody = ''
    cueaudit = []
    for i, cue in enumerate(lock['captions']):
        wrapped = wrap_caption(cue['text'], font)
        assert re.sub(r'\s', '', wrapped) == re.sub(r'\s', '', cue['text'])
        capbody += f'<div id="cap-{i:03d}" class="clip caption-group" data-start="{cue["start_s"]:.9f}" data-duration="{cue["end_s"]-cue["start_s"]:.9f}" data-track-index="0"><div class="caption-rail" data-layout-ignore></div><div id="cap-{i:03d}-text" class="caption" data-critical="caption">{esc(wrapped)}</div></div>'
        cueaudit.append({**cue, 'wrapped_text':wrapped, 'lexical_change':False})
    write(project / 'compositions/captions.html', scene_file('captions', capbody, '', lock['total_s']))
    hosts.append(f'<div id="captions-host" class="clip scene-host" style="z-index:10" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{lock["total_s"]:.9f}" data-width="1080" data-height="1920" data-track-index="1" data-track-kind="captions"></div>')
    hosts.append(f'<audio id="master-audio" src="assets/master_audio.wav" data-start="0" data-duration="{lock["total_s"]:.9f}" data-track-index="2" data-volume="1"></audio>')
    document = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><link rel="stylesheet" href="style.css"></head><body>'
    document += f'<div id="short" data-composition-id="short" data-duration="{lock["total_s"]:.9f}" data-width="1080" data-height="1920" data-fps="30">' + ''.join(hosts) + '</div><script>window.__timelines["short"]=gsap.timeline({paused:true});</script></body></html>'
    write(project / 'index.html', document)
    save(project / 'hyperframes.json', {'name':short_id.lower(), 'width':1080,'height':1920,'fps':30,'skill':'general-video'})
    save(project / 'price_anchor_audit.json', anchors)
    save(project / 'caption_integrity.json', {'source_lock_sha256':sha(lockfile), 'source_srt_sha256':sha(lockfile.parent/'captions.srt'), 'cues':cueaudit, 'lexical_change':False,'timing_changed':False,'font_px':54})
    credits = {'photos':[facts[r]['photo'] for r in used_regions], 'photo_edits':'native portrait crop; subtle still-image background scale only; not generated moving footage', 'music':lock['music_credit'], 'data':'국가데이터처 2024.11.01 거주 수; 국토교통부 전용83~85㎡ 아파트 2026.05~10 실거래; 2026.11.03 조회·취소 제외; 10월 조회일까지 신고분', 'price_facts':[facts[r] for r in [x['region_id']for x in regions]], 'not_current_listing_availability':True}
    save(project / 'credits_manifest.json', credits)
    save(project / 'storyboard.json', {'short_id':short_id,'native_portrait':True,'safe_profile':lock['vertical_profile'], 'scenes':scenes,'single_caption_track':True,'price_anchor_count':len(anchors),'main_video_used':False,'actual_listening':False,'continuous_playback':False})
    inputs = [lockfile,planfile,FACTS,PROFILE,Path(__file__),BASE/'references/animated-bar-chart.html']
    inputs += [Path(facts[r]['photo']['file']) for r in used_regions]
    inputs += [Path(facts[r]['source_file']) for r in used_regions]
    inputs += [Path(lock['master_audio']),lockfile.parent/'captions.srt',ttf]
    inputs += [BASE/'assets'/n for n in ['gsap.min.js','Pretendard-Regular.woff2','Pretendard-Bold.woff2']]
    render_files = [project/n for n in ['index.html','style.css','hyperframes.json','captions.srt','credits_manifest.json','storyboard.json','price_anchor_audit.json','caption_integrity.json']]
    render_files += [p for folder in ['assets','compositions','references']for p in (project/folder).rglob('*')if p.is_file()]
    manifest = {'short_id':short_id,'version':version,'lock_sha256':sha(lockfile),'master_audio_sha256':lock['master_audio_sha256'],'source_plan_sha256':sha(planfile), 'safe_profile':'youtube_portrait_full_frame_v2','safe_rect':[140,260,840,1360],'canvas':[1080,1920,30],'total_s':lock['total_s'],'total_frames':lock['total_frames'],'inputs':[{'path':str(p),'sha256':sha(p)}for p in inputs], 'project_files':[{'path':str(p.relative_to(project)),'sha256':sha(p)}for p in sorted(render_files)]}
    save(project / 'input_manifest.json', manifest)
    write(project / 'BRIEF.md', f'# {short_id}\n\n승인된 작업 packet 3-native-vertical-shorts-Jun-v1. 실제 Jun lock {sha(lockfile)} 기준.\n1080×1920 원생 세로 화면, 30fps, {lock["total_s"]:.6f}초. 새 유료 생성·외부 API·업로드 없음.\n다섯 지역 목록과 활성 지역 강조, 원문 의미 자막, 가격은 native character anchor에서 정확한 값으로 공개.\n상시 흰 자막 레이어와 별도 출처. 현재 매물/매수 가능성으로 해석하지 않음.\n최종 여운은 총괄 lock의 1.05초를 그대로 보존. 전면 브랜드 범퍼 없음.\n')
    return project


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--version', default='native-v4')
    p.add_argument('--short', choices=IDS)
    a = p.parse_args()
    paths = [str(build(i, a.version)) for i in ([a.short] if a.short else IDS)]
    print(json.dumps({'status':'projects_built_from_actual_native_locks','projects':paths},ensure_ascii=False))
