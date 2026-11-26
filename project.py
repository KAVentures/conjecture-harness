"""Chat-first research package scaffolding and integrity validation. No proof certification."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from runtime import strict_json
import citations
import discovery_citation

REQUIRED = frozenset(('README.md','target.json','STATUS.json','research/STATE.md','research/ATTEMPTS.md','research/SOURCES.md','research/CLAIMS.md','research/REVIEW.md','paper/paper.tex','paper/references.bib','paper/references.tex','research/references.json','repro/README.md','AUTHORSHIP.md'))
STATES = {'in_progress','partial','candidate_proof','candidate_counterexample','known_control'}
NOVELTY = {'unknown','prior_related','rediscovery','prior_implication','no_prior_identified_bounded_search','known_control'}

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')

def tex_escape(s):
    mapping={'\\':r'\textbackslash{}','{':r'\{','}':r'\}','%':r'\%','&':r'\&','#':r'\#','$':r'\$','_':r'\_','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(mapping.get(c,c) for c in s)

def nonempty(s):
    return isinstance(s,str) and bool(s.strip())

def initialize(root, ident, statement, author=None):
    root=Path(root)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',ident): raise ValueError('invalid target id')
    if not nonempty(statement) or (author is not None and not nonempty(author)): raise ValueError('statement and provided author must be nonempty')
    if root.exists() or root.is_symlink(): raise ValueError('destination already exists; refusing overwrite')
    root.mkdir(parents=True)
    for d in ('research','paper','repro'): (root/d).mkdir()
    write_json(root/'target.json',{'id':ident,'statement':statement,'definitions':[],'source':None,'source_status':'user_supplied_unverified','status_evidence_date':None})
    write_json(root/'research/references.json',{'schema':1,'references':[]})
    write_json(root/'STATUS.json',{'research_status':'in_progress','novelty':'unknown','verification':[],'human_review':'pending'})
    files={'README.md':f'# {ident}\n\nResearch in progress. No resolution claimed. See target.json and research/STATE.md.\n',
      'research/STATE.md':'# Checkpoint\n\n- Target recorded; source and definitions require verification.\n- Next: literature audit and competing approaches.\n',
      'research/ATTEMPTS.md':'# Attempt log\n\nNo attempts recorded yet.\n',
      'research/SOURCES.md':'# Source audit\n\nNo source checked yet.\n',
      'research/CLAIMS.md':'# Claims and dependencies\n\nNo claims verified yet.\n',
      'research/REVIEW.md':'# Review\n\nNo independent review performed.\n',
      'repro/README.md':'# Reproduction\n\nNo computational claims yet. Add exact inputs, commands, dependencies and actual results.\n',
      'AUTHORSHIP.md':f'# Authorship\n\nHuman author: {author or "[confirmation pending]"}\n\nAI-assisted research and drafting; document actual contributions before release. Human review and approval pending.\n',
      'paper/references.bib':'',
      'paper/paper.tex':r'''\documentclass{article}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb}
\title{Research in progress: '''+tex_escape(ident)+r'''}
\author{'''+tex_escape(author or '[Author confirmation pending]')+r'''}
\date{}
\begin{document}
\maketitle
\begin{abstract}Incomplete research draft. No mathematical resolution is claimed.\end{abstract}
\section{Target}
'''+tex_escape(statement)+r'''
\section{Research status}
Proof and novelty review pending.
\section*{AI disclosure}
AI assisted with preparation of this draft. Human review is pending.
\input{references.tex}
\end{document}
'''}
    for name,body in files.items(): (root/name).write_text(body,encoding='utf-8')
    citations.generate(root)
    seal(root)

def inventory(root):
    root=Path(root)
    if root.is_symlink() or not root.is_dir(): raise ValueError('expected a real package directory')
    found={}
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink(): raise ValueError(f'symlink forbidden: {rel}')
        if rel=='manifest.json':
            if not p.is_file(): raise ValueError('manifest must be a file')
            continue
        if p.is_dir():
            if p.name in {'.git','__pycache__'}: raise ValueError(f'remove transient directory {rel}')
            continue
        if not p.is_file(): raise ValueError(f'not a regular file: {rel}')
        if p.name in {'.env','config.json'} or p.suffix in {'.pem','.key','.pyc'}: raise ValueError(f'potential secret or transient file: {rel}')
        digest=hashlib.sha256(); size=0
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(65536),b''):
                digest.update(chunk); size+=len(chunk)
        found[rel]={'sha256':digest.hexdigest(),'bytes':size}
    if not REQUIRED <= found.keys(): raise ValueError(f'missing required files: {sorted(REQUIRED-found.keys())}')
    return found

def metadata(root):
    target=strict_json((root/'target.json').read_text(encoding='utf-8'))
    status=strict_json((root/'STATUS.json').read_text(encoding='utf-8'))
    if not isinstance(target,dict) or not isinstance(status,dict): raise ValueError('metadata must be JSON objects')
    if not isinstance(target.get('id'),str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',target['id']) or not nonempty(target.get('statement')): raise ValueError('invalid target metadata')
    if status.get('research_status') not in STATES or status.get('novelty') not in NOVELTY: raise ValueError('unknown or unsupported research/novelty status')
    if not isinstance(status.get('verification'),list) or not nonempty(status.get('human_review')): raise ValueError('verification list and human review status required')
    if (status['research_status']=='known_control') != (status['novelty']=='known_control'): raise ValueError('known controls must be labeled consistently')

def seal(root):
    root=Path(root); found=inventory(root); metadata(root); citations.check(root); discovery_citation.check(root)
    write_json(root/'manifest.json',{'schema':1,'target_sha256':found['target.json']['sha256'],'files':found})

def validate(root, publication=False):
    root=Path(root); found=inventory(root); metadata(root); citations.check(root); discovery_citation.check(root)
    if publication: discovery_citation.check(root, required=True)
    expected={'schema':1,'target_sha256':found['target.json']['sha256'],'files':found}
    if strict_json((root/'manifest.json').read_text(encoding='utf-8'))!=expected: raise ValueError('manifest mismatch: changed, missing or extra files')
    return {'structure_and_integrity':'pass','files':len(found),'mathematical_certification':False}

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('init'); q.add_argument('root',type=Path); q.add_argument('--id',required=True); q.add_argument('--statement',required=True); q.add_argument('--author')
    for cmd in ('seal','validate'):
        q=sub.add_parser(cmd); q.add_argument('root',type=Path)
        if cmd=='validate': q.add_argument('--publication',action='store_true')
    a=p.parse_args()
    try:
        if a.cmd=='init': initialize(a.root,a.id,a.statement,a.author)
        elif a.cmd=='seal': seal(a.root)
        print(json.dumps(validate(a.root, publication=getattr(a,'publication',False))))
    except (ValueError,OSError,TypeError,KeyError) as e: p.exit(1,f'Package error: {e}\n')
if __name__=='__main__': main()
