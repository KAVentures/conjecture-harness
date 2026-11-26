"""Opt-in, bounded cross-target strategy priors. No mathematical evidence transfer."""
import argparse,json,math,re
from pathlib import Path
from discovery import MODES,check
from strategy import statistics
from runtime import read_json


def domain(g):
    from affine import PREFIX as a
    from polynomial import PREFIX as p
    from capacity import PREFIX as c
    from finite_power import PREFIX as f
    s=g['nodes']['goal']['statement']
    return next((name for name,prefix in [('affine',a),('polynomial',p),('capacity',c),('finite_power',f)] if s.startswith(prefix)), 'other')


def build(states,*,audited=False):
    if not isinstance(states,list) or not 1<=len(states)<=256:raise ValueError('expected 1..256 reviewed state snapshots')
    targets={}
    for g in states:
        check(g);key=g['target_sha256']
        if key in targets:raise ValueError('duplicate target; select a single reviewed snapshot')
        if audited:
            from audited_strategy import statistics as audited_statistics
            stats=audited_statistics(g)
        else:stats=statistics(g['history'],MODES)
        targets[key]=dict(domain=domain(g),modes={m:dict(attempts=s['attempts'],credits=s['credits'],adverse=s['adverse']) for m,s in stats.items()})
    return validate(dict(schema=1,targets=targets))


def validate(p):
    if not isinstance(p,dict) or set(p)!={'schema','targets'} or type(p['schema']) is not int or p['schema']!=1 or not isinstance(p['targets'],dict) or len(p['targets'])>256:raise ValueError('invalid strategy profile')
    for key,t in p['targets'].items():
        if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or not isinstance(t,dict) or set(t)!={'domain','modes'} or t['domain'] not in ('affine','polynomial','capacity','finite_power','other') or not isinstance(t['modes'],dict) or set(t['modes'])!=set(MODES):raise ValueError('invalid profile target')
        for r in t['modes'].values():
            if not isinstance(r,dict) or set(r)!={'attempts','credits','adverse'} or any(type(v) is not int or not 0<=v<=5000 for v in r.values()) or max(r['credits'],r['adverse'])>r['attempts']:raise ValueError('invalid strategy counts')
    return p


def prior(p,g):
    """Average per-target outcome rates, not per-attempt totals; weak bias only."""
    validate(p);check(g);d=domain(g);out={}
    for m in MODES:
        rates=[]
        for key,t in p['targets'].items():
            if key==g['target_sha256'] or t['domain']!=d:continue
            r=t['modes'][m]
            if r['attempts']:rates.append((r['credits']-0.5*r['adverse'])/(r['attempts']+2))
        # Shrink to zero for sparse source targets; bound across any corpus size.
        out[m]=0.15*sum(rates)/(len(rates)+2)
    return out


def load(path):return validate(read_json(path)) if path is not None else None


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('states',type=Path,nargs='+');p.add_argument('--audited',action='store_true',help='credit only independently replayed proof routes and exact refutations');a=p.parse_args()
    profile=build([read_json(path,limit=32*1024*1024) for path in a.states],audited=a.audited)
    with a.output.open('x',encoding='utf-8') as f:json.dump(profile,f,indent=2,sort_keys=True);f.write('\n')
    print('Saved aggregate strategy counts; no proof evidence imported.')
if __name__=='__main__':main()
