import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('activation_score',Path(__file__).resolve().parents[1]/'evaluation/activation_v1/score.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class ScoreTests(unittest.TestCase):
    def test_paired_design(self):
        rows=[dict(target='x',arm=a,verdict='partial',reviewer='r',trace_observed=False,
                   verified_lemmas=1,meaningful_pivots=0,tool_calls=0) for a in mod.ARMS]
        self.assertEqual(mod.score(rows)['arms']['legacy']['reviewed_solved'],0)
        with self.assertRaises(ValueError):mod.score(rows[:-1])
        with self.assertRaises(ValueError):mod.score(rows+[rows[0]])
