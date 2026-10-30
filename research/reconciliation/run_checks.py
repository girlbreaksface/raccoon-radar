"""Guarded isolated runner. Execute from repository root with Python 3.11+."""
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from offline_checks import OfflineGuard
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE/'vendor'))

with tempfile.TemporaryDirectory(prefix='synthetic-reconciliation-') as temp:
    with OfflineGuard(temp):
        suite=unittest.TestSuite()
        suite.addTests(unittest.defaultTestLoader.discover(str(HERE),pattern='test_comparison.py'))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName('test_market_structure_v12'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
