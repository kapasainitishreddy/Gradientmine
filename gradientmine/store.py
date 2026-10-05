"""Single-instance durable store with transactional state changes and uniqueness constraints."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from .crypto import canonical


def atomic_write(path: Path, value: bytes, mode: int = 0o600):
    import uuid

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(value)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class Store:
    def __init__(self, path: Path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, creator TEXT NOT NULL,
                    idempotency_key TEXT, request_hash TEXT NOT NULL, document TEXT NOT NULL,
                    UNIQUE(creator,idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
                    worker TEXT NOT NULL, document TEXT NOT NULL, UNIQUE(job_id,worker)
                );
                CREATE TABLE IF NOT EXISTS nonces (
                    nonce TEXT PRIMARY KEY, address TEXT NOT NULL, message TEXT NOT NULL,
                    expires REAL NOT NULL, used INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,address TEXT NOT NULL,expires REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT,created REAL,kind TEXT,message TEXT
                );
                CREATE INDEX IF NOT EXISTS submission_job ON submissions(job_id);
                CREATE INDEX IF NOT EXISTS event_job ON events(job_id,seq);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None, factory=ClosingConnection)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def job(db, job_id):
        row = db.execute("SELECT document FROM jobs WHERE id=?", (job_id,)).fetchone()
        return json.loads(row["document"]) if row else None

    @staticmethod
    def save_job(db, job):
        db.execute("UPDATE jobs SET document=? WHERE id=?", (canonical(job).decode(), job["id"]))

    @staticmethod
    def submissions(db, job_id):
        return [
            json.loads(row["document"])
            for row in db.execute("SELECT document FROM submissions WHERE job_id=? ORDER BY id", (job_id,))
        ]

    @staticmethod
    def save_submission(db, submission):
        db.execute(
            "UPDATE submissions SET document=? WHERE id=?", (canonical(submission).decode(), submission["id"])
        )

    @staticmethod
    def event(db, job_id, now, kind, message):
        db.execute(
            "INSERT INTO events(job_id,created,kind,message) VALUES(?,?,?,?)", (job_id, now, kind, message)
        )
