"""Independent caption-only timing/text audit; never writes producer files."""
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

QA = Path(__file__).resolve().parent
EP = QA.parents[1]
OLD = EP / 'narration/free-tts-v1/final_timing.v6.json'
NEW = EP / 'narration/free-tts-v1/caption-v7/final_timing.json'
DEST = QA / 'caption-v7'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compact(text):
    return re.sub(r'\s+', '', text)

TOKEN = re.compile(r'\d[\d,.]*(?:[억천백만]\d[\d,.]*)*[억천백만]*\s*(?:원|%|개월|년|배)|\d{4}년\s*\d+분기|ETF|S&P\s*500')

def main():
    global DEST
    if not NEW.is_file():
        print(json.dumps({'status': 'awaiting_completed_v7_timing', 'path': str(NEW)}))
        return
    input_sha = sha(NEW)
    DEST = QA/'caption-v7'/('audit-'+input_sha[:12])
    old, new = read(OLD), read(NEW)
    assert old['script_sha256'] == new['script_sha256']
    assert old['audio_revision'] == new['audio_revision']
    assert len(old['chapters']) == len(new['chapters']) == 10
    assert sha(EP/'outputs/script-final-v6/script_v6.md') == new['script_sha256']
    native_evidence = []
    chapters = []
    meanings = []
    short_cues = []
    for a, b in zip(old['chapters'], new['chapters']):
        assert {k:v for k,v in a.items() if k!='cues'} == {k:v for k,v in b.items() if k!='cues'}, 'Non-caption chapter mutation'
        chapter = b['chapter']
        for key in ('text', 'spoken_text'):
            assert compact(''.join(c[key] for c in a['cues'])) == compact(''.join(c[key] for c in b['cues']))
        previous = 0
        paragraph_checks = []
        for paragraph in b['paragraphs']:
            pid = paragraph['paragraph']
            directory = Path(paragraph['wave_file']).parent
            request_path = directory/'request.json'
            boundary_path = directory/'native_boundaries.json'
            request, words = read(request_path), read(boundary_path)
            words = [x for x in words if x['type']=='WordBoundary']
            cues = [c for c in b['cues'] if c['paragraph']==pid]
            original = [c for c in a['cues'] if c['paragraph']==pid]
            assert cues and original
            for key in ('text','spoken_text'):
                assert compact(''.join(c[key] for c in cues)) == compact(request[key])
            used = []
            for c in cues:
                assert c['end_s'] > c['start_s'] >= previous - 1e-6
                assert c['end_s'] <= b['total_seconds'] + 1e-6
                previous = c['end_s']
                first, last = c['first_word_index'], c['last_word_index']
                assert 0 <= first <= last < len(words)
                start = paragraph['offset_s'] + words[first]['offset']/10_000_000
                end = paragraph['offset_s'] + (words[last]['offset']+words[last]['duration'])/10_000_000
                assert abs(start-c['start_s']) < 1.1e-6 and abs(end-c['end_s']) < 1.1e-6
                assert abs(c['native_start_s']-c['start_s']) < 1.1e-6
                assert abs(c['native_end_s']-c['end_s']) < 1.1e-6
                assert compact(request['text'][c['source_start']:c['source_end']]) == compact(c['text'])
                used.extend(range(first,last+1))
                lines = c.get('display_lines')
                assert isinstance(lines,list) and 1 <= len(lines) <= 2 and all(isinstance(s,str) and s.strip() for s in lines)
                assert compact(''.join(lines)) == compact(c['text'])
                assert c['text'].strip() not in ['어렵습니다.','바뀝니다.','있습니다.','됩니다.','합니다.','나옵니다.']
                if len(compact(c['text']))<=9:
                    short_cues.append(dict(chapter=chapter,id=c['id'],text=c['text']))
                meanings.append(dict(chapter=chapter,paragraph=pid,id=c['id'],text=c['text'],display_lines=lines,start_s=c['start_s'],end_s=c['end_s']))
            assert used == list(range(len(words))), 'Native word omitted, duplicated, or reordered'
            for token in TOKEN.findall(request['text']):
                protected = compact(token)
                assert any(protected in compact(c['text']) for c in cues), f'Token split across cues: {token}'
                assert any(protected in compact(line) for c in cues for line in c['display_lines']), f'Token split across display lines: {token}'
            paragraph_checks.append(dict(paragraph=pid,cues=len(cues),native_words=len(words),protected_tokens=TOKEN.findall(request['text'])))
            native_evidence.append(dict(paragraph=pid,request_sha256=sha(request_path),native_boundary_sha256=sha(boundary_path)))
        chapters.append(dict(chapter=chapter,old_cues=len(a['cues']),new_cues=len(b['cues']),audio_sha256=b['audio_sha256'],total_seconds=b['total_seconds'],paragraphs=paragraph_checks))
    DEST.mkdir(parents=True,exist_ok=True)
    assert sha(NEW) == input_sha, 'Producer timing changed during audit; rerun on completed input'
    report=dict(status='programmatic_text_native_timing_preservation_pass_semantic_and_glyph_review_pending',checked_at=datetime.now(timezone.utc).isoformat(),script_sha256=new['script_sha256'],v6_timing_sha256=sha(OLD),v7_timing_sha256=sha(NEW),chapters=chapters,native_evidence=native_evidence,checked_native_paragraphs=len(native_evidence),old_cues=sum(len(c['cues']) for c in old['chapters']),new_cues=len(meanings),short_cues=short_cues,display_lines_join_matches_text=True,text_spoken_text_and_native_words_conserved=True,chapter_noncaption_data_exactly_unchanged=True,actual_glyph_BBox_checked=False,all_meanings_manually_inspected=False,actual_listening=False,ASR_rerun=False,approved=False,code_sha256=sha(Path(__file__)))
    (DEST/'timing_text_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DEST/'cue_readthrough.json').write_text(json.dumps(meanings,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({**{k:report[k] for k in ['status','old_cues','new_cues','checked_native_paragraphs','short_cues','approved']},'evidence_dir':str(DEST),'v7_timing_sha256':input_sha},ensure_ascii=False))

if __name__=='__main__':
    main()
