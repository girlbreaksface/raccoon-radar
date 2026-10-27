"""Regression tests for SQL-level file-opening escapes; synthetic stores only."""
import _sqlite3
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from offline_checks import OfflineGuard


class SQLiteSQLGuardTests(unittest.TestCase):
    def fixture(self, root):
        outside = root / "synthetic-external.sqlite3"
        with closing(sqlite3.connect(outside)) as db:
            db.execute("CREATE TABLE sentinel(value)")
            db.execute("INSERT INTO sentinel VALUES ('unchanged')")
            db.commit()
        allowed = root / "allowed"
        allowed.mkdir()
        return allowed, outside

    def test_attach_existing_external_fixture_is_denied_and_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            allowed, outside = self.fixture(Path(folder))
            before = hashlib.sha256(outside.read_bytes()).hexdigest()
            with OfflineGuard(allowed), closing(sqlite3.connect(allowed / "main.sqlite3")) as db:
                with self.assertRaises(sqlite3.DatabaseError):
                    db.execute("ATTACH DATABASE ? AS escaped", (str(outside),))
                self.assertEqual([row[1] for row in db.execute("PRAGMA database_list")], ["main"])
            self.assertEqual(hashlib.sha256(outside.read_bytes()).hexdigest(), before)

    def test_attach_literals_expressions_and_scripts_cannot_create_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            allowed = root / "allowed"
            allowed.mkdir()
            with OfflineGuard(allowed), closing(sqlite3.connect(":memory:")) as db:
                for index, variant in enumerate(("parameter", "expression", "script")):
                    target = root / f"synthetic-attach-{index}.sqlite3"
                    literal = "'" + str(target).replace("'", "''") + "'"
                    with self.subTest(variant=variant):
                        with self.assertRaises(sqlite3.DatabaseError):
                            if variant == "parameter":
                                db.execute("ATTACH ? AS escaped", (str(target),))
                            elif variant == "expression":
                                db.execute("ATTACH (" + literal + " || '') AS escaped")
                            else:
                                db.executescript("/* synthetic */ aTtAcH DATABASE " + literal + " AS escaped;")
                        self.assertFalse(target.exists())

    def test_vacuum_into_parameter_expression_and_literal_cannot_create_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            allowed = root / "allowed"
            allowed.mkdir()
            with OfflineGuard(allowed), closing(sqlite3.connect(allowed / "main.sqlite3")) as db:
                db.execute("CREATE TABLE synthetic(value)")
                db.commit()
                for index, variant in enumerate(("parameter", "expression", "literal")):
                    target = root / f"synthetic-vacuum-{index}.sqlite3"
                    literal = "'" + str(target).replace("'", "''") + "'"
                    with self.subTest(variant=variant):
                        with self.assertRaises(sqlite3.DatabaseError):
                            if variant == "parameter":
                                db.execute("VACUUM INTO ?", (str(target),))
                            else:
                                expression = "(" + literal + " || '')" if variant == "expression" else literal
                                db.execute("VACUUM main INTO " + expression)
                        self.assertFalse(target.exists())

    def test_vacuum_into_cannot_populate_existing_empty_external_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            allowed = root / "allowed"
            allowed.mkdir()
            external = root / "synthetic-empty.sqlite3"
            external.touch()
            with OfflineGuard(allowed), closing(sqlite3.connect(":memory:")) as db:
                with self.assertRaises(sqlite3.DatabaseError):
                    db.execute("VACUUM INTO ?", (str(external),))
            self.assertEqual(external.read_bytes(), b"")

    def test_policy_retained_for_connection_lifetime_and_nested_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with OfflineGuard(root):
                with OfflineGuard(root):
                    db = sqlite3.connect(":memory:")
                with closing(db):
                    with self.assertRaises(sqlite3.DatabaseError):
                        db.execute("ATTACH ':memory:' AS escaped")
            # A connection opened under the guard retains its SQL restrictions.
            with OfflineGuard(root):
                db = sqlite3.connect(":memory:")
            with closing(db), self.assertRaises(sqlite3.DatabaseError):
                db.execute("VACUUM INTO ?", (str(root / "synthetic-after.sqlite3"),))
            self.assertFalse((root / "synthetic-after.sqlite3").exists())

    def test_raw_connection_alias_cannot_skip_authorizer_installation(self):
        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            with self.assertRaises(PermissionError):
                with closing(_sqlite3.connect(":memory:")):
                    pass

    def test_directory_pragmas_file_functions_and_virtual_tables_are_denied(self):
        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            with closing(sqlite3.connect(":memory:")) as db:
                called = []
                for name in ("readfile", "writefile"):
                    db.create_function(name, 1, lambda value: called.append(value))
                for statement in ("PRAGMA temp_store=FILE",
                                  "PRAGMA temp_store_directory='.'",
                                  "PRAGMA data_store_directory='.'",
                                  "SELECT load_extension('synthetic-never-load')",
                                  "SELECT readfile('synthetic-never-read')",
                                  "SELECT writefile('synthetic-never-write')",
                                  "CREATE VIRTUAL TABLE synthetic USING fts5(value)"):
                    with self.subTest(sql=statement):
                        with self.assertRaises(sqlite3.DatabaseError) as exc:
                            db.execute(statement)
                        self.assertIn("not authorized", str(exc.exception).lower())
                self.assertEqual(called, [])
                self.assertEqual(db.execute("PRAGMA temp_store").fetchone(), (2,))
                if hasattr(db, "enable_load_extension"):
                    with self.assertRaises(PermissionError):
                        db.enable_load_extension(True)

    def test_custom_factory_cannot_execute_before_sql_policy_installation(self):
        called = []

        def factory(*args, **kwargs):
            called.append(True)
            return sqlite3.Connection(*args, **kwargs)

        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            with self.assertRaises(PermissionError):
                with closing(sqlite3.connect(":memory:", factory=factory)):
                    pass
        self.assertEqual(called, [])

    def test_regular_transactions_and_backup_between_guarded_fixtures_still_work(self):
        with tempfile.TemporaryDirectory() as folder, OfflineGuard(folder):
            with closing(sqlite3.connect(":memory:")) as source:
                source.execute("CREATE TABLE synthetic(value)")
                source.execute("INSERT INTO synthetic VALUES (7)")
                source.commit()
                with closing(sqlite3.connect(Path(folder) / "synthetic-backup.sqlite3")) as target:
                    source.backup(target)
                    self.assertEqual(target.execute("SELECT value FROM synthetic").fetchone(), (7,))


if __name__ == "__main__":
    unittest.main()
