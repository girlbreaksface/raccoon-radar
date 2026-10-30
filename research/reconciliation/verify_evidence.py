"""Exact evidence reproduction under the existing offline guard."""
from pathlib import Path
import json
import sys
import tempfile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from offline_checks import OfflineGuard
from compare import evidence

with tempfile.TemporaryDirectory(prefix='synthetic-evidence-') as temp:
    with OfflineGuard(temp):
        actual=evidence()
        expected=json.loads((HERE/'evidence.json').read_text(encoding='utf-8'))
        assert json.loads(json.dumps(actual))==expected, 'Evidence changed: investigate, do not overwrite to hide a failure'
print('Exact synthetic evidence reproduced: '+str(len(actual['cases']))+' case variants')
