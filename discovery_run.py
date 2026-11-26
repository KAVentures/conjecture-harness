"""Bounded single-coordinator discovery proposals via trusted external commands.
No model-generated code execution or model self-certification. Review separately.
"""
import argparse,json,time,math,tempfile
from pathlib import Path
from discovery import MODES, plan,prompt,record,save,check
from runtime import invoke,strict_json,read_json
from harness import coordinator_lock
from affine_lab import auto_discharge as affine_discharge
from polynomial_lab import auto_discharge as polynomial_discharge
from affine_bridge import auto_discharge as bridge_discharge
from equivalence import auto_reuse
from polynomial_transform import auto_discharge as shift_discharge
from hypothesis import auto_refine,auto_compose
from lemma_invention import auto_invent
from recursive_invention import auto_recursive
from capacity_lab import auto_discharge as capacity_discharge
from finite_power_lab import auto_discharge as finite_discharge
from graph_reduction_lab import auto_discharge as reduction_discharge
from theorem_transfer import auto_transfer
from symbolic_lab import auto_discharge as symbolic_discharge
from proof_synthesis import auto_discharge as synthesis_discharge
from representation_transfer import auto_discharge as representation_discharge
from dynamics_lab import auto_discharge as dynamics_discharge
from structured_algebra_lab import auto_discharge as structured_discharge
from extremal_reduction import auto_discharge as extremal_discharge
from conditional_lab import auto_discharge as conditional_discharge
from theorem_application import auto_discharge as application_discharge
from univariate_lab import auto_discharge as sturm_discharge
from sign_cells_lab import auto_discharge as sign_cell_discharge
from projective_lab import auto_discharge as projective_discharge
from equational_lab import auto_discharge as equational_discharge
from graph_structure_lab import auto_discharge as structural_discharge
from graph_consequence_lab import auto_discharge as graph_linear_discharge
from ideal_consequence_lab import auto_discharge as ideal_consequence_discharge

def auto_discharge(g):
    g=auto_transfer(g)
    g=auto_reuse(bridge_discharge(shift_discharge(polynomial_discharge(affine_discharge(auto_reuse(g))))))
    g=reduction_discharge(finite_discharge(capacity_discharge(auto_recursive(auto_invent(auto_compose(auto_refine(g)))))))
    g=dynamics_discharge(representation_discharge(synthesis_discharge(symbolic_discharge(g))))
    g=extremal_discharge(structured_discharge(g))
    g=ideal_consequence_discharge(g)
    return graph_linear_discharge(structural_discharge(equational_discharge(application_discharge(projective_discharge(sign_cell_discharge(conditional_discharge(sturm_discharge(g))))))))

def run(path,cmd,attempts,seconds,timeout,profile=None,metareasoning=False):
    from metareasoning import select,research_prompt,annotate
    planner=select if metareasoning else plan
    prompter=research_prompt if metareasoning else prompt
    path=Path(path).resolve()
    if not isinstance(cmd,list) or not cmd or not all(isinstance(x,str) and x for x in cmd):raise ValueError('expected trusted command array')
    if type(attempts) is not int or attempts<1 or not all(math.isfinite(x) and x>0 for x in (seconds,timeout)):raise ValueError('positive finite limits required')
    log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
    with coordinator_lock(log):
        g=check(read_json(path,limit=32*1024*1024));deadline=time.monotonic()+seconds
        for _ in range(attempts):
            remaining=deadline-time.monotonic()
            if remaining<=0:break
            h=auto_discharge(g)
            if h!=g:save(path,h);g=h
            remaining=deadline-time.monotonic()
            if remaining<=0:break
            p=planner(g,profile)
            if 'stop' in p:break
            folder=Path(tempfile.mkdtemp(prefix=str(len(g['history']))+'-',dir=log))
            data=prompter(g,p);(folder/'prompt.txt').write_text(data,encoding='utf-8')
            raw=invoke(cmd,data,min(timeout,remaining),folder)
            (folder/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
            try:
                if raw['returncode']:raise ValueError('worker failed')
                ops=strict_json(raw['stdout'])
                if not isinstance(ops,list):raise ValueError('expected list')
                from discovery_portfolio import reconcile
                ops=reconcile(g,g,ops,folder.name,p['mode']=='blind')
                h=record(g,p['mode'],p['focus'],ops)
            except (ValueError,TypeError,KeyError,RecursionError) as e:
                (folder/'rejected.txt').write_text(str(e),encoding='utf-8');h=record(g,p['mode'],p['focus'],[])
            h['history'][-1]['elapsed_seconds']=raw.get('elapsed',0)
            if metareasoning:annotate(h,p)
            save(path,h);g=h
        if time.monotonic()<deadline:
            h=auto_discharge(g)
            if h!=g:save(path,h);g=h
    return planner(g,profile)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state',type=Path);p.add_argument('--config',type=Path,required=True);p.add_argument('--attempts',type=int,default=5);p.add_argument('--seconds',type=float,default=600);p.add_argument('--timeout',type=float,default=120);p.add_argument('--strategy-profile',type=Path);p.add_argument('--metareasoning',action='store_true');a=p.parse_args()
    from strategy_profile import load
    print(json.dumps(run(a.state,read_json(a.config)['worker'],a.attempts,a.seconds,a.timeout,load(a.strategy_profile),a.metareasoning),indent=2))
if __name__=='__main__':main()
