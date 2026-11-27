import copy,unittest
import experiment_dispatch as ed

class ExperimentTests(unittest.TestCase):
    def request(self):
        return dict(operation="modular",budget=16,spec=dict(variables=1,modulus=2,assumptions=[],conclusion=dict(terms=[[[2],1],[[1],-1]],allowed=[0])))
    def test_receipt_and_tamper(self):
        r=ed.execute(self.request())
        self.assertEqual(r["outcome"]["status"],"captured")
        self.assertEqual(r["outcome"]["result"]["status"],"proved")
        self.assertTrue(ed.replay(r))
        t=copy.deepcopy(r);t["request"]["budget"]=1
        self.assertFalse(ed.replay(t))
        t=copy.deepcopy(r);t["outcome"]["result"]["certificate"]["count"]=1
        self.assertFalse(ed.replay(t))
    def test_allowlist_and_bounds(self):
        with self.assertRaises(ValueError):ed.execute(dict(self.request(),operation="python"))
        with self.assertRaises(ValueError):ed.execute(dict(self.request(),budget=999999))
        with self.assertRaises(ValueError):ed.execute(self.request(),seconds=0)
    def test_unknown(self):
        r=ed.execute(dict(self.request(),budget=1))
        self.assertEqual(r["outcome"]["result"]["status"],"unknown")
        self.assertTrue(ed.replay(r))
