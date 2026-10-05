import os
import stat

import pytest

from gradientmine.store import Store, atomic_write


@pytest.mark.skipif(os.name != "posix", reason="Directory fsync is a POSIX durability guarantee")
def test_atomic_artifact_is_durable_before_database_commit(tmp_path, monkeypatch):
    events = []
    original_sync = os.fsync
    original_replace = os.replace

    def sync(fd):
        events.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
        original_sync(fd)

    def replace(source, destination):
        events.append("replace")
        original_replace(source, destination)

    monkeypatch.setattr(os, "fsync", sync)
    monkeypatch.setattr(os, "replace", replace)
    target = tmp_path / "artifact.json"
    atomic_write(target, b'{"artifact":1}')
    assert target.read_bytes() == b'{"artifact":1}'
    assert events == ["file", "replace", "directory"]


def test_store_transaction_rolls_back_and_enforces_foreign_keys(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    with pytest.raises(RuntimeError):
        with store.transaction() as db:
            db.execute("INSERT INTO jobs VALUES(?,?,?,?,?)", ("job", "creator", None, "hash", "{}"))
            raise RuntimeError("simulated process failure")
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
