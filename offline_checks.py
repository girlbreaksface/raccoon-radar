"""Guarded offline release checks. No provider or user research DB is required."""
import ast
import hashlib
import json
import os
import platform
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from contextvars import ContextVar
from urllib.parse import urlsplit
from urllib.request import url2pathname


_MANAGED_CONNECT = ContextVar("raccoon_managed_sqlite_connect", default=False)


def _sqlite_authorizer(action, first, second, database, trigger):
    """Permanent conservative SQL policy for each managed connection."""
    if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
                  sqlite3.SQLITE_CREATE_VTABLE, sqlite3.SQLITE_DROP_VTABLE):
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA:
        name = (first or "").lower()
        if name in ("temp_store_directory", "data_store_directory"):
            return sqlite3.SQLITE_DENY
        if name == "temp_store" and second is not None and str(second).lower() not in ("2", "memory"):
            return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and (second or "").lower() in (
            "load_extension", "readfile", "writefile"):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


class OfflineGuard:
    """Scoped Python-side checks, not a general filesystem sandbox.

    New connections must pass through the managed wrapper. They keep a
    conservative authorizer for their lifetime, including after context exit.
    Existing foreign handles, malicious Python/native code and arbitrary file
    writes are outside the guarantee. Enter before test discovery/connections.
    """
    def __init__(self, temporary_root):
        self.root = Path(temporary_root).resolve()
        self.active = False

    def _audit(self, event, args):
        if not self.active:
            return
        if ((event.startswith("socket.") and event != "socket.__new__")
                or event in ("urllib.Request", "subprocess.Popen", "os.system",
                             "os.posix_spawn", "os.spawn",
                             "sqlite3.enable_load_extension", "sqlite3.load_extension")):
            raise PermissionError("Offline checks prohibit network, child processes and extensions")
        if event == "sqlite3.connect":
            if not _MANAGED_CONNECT.get():
                raise PermissionError("SQLite connection aliases must use the managed connect wrapper")
            raw = os.fsdecode(os.fspath(args[0]))
            if raw == ":memory:":
                return
            if not raw:
                raise PermissionError("Offline checks prohibit empty SQLite paths")
            if raw.lower().startswith("file:"):
                try:
                    parts = urlsplit(raw)
                    if parts.query != "mode=ro" or parts.netloc or parts.fragment:
                        raise ValueError("Unexpected URI options")
                    candidate = Path(url2pathname(parts.path)).resolve()
                    if raw != candidate.as_uri() + "?mode=ro":
                        raise ValueError("Noncanonical URI")
                except (ValueError, OSError) as exc:
                    raise PermissionError("Only canonical read-only temporary SQLite URIs are allowed") from exc
            else:
                candidate = Path(raw).resolve()
            if not candidate.is_relative_to(self.root):
                raise PermissionError("Offline checks prohibit SQLite outside the temporary root")

    def __enter__(self):
        if self.active:
            raise RuntimeError("OfflineGuard is already active")
        previous = sqlite3.connect

        def managed_connect(*args, **kwargs):
            factory = kwargs.get("factory", args[5] if len(args) > 5 else sqlite3.Connection)
            if factory is not sqlite3.Connection:
                raise PermissionError("Custom SQLite factories can run before SQL policy installation")
            token = _MANAGED_CONNECT.set(True)
            try:
                connection = previous(*args, **kwargs)
            finally:
                _MANAGED_CONNECT.reset(token)
            try:
                # The connect/handle audit event fires before Connection.__init__
                # finishes, so authorizer setup must happen after connect returns.
                sqlite3.Connection.execute(connection, "PRAGMA temp_store=MEMORY")
                sqlite3.Connection.set_authorizer(connection, _sqlite_authorizer)
            except BaseException:
                connection.close()
                raise
            return connection

        self._previous_connect = previous
        self._wrapper = managed_connect
        sys.addaudithook(self._audit)
        self.active = True
        sqlite3.connect = managed_connect
        return self

    def __exit__(self, *exc):
        if sqlite3.connect is self._wrapper:
            sqlite3.connect = self._previous_connect
        self.active = False


def main():
    """Syntax/hash inventory plus guarded discovery; returns nonzero on failure."""
    project = Path(__file__).resolve().parent
    sys.dont_write_bytecode = True
    sources = {}
    try:
        for path in sorted(project.glob("*.py")):
            raw = path.read_bytes()
            ast.parse(raw.decode("utf-8-sig"), filename=str(path))
            sources[path.name] = hashlib.sha256(raw).hexdigest()
    except (SyntaxError, UnicodeError, OSError) as exc:
        print(f"Source check failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "python": platform.python_version(), "platform": platform.system(),
        "sqlite": sqlite3.sqlite_version, "source_sha256": sources,
        "limitations": "Offline regression evidence only; no GUI/provider/market verification.",
    }, sort_keys=True), flush=True)
    previous_tempdir = tempfile.tempdir
    # Install before discovery so test imports cannot open project DB defaults.
    with tempfile.TemporaryDirectory(prefix="raccoon-offline-") as root:
        try:
            tempfile.tempdir = root
            with OfflineGuard(root):
                suite = unittest.defaultTestLoader.discover(
                    str(project), pattern="test_*.py", top_level_dir=str(project))
                count = suite.countTestCases()
                if not count:
                    print("No tests discovered", file=sys.stderr)
                    return 1
                result = unittest.TextTestRunner(verbosity=2).run(suite)
        finally:
            tempfile.tempdir = previous_tempdir
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
