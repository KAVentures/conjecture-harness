"""Rebuild the committed text-transfer bundle from exact upstream modules."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ["runtime.py", "combinatorial_cover.py", "finite_csp.py", "modular_discovery.py"]
HEADER = "#!/usr/bin/env python3\n\"\"\"Generated portable subset of Conjecture Harness. Do not edit by hand.\nReview the pinned source before execution. Standard library only.\n\"\"\"\nimport hashlib\nimport json\nfrom pathlib import Path\nimport subprocess\nimport sys\nimport tempfile\n\n"
FOOTER = "\n\ndef main():\n    # Keep module names isolated from the calling notebook and preserve caller cwd\n    # so relative experiment and state paths remain valid.\n    with tempfile.TemporaryDirectory(prefix=\"conjecture-portable-\") as tmp:\n        for name, source in SOURCES.items():\n            (Path(tmp) / name).write_bytes(source.encode(\"utf-8\"))\n        completed = subprocess.run([sys.executable, \"-E\", \"-s\",\n                                    str(Path(tmp) / \"portable_core.py\"), *sys.argv[1:]])\n        return completed.returncode\n\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n"


def render():
    sources = {name: (ROOT / "engine" / name).read_bytes().decode("utf-8")
               for name in MODULES}
    sources["portable_core.py"] = (ROOT / "chat" / "portable_core.py").read_bytes().decode("utf-8")
    return HEADER + "SOURCES = " + json.dumps(sources, ensure_ascii=False, separators=(",", ":")) + FOOTER


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    path = ROOT / "chat" / "portable.py"
    data = render().encode("utf-8")
    if args.check:
        if path.read_bytes() != data:
            p.exit(1, "Portable bundle is stale; run python chat/build.py\n")
    else:
        path.write_bytes(data)


if __name__ == "__main__":
    main()
