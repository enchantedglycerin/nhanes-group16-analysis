"""Vancouver references numbered by their first appearance in report prose."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'references.json').read_text(encoding='utf-8'))
CITATION = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')


def identifiers(variant):
    common = {1: 'cdc', 2: 'age', 3: 'welch', 4: 'hc3', 9: 'normality', 10: 'large_samples'}
    common.update({
        1: {5: 'paq', 6: 'beijer', 7: 'mcgregor', 8: 'bpxo'},
        2: {5: 'cbc', 6: 'nah', 7: 'su'},
        3: {5: 'bmx', 6: 'cattermole2017', 7: 'cattermole2021'},
    }[variant])
    return common


def citation(reference):
    if reference['type'] == 'journal':
        authors = reference['authors'][:6]
        if len(reference['authors']) > 6:
            authors = [*authors, 'et al']
        issue = '(' + reference['issue'] + ')' if reference.get('issue') else ''
        return (', '.join(authors) + '. ' + reference['title'] + '. '
                + reference['journal'] + '. ' + reference['year'] + ';'
                + reference['volume'] + issue + ':' + reference['pages'] + '. '
                + 'doi:' + reference['doi'] + '. [ต้นฉบับ](' + reference['url'] + ')')
    return (reference['author'] + '. ' + reference['title']
            + ' [Internet]. [cited 2026 Oct 16]. Available from: '
            + '[ต้นฉบับ](' + reference['url'] + ')')


def append_references(doc):
    doc.page()
    doc.h('เอกสารอ้างอิง')
    for key in identifiers(doc.variant).values():
        doc.p(citation(CATALOG[key]), main=False, style='reference')


def finalize(doc):
    lookup = identifiers(doc.variant)
    order = []
    for block in doc.blocks:
        if block.get('style') == 'reference':
            continue
        for field in ['text', 'title', 'caption']:
            for match in CITATION.finditer(block.get(field, '')):
                for value in match.group(1).split(','):
                    number = int(value)
                    assert number in lookup, ('Unknown citation', number)
                    if number not in order:
                        order.append(number)
    assert set(order) == set(lookup), ('Unused reference', set(lookup) - set(order))
    renumber = {old: new for new, old in enumerate(order, 1)}
    used = [dict(number=i, key=lookup[old], **CATALOG[lookup[old]])
            for i, old in enumerate(order, 1)]
    references = iter(used)
    for block in doc.blocks:
        if block.get('style') == 'reference':
            item = next(references)
            block['text'] = str(item['number']) + '. ' + citation(item)
        else:
            for field in ['text', 'title', 'caption']:
                if field in block:
                    block[field] = CITATION.sub(
                        lambda m: '[' + ', '.join(str(renumber[int(v)])
                                                 for v in m.group(1).split(',')) + ']',
                        block[field])
    (doc.folder / 'references_used.json').write_text(
        json.dumps({'style': 'Vancouver', 'numbering': 'first appearance',
                    'verified_on': '2026-10-16', 'references': used},
                   ensure_ascii=False, indent=2), encoding='utf-8')
