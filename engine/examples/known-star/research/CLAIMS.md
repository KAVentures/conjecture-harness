# Claims
- C1: The star is connected (each leaf adjacent to vertex 0).
- C2: A leaf cannot be internal to a simple path, since it has only one neighbor.
- C3: Three leaves require three distinct endpoints, impossible for a path. Thus C1–C2 refute the control statement.
- C4: Exhaustive enumeration checks C3 for this exact graph; see repro/verify.py and actual log.
