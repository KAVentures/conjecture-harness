"""Run the exact discovery adapters without invoking any external model."""
import argparse,json,math,time
from pathlib import Path
from discovery import check,plan,save
from discovery_run import auto_discharge
from harness import coordinator_lock
from runtime import read_json


def run(path,passes=8,seconds=60):
    if type(passes) is not int or not 1<=passes<=100 or type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=0:raise ValueError('invalid limits')
    path=Path(path).resolve();log=path.with_name(path.name+'.runs');log.mkdir(exist_ok=True)
    with coordinator_lock(log):
        g=check(read_json(path,limit=32*1024*1024));deadline=time.monotonic()+seconds;count=0;reason='pass_limit'
        while count<passes:
            if 'stop' in plan(g):reason='closed';break
            if time.monotonic()>=deadline:reason='time_limit';break
            h=auto_discharge(g);count+=1
            if h==g:reason='fixed_point';break
            save(path,h);g=h
        result=plan(g)
        if 'stop' in result:reason='closed'
    return dict(passes=count,reason=reason,model_calls=0,next=result)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('state',type=Path);p.add_argument('--passes',type=int,default=8);p.add_argument('--seconds',type=float,default=60);a=p.parse_args()
    print(json.dumps(run(a.state,a.passes,a.seconds),indent=2))
if __name__=='__main__':main()
