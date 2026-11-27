"""Acquire a pinned full harness checkout without git or third-party packages.

This is transport, not authorization to execute downloaded code. Review the
trusted revision before running its engine. No network except the explicit
GitHub archive request; --archive supports a host-provided download.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import urllib.request
import zipfile

MAX_BYTES = 64 * 1024 * 1024
MAX_FILES = 4000
REPO = "KAVentures/conjecture-harness"


def unpack(data, revision, destination, expected_sha256=None):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("pin a full lowercase Git commit SHA")
    if len(data) > MAX_BYTES:
        raise ValueError("archive size limit")
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("archive digest mismatch")
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    prefix = "conjecture-harness-" + revision
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if len(members) > MAX_FILES or sum(m.file_size for m in members) > MAX_BYTES:
            raise ValueError("expanded archive limit")
        seen = set()
        files = []
        for m in members:
            p = PurePosixPath(m.filename)
            if (not p.parts or p.parts[0] != prefix or p.is_absolute()
                    or ".." in p.parts or "\\" in m.filename
                    or any(":" in x for x in p.parts)
                    or stat.S_ISLNK(m.external_attr >> 16)):
                raise ValueError("unsafe or unexpected archive member")
            relative = p.parts[1:]
            if not relative:
                if not m.is_dir():
                    raise ValueError("invalid archive root")
                continue
            if relative in seen:
                raise ValueError("duplicate archive member")
            seen.add(relative)
            if not m.is_dir():
                files.append((m, relative))
        required = {("HARNESS.md",), ("engine", "activate.py"),
                    ("engine", "CAPABILITIES.json"), ("engine", "engine_readiness.py")}
        if not required.issubset({p for _, p in files}):
            raise ValueError("not a full harness archive")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
            stage = Path(tmp) / "checkout"
            stage.mkdir()
            for m, relative in files:
                out = stage.joinpath(*relative)
                out.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(m) as source, out.open("xb") as target:
                    shutil.copyfileobj(source, target)
            provenance = {"revision": revision, "archive_sha256": digest,
                          "digest_compared": expected_sha256 is not None,
                          "scope": "Transport receipt; not code review or proof."}
            (stage / ".harness-transport.json").write_text(json.dumps(provenance, indent=2))
            if destination.exists():
                raise FileExistsError(destination)
            stage.rename(destination)
    return dict(provenance, checkout=str(destination))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--archive", help="already downloaded ZIP")
    parser.add_argument("--sha256", help="expected archive digest, if independently available")
    a = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.revision):
        parser.error("pin a full lowercase Git commit SHA")
    if a.sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", a.sha256):
        parser.error("expected a lowercase SHA-256")
    try:
        if a.archive:
            with open(a.archive, "rb") as source:
                data = source.read(MAX_BYTES + 1)
        else:
            url = f"https://codeload.github.com/{REPO}/zip/{a.revision}"
            with urllib.request.urlopen(url, timeout=20) as response:
                data = response.read(MAX_BYTES + 1)
        print(json.dumps(unpack(data, a.revision, a.output, a.sha256), indent=2))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Full engine transport failed: {exc}. See chat/README.md for connector fallback.\n")


if __name__ == "__main__":
    main()
