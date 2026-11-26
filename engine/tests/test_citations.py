import json, tempfile, unittest
from pathlib import Path
import citations, project, discovery_citation

class CitationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'result'; project.initialize(self.root,'result','Example statement')
        self.r={'key':'smith2020','type':'article','authors':['Smith, Jane'],'title':'A theorem & proof','year':2020,'venue':'Example Journal','doi':'10.1234/test','role':'theorem','state':'checked','checked_on':'2026-11-26','locator':'Theorem 2','evidence':'Synthetic fixture, not a real source'}
    def ledger(self, records):
        (self.root/'research/references.json').write_text(json.dumps({'schema':1,'references':records}))
    def paper_cite(self,key):
        p=self.root/'paper/paper.tex'; p.write_text(p.read_text().replace(r'\input{references.tex}',r'\cite{'+key+'}\n'+r'\input{references.tex}'))
    def test_exports_and_manifest(self):
        self.ledger([self.r]); self.paper_cite('smith2020'); citations.generate(self.root); project.seal(self.root)
        self.assertEqual(citations.check(self.root)['cited_keys'],['smith2020']);self.assertFalse(citations.check(self.root)['source_truth_certified'])
        self.assertIn('author = {Smith, Jane}',(self.root/'paper/references.bib').read_text()); self.assertIn(r'A theorem \& proof',(self.root/'paper/references.tex').read_text());project.validate(self.root)
    def test_unknown_key(self):
        self.paper_cite('missing');self.assertRaises(ValueError,project.seal,self.root)
    def test_unverified_excluded(self):
        r=dict(self.r,state='unverified');r.pop('checked_on');self.ledger([r]);citations.generate(self.root);self.assertEqual((self.root/'paper/references.bib').read_text(),'');self.paper_cite(r['key']);self.assertRaises(ValueError,citations.check,self.root)
    def test_duplicate_keys(self):
        self.ledger([self.r,dict(self.r,key='SMITH2020',doi='10.1234/other')]);self.assertRaises(ValueError,citations.generate,self.root)
    def test_duplicate_doi(self):
        self.ledger([self.r,dict(self.r,key='smith2',doi='10.1234/TEST')]);self.assertRaises(ValueError,citations.generate,self.root)
    def test_evidence_required(self):
        for field in ['locator','checked_on','evidence']:
            r=dict(self.r);r.pop(field);self.ledger([r]);self.assertRaises(ValueError,citations.generate,self.root)
    def test_bad_date_doi_url(self):
        for updates in [{'checked_on':'2026-02-30'},{'doi':'fake'},{'url':'file:///etc/passwd'},{'url':'https://user:pw@example.com'}]:
            self.ledger([dict(self.r,**updates)]);self.assertRaises(ValueError,citations.generate,self.root)
    def test_stale_bibliography(self):
        self.ledger([self.r]);citations.generate(self.root);(self.root/'paper/references.bib').write_text('tampered');self.assertRaises(ValueError,project.seal,self.root)
    def test_corporate_author(self):
        r=dict(self.r,authors=['Example Organization'],corporate_authors=['Example Organization']);self.ledger([r]);citations.generate(self.root);self.assertIn('author = {{Example Organization}}',(self.root/'paper/references.bib').read_text())
    def test_discovery_cff(self):
        meta={'title':'Example result','authors':[{'given-names':'Jane','family-names':'Smith'}],'repository-code':'https://github.com/example/result','version':'1.0'}
        p=discovery_citation.generate(self.root,meta);self.assertEqual(json.loads(p.read_text())['cff-version'],'1.2.0');project.seal(self.root);project.validate(self.root);self.assertRaises(FileExistsError,discovery_citation.generate,self.root,meta)
    def test_discovery_reject_placeholder(self):
        self.assertRaises(ValueError,discovery_citation.build,{'title':'[Title]','authors':[{'name':'[Author]'}],'repository-code':'https://example.com'})
