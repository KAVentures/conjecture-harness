import json, tempfile, unittest, subprocess, sys, shutil
from pathlib import Path
from project import initialize, seal, validate

ROOT=Path(__file__).resolve().parents[1]
class PackageTests(unittest.TestCase):
    def test_scaffold(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'result'; initialize(p,'test-result','Claim: 100% & x_y $','Example & Author')
            self.assertEqual(validate(p)['files'],14)
            self.assertFalse(validate(p)['mathematical_certification'])
            self.assertIn(r'Example \& Author',(p/'paper/paper.tex').read_text())
            self.assertIn(r'100\%',(p/'paper/paper.tex').read_text())
            self.assertEqual(json.loads((p/'STATUS.json').read_text())['research_status'],'in_progress')
            with self.assertRaises(ValueError): initialize(p,'test-result','new')
    def test_missing_author(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r'; initialize(p,'r','claim')
            self.assertIn('confirmation pending',(p/'AUTHORSHIP.md').read_text())
    def test_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r'; initialize(p,'r','claim'); (p/'target.json').write_text('{"id":"r","statement":"different"}')
            with self.assertRaises(ValueError):validate(p)
    def test_extra_missing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r'; initialize(p,'r','claim'); (p/'extra').touch()
            with self.assertRaises(ValueError): validate(p)
            (p/'extra').unlink(); (p/'research/REVIEW.md').unlink()
            with self.assertRaises(ValueError):seal(p)
    def test_secret_and_status(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r'; initialize(p,'r','claim'); (p/'.env').touch()
            with self.assertRaises(ValueError):seal(p)
            (p/'.env').unlink(); (p/'STATUS.json').write_text('{"research_status":"solved","novelty":"novel","verification":[],"human_review":"pending"}')
            with self.assertRaises(ValueError):seal(p)
    def test_bad_id(self):
        with tempfile.TemporaryDirectory() as d:
            for x in ['../x','A','a/b','']:
                with self.assertRaises(ValueError):initialize(Path(d)/'r',x,'claim')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r'; initialize(p,'r','claim')
            try: (p/'link').symlink_to(p/'target.json')
            except (OSError,NotImplementedError): self.skipTest('symlinks unavailable')
            with self.assertRaises(ValueError):seal(p)
    def test_known_control_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'control'; shutil.copytree(ROOT/'examples/known-star',p)
            self.assertFalse(validate(p)['mathematical_certification'])
            out=subprocess.check_output([sys.executable,str(p/'repro/verify.py')],text=True)
            self.assertEqual(json.loads(out),json.loads((p/'repro/actual.txt').read_text()))
            (p/'repro/witness.json').write_text('{"vertices":[0,1,2,3],"edges":[[0,1],[1,2],[2,3]]}')
            r=subprocess.run([sys.executable,str(p/'repro/verify.py')],capture_output=True)
            self.assertNotEqual(r.returncode,0)
            with self.assertRaises(ValueError):validate(p)
