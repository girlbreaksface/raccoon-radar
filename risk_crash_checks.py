"""Explicit process crash test, separate from the no-child-process root guard."""
import subprocess
import sys
import tempfile
from pathlib import Path
from durable_daily_risk import Ledger
from test_durable_daily_risk import ACCOUNT, LIMITS, ORIGIN, NOW


def check():
    with tempfile.TemporaryDirectory(prefix='fictional-risk-crash-') as tmp:
        path=Path(tmp)/'synthetic.sqlite3'
        ledger=Ledger(path,ACCOUNT,LIMITS,create=True)
        try:
            ledger.append(ORIGIN,now=NOW)
            before=dict(ledger.receipt)
        finally: ledger.close()
        code="import sqlite3,os,sys; d=sqlite3.connect(sys.argv[1]); d.execute('BEGIN IMMEDIATE'); d.execute('DELETE FROM events'); os._exit(7)"
        p=subprocess.run([sys.executable,'-B','-c',code,str(path)],capture_output=True,timeout=20)
        if p.returncode != 7: raise AssertionError('Crash subprocess failed')
        reopened=Ledger(path,ACCOUNT,LIMITS,checkpoint=before)
        try:
            if reopened.state(NOW)['trades'] != 0: raise AssertionError('Rollback failed')
        finally: reopened.close()
    print('PASS: process death before commit rolls back; independent receipt accepted')


if __name__ == '__main__': check()
