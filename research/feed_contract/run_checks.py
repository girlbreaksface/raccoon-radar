from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from offline_checks import OfflineGuard
sys.path.insert(0,str(Path(__file__).resolve().parent))
with tempfile.TemporaryDirectory(prefix='synthetic-feed-') as temp:
    with OfflineGuard(temp):
        suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='test_adapter.py')
        result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
