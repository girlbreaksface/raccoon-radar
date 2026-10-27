# Issue #3: offline baseline validation

## Change
The migration test's synthetic legacy fixture used a SQLite transaction context, which commits/rolls back but leaves the connection open. Keep that transaction context inside contextlib.closing so the handle closes before TemporaryDirectory cleanup. No production module or database schema is changed.

The existing Python 3.11 workflow now runs independent ubuntu-latest and windows-latest jobs with fail-fast disabled. Each job compiles source and discovers all test_*.py files. It requires no optional broker packages, service access, credentials or user databases.

## Commands and observed results
On Windows with Python 3.12.14:
```text
python -B -m unittest discover -v -p "test_*.py"
python -m compileall -q .
```
Before the fix: four passed, test_migration failed on WinError 32 during temporary-directory cleanup. After the fix: all five passed and compilation succeeded. Persistence tests explicitly use disposable test.sqlite3 paths inside TemporaryDirectory, never module default/user store paths.

PR #1 was reviewed at commit a18b3e63c3c34025177985ebb196b831cfd4cca6. Its five tests cover complete start-labeled ranges, missing 09:30, full-session end-label evidence remaining provisional, an interior gap, and invalid OHLC. The exact test_market_intelligence.py content was fetched from that commit and executed as a separate in-memory module alongside discovery on this fix: all ten tests passed. No PR #1 files or market calculations are copied into this branch.

To reproduce that combined check from a Git checkout containing PR #1's commit, run the following with Python (fetch the PR ref first if needed):
```python
import subprocess
import types
import unittest

source = subprocess.run(
    ["git", "show",
     "a18b3e63c3c34025177985ebb196b831cfd4cca6:test_market_intelligence.py"],
    check=True, capture_output=True, text=True,
).stdout
parallel_tests = types.ModuleType("pr1_test_market_intelligence")
exec(compile(source, "PR1/test_market_intelligence.py", "exec"),
     parallel_tests.__dict__)
suite = unittest.TestSuite([
    unittest.defaultTestLoader.discover(".", pattern="test_*.py"),
    unittest.defaultTestLoader.loadTestsFromModule(parallel_tests),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
```

## Platform and scope limits
There is no local Linux/WSL installation; Linux validation runs through the new GitHub Actions matrix. Python 3.11 Windows/Linux CI results are recorded in the PR, separately from local Python 3.12.14 results. Until PR #1 merges, ordinary CI on this branch discovers five tests; the ten-test combined check above accounts for the parallel branch without coupling CI to another PR.

Opening-range fixtures are synthetic regression checks, not independent proof of provider timestamp semantics. They do not currently test conditional evidence wording, report formatting, fetch filtering, pagination, or input immutability; those remain future work. No GUI, OpenD, SEC, real research database or trading behavior was exercised. Nothing is merged by this change.
