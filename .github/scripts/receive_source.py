"""Recover an explicitly hash-pinned source patch from the offline build environment."""
import base64
import bz2
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path('.delivery')
manifest = json.loads((root / 'manifest.json').read_text())
assert manifest['cycle'] == 1
assert manifest['sha256'] == '2de3cbd7a987a2f3596ba3c0189aa1900102730df2184723e7ccc7e90a891114'
parts = []
for index, expected in enumerate(manifest['chunks']):
    value = (root / 'cycle-1' / f'{index:03}.b64').read_text('ascii')
    if index == 0:
        # Correct a known single-character transport insertion, then verify original Git blob.
        assert value.count('PUUqSHiZ6J6bL') == 1
        value = value.replace('PUUqSHiZ6J6bL', 'PUUqSHiZ6JbL', 1)
    encoded = value.encode('ascii')
    assert hashlib.sha1(b'blob ' + str(len(encoded)).encode() + b'\0' + encoded).hexdigest() == expected, f'Corrupt chunk {index}'
    parts.append(value)
compressed = base64.b64decode(''.join(parts), validate=True)
decoder = bz2.BZ2Decompressor()
patch = decoder.decompress(compressed, max_length=2_000_000)
assert decoder.eof and not decoder.unused_data
assert len(patch) == manifest['bytes']
assert hashlib.sha256(patch).hexdigest() == manifest['sha256']
actual_paths = []
for line in patch.decode().splitlines():
    if line.startswith('diff --git '):
        fields = line.split(' ')
        assert len(fields) == 4 and fields[2][2:] == fields[3][2:]
        actual_paths.append(fields[2][2:])
assert sorted(actual_paths) == sorted(manifest['paths'])
for path in actual_paths:
    assert path.startswith(('docs/', 'gradientmine/', 'tests/')) and '..' not in Path(path).parts
subprocess.run(['git', 'diff', '--exit-code', manifest['base'], 'HEAD', '--', *actual_paths], check=True)
subprocess.run(['git', 'apply', '--check', '--whitespace=nowarn', '-'], input=patch, check=True)
subprocess.run(['git', 'apply', '--index', '--whitespace=nowarn', '-'], input=patch, check=True)
compiled = Path(os.environ['COMPILED_ARTIFACT'])
lock = (compiled / 'program/Cargo.lock').read_bytes()
assert hashlib.sha256(lock).hexdigest() == '2c9bede09a0f5011194b229ed19664fca0176ab087238992d1a61ab62ff0bb49'
Path('program/Cargo.lock').write_bytes(lock)
subprocess.run(['git', 'add', 'program/Cargo.lock'], check=True)
program = (compiled / 'ci-evidence/sbf/gradientmine_escrow.so').read_bytes()
assert hashlib.sha256(program).hexdigest() == '6a19d26db5f7e5f4a67a021aa55d7f1984064718762bd17276a143745e6e18fb'
print(json.dumps({'source_patch_sha256': manifest['sha256'], 'source_paths': actual_paths, 'sbf_sha256': hashlib.sha256(program).hexdigest()}, indent=2))
