"""Local manual swing research watchlist. No market feed, predictions or orders."""
import sqlite3, re, csv
from pathlib import Path
from datetime import datetime, timezone
from contextlib import closing
DB_PATH=Path(__file__).resolve().parent/'raccoon_swing.sqlite3'
FIELDS=('ticker','direction','status','source','thesis','catalyst','filings','cashflow','liquidity','invalidation')

def initialize(path=DB_PATH):
    with closing(sqlite3.connect(path)) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS swing_cases (id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL, updated_utc TEXT NOT NULL, ticker TEXT NOT NULL, direction TEXT NOT NULL, status TEXT NOT NULL, source TEXT NOT NULL, thesis TEXT NOT NULL, catalyst TEXT NOT NULL, filings TEXT NOT NULL, cashflow TEXT NOT NULL, liquidity TEXT NOT NULL, invalidation TEXT NOT NULL)""")
        db.commit()

def save_case(values,case_id=None,path=DB_PATH):
    ticker=values['ticker'].strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,11}',ticker):raise ValueError('Enter a valid ticker (letters, numbers, dot or hyphen).')
    if values['direction'] not in ('Bullish','Bearish','Undecided'):raise ValueError('Invalid direction')
    if values['status'] not in ('Investigating','Watching','Rejected','Archived'):raise ValueError('Invalid status')
    cleaned={k:(ticker if k=='ticker' else str(values.get(k,'')).strip()[:10000]) for k in FIELDS}
    initialize(path)
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    with closing(sqlite3.connect(path)) as db:
        if case_id is None:
            db.execute('INSERT INTO swing_cases (created_utc,updated_utc,'+','.join(FIELDS)+') VALUES ('+','.join(['?']*(len(FIELDS)+2))+')',[now,now]+[cleaned[k] for k in FIELDS])
        else:
            result=db.execute('UPDATE swing_cases SET updated_utc=?, '+', '.join(k+'=?' for k in FIELDS)+' WHERE id=?',[now]+[cleaned[k] for k in FIELDS]+[case_id])
            if result.rowcount!=1:raise ValueError('Case not found')
        db.commit()

def list_cases(path=DB_PATH):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        return [dict(r) for r in db.execute('SELECT * FROM swing_cases ORDER BY updated_utc DESC,id DESC')]

def export_csv(destination,path=DB_PATH):
    rows=list_cases(path)
    with open(destination,'w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=('id','created_utc','updated_utc')+FIELDS)
        writer.writeheader();writer.writerows(rows)
