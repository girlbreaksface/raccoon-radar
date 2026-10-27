import unittest, tempfile, sqlite3
from contextlib import closing
from pathlib import Path
from datetime import date,timedelta
from volume_discovery import evaluate,save_results,list_results,list_snapshots

class VolumeTests(unittest.TestCase):
 def bars(self,n=51):
  return [dict(time_key=(date(2026,1,1)+timedelta(days=i)).isoformat(),open=10,high=11,low=9,close=10,volume=100 if i<n-1 else 200) for i in range(n)]
 def test_ratios(self):
  r=evaluate('TEST',self.bars());self.assertAlmostEqual(r['rvol'],2);self.assertAlmostEqual(r['rvol50'],2);self.assertAlmostEqual(r['avg_dollar_volume20'],1000)
 def test_insufficient_50(self):
  r=evaluate('TEST',self.bars(21));self.assertIsNone(r['rvol50'])
 def test_bad_candle(self):
  bars=self.bars();bars[-1]['high']=5;self.assertEqual(evaluate('TEST',bars),None)
 def test_preserve_snapshots(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.sqlite3';r=evaluate('TEST',self.bars());save_results([r],p);save_results([r],p)
   self.assertEqual(len(list_results(p)),1);self.assertEqual(len(list_snapshots(p)),2)
 def test_migration(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.sqlite3'
   # Keep transaction commit/rollback, then explicitly close before temp cleanup.
   with closing(sqlite3.connect(p)) as db, db:
    db.execute('CREATE TABLE discoveries (id INTEGER PRIMARY KEY, scan_utc TEXT NOT NULL, symbol TEXT NOT NULL, session TEXT NOT NULL, close REAL NOT NULL, volume REAL NOT NULL, baseline_volume REAL NOT NULL, rvol REAL NOT NULL, change_pct REAL, range_pct REAL, notes TEXT NOT NULL, UNIQUE(symbol,session))')
    db.execute("INSERT INTO discoveries(scan_utc,symbol,session,close,volume,baseline_volume,rvol,notes) VALUES('old','TEST','2026-01-01',10,100,100,1,'legacy')")
   save_results([evaluate('NEW',self.bars())],p)
   self.assertEqual(len(list_results(p)),2)
if __name__=='__main__':unittest.main()
