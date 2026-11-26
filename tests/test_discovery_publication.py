import json
import tempfile
import unittest
from pathlib import Path
import project
import discovery_citation as d

class PublicationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root=Path(t.name)/'result'; project.initialize(self.root,'result','A statement')
        self.meta={'title':'A research package','paper-title':'A manuscript','authors':[{'given-names':'Jane','family-names':'Smith'}],'repository-code':'https://github.com/example/result','paper-url':'https://github.com/example/result/blob/main/paper/paper.tex','version':'1.0','year':2026}
    def test_publication_requires_citation(self):
        with self.assertRaises(ValueError): project.validate(self.root,publication=True)
    def test_all_exports(self):
        d.generate(self.root,self.meta);project.seal(self.root);project.validate(self.root,publication=True)
        cff=json.loads((self.root/'CITATION.cff').read_text());self.assertEqual(cff['preferred-citation']['type'],'unpublished');self.assertEqual(cff['preferred-citation']['title'],'A manuscript')
        self.assertIn('@misc{researchpaper,',(self.root/'CITATION.bib').read_text());self.assertIn('@misc{researchpackage,',(self.root/'CITATION.bib').read_text())
    def test_drift(self):
        d.generate(self.root,self.meta);(self.root/'CITATION.bib').write_text('modified')
        with self.assertRaises(ValueError): project.seal(self.root)
    def test_distinct_dois(self):
        with self.assertRaises(ValueError): d.build(dict(self.meta,doi='10.1234/abc',**{'paper-doi':'10.1234/ABC'}))
    def test_paper_url_rejects_credentials(self):
        with self.assertRaises(ValueError): d.build(dict(self.meta,**{'paper-url':'https://user:password@example.com'}))
    def test_no_fabricated_doi(self):
        cff=d.build(self.meta);self.assertNotIn('doi',cff);self.assertNotIn('doi',cff['preferred-citation'])
    def test_partial_export(self):
        (self.root/'CITATION.md').write_text('stale')
        with self.assertRaises(FileExistsError): d.generate(self.root,self.meta)
