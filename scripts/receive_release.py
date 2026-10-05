"""Apply an authenticated-repository delivery only after exact whole-payload and per-file checks.
Transport exists because the authoring runtime cannot reach git over its network.
"""

import base64
import bz2
import hashlib
import json
from pathlib import Path


def receive(root=Path(".")):
    meta = json.loads((root / ".delivery/release.json").read_text())
    if meta["format"] != "gradientmine.source-delivery.v1":
        raise ValueError("Unknown delivery format")
    joined = "".join((root / ".delivery" / name).read_text().strip() for name in meta["chunks"])
    compressed = base64.b64decode(joined, validate=True)
    if hashlib.sha256(compressed).hexdigest() != meta["sha256"]:
        raise ValueError("Delivery checksum mismatch; source left untouched")
    source = json.loads(bz2.decompress(compressed))
    if len(source) > 150:
        raise ValueError("Too many source files")
    paths = set()
    for item in source:
        name = item["path"]
        if (
            name in paths
            or name.startswith("/")
            or any(part in ("..", ".git", ".local", ".delivery") for part in Path(name).parts)
        ):
            raise ValueError("Unsafe or duplicate source path")
        paths.add(name)
        path = root / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
            raise ValueError("Symlink source paths are not permitted")
        old = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if old != item["old_sha256"]:
            raise ValueError(f"Concurrent modification or unexpected source baseline: {name}")
        raw = item["content"].encode("utf-8")
        if len(raw) > 400_000 or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError(f"New source integrity failure: {name}")
    for item in source:
        path = root / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["content"], encoding="utf-8")
    print(f"Applied {len(source)} exact, hash-verified source files for {meta['cycle']}")
    return source


if __name__ == "__main__":
    receive()
