import json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
import literature_discovery as l
import polynomial as p
from discovery import new,closure
from proof_audit import audit

class LiteratureTests(unittest.TestCase):
    def setUp(self):
        self.d=l.document('https://arxiv.org/abs/1234.56789','Synthetic fixture','p. 1','If x is nonnegative, then x cubed is nonnegative.')
        self.row=dict(theorem=dict(variables=['x'],domain='real',assumptions=[dict(relation='nonnegative',terms=[[[1],1]])],conclusion=[[[3],1]]),excerpt=self.d['text'],locator='Lemma 1',relevance='Synthetic control')
        self.target=p.statement(dict(variables=['x'],domain='real',relation='nonnegative',terms=[[[6],1]]))
    def test_atom(self):
        raw=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/1234.56789</id><title>Test</title><summary>Test abstract</summary></entry></feed>'
        self.assertEqual(l.parse_atom(raw,1)[0]['locator'],'arXiv abstract')
        with self.assertRaises(ValueError):l.parse_atom(b'<!DOCTYPE foo>',1)
    def test_extract_and_apply(self):
        raw=dict(returncode=0,stdout=json.dumps([self.row,dict(self.row,excerpt='fabricated')]))
        with tempfile.TemporaryDirectory() as td,patch.object(l,'invoke',return_value=raw):
            r=l.extract(self.target,[self.d],[sys.executable],Path(td)/'out',calls=2)
        self.assertEqual(len(r['leads']),1);self.assertEqual(r['calls'],1)
        g,count=l.apply_leads(new(self.target),[self.d],r['leads'])
        self.assertEqual(count,1);self.assertNotIn('goal',closure(g))
        self.assertEqual(audit(g)['status'],'unverified')
        self.assertTrue(audit(g)['checked_edges'])
    def test_tampering(self):
        x=l.lead(self.d,0,self.d['text'],self.row)
        self.assertTrue(l.verify_lead(x,[self.d]))
        self.assertFalse(l.verify_lead(dict(x,offset=1),[self.d]))
        with self.assertRaises(ValueError):l.apply_leads(new(self.target),[self.d],[dict(x,excerpt='fake')])
    def test_chunk_offsets(self):
        d=l.document('local','title','p. 1','a'*10000+'b'*1000)
        cs=list(l.chunks(d))
        self.assertEqual(cs[1][0],9500)
        self.assertEqual(cs[1][1],d['text'][9500:])
