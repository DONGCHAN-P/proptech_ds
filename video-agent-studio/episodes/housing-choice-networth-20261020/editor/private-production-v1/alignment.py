"""Audited text alignment. Missing literals never mean time zero."""
import re
from difflib import SequenceMatcher


def norm(text):
    return ''.join(c.lower() for c in text if c.isalnum())


def parse_script(text):
    result = {}
    for m in re.finditer(r'^## (\d+)\.\s*(.*?)\n(.*?)(?=^## |\Z)', text, re.M | re.S):
        n, title, body = m.groups()
        result[int(n)] = {'title': title.strip(), 'paragraphs': [p.strip() for p in body.strip().split('\n\n') if p.strip()]}
    if set(result) != set(range(1, 11)):
        raise ValueError('Expected exactly chapters 1..10')
    return result


class Alignment:
    def __init__(self, old_paras, new_paras, cues, aliases=None):
        self.old_paras, self.new_paras, self.cues = old_paras, new_paras, cues
        self.old = ''.join(map(norm, old_paras))
        self.new = ''.join(map(norm, new_paras))
        if ''.join(norm(c['text']) for c in cues) != self.new:
            raise ValueError('Cue display text differs from script (normalized punctuation/spacing only)')
        self.aliases = aliases or {}
        self.audit = []
        self.blocks = SequenceMatcher(None, self.old, self.new, autojunk=False).get_matching_blocks()
        self.paragraph_audit = []
        for i, p in enumerate(old_paras):
            scores = [SequenceMatcher(None, norm(p), norm(q), autojunk=False).ratio() for q in new_paras]
            j = max(range(len(scores)), key=scores.__getitem__)
            self.paragraph_audit.append({'old_paragraph': i, 'new_paragraph': j, 'similarity': round(scores[j], 4),
                                         'old_text': p, 'new_text': new_paras[j]})

    def locate(self, literal):
        query = norm(self.aliases.get(literal, literal))
        found = [m.start() for m in re.finditer(re.escape(query), self.new)] if query else []
        method = 'explicit_semantic_alias' if literal in self.aliases else 'exact_normalized_literal'
        score = 1.0
        review = False
        if found:
            oldpos = self.old.find(norm(literal))
            if len(found) > 1:
                # Old sequence position disambiguates identical short phrases; record every candidate.
                target = oldpos / max(1, len(self.old)) if oldpos >= 0 else 0.5
                pos = min(found, key=lambda v: abs(v / len(self.new) - target))
                method += '_disambiguated'
                review = True
            else:
                pos = found[0]
        else:
            oldquery = norm(literal)
            oldpos = self.old.find(oldquery)
            if oldpos < 0:
                raise ValueError(f'Anchor absent from both scripts and aliases: {literal}')
            covered = [(max(oldpos, b.a), min(oldpos + len(oldquery), b.a + b.size), b) for b in self.blocks]
            covered = [(a, z, b) for a, z, b in covered if z > a]
            if not covered:
                raise ValueError(f'Deleted anchor requires explicit semantic mapping: {literal}')
            a, z, b = max(covered, key=lambda x: x[1] - x[0])
            score = (z - a) / len(oldquery)
            if score < 0.45 or z - a < min(3, len(oldquery)):
                raise ValueError(f'Low-confidence anchor requires mapping ({score:.2f}): {literal}')
            pos = b.b + a - b.a
            method = 'SequenceMatcher_equal_block'
            review = True
        cursor = 0
        for c in self.cues:
            end = cursor + len(norm(c['text']))
            if cursor <= pos < end:
                break
            cursor = end
        else:
            raise ValueError(f'No cue owns mapped position: {literal}')
        pi = 0
        offset = 0
        for i, p in enumerate(self.new_paras):
            if offset <= pos < offset + len(norm(p)):
                pi = i
                break
            offset += len(norm(p))
        record = {'literal': literal, 'replacement': self.aliases.get(literal), 'method': method,
                  'new_character_offset': pos, 'new_paragraph': pi, 'cue_id': c['id'], 'cue_text': c['text'],
                  'time_s': c['start_s'], 'match_ratio': round(score, 4), 'review_required': review,
                  'time_basis': 'containing audio/display cue start; no fabricated sub-word precision',
                  'candidate_positions': found}
        self.audit.append(record)
        return c['start_s']
