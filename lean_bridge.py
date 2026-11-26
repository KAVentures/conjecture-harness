"""Opt-in Lean 4 / Mathlib bridge for exact structured real inequalities.

Generate theorem statements from canonical claim data; no arbitrary model
Lean source, tactics, imports, commands or executable configuration. External
verification requires an operator-trusted Lake project and local toolchain.
Results are deliberately separate from the Python proof audit.
"""
import argparse,hashlib,json,re,tempfile,time
from pathlib import Path
import affine,polynomial as p,conditional_theorems as ct,simplex_discovery as sx
from runtime import invoke,read_json
from discovery import check

TACTICS=('ring','positivity','norm_num','linarith','nlinarith','nlinarith-squares')
ALLOWED_AXIOMS={'propext','Classical.choice','Quot.sound'}
THEOREM='harness_checked'

def sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def file_sha(path):
    with Path(path).open('rb') as f:
        b=f.read(4*1024*1024+1)
    if len(b)>4*1024*1024:raise ValueError('toolchain metadata exceeds limit')
    return hashlib.sha256(b).hexdigest()

def number(x):
    q=affine.rational(x)
    a='('+str(q.numerator)+' : ℝ)'
    return a if q.denominator==1 else '('+a+' / ('+str(q.denominator)+' : ℝ))'

def expr(terms,variables):
    parts=[]
    for exps,c in terms:
        factors=[number(c)]
        for x,e in zip(variables,exps):
            if e:factors.append(x if e==1 else '('+x+' ^ '+str(e)+')')
        parts.append('('+' * '.join(factors)+')')
    return '('+' + '.join(parts)+')' if parts else '(0 : ℝ)'

def relation(terms,variables,rel):
    x=expr(terms,variables)
    if rel=='zero':return x+' = 0'
    if rel=='nonnegative':return '0 ≤ '+x
    raise ValueError('unsupported relation')

def row_terms(row):
    n=len(row)-1
    return [[([0]*n if i==0 else [int(j==i-1) for j in range(n)]),v] for i,v in enumerate(row) if affine.rational(v)]

def formalize(text):
    """Deterministic translation, including every domain and hypothesis."""
    if not isinstance(text,str) or len(text)>20000:raise ValueError('claim size')
    hypotheses=[]
    if text.startswith(p.PREFIX):
        s=p.parse_statement(text);n=len(s['variables']);vs=['x'+str(i) for i in range(n)]
        if s['domain']=='nonnegative':hypotheses.extend('0 ≤ '+v for v in vs)
        goal=relation(s['terms'],vs,s['relation'])
    elif text.startswith(ct.PREFIX):
        s=ct.parse_statement(text);n=len(s['variables']);vs=['x'+str(i) for i in range(n)]
        if s['domain']=='nonnegative':hypotheses.extend('0 ≤ '+v for v in vs)
        hypotheses.extend(relation(a['terms'],vs,a['relation']) for a in s['assumptions'])
        goal=relation(s['conclusion'],vs,'nonnegative')
    elif text.startswith(sx.PREFIX):
        s=sx.parse_statement(text);n=len(s['variables']);vs=['x'+str(i) for i in range(n)]
        hypotheses.extend('0 ≤ '+v for v in vs)
        hypotheses.append(' + '.join(vs)+' = 1')
        goal=relation(s['terms'],vs,'nonnegative')
    elif text.startswith(affine.PREFIX):
        s=affine.parse_statement(text);n=len(s['variables']);vs=['x'+str(i) for i in range(n)]
        # affine.parse_statement in legacy versions must still be normalized.
        if affine.statement(s)!=text:raise ValueError('noncanonical affine claim')
        hypotheses.extend(relation(row_terms(a),vs,'nonnegative') for a in s['assumptions'])
        goal=relation(row_terms(s['conclusion']),vs,'nonnegative')
    else:raise ValueError('unsupported Lean translation')
    binders='('+' '.join(vs)+' : ℝ)'
    for i,h in enumerate(hypotheses):binders+=' (h'+str(i)+' : '+h+')'
    return dict(binders=binders,goal=goal,variables=vs,hypotheses=hypotheses)

