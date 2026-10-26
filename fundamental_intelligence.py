"""Read-only SEC EDGAR research snapshots. No trading or predictions."""
import json, sqlite3, re, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from contextlib import closing
DB_PATH=Path(__file__).resolve().parent/'raccoon_fundamentals.sqlite3'
HEADERS={'Accept':'application/json','Accept-Encoding':'identity'}

def initialize(path=DB_PATH):
    with closing(sqlite3.connect(path)) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL, fetched_utc TEXT NOT NULL, cik TEXT NOT NULL, company TEXT NOT NULL, data_json TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS evidence_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL, created_utc TEXT NOT NULL, category TEXT NOT NULL, assessment TEXT NOT NULL, source_url TEXT NOT NULL, note TEXT NOT NULL)''')
        db.commit()

def _get(url,agent):
    if not agent or '@' not in agent or len(agent)<12: raise ValueError('Enter a contact User-Agent such as RaccoonRadar/1.5 your-email@example.com for SEC requests.')
    req=urllib.request.Request(url,headers={**HEADERS,'User-Agent':agent})
    with urllib.request.urlopen(req,timeout=18) as resp:
        if resp.status!=200: raise RuntimeError('SEC HTTP '+str(resp.status))
        return json.load(resp)

def _metric(facts,names):
    us=facts.get('facts',{}).get('us-gaap',{})
    for name in names:
        units=us.get(name,{}).get('units',{}).get('USD',[])
        valid=[x for x in units if x.get('form') in ('10-K','10-Q') and x.get('filed') and x.get('end') and isinstance(x.get('val'),(int,float))]
        if not valid:continue
        # Prefer latest filed report, then latest period; avoid treating 10-Q YTD cash flows as quarterly values.
        valid.sort(key=lambda x:(x['filed'],x['end'],x.get('accn','')),reverse=True)
        x=valid[0]
        return {'name':name,'value':x['val'],'end':x['end'],'filed':x['filed'],'form':x['form'],'accession':x.get('accn',''),'start':x.get('start','')}
    return None

def fetch(ticker,agent):
    ticker=ticker.strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,11}',ticker):raise ValueError('Invalid ticker')
    mapping=_get('https://www.sec.gov/files/company_tickers.json',agent)
    matches=[v for v in mapping.values() if str(v.get('ticker','')).upper()==ticker]
    if not matches:raise ValueError('Ticker not found in SEC company mapping. Not all ETFs/foreign issuers report companyfacts.')
    item=matches[0];cik=str(item['cik_str']).zfill(10)
    submissions=_get(f'https://data.sec.gov/submissions/CIK{cik}.json',agent)
    facts=_get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',agent)
    recent=submissions.get('filings',{}).get('recent',{})
    filings=[]
    for i,form in enumerate(recent.get('form',[])):
        if form not in ('10-K','10-Q','8-K','S-3','S-1','424B5','424B2','DEF 14A','4'):continue
        acc=recent['accessionNumber'][i];primary=recent['primaryDocument'][i]
        filings.append({'form':form,'filed':recent['filingDate'][i], 'accession':acc,'url':f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{primary}"})
        if len(filings)>=20:break
    metrics={
      'Cash and cash equivalents':_metric(facts,['CashAndCashEquivalentsAtCarryingValue','CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']),
      'Current assets':_metric(facts,['AssetsCurrent']),
      'Current liabilities':_metric(facts,['LiabilitiesCurrent']),
      'Total assets':_metric(facts,['Assets']),
      'Total liabilities':_metric(facts,['Liabilities']),
      'Operating cash flow (reported period)':_metric(facts,['NetCashProvidedByUsedInOperatingActivities']),
      'Net income (reported period)':_metric(facts,['NetIncomeLoss']),
      'Shares outstanding':None,
    }
    # Shares are typically reported in shares, not USD.
    shares=facts.get('facts',{}).get('dei',{}).get('EntityCommonStockSharesOutstanding',{}).get('units',{}).get('shares',[])
    if shares:
        shares=[x for x in shares if x.get('filed') and x.get('end') and isinstance(x.get('val'),(int,float))]
        if shares:
            x=sorted(shares,key=lambda x:(x['filed'],x['end']),reverse=True)[0]
            metrics['Shares outstanding']={'value':x['val'],'end':x['end'],'filed':x['filed'],'form':x.get('form',''),'accession':x.get('accn','')}
    return {'ticker':ticker,'cik':cik,'company':submissions.get('name',item.get('title',ticker)),'fetched_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'filings':filings,'metrics':metrics,'sources':{'submissions':f'https://data.sec.gov/submissions/CIK{cik}.json','companyfacts':f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'}}

def save_snapshot(data,path=DB_PATH):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.execute('INSERT INTO snapshots(ticker,fetched_utc,cik,company,data_json) VALUES(?,?,?,?,?)',(data['ticker'],data['fetched_utc'],data['cik'],data['company'],json.dumps(data)))
        db.commit()

def latest(ticker,path=DB_PATH):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        row=db.execute('SELECT data_json FROM snapshots WHERE ticker=? ORDER BY id DESC LIMIT 1',(ticker.strip().upper(),)).fetchone()
        return json.loads(row[0]) if row else None

def add_note(ticker,category,assessment,url,note,path=DB_PATH):
    if not ticker.strip() or not note.strip():raise ValueError('Ticker and note are required')
    if assessment not in ('Unverified','Supported','Concern','Needs review'):raise ValueError('Invalid assessment')
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.execute('INSERT INTO evidence_notes(ticker,created_utc,category,assessment,source_url,note) VALUES(?,?,?,?,?,?)',(ticker.strip().upper(),datetime.now(timezone.utc).isoformat(timespec='seconds'),category.strip(),assessment,url.strip(),note.strip()))
        db.commit()

def list_notes(ticker,path=DB_PATH):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT created_utc,category,assessment,source_url,note FROM evidence_notes WHERE ticker=? ORDER BY id DESC',(ticker.strip().upper(),)).fetchall()
