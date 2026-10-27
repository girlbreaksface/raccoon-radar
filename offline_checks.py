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


class OfflineGuard:
    """Catch accidental Python network/process/SQLite access, not hostile code.

    Audit hooks cannot be removed; exiting disables this instance's hook.
    SQLite is allowed only in the caller-owned temporary root or :memory:.
    URI filenames are deliberately rejected rather than ambiguously decoded.
    """
    def __init__(self, temporary_root):
        self.root = Path(temporary_root).resolve()
        self.active = False

    def _audit(self, event, args):
        if not self.active:
            return
        if ((event.startswith("socket.") and event != "socket.__new__")
                or event in ("urllib.Request", "subprocess.Popen", "os.system",
                             "os.posix_spawn", "os.spawn")):
            raise PermissionError("Offline checks prohibit network and child processes")
        if event == "sqlite3.connect":
            raw = os.fsdecode(os.fspath(args[0]))
            if raw == ":memory:":
                return
            if (not raw or raw.lower().startswith("file:")
                    or not Path(raw).resolve().is_relative_to(self.root)):
                raise PermissionError("Offline checks prohibit SQLite outside the temporary root")

    def __enter__(self):
        # Do not stack the same instance's hook on accidental re-entry.
        if self.active:
            raise RuntimeError("OfflineGuard is already active")
        sys.addaudithook(self._audit)
        self.active = True
        return self

    def __exit__(self, *exc):
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
