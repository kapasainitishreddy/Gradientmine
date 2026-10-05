"""Audit the installed inventory, including CPU PyTorch's upstream release.

PyPI advisories describe torch's upstream version, not its +cpu wheel label.
Only that known build label is normalized. The local application is reviewed
as source rather than substituted with an unrelated PyPI package.
"""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
import re
import subprocess
import sys


def inventory(distributions=None):
    packages = {}
    for distribution in distributions if distributions is not None else metadata.distributions():
        name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
        if name == "gradientmine":
            continue
        version = distribution.version
        if name == "torch" and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\+cpu", version):
            version = version.removesuffix("+cpu")
        if not re.fullmatch(r"[A-Za-z0-9.!_-]+", version):
            raise ValueError(f"Cannot map {name}'s build version to an advisory release: {version}")
        if name in packages and packages[name] != version:
            raise ValueError(f"Conflicting installed versions for {name}")
        packages[name] = version
    return "".join(f"{name}=={version}\n" for name, version in sorted(packages.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path(".local/pip-audit-cache"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    requirements = args.out.with_suffix(".requirements.txt")
    requirements.write_text(inventory())
    # Every installed transitive dependency is already pinned in this inventory;
    # resolving it again would download a different non-CPU torch distribution.
    return subprocess.run([
        sys.executable, "-m", "pip_audit", "--progress-spinner", "off", "--format", "json",
        "--cache-dir", str(args.cache_dir), "--no-deps", "--disable-pip", "-r", str(requirements),
        "--output", str(args.out),
    ], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
