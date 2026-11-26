# Release audit regression evidence

Run from the repository root on a POSIX shell:

    PYTHONPATH=tests:. python -m unittest $(ls tests/test_*.py | sed 's@tests/@@;s@.py@@' | head -15)
    PYTHONPATH=tests:. python -m unittest $(ls tests/test_*.py | sed 's@tests/@@;s@.py@@' | tail -n +16)

First batch: 160 tests in 27.372 seconds, OK.
Second batch: 157 tests in 14.319 seconds, OK.
These two disjoint module lists cover all 29 test modules, 317 tests total. Both commands completed normally. The focused proof-audit module passed 13 tests in 0.127 seconds.

Remote CI, external live-model performance and independent fresh-chat validation are separate gates. The audit uses the existing exact replay functions and is not formal verification by a theorem-proving kernel.
