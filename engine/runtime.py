"""Bounded subprocess execution and deterministic, strict JSON utilities.
Trusted commands only: process containment is not a security sandbox.
"""
import json
import math
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

MAX_JSON = 2 * 1024 * 1024


def strict_json(s):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError(f'duplicate JSON key: {k}')
            out[k] = v
        return out
    def invalid(x):
        raise ValueError(f'nonfinite JSON number: {x}')
    def finite(x):
        y=float(x)
        if not math.isfinite(y): return invalid(x)
        return y
    return json.loads(s, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite)


def invoke(cmd, prompt_text, timeout, cwd, output_limit=MAX_JSON):
    """Use disk-backed streams, monitor limits, terminate POSIX process groups.

    The size limit is polled, not an OS quota. Child processes that deliberately
    escape a process group are outside this containment boundary.
    """
    start = time.monotonic()
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        inp.write(prompt_text.encode('utf-8')); inp.seek(0)
        try:
            p = subprocess.Popen(cmd, stdin=inp, stdout=out, stderr=err, cwd=cwd,
                                 start_new_session=(os.name == 'posix'))
        except OSError as e:
            return dict(returncode=127, stdout='', stderr=str(e), elapsed=0, termination='spawn_error')
        reason = None
        def stop():
            try:
                if os.name == 'posix': os.killpg(p.pid, signal.SIGKILL)
                elif p.poll() is None: p.kill()
            except ProcessLookupError:
                pass
            p.wait()
        try:
            while True:
                if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > output_limit:
                    reason = 'output_limit'; break
                if time.monotonic() - start >= timeout:
                    reason = 'timeout'; break
                if p.poll() is not None: break
                time.sleep(min(.02, timeout))
        finally:
            # Also kill descendants left behind by a successful wrapper on POSIX.
            stop()
        out.seek(0); err.seek(0)
        stdout = out.read(output_limit).decode('utf-8', errors='replace')
        stderr = err.read(max(0,output_limit-len(stdout.encode('utf-8')))).decode('utf-8', errors='replace')
        if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > output_limit:
            reason = 'output_limit'
        return dict(returncode=124 if reason == 'timeout' else 125 if reason else p.returncode,
                    stdout=stdout, stderr=stderr, elapsed=round(time.monotonic()-start, 3), termination=reason)


def read_json(path, limit=MAX_JSON):
    with Path(path).open('rb') as f:
        b = f.read(limit + 1)
    if len(b) > limit: raise ValueError(f'JSON exceeds limit: {path}')
    return strict_json(b.decode('utf-8'))
