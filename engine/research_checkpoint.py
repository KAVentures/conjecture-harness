"""Create and inspect portable research states; status is not proof certification."""
import argparse,json
from pathlib import Path
from discovery import new,save,check,closure,frontier,plan
from harness import coordinator_lock
from runtime import read_json


def typed(kind,data):
    if kind=='prose':return data
    if kind=='affine':from affine import statement
    elif kind=='polynomial':from polynomial import statement
    elif kind=='capacity':from capacity import statement
    elif kind=='finite-power':from finite_power import statement
    else:raise ValueError('unknown problem language')
    return statement(data)


def initialize(path,kind,data):
    path=Path(path).resolve();g=new(typed(kind,data));log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
    with coordinator_lock(log):
        if path.exists():raise FileExistsError('research state already exists')
        save(path,g)
    return g


def report(g):
    check(g);known=closure(g);goal=g['nodes']['goal'];status='established' if 'goal' in known else goal['status']
    # Report every recorded review and observation, even detached or failed ones.
    # Consumers must audit proof evidence; closure reflects the local review trust.
    return dict(schema=1,target=goal['statement'],target_sha256=g['target_sha256'],status=status,
                trust='Recorded local review state; not independent formal proof or novelty certification.',
                unresolved=frontier(g),established=sorted(known),refuted=sorted(i for i,n in g['nodes'].items() if n['status']=='refuted'),
                accepted_edges=sorted(i for i,e in g['edges'].items() if e['rule']=='accepted'),
                rejected_edges=sorted(i for i,e in g['edges'].items() if e['rule']=='rejected'),
                attempts=sum(not h['trusted_review'] for h in g['history']),next=plan(g),state=g)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('init');q.add_argument('state',type=Path);q.add_argument('kind',choices=['prose','affine','polynomial','capacity','finite-power']);q.add_argument('input',help='Literal statement for prose; JSON spec filename otherwise')
    q=sub.add_parser('checkpoint');q.add_argument('state',type=Path);q.add_argument('output',type=Path)
    q=sub.add_parser('resume');q.add_argument('checkpoint',type=Path);q.add_argument('state',type=Path)
    a=p.parse_args()
    if a.cmd=='init':
        g=initialize(a.state,a.kind,a.input if a.kind=='prose' else read_json(a.input));print(g['target_sha256'])
    elif a.cmd=='checkpoint':
        r=report(read_json(a.state,limit=32*1024*1024));
        with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2,ensure_ascii=False);f.write('\n')
        print(r['status'])
    else:
        r=read_json(a.checkpoint,limit=64*1024*1024);g=check(r['state'])
        if r!=report(g):raise ValueError('checkpoint metadata/state mismatch')
        path=a.state.resolve();log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
        with coordinator_lock(log):
            if path.exists():raise FileExistsError('research state already exists')
            save(path,g)
        print(g['target_sha256'])
if __name__=='__main__':main()
