"""Optional CLI adapters. Requires installed, authenticated provider CLI; not live-tested here."""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument('backend',choices=['codex','claude']); p.add_argument('--model'); a=p.parse_args()
    prompt=sys.stdin.read()
    if a.backend=='codex':
        with tempfile.TemporaryDirectory() as d:
            answer=Path(d)/'answer.json'
            cmd=['codex','exec','--skip-git-repo-check','--sandbox','read-only','--output-last-message',str(answer)]
            if a.model:cmd+=['--model',a.model]
            cmd+=['-']
            result=subprocess.run(cmd,input=prompt,text=True,stdout=sys.stderr)
            if result.returncode:sys.exit(result.returncode)
            if not answer.exists():sys.exit('Codex did not produce a final message')
            print(answer.read_text())
    else:
        cmd=['claude','-p','--output-format','text']
        if a.model:cmd+=['--model',a.model]
        result=subprocess.run(cmd,input=prompt,text=True)
        sys.exit(result.returncode)
if __name__=='__main__': main()
