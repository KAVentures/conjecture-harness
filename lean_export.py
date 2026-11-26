"""Generate fixed Lean 4/mathlib proof attempts from validated typed statements.
Never accepts arbitrary Lean source or certifies a claim from an external log.
"""
import argparse
from pathlib import Path
from fractions import Fraction
import affine, polynomial
from runtime import read_json


def number(x):
    q=Fraction(x)
    return f'(({q.numerator} : ℝ) / {q.denominator})' if q.denominator!=1 else f'({q.numerator} : ℝ)'


def sum_expr(xs):return '('+' + '.join(xs or ['(0 : ℝ)'])+')'


def affine_row(row):return sum_expr([number(row[0])]+[number(c)+f' * v{i}' for i,c in enumerate(row[1:]) if Fraction(c)])


def poly_expr(terms):
    return sum_expr([' * '.join([number(c)]+[f'v{i}^{e}' for i,e in enumerate(es) if e]) for es,c in terms])


def source(kind,spec):
    if kind=='affine':
        s=affine.normalize(spec);hyp=[affine_row(r)+' ≥ 0' for r in s['assumptions']];goal=affine_row(s['conclusion'])+' ≥ 0';tactic='linarith'
    elif kind=='polynomial':
        s=polynomial.normalize(spec);hyp=[f'v{i} ≥ 0' for i in range(len(s['variables']))] if s['domain']=='nonnegative' else []
        goal=poly_expr(s['terms'])+(' = 0' if s['relation']=='zero' else ' ≥ 0');tactic='ring' if s['relation']=='zero' else 'first | positivity | nlinarith'
    else:raise ValueError('unknown typed language')
    # Internal generated identifiers avoid reserved words and injection from variable names.
    args=' '.join(f'(v{i} : ℝ)' for i in range(len(s['variables'])))
    hs=' '.join(f'(h{i} : {h})' for i,h in enumerate(hyp))
    return 'import Mathlib\n\nset_option autoImplicit false\nset_option maxHeartbeats 200000\n\ntheorem conjecture_harness_claim '+args+' '+hs+' : '+goal+' := by\n  '+tactic+'\n\n#print axioms conjecture_harness_claim\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('kind',choices=['affine','polynomial']);p.add_argument('spec',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.suffix!='.lean':p.error('expected .lean output')
    with a.output.open('x',encoding='utf-8') as f:f.write(source(a.kind,read_json(a.spec)))
    print('Generated Lean attempt only; run in a pinned trusted mathlib project and audit axioms. Not verified.')
if __name__=='__main__':main()
