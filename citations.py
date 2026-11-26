"""Structured reference ledger, deterministic BibTeX/LaTeX export and consistency checks.
Checks metadata and links between artifacts, NOT the truth or provenance of a source.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from runtime import strict_json

KEY = re.compile(r'[A-Za-z][A-Za-z0-9:._-]{0,79}\Z')
DOI = re.compile(r'10\.\d{4,9}/\S+\Z', re.I)
ROLES = {'target','theorem','related_work','method','software','data','novelty'}
TYPES = {'article','book','inproceedings','misc','techreport'}
FIELDS = {'key','type','authors','title','year','url','doi','venue','version','locator','role','checked_on','evidence','state','corporate_authors'}
CITE = re.compile(r'\\cite(?:t|p)?\s*(?:\[[^\]]*\]\s*){0,2}\{([^{}]+)\}')


def plain(value):
    return isinstance(value,str) and bool(value.strip()) and not any(ord(c)<32 or ord(c)==127 for c in value)


def escape(s):
    return ''.join({'\\':r'\textbackslash{}','{':r'\{','}':r'\}','%':r'\%','&':r'\&','#':r'\#','$':r'\$','_':r'\_','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in s)


def validate_ledger(obj):
    if not isinstance(obj,dict) or set(obj)!={'schema','references'} or obj['schema']!=1 or not isinstance(obj['references'],list):
        raise ValueError('expected schema 1 and references list')
    seen=set(); identifiers=set()
    for r in obj['references']:
        if not isinstance(r,dict) or set(r)-FIELDS: raise ValueError('invalid reference fields')
        k=r.get('key')
        if not isinstance(k,str) or not KEY.fullmatch(k) or k.casefold() in seen: raise ValueError('invalid or duplicate reference key')
        seen.add(k.casefold())
        if r.get('type') not in TYPES or r.get('role') not in ROLES or r.get('state') not in {'checked','unverified'}: raise ValueError(f'{k}: invalid type, role or state')
        if not plain(r.get('title')) or not isinstance(r.get('authors'),list) or not r['authors'] or not all(plain(x) for x in r['authors']): raise ValueError(f'{k}: title and authors required')
        if 'corporate_authors' in r and (not isinstance(r['corporate_authors'],list) or not all(isinstance(a,str) and a in r['authors'] for a in r['corporate_authors'])): raise ValueError(f'{k}: invalid corporate authors')
        if type(r.get('year')) is not int or not 1<=r['year']<=9999: raise ValueError(f'{k}: invalid year')
        for field in ('url','doi','venue','version','locator','evidence','checked_on'):
            if field in r and not plain(r[field]): raise ValueError(f'{k}: invalid {field}')
        url=r.get('url'); doi=r.get('doi')
        if url:
            u=urlsplit(url)
            if u.scheme not in {'http','https'} or not u.hostname or u.username or u.password or any(c.isspace() for c in url): raise ValueError(f'{k}: invalid source URL')
        if doi and not DOI.fullmatch(doi): raise ValueError(f'{k}: invalid DOI syntax')
        if not (url or doi or r.get('venue')): raise ValueError(f'{k}: missing bibliographic locator')
        if doi:
            identity=doi.casefold()
            if identity in identifiers: raise ValueError(f'{k}: duplicate DOI')
            identifiers.add(identity)
        if r['state']=='checked':
            if not all(r.get(f) for f in ('checked_on','evidence','locator')): raise ValueError(f'{k}: checked source needs date, evidence and locator')
            try: date.fromisoformat(r['checked_on'])
            except ValueError: raise ValueError(f'{k}: invalid check date') from None
        elif 'checked_on' in r: raise ValueError(f'{k}: unverified reference cannot have a check date')
    return obj['references']


def read_ledger(root):
    return validate_ledger(strict_json((Path(root)/'research/references.json').read_text(encoding='utf-8')))


def exports(records):
    bib=[]; tex=[]
    for r in sorted(records,key=lambda r:r['key']):
        if r['state']!='checked': continue
        k=r['key']; authors=' and '.join(('{'+escape(a)+'}') if a in r.get('corporate_authors',[]) else escape(a) for a in r['authors'])
        fields=[('author',authors),('title','{'+escape(r['title'])+'}'),('year',str(r['year']))]
        if r.get('venue'): fields.append(({'article':'journal','inproceedings':'booktitle','book':'publisher'}.get(r['type'],'howpublished'),escape(r['venue'])))
        for f in ('version','doi','url'):
            if r.get(f): fields.append((f,escape(r[f])))
        bib.append('@'+r['type']+'{'+k+',\n'+',\n'.join('  '+f+' = {'+v+'}' for f,v in fields)+'\n}\n')
        line=', '.join(escape(a) for a in r['authors'])+'. '+escape(r['title'])+'. '+str(r['year'])+'.'
        for f in ('venue','version','doi','url'):
            if r.get(f): line+=' '+escape(('Version ' if f=='version' else 'DOI: ' if f=='doi' else '')+r[f])+'.'
        tex.append(r'\bibitem{'+k+'} '+line)
    return '\n'.join(bib), ('\\begin{thebibliography}{99}\n\\raggedright\n'+'\n'.join(tex)+'\n\\end{thebibliography}\n') if tex else '% No checked references.\n'


def generate(root):
    root=Path(root); bib,tex=exports(read_ledger(root))
    (root/'paper/references.bib').write_text(bib,encoding='utf-8',newline='\n')
    (root/'paper/references.tex').write_text(tex,encoding='utf-8',newline='\n')


def check(root):
    root=Path(root); records=read_ledger(root); bib,tex=exports(records)
    for name,expected in [('references.bib',bib),('references.tex',tex)]:
        if (root/'paper'/name).read_text(encoding='utf-8')!=expected: raise ValueError(f'stale {name}; regenerate from ledger')
    checked={r['key'] for r in records if r['state']=='checked'}
    cited=set()
    # Deliberately limited to ordinary literal cite commands; not a TeX parser.
    for p in sorted((root/'paper').rglob('*.tex')):
        if p.name=='references.tex': continue
        source='\n'.join(re.split(r'(?<!\\)%',line,maxsplit=1)[0] for line in p.read_text(encoding='utf-8').splitlines())
        for group in CITE.findall(source): cited.update(k.strip() for k in group.split(','))
    if cited-checked: raise ValueError(f'unknown or unchecked citation keys: {sorted(cited-checked)}')
    return {'citation_consistency':'pass','checked_records':len(checked),'cited_keys':sorted(cited),'uncited_checked_keys':sorted(checked-cited),'source_truth_certified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('command',choices=['generate','check']); p.add_argument('root',type=Path); a=p.parse_args()
    try:
        if a.command=='generate': generate(a.root)
        print(json.dumps(check(a.root)))
    except (ValueError,OSError,TypeError,KeyError) as e: p.exit(1,f'Citation error: {e}\n')

if __name__=='__main__': main()