def render(text,tactic):
    if tactic not in TACTICS:raise ValueError('unsupported tactic')
    x=formalize(text)
    body=tactic
    if tactic=='nlinarith-squares':
        body='nlinarith ['+', '.join('sq_nonneg '+v for v in x['variables'])+']'
    return ('import Mathlib\n\nset_option maxHeartbeats 200000 in\n'
            'theorem '+THEOREM+' '+x['binders']+' : '+x['goal']+' := by\n  '+body+
            '\n\n#print axioms '+THEOREM+'\n')

def axioms(output):
    """Fail closed if the exact theorem's dependency report is absent/ambiguous."""
    if not isinstance(output,str) or len(output)>200000:return None
    pattern=r"'"+THEOREM+r"' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)"
    matches=list(re.finditer(pattern,output))
    if len(matches)!=1:return None
    body=matches[0].group(1)
    result=[] if not body else [s.strip() for s in body.split(',')]
    if len(set(result))!=len(result) or not set(result)<=ALLOWED_AXIOMS:return None
    return sorted(result)

def verify(text,project,timeout=30,tactics=TACTICS):
    """Rebuild generated source locally; a cached success label is not replay."""
    formalize(text)
    if type(timeout) not in (int,float) or not 0<timeout<=300 or not isinstance(tactics,(list,tuple)) or not 1<=len(tactics)<=len(TACTICS) or any(t not in TACTICS for t in tactics):raise ValueError('verification limits')
    project=Path(project).resolve()
    if not project.is_dir() or not (project/'lean-toolchain').is_file() or not (project/'lake-manifest.json').is_file():raise ValueError('trusted Lake project with toolchain and dependency manifest required')
    env=dict(toolchain_sha256=file_sha(project/'lean-toolchain'),manifest_sha256=file_sha(project/'lake-manifest.json'))
    results=[];deadline=time.monotonic()+timeout
    with tempfile.TemporaryDirectory(prefix='harness-lean-') as td:
        path=Path(td)/'HarnessCheck.lean'
        for t in tactics:
            remaining=deadline-time.monotonic()
            if remaining<=0:break
            source=render(text,t);path.write_text(source,encoding='utf-8')
            raw=invoke(['lake','env','lean',str(path)],'',remaining,project,65536)
            out=raw.get('stdout','')+'\n'+raw.get('stderr','')
            deps=axioms(out) if raw.get('returncode')==0 and raw.get('termination') is None else None
            # Explicitly disallow any sorry warning even if no dependency
            # reached the checked declaration.
            if re.search(r'\bsorry\b|sorryAx',out,re.IGNORECASE):deps=None
            results.append(dict(tactic=t,source_sha256=sha(source),returncode=raw.get('returncode'),termination=raw.get('termination'),axioms=deps,stdout=raw.get('stdout',''),stderr=raw.get('stderr','')))
            if deps is not None:
                return dict(status='lean-verified',statement_sha256=sha(text),environment=env,tactic=t,axioms=deps,source=source,attempts=results,scope='trusted local Lean/Mathlib environment; not natural-language correspondence or novelty verification')
            if raw.get('termination')=='spawn_error':break
    return dict(status='unknown',statement_sha256=sha(text),environment=env,attempts=results,scope='no successful allowed-axiom replay; not a refutation')

def main():
    q=argparse.ArgumentParser(description=__doc__);sub=q.add_subparsers(dest='action',required=True)
    a=sub.add_parser('export');a.add_argument('state');a.add_argument('output');a.add_argument('--focus',default='goal');a.add_argument('--tactic',choices=TACTICS,default='nlinarith')
    a=sub.add_parser('verify');a.add_argument('state');a.add_argument('--focus',default='goal');a.add_argument('--project',required=True);a.add_argument('--timeout',type=float,default=30);a.add_argument('--report')
    a=q.parse_args();g=check(read_json(a.state,limit=32*1024*1024));text=g['nodes'][a.focus]['statement']
    if a.action=='export':
        with Path(a.output).open('x',encoding='utf-8') as f:f.write(render(text,a.tactic))
        print(json.dumps(dict(status='exported-unverified',statement_sha256=sha(text))));return
    r=verify(text,a.project,a.timeout)
    if a.report:
        with Path(a.report).open('x',encoding='utf-8') as f:json.dump(r,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps(dict(status=r['status'],statement_sha256=r['statement_sha256'],attempts=len(r['attempts']))))
    if r['status']!='lean-verified':q.exit(1)
if __name__=='__main__':main()
