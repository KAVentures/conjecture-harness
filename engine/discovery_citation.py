"""Generate citable research package metadata from confirmed facts, not placeholders.
No DOI lookup/registration, author verification or publication is performed.
JSON output is valid YAML 1.2. The paper is a manuscript unless verified otherwise.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from runtime import strict_json
from citations import plain, DOI, escape

FILES = ('CITATION.cff', 'CITATION.bib', 'CITATION.md')


def checked(value):
    return plain(value) and not any(c in value for c in '[]')


def url(value):
    if not checked(value) or any(c.isspace() for c in value):
        raise ValueError('invalid URL')
    u = urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise ValueError('invalid HTTPS URL')
    return value


def build(data):
    fields = {'title', 'authors', 'repository-code', 'version', 'doi', 'year', 'paper-url', 'paper-doi', 'paper-title'}
    if not isinstance(data, dict) or set(data) - fields:
        raise ValueError('invalid metadata fields')
    if not checked(data.get('title')) or not isinstance(data.get('authors'), list) or not data['authors']:
        raise ValueError('confirmed title and authors required')
    for a in data['authors']:
        if not isinstance(a, dict) or set(a) not in ({'given-names', 'family-names'}, {'name'}) or not all(checked(v) for v in a.values()):
            raise ValueError('confirmed given/family names or organization required')
    repo = url(data.get('repository-code'))
    for field in ('doi', 'paper-doi'):
        if field in data and (not checked(data[field]) or not DOI.fullmatch(data[field])):
            raise ValueError('invalid DOI syntax')
    if 'version' in data and not checked(data['version']):
        raise ValueError('invalid version')
    if 'year' in data and (type(data['year']) is not int or not 1 <= data['year'] <= 9999):
        raise ValueError('invalid year')
    if 'paper-title' in data and not checked(data['paper-title']):
        raise ValueError('invalid paper title')
    if 'doi' in data and 'paper-doi' in data and data['doi'].casefold() == data['paper-doi'].casefold():
        raise ValueError('do not assign one DOI to distinct artifacts')
    cff = {'cff-version': '1.2.0', 'message': 'Please cite the manuscript and/or reproducibility package.', 'title': data['title'], 'authors': data['authors'], 'repository-code': repo, 'type': 'software'}
    for field in ('version', 'doi'):
        if field in data:
            cff[field] = data[field]
    paper = {'type': 'unpublished', 'title': data.get('paper-title', data['title']), 'authors': data['authors'], 'url': url(data.get('paper-url', repo)), 'notes': 'Research manuscript; peer-review status is not asserted.'}
    if 'year' in data:
        paper['year'] = data['year']
    if 'paper-doi' in data:
        paper['doi'] = data['paper-doi']
    cff['preferred-citation'] = paper
    return cff


def render(data):
    cff = build(data)
    paper = cff['preferred-citation']
    authors = ' and '.join('{' + escape(a['name']) + '}' if 'name' in a else escape(a['family-names'] + ', ' + a['given-names']) for a in data['authors'])
    def bib(key, title, link, doi=None, version=None):
        pairs = [('author', authors), ('title', '{' + escape(title) + '}'), ('url', escape(link))]
        if 'year' in data:
            pairs.append(('year', str(data['year'])))
        if doi:
            pairs.append(('doi', escape(doi)))
        if version:
            pairs.append(('version', escape(version)))
        return '@misc{' + key + ',\n' + ',\n'.join('  ' + k + ' = {' + v + '}' for k, v in pairs) + '\n}\n'
    b = bib('researchpackage', cff['title'], cff['repository-code'], cff.get('doi'), cff.get('version')) + '\n' + bib('researchpaper', paper['title'], paper['url'], paper.get('doi'))
    m = '# How to cite\n\nUse the paper citation for mathematical claims and the repository citation for reproducibility artifacts. Manuscript status is not a peer-review claim.\n\n## Manuscript and research package (BibTeX)\n\n```bibtex\n' + b + '```\n\nGitHub-compatible metadata: `CITATION.cff`. Cite the exact revision used; add a DOI only after it is actually issued and verified.\n'
    return dict(zip(FILES, (json.dumps(cff, ensure_ascii=False, indent=2)+'\n', b, m)))


def generate(root, metadata):
    root = Path(root)
    if not (root/'target.json').is_file():
        raise ValueError('not a research package')
    paths = [root/name for name in (*FILES, 'citation-metadata.json')]
    if any(p.exists() or p.is_symlink() for p in paths):
        raise FileExistsError('citation files already exist; review and update explicitly')
    outputs = render(metadata)
    outputs['citation-metadata.json'] = json.dumps(metadata, ensure_ascii=False, indent=2)+'\n'
    for name, body in outputs.items():
        with (root/name).open('x', encoding='utf-8', newline='\n') as f:
            f.write(body)
    return root/'CITATION.cff'


def check(root, required=False):
    root = Path(root)
    names = (*FILES, 'citation-metadata.json')
    if not any((root/name).exists() for name in names):
        if required:
            raise ValueError('publication requires confirmed discovery citation metadata')
        return False
    data = strict_json((root/'citation-metadata.json').read_text(encoding='utf-8'))
    if required and ('paper-url' not in data or data['paper-url'].rstrip('/') == data['repository-code'].rstrip('/')):
        raise ValueError('publication requires a distinct actual manuscript URL')
    for name, expected in render(data).items():
        if (root/name).read_text(encoding='utf-8') != expected:
            raise ValueError('stale discovery citation: '+name)
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('metadata', type=Path, nargs='?')
    a = p.parse_args()
    try:
        if a.metadata:
            print(generate(a.root, strict_json(a.metadata.read_text(encoding='utf-8'))))
        else:
            check(a.root, required=True)
            print('Citation consistency passed (not authorship or DOI certification).')
    except (ValueError, OSError, TypeError, KeyError) as e:
        p.exit(1, f'Citation metadata error: {e}\n')


if __name__ == '__main__':
    main()
