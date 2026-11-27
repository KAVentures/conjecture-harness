import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootstrap

ROOT = Path(__file__).resolve().parent
REV = "a" * 40


def archive(extra=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        prefix = "conjecture-harness-" + REV + "/"
        for name in ("HARNESS.md", "engine/activate.py", "engine/CAPABILITIES.json",
                     "engine/engine_readiness.py"):
            z.writestr(prefix + name, "fixture")
        if extra:
            z.writestr(extra, "bad")
    return buf.getvalue()


class TransportTests(unittest.TestCase):
    def test_pinned_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "engine"
            data = archive()
            r = bootstrap.unpack(data, REV, dest, hashlib.sha256(data).hexdigest())
            self.assertTrue(r["digest_compared"])
            self.assertTrue((dest / "engine" / "activate.py").is_file())
            with self.assertRaises(FileExistsError):
                bootstrap.unpack(data, REV, dest)

    def test_bad_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "engine"
            for data, revision, digest in (
                (archive("conjecture-harness-" + REV + "/../escape"), REV, None),
                (archive(), "b"*40, None), (archive(), REV, "0"*64),
            ):
                with self.assertRaises(ValueError):
                    bootstrap.unpack(data, revision, dest, digest)
                self.assertFalse(dest.exists())

    def test_portable(self):
        with tempfile.TemporaryDirectory() as tmp:
            def cli(*args):
                return json.loads(subprocess.check_output(
                    [sys.executable, str(ROOT / "portable.py"), *args], cwd=tmp))
            self.assertEqual(cli("selftest")["passed"], 4)
            self.assertEqual(cli("run", "--target", "universal prose claim",
                                 "--output", "state")["root_status"], "unverified")
            spec = {"kind": "cover", "items": 2, "rows": [[[0,1],[]]],
                    "resources": [], "max_pieces": 1}
            (Path(tmp) / "spec.json").write_text(json.dumps(spec))
            result = cli("solve", "--output", "state", "--kind", "cover", "--spec", "spec.json")
            self.assertEqual(result["latest"]["result"]["status"], "proved")
            self.assertEqual(cli("resume", "--output", "state")["root_status"], "unverified")
            self.assertEqual(cli("audit", "--output", "state")["replayed"], 1)
            typed = cli("run", "--target", result["latest"]["statement"], "--output", "typed")
            self.assertEqual(typed["root_status"], "unverified")
            self.assertEqual(cli("solve", "--output", "typed", "--kind", "cover",
                                 "--spec", "spec.json")["root_status"], "proved")


if __name__ == "__main__":
    unittest.main()
