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

def auto_discharge(g):
    g=auto_reuse(bridge_discharge(shift_discharge(polynomial_discharge(affine_discharge(auto_reuse(g))))))
    return auto_invent(auto_compose(auto_refine(g)))

def run(path,cmd,attempts,seconds,timeout):
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
            p=plan(g)
            if 'stop' in p:break
            folder=Path(tempfile.mkdtemp(prefix=str(len(g['history']))+'-',dir=log))
            data=prompt(g,p);(folder/'prompt.txt').write_text(data,encoding='utf-8')
            raw=invoke(cmd,data,min(timeout,remaining),folder)
            (folder/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
            try:
                if raw['returncode']:raise ValueError('worker failed')
                ops=strict_json(raw['stdout'])
                if not isinstance(ops,list):raise ValueError('expected list')
                h=record(g,p['mode'],p['focus'],ops)
            except (ValueError,TypeError,KeyError,RecursionError) as e:
                (folder/'rejected.txt').write_text(str(e),encoding='utf-8');h=record(g,p['mode'],p['focus'],[])
            save(path,h);g=h
        if time.monotonic()<deadline:
            h=auto_discharge(g)
            if h!=g:save(path,h);g=h
    return plan(g)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state',type=Path);p.add_argument('--config',type=Path,required=True);p.add_argument('--attempts',type=int,default=5);p.add_argument('--seconds',type=float,default=600);p.add_argument('--timeout',type=float,default=120);a=p.parse_args()
    print(json.dumps(run(a.state,read_json(a.config)['worker'],a.attempts,a.seconds,a.timeout),indent=2))
if __name__=='__main__':main()
