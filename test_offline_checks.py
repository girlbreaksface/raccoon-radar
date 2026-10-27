"""Temporary fixtures verify the guard stops access before side effects."""
import hashlib
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from offline_checks import OfflineGuard


class OfflineGuardTests(unittest.TestCase):
    def test_temporary_sqlite_transactions_are_allowed(self):
        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            with closing(sqlite3.connect(Path(folder) / "synthetic.sqlite3")) as db:
                db.execute("CREATE TABLE synthetic (value INTEGER)")
                db.execute("INSERT INTO synthetic VALUES (1)")
                db.commit()
                self.assertEqual(db.execute("SELECT value FROM synthetic").fetchone(), (1,))

    def test_existing_database_outside_guard_is_never_opened_or_changed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sentinel = root / "synthetic-sentinel.sqlite3"
            with closing(sqlite3.connect(sentinel)) as db:
                db.execute("CREATE TABLE sentinel (value INTEGER)")
                db.commit()
            before = hashlib.sha256(sentinel.read_bytes()).hexdigest()
            allowed = root / "allowed"
            allowed.mkdir()
            with OfflineGuard(allowed), self.assertRaises(PermissionError):
                sqlite3.connect(sentinel)
            self.assertEqual(hashlib.sha256(sentinel.read_bytes()).hexdigest(), before)

    def test_outside_database_is_not_created_and_guard_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            allowed = root / "allowed"
            allowed.mkdir()
            target = root / "synthetic-blocked.sqlite3"
            with OfflineGuard(allowed), self.assertRaises(PermissionError):
                sqlite3.connect(target)
            self.assertFalse(target.exists())
            with closing(sqlite3.connect(target)):
                pass
            self.assertTrue(target.exists())

    def test_sqlite_uri_and_empty_path_cannot_bypass_root(self):
        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            for path in ("file::memory:?cache=shared", ""):
                with self.subTest(path=path), self.assertRaises(PermissionError):
                    sqlite3.connect(path, uri=True)
            with closing(sqlite3.connect(":memory:")) as db:
                self.assertEqual(db.execute("SELECT 1").fetchone(), (1,))

    def test_only_canonical_read_only_uri_inside_root_is_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic space.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE synthetic (value INTEGER)")
                db.commit()
            uri = path.resolve().as_uri() + "?mode=ro"
            with OfflineGuard(folder):
                with closing(sqlite3.connect(uri, uri=True)) as db:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM synthetic").fetchone(), (0,))
                    with self.assertRaises(sqlite3.OperationalError):
                        db.execute("INSERT INTO synthetic VALUES (1)")
                for suffix in ("?mode=rw", "?mode=ro&cache=shared"):
                    with self.subTest(suffix=suffix), self.assertRaises(PermissionError):
                        sqlite3.connect(path.resolve().as_uri() + suffix, uri=True)

    def test_local_opend_connection_is_blocked_before_connect(self):
        with tempfile.TemporaryDirectory() as folder, socket.socket() as sock:
            with OfflineGuard(folder), self.assertRaises(PermissionError):
                sock.connect(("127.0.0.1", 11111))

    def test_dns_and_subprocess_are_blocked(self):
        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            with self.assertRaises(PermissionError):
                socket.getaddrinfo("example.invalid", 80)
            with self.assertRaises(PermissionError):
                subprocess.run([sys.executable, "-c", "raise SystemExit(0)"], check=True)

    def test_exception_does_not_leave_guard_enabled(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            child = root / "allowed"
            child.mkdir()
            with self.assertRaises(RuntimeError):
                with OfflineGuard(child):
                    raise RuntimeError("synthetic failure")
            with closing(sqlite3.connect(root / "synthetic-after.sqlite3")):
                pass


if __name__ == "__main__":
    unittest.main()
