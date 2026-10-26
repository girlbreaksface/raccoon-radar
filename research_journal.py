"""Append-only local research ledger. No order placement or account access."""
import json, sqlite3, hashlib
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from strategy_validation import DB_PATH

def initialize(path=DB_PATH):
    with closing(sqlite3.connect(path)) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS research_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, recorded_utc TEXT NOT NULL,
            candle_hash TEXT NOT NULL, candle_count INTEGER NOT NULL,
            event_count INTEGER NOT NULL, methodology TEXT NOT NULL,
            date_first TEXT, date_last TEXT, train_holdout_note TEXT,
            validation_json TEXT NOT NULL, weekday_json TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, recorded_utc TEXT NOT NULL,
            hypothesis TEXT NOT NULL, assessment TEXT NOT NULL,
            evidence TEXT NOT NULL, run_id INTEGER,
            FOREIGN KEY(run_id) REFERENCES research_runs(id))""")

def fingerprint(candles):
    h=hashlib.sha256()
    for row in sorted(candles,key=lambda r:(r['symbol'],r['time'])):
        h.update(json.dumps({k:row.get(k) for k in ('symbol','time','open','high','low','close','volume')},sort_keys=True,separators=(',',':')).encode())
        h.update(b'\n')
    return h.hexdigest()

def record_run(candles,events,validation_rows,weekday_rows,info,path=DB_PATH):
    initialize(path)
    dates=sorted({str(c['time'])[:10] for c in candles})
    method={'detector':'setup_detective.detect (source shipped in archive)',
        'spacing':'greedy 5-minute cooldown per symbol; alphabetical setup tie-break',
        'validation_window_et':'09:40-11:30','holdout':'last 2 observed sessions; fixed chronological split',
        'outcome':'ETF directional close-to-close 3-minute percent; not options returns',
        'warning':'Exploratory. Correlated SPY/QQQ, repeated sessions, lookahead selection and retesting risks.'}
    with closing(sqlite3.connect(path)) as db:
        cur=db.execute('INSERT INTO research_runs (recorded_utc,candle_hash,candle_count,event_count,methodology,date_first,date_last,train_holdout_note,validation_json,weekday_json) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(timespec='seconds'),fingerprint(candles),len(candles),len(events),json.dumps(method,sort_keys=True),dates[0] if dates else '',dates[-1] if dates else '',info,json.dumps(validation_rows),json.dumps(weekday_rows)))
        db.commit()
        return cur.lastrowid

def record_note(hypothesis,assessment,evidence,run_id=None,path=DB_PATH):
    if not hypothesis.strip(): raise ValueError('Hypothesis cannot be blank')
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        cur=db.execute('INSERT INTO research_notes (recorded_utc,hypothesis,assessment,evidence,run_id) VALUES (?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(timespec='seconds'),hypothesis.strip(),assessment,evidence.strip(),run_id))
        db.commit()
        return cur.lastrowid

def get_runs(path=DB_PATH):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        return [dict(r) for r in db.execute('SELECT * FROM research_runs ORDER BY id DESC')]

def get_notes(path=DB_PATH):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        return [dict(r) for r in db.execute('SELECT * FROM research_notes ORDER BY id DESC')]

def export_json(path=DB_PATH):
    return {'schema_version':1,'runs':get_runs(path),'notes':get_notes(path)}
