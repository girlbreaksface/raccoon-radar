"""Raccoon Radar visual dashboard v0.3 â€” offline, read-only.
Python standard library only. No brokerage connection or order code.
"""
import csv
import json
import zipfile
import io
from datetime import timedelta
from price_action_engine import load_ohlcv, analyze
from setup_detective import detect, summary
import subprocess
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Raccoon Radar | Research Dashboard v1.5.12')
        self.geometry('1250x820')
        self.minsize(940, 650)
        self.configure(bg='#151724')
        self.active = False
        self.scanner_proc = None
        self.scanner_path = None
        self.scanner_events = queue.Queue()
        self.scanner_errors = 0
        self.csv_path = None
        self.trade_path = None
        self.last_mtimes = {}
        self.signal_rows = []  # Raw CSV rows remain inspectable, never assumed verified.
        self.refresh_ms = 5000
        self.candle_queue = queue.Queue()
        self.candle_busy = False
        self.live_candles = False
        self.last_ohlcv = []
        self.validation_events = []
        self.rolling_rows = []
        self.daily_validation_rows = []
        self.latest_run_id = None
        self.detective_events = []
        self.filtered_events = []
        self.deoverlap = tk.BooleanVar(value=True)
        self.last_candle_ts = None
        self.last_fetch_at = None
        self.range_start = tk.StringVar(value=(datetime.now()-timedelta(days=7)).date().isoformat())
        self.range_end = tk.StringVar(value=(datetime.now()-timedelta(days=1)).date().isoformat())
        self.after(350, self.process_candle_events)
        self.build()
        self.after(self.refresh_ms, self.poll)
        self.after(250, self.process_scanner_events)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview', background='#23263a', foreground='#f2f1fb', fieldbackground='#23263a', rowheight=27, borderwidth=0)
        style.configure('Treeview.Heading', background='#343752', foreground='white', font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected','#6952a2')])
        top = tk.Frame(self, bg='#151724'); top.pack(fill='x', padx=22, pady=(10, 3))
        tk.Label(top, text='RACCOON RADAR', bg='#151724', fg='#f4efff', font=('Segoe UI', 20, 'bold')).pack(side='left')
        tk.Label(top, text='v1.5.12  |  COMPACT LAYOUT  |  NO ORDERS', bg='#151724', fg='#b8a3df', font=('Segoe UI', 10, 'bold')).pack(side='right')
        tk.Label(self, text='A visual home for your SPY / QQQ research. Load your existing CSV to inspect recorded observations.', bg='#151724', fg='#b7b8cb', font=('Segoe UI', 11)).pack(anchor='w', padx=24, pady=(0, 5))
        strip = tk.Frame(self, bg='#151724'); strip.pack(fill='x', padx=20)
        self.status = self.tile(strip, 'MODE', 'OFFLINE / IDLE', 0)
        self.rows_label = self.tile(strip, 'ROWS LOADED', '0', 1)
        self.spy_label = self.tile(strip, 'SPY VERIFIED BIAS', 'UNAVAILABLE', 2)
        self.qqq_label = self.tile(strip, 'QQQ VERIFIED BIAS', 'UNAVAILABLE', 3)
        scanner_controls = tk.Frame(self, bg='#151724'); scanner_controls.pack(fill='x', padx=23, pady=(4,0))
        self.scanner_label = tk.Label(scanner_controls, text='SCANNER: STOPPED', bg='#151724', fg='#b8a3df', font=('Segoe UI', 10, 'bold'))
        self.scanner_label.pack(side='left', padx=(0,15))
        self.button(scanner_controls, 'Start scanner', self.start_scanner, bg='#276653').pack(side='left', padx=(0,10))
        self.button(scanner_controls, 'Stop scanner', self.stop_scanner, bg='#703f57').pack(side='left', padx=(0,10))
        self.button(scanner_controls, 'Choose scanner .py', self.choose_scanner).pack(side='left')
        controls = tk.Frame(self, bg='#151724'); controls.pack(fill='x', padx=23, pady=(4,2))
        self.button(controls, 'Analyze candle CSV', self.load_price_action, bg='#37547a').pack(side='left', padx=(0,8))
        self.button(controls, 'Fetch latest session', self.fetch_candles, bg='#276653').pack(side='left', padx=(0,8))
        self.button(controls, 'Setup detective', self.run_detective, bg='#37547a').pack(side='left', padx=(0,8))
        self.button(controls, 'Load signal CSV', self.load_csv).pack(side='left', padx=(0,8))
        self.button(controls, 'Load trade journal', self.load_trade_csv).pack(side='left')
        range_controls = tk.Frame(self, bg='#151724'); range_controls.pack(fill='x', padx=23, pady=(2,4))
        tk.Label(range_controls,text='From YYYY-MM-DD',bg='#151724',fg='#b7b8cb').pack(side='left')
        tk.Entry(range_controls,textvariable=self.range_start,width=12).pack(side='left',padx=(5,12))
        tk.Label(range_controls,text='To',bg='#151724',fg='#b7b8cb').pack(side='left')
        tk.Entry(range_controls,textvariable=self.range_end,width=12).pack(side='left',padx=(5,12))
        self.button(range_controls,'Fetch date range',self.fetch_range,bg='#276653').pack(side='left',padx=(0,8))
        self.button(range_controls,'Export research ZIP',self.export_research,bg='#54417d').pack(side='left',padx=(0,8))
        self.button(range_controls,'Start CSV refresh',self.start).pack(side='left',padx=(0,8))
        self.button(range_controls,'Stop monitoring',self.stop,bg='#703f57').pack(side='left')
        tk.Checkbutton(range_controls, text='De-overlap 5 min', variable=self.deoverlap, bg='#151724', fg='#d9c7ff', selectcolor='#343752', activebackground='#151724', activeforeground='white', font=('Segoe UI',9)).pack(side='left',padx=(10,0))
        validation_controls=tk.Frame(self,bg='#151724'); validation_controls.pack(fill='x',padx=23,pady=(0,6))
        self.button(validation_controls,'Load saved history',self.load_saved_history,bg='#276653').pack(side='left',padx=(0,8))
        self.button(validation_controls,'Run validation',self.run_validation,bg='#37547a').pack(side='left',padx=(0,8))
        self.button(validation_controls,'Export research archive',self.export_archive,bg='#54417d').pack(side='left',padx=(0,8))
        tk.Label(validation_controls,text='Window ET: 09:40–11:30  |  Holdout: last 2 sessions  |  Strict 5m symbol spacing',bg='#151724',fg='#b8a3df').pack(side='left')
        self.note = tk.StringVar(value='Scanner is stopped. This app may launch the existing read-only Moomoo scanner; no order APIs are used.')
        tk.Label(self, textvariable=self.note, bg='#151724', fg='#b8a3df', font=('Segoe UI', 10), wraplength=990, justify='left').pack(anchor='w', padx=24, pady=(0,4))
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True, padx=22, pady=(0,8))
        self.signals_frame = tk.Frame(self.tabs, bg='#23263a'); self.trades_frame = tk.Frame(self.tabs, bg='#23263a'); self.price_frame = tk.Frame(self.tabs, bg='#23263a'); self.detective_frame = tk.Frame(self.tabs, bg='#23263a'); self.period_frame = tk.Frame(self.tabs, bg='#23263a'); self.daily_frame = tk.Frame(self.tabs, bg='#23263a'); self.consistency_frame = tk.Frame(self.tabs, bg='#23263a')
        self.tabs.add(self.signals_frame, text='  Signal observations  ')
        self.tabs.add(self.trades_frame, text='  Shadow trade journal  ')
        self.tabs.add(self.price_frame, text='  Price action lab  ')
        self.tabs.add(self.detective_frame, text='  Setup detective  ')
        self.tabs.add(self.period_frame, text='  Time-of-day comparison  ')
        self.tabs.add(self.daily_frame, text='  Daily breakdown  ')
        self.tabs.add(self.consistency_frame, text='  Consistency  ')
        self.validation_frame=tk.Frame(self.tabs,bg='#23263a'); self.weekday_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.add(self.validation_frame,text='  Walk-forward holdout  ')
        self.tabs.add(self.weekday_frame,text='  Weekday study  ')
        self.rolling_frame=tk.Frame(self.tabs,bg='#23263a'); self.day_validation_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.add(self.rolling_frame,text='  Rolling validation  ')
        self.tabs.add(self.day_validation_frame,text='  Day-level outcomes  ')
        self.journal_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.add(self.journal_frame,text='  Research journal  ')
        self.signal_tree = self.tree(self.signals_frame, ['bar_time_et','symbol','close','bias','volume_ratio','pattern'])
        self.trade_tree = self.tree(self.trades_frame, ['entry','symbol','contract','side','exit','pnl','reason'])
        self.price_tree = self.tree(self.price_frame, ['time','symbol','close','auction_proxy','setup','range_ratio','volume_ratio'])
        self.detective_tree = self.tree(self.detective_frame, ['symbol','setup','events','1m_n','1m_winrate','1m_avg','3m_n','3m_winrate','3m_avg','5m_n','5m_winrate','5m_avg'])
        self.period_tree = self.tree(self.period_frame, ['symbol','period','setup','events','1m_n','1m_winrate','1m_avg','3m_n','3m_winrate','3m_avg','5m_n','5m_winrate','5m_avg'])
        self.daily_tree = self.tree(self.daily_frame, ['day','symbol','setup','events','sample','1m_n','1m_winrate','1m_avg','3m_n','3m_winrate','3m_avg','5m_n','5m_winrate','5m_avg'])
        self.consistency_tree = self.tree(self.consistency_frame, ['symbol','setup','events','sessions','positive_days_3m','days_with_3m','3m_daily_avg','3m_winrate','sample','warning'])
        self.validation_tree=self.tree(self.validation_frame,['symbol','setup','train_n','train_days','train_win_%','train_avg_%','test_n','test_days','test_win_%','test_avg_%','warning'])
        self.weekday_tree=self.tree(self.weekday_frame,['symbol','setup','weekday','events','sessions','win_%','avg_%','warning'])
        self.rolling_tree=self.tree(self.rolling_frame,['fold','symbol','setup','train_days','train_n','train_avg_%','test_first','test_last','test_n','test_avg_%','test_favorable_%','warning'])
        self.day_validation_tree=self.tree(self.day_validation_frame,['day','symbol','setup','n','favorable_%','avg_move_%','min_move_%','max_move_%'])
        self.build_journal()
        self.swing_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.add(self.swing_frame,text='  Swing opportunity desk  ')
        self.build_swing_desk()
        self.discovery_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.add(self.discovery_frame,text='  Volume discovery  ')
        self.build_discovery()
        self.fund_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.add(self.fund_frame,text='  SEC fundamentals  ')
        self.build_fundamentals()
        self.intelligence_frame=tk.Frame(self.tabs,bg='#23263a')
        self.tabs.insert(0,self.intelligence_frame,text='  Market intelligence  ')
        self.build_intelligence()
        foot = tk.Label(self, text='Research only. Candle proxies are exploratory, not validated signals. Option stops and daily limits cannot guarantee fills or maximum losses.', bg='#151724', fg='#8d90a9', font=('Segoe UI', 9))
        foot.pack(pady=(0,5))

    def build_intelligence(self):
        panel=self.intelligence_frame
        header=tk.Frame(panel,bg='#23263a');header.pack(fill='x',padx=12,pady=(12,4))
        tk.Label(header,text='MARKET INTELLIGENCE  |  SPY / QQQ  |  RESEARCH ONLY',bg='#23263a',fg='#d9c7ff',font=('Segoe UI',12,'bold')).pack(side='left')
        self.button(header,'Refresh from loaded candles',self.refresh_intelligence,bg='#276653').pack(side='right')
        self.button(header,"Fetch today's completed candles",self.fetch_candles,bg='#37547a').pack(side='right',padx=(0,8))
        self.button(header,'Verify provider candles',self.verify_provider_candles,bg='#5d4677').pack(side='right',padx=(0,8))
        tk.Label(panel,text='Uses saved or fetched completed regular-session candles. News, VIX, yields and breadth are NOT connected; no synthetic sentiment.',bg='#23263a',fg='#b7b8cb',wraplength=950,justify='left').pack(anchor='w',padx=12,pady=(0,6))
        self.intelligence_text=tk.Text(panel,bg='#181c2c',fg='#e7e7f5',insertbackground='white',font=('Consolas',10),wrap='word',borderwidth=0)
        self.intelligence_text.pack(fill='both',expand=True,padx=12,pady=(0,12))
        self.intelligence_text.insert('end','Load saved history or fetch today\'s completed candles, then click Refresh from loaded candles.\n\nNews sentiment: UNAVAILABLE (no verified source connected)\nEconomic events: UNAVAILABLE (no verified calendar connected)\nVIX / yields / breadth: UNAVAILABLE (no verified feed connected)')
        self.intelligence_text.config(state='disabled')

    def refresh_intelligence(self):
        """Prefer loaded candles, then independently read saved history without modifying it."""
        from market_intelligence import calculate,format_report
        import sqlite3
        try:
            rows=list(self.last_ohlcv or [])
            source='loaded memory'
            db=Path(__file__).resolve().parent/'raccoon_history.sqlite3'
            db_rows=[]
            if db.exists():
                with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as con:
                    con.row_factory=sqlite3.Row
                    db_rows=[dict(r) for r in con.execute('SELECT symbol,time,open,high,low,close,volume FROM candles ORDER BY symbol,time')]
            # Keep current-session fetched bars authoritative, supplement missing dates
            # from the persisted history. No database writes or fabricated candles.
            indexed={}
            for r in db_rows+rows:
                sym=str(r.get('symbol','')).upper().replace('US.','')
                key=(sym,str(r.get('time') or r.get('bar_time_et')))
                indexed[key]=r
            rows=list(indexed.values())
            source='loaded memory + read-only SQLite' if self.last_ohlcv and db_rows else ('read-only SQLite history' if db_rows else 'loaded memory')
            result=calculate(rows)
            message=format_report(result)
            message+='\n\nSOURCE: '+source+' | ROWS EXAMINED: '+str(len(rows))
            from zoneinfo import ZoneInfo
            today=datetime.now(ZoneInfo('America/New_York')).date().isoformat()
            sessions=[r.get('session') for r in result.values() if r.get('status')=='OK']
            if sessions and max(sessions)!=today:
                message+='\nSTALE DATA WARNING: latest session '+max(sessions)+'; today '+today+'. Do NOT use as today\'s opening range.'
            else:
                message+='\nDATA NOTE: snapshot of completed candles, NOT streaming; check last timestamp before trading.'
            if not any(r.get('status')=='OK' for r in result.values()):
                message+='\nDIAGNOSTIC: No valid SPY/QQQ candles parsed. Check project directory, database and candle timestamp format.'
            self.intelligence_text.config(state='normal')
            self.intelligence_text.delete('1.0','end')
            self.intelligence_text.insert('end',message)
            self.intelligence_text.config(state='disabled')
            self.tabs.select(self.intelligence_frame)
        except Exception as exc:
            messagebox.showerror('Market intelligence',f'{type(exc).__name__}: {exc}')

    def verify_provider_candles(self):
        """Compare read-only provider endpoints without modifying candle history."""
        if self.candle_busy:
            self.note.set('Another candle request is in progress.');return
        self.candle_busy=True
        self.note.set('Comparing provider candle endpoints (read-only)...')
        threading.Thread(target=self._verify_provider_worker,daemon=True).start()

    def _verify_provider_worker(self):
        q=None
        try:
            from moomoo import OpenQuoteContext, RET_OK, KLType, AuType
            from zoneinfo import ZoneInfo
            from collections import Counter
            import json
            now=datetime.now(ZoneInfo('America/New_York'))
            dates=['2026-10-23',now.date().isoformat()]
            q=OpenQuoteContext(host='127.0.0.1',port=11111)
            report={'requested_at_et':now.isoformat(timespec='seconds'), 'read_only':True,
                    'no_database_writes':True,'no_timestamp_shift':True,'results':{}}
            def describe(ret,data,page=None):
                e={'status':str(ret),'page_key_present':bool(page)}
                if ret!=RET_OK or not hasattr(data,'iterrows'):
                    e['error']=str(data)[:350];return e
                stamps=[str(row.get('time_key','')) for _,row in data.iterrows()]
                counts=Counter(x[11:16] for x in stamps if len(x)>=16)
                e.update(count=len(stamps),first=stamps[:6],last=stamps[-6:],
                         count_0930=counts.get('09:30',0),count_0931=counts.get('09:31',0),
                         count_1559=counts.get('15:59',0),count_1600=counts.get('16:00',0),
                         duplicates=len(stamps)-len(set(stamps)))
                for stamp in stamps:
                    if stamp.endswith('09:30:00') or stamp.endswith('09:31:00'):
                        row=data.loc[data['time_key'].astype(str)==stamp].iloc[0]
                        e.setdefault('opening_ohlcv',{})[stamp]={k:str(row.get(k,'')) for k in ('open','high','low','close','volume')}
                return e
            for sym in ('US.SPY','US.QQQ'):
                result={}
                for day in dates:
                    try:
                        # Use explicit dates and no app-side time filters.
                        ret,data,page=q.request_history_kline(sym,start=day,end=day,ktype=KLType.K_1M,max_count=1000)
                        e=describe(ret,data,page)
                        # Some OpenD responses paginate. Capture pages, don't assume one page is complete.
                        pages=[e];seen=set()
                        for _ in range(5):
                            if ret!=RET_OK or not page or str(page) in seen:break
                            seen.add(str(page))
                            ret,data,page=q.request_history_kline(sym,start=day,end=day,ktype=KLType.K_1M,max_count=1000,page_req_key=page)
                            pages.append(describe(ret,data,page))
                        result['historical_'+day]={'pages':pages,'page_limit_reached':bool(page) and len(pages)>=6}
                    except Exception as ex:
                        result['historical_'+day]={'error':type(ex).__name__+': '+str(ex)[:250]}
                try:
                    ret,data=q.get_cur_kline(sym,1000,KLType.K_1M,AuType.QFQ)
                    result['recent_candles']=describe(ret,data)
                except Exception as ex:
                    result['recent_candles']={'error':type(ex).__name__+': '+str(ex)[:250]}
                report['results'][sym]=result
            folder=Path(__file__).resolve().parent/'diagnostics_reports';folder.mkdir(exist_ok=True)
            path=folder/('raccoon_provider_verification_'+now.strftime('%Y%m%d_%H%M%S')+'.json')
            path.write_text(json.dumps(report,indent=2),encoding='utf-8')
            lines=['PROVIDER VERIFICATION — READ ONLY — '+now.isoformat(timespec='seconds')]
            for sym,items in report['results'].items():
                lines.append('\n'+sym)
                for key,item in items.items():
                    if 'pages' in item:
                        pages=item['pages'];count=sum(p.get('count',0) for p in pages)
                        has30=sum(p.get('count_0930',0) for p in pages)
                        first=next((p.get('first',[None])[0] for p in pages if p.get('first')),None)
                        lines.append(f'  {key}: bars={count}, 09:30={has30}, first={first}, pages={len(pages)}')
                        for pg in pages:
                            if pg.get('error'):lines.append('    ERROR: '+pg['error'])
                    else:
                        lines.append(f"  {key}: bars={item.get('count','?')}, 09:30={item.get('count_0930','?')}, first={item.get('first',[None])[0] if item.get('first') else '?'}, error={item.get('error','none')}")
            lines.append('\nSaved full OHLCV and pagination evidence: '+str(path))
            lines.append('No candles modified. 09:30 remains unverified until evidence supports it.')
            self.after(0,lambda: self._opening_feed_done('\n'.join(lines)))
        except Exception as exc:
            self.after(0,lambda message='Provider verification failed: '+type(exc).__name__+': '+str(exc): self._opening_feed_done(message))
        finally:
            if q is not None:
                try:q.close()
                except Exception:pass
            self.after(0,lambda:setattr(self,'candle_busy',False))

    def inspect_opening_feed(self):
        """Read-only raw OpenD 09:30 investigation, never writes research databases."""
        if self.candle_busy:
            self.note.set('Another candle request is in progress.');return
        self.candle_busy=True
        self.note.set('Inspecting raw OpenD opening candles (read-only)...')
        threading.Thread(target=self._inspect_opening_feed_worker,daemon=True).start()

    def _inspect_opening_feed_worker(self):
        q=None
        try:
            from moomoo import OpenQuoteContext, RET_OK, KLType
            from zoneinfo import ZoneInfo
            from collections import Counter
            import json
            now=datetime.now(ZoneInfo('America/New_York'))
            day=now.date().isoformat()
            q=OpenQuoteContext(host='127.0.0.1',port=11111)
            report={'requested_session':day,'requested_at_et':now.isoformat(timespec='seconds'),
                    'read_only':True,'note':'Raw provider timestamps before application filtering; no candle timestamps shifted.',
                    'symbols':{}}
            for symbol in ('US.SPY','US.QQQ'):
                ret,data,page=q.request_history_kline(symbol,start=day,end=day,ktype=KLType.K_1M,max_count=1000)
                entry={'request_status':str(ret),'pagination_key_present':bool(page)}
                if ret!=RET_OK or not hasattr(data,'iterrows'):
                    entry['error']=str(data)[:250]
                else:
                    stamps=[str(bar.get('time_key','')) for _,bar in data.iterrows()]
                    counts=Counter(x[11:16] for x in stamps if len(x)>=16)
                    entry.update(raw_count=len(stamps),first_timestamps=stamps[:12],
                                 last_timestamps=stamps[-5:],raw_0930_count=counts.get('09:30',0),
                                 raw_0931_count=counts.get('09:31',0),
                                 duplicate_timestamps=len(stamps)-len(set(stamps)),
                                 interpretation=('Provider response contains 09:30: check downstream filtering/storage.'
                                                 if counts.get('09:30') else
                                                 'Provider response itself has no 09:30. Do not shift 09:31; investigate source entitlement/provider behavior.'))
                report['symbols'][symbol]=entry
            folder=Path(__file__).resolve().parent/'diagnostics_reports';folder.mkdir(exist_ok=True)
            name='raccoon_opening_feed_'+now.strftime('%Y%m%d_%H%M%S')+'.json'
            path=folder/name;path.write_text(json.dumps(report,indent=2),encoding='utf8')
            summary='RAW OPENING FEED INSPECTION — '+day+'\n'
            for sym,entry in report['symbols'].items():
                summary+=f"{sym}: raw={entry.get('raw_count','error')}, 09:30={entry.get('raw_0930_count','?')}, 09:31={entry.get('raw_0931_count','?')}\n"
                summary+=entry.get('interpretation',entry.get('error',''))+'\n'
                summary+='First: '+', '.join(entry.get('first_timestamps',[])[:5])+'\n'
            summary+='\nSaved diagnostic: '+str(path)+'\nNo market levels were changed.'
            self.after(0,lambda: self._opening_feed_done(summary))
        except Exception as exc:
            error=f'Raw feed inspection failed: {type(exc).__name__}: {exc}'
            self.after(0,lambda: self._opening_feed_done(error))
        finally:
            if q is not None:
                try:q.close()
                except Exception:pass
            self.after(0,lambda: setattr(self,'candle_busy',False))

    def _opening_feed_done(self,message):
        self.intelligence_text.config(state='normal')
        self.intelligence_text.insert('end','\n\n'+message)
        self.intelligence_text.see('end')
        self.intelligence_text.config(state='disabled')
        self.tabs.select(self.intelligence_frame)
        self.note.set('Raw opening-feed inspection finished. See Market Intelligence tab.')

    def build_swing_desk(self):
        from swing_watchlist import FIELDS
        outer=tk.Frame(self.swing_frame,bg='#23263a');outer.pack(fill='both',expand=True,padx=12,pady=12)
        tk.Label(outer,text='SWING OPPORTUNITY DESK  |  MANUAL RESEARCH CASES  |  NO LIVE MARKET DATA',bg='#23263a',fg='#d9c7ff',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,8))
        tk.Label(outer,text='Track stock and options swing ideas, filings, cash flow, catalysts and liquidity. Entries are your notes, not verified signals.',bg='#23263a',fg='#b7b8cb',wraplength=960).pack(anchor='w')
        self.swing_tree=self.tree(outer,['id','ticker','direction','status','updated_utc','source','thesis'], fixed_height=145)
        self.swing_tree.bind('<<TreeviewSelect>>',self.swing_select)
        form=tk.Frame(outer,bg='#23263a');form.pack(fill='x',pady=(10,4))
        self.swing_vars={}
        choices={'direction':('Undecided','Bullish','Bearish'),'status':('Investigating','Watching','Rejected','Archived')}
        for i,k in enumerate(('ticker','direction','status','source')):
            cell=tk.Frame(form,bg='#23263a');cell.grid(row=0,column=i,sticky='ew',padx=4)
            tk.Label(cell,text=k.upper(),bg='#23263a',fg='#d9c7ff').pack(anchor='w')
            var=tk.StringVar(value=choices[k][0] if k in choices else '')
            self.swing_vars[k]=var
            if k in choices:ttk.Combobox(cell,textvariable=var,values=choices[k],state='readonly',width=18).pack(fill='x')
            else:tk.Entry(cell,textvariable=var,bg='#343752',fg='white',insertbackground='white',width=24).pack(fill='x')
            form.columnconfigure(i,weight=1)
        details=tk.Frame(outer,bg='#23263a');details.pack(fill='x')
        self.swing_text={}
        for i,k in enumerate(('thesis','catalyst','filings','cashflow','liquidity','invalidation')):
            cell=tk.Frame(details,bg='#23263a');cell.grid(row=i//3,column=i%3,sticky='nsew',padx=4,pady=3)
            tk.Label(cell,text=k.upper(),bg='#23263a',fg='#d9c7ff').pack(anchor='w')
            widget=tk.Text(cell,height=2,width=24,bg='#343752',fg='white',insertbackground='white',wrap='word')
            widget.pack(fill='both',expand=True);self.swing_text[k]=widget
        for i in range(3):details.columnconfigure(i,weight=1)
        buttons=tk.Frame(outer,bg='#23263a');buttons.pack(fill='x',pady=6)
        self.button(buttons,'New case',self.swing_clear).pack(side='left',padx=(0,7))
        self.button(buttons,'Save case',self.swing_save,bg='#276653').pack(side='left',padx=(0,7))
        self.button(buttons,'Refresh',self.swing_refresh).pack(side='left',padx=(0,7))
        self.button(buttons,'Export cases CSV',self.swing_export).pack(side='left')
        self.swing_case_id=None
        self.swing_refresh()

    def build_discovery(self):
        outer=tk.Frame(self.discovery_frame,bg='#23263a');outer.pack(fill='both',expand=True,padx=12,pady=12)
        tk.Label(outer,text='PROFESSOR TRASH PANDA | VOLUME DISCOVERY LAB',bg='#23263a',fg='#d9c7ff',font=('Segoe UI',13,'bold')).pack(anchor='w',pady=5)
        tk.Label(outer,text='Daily stock-volume anomalies only. OpenD must be running; history entitlements/rate limits apply. Not options flow, not buy/sell signals.',bg='#23263a',fg='#b7b8cb',wraplength=1000).pack(anchor='w')
        controls=tk.Frame(outer,bg='#23263a');controls.pack(fill='x',pady=10)
        self.discovery_button=self.button(controls,'Scan Market (40 tickers)',self.discovery_scan,bg='#276653');self.discovery_button.pack(side='left',padx=(0,8))
        self.button(controls,'Load saved scans',self.discovery_refresh).pack(side='left',padx=(0,8))
        self.button(controls,'Investigate selected ticker',self.discovery_promote,bg='#54417d').pack(side='left',padx=(0,8))
        self.button(controls,'Save selected as research case',self.discovery_save,bg='#276653').pack(side='left',padx=(0,8))
        self.button(controls,'Run Diagnostics',self.run_diagnostics).pack(side='left',padx=(0,8))
        self.button(controls,'Audit Historical Candles',self.run_signal_audit).pack(side='left',padx=(0,8))
        self.button(controls,'Validate Setup Outcomes',self.run_outcome_validation).pack(side='left')
        self.discovery_status=tk.StringVar(value='Idle. Scans use completed daily bars and compare against the preceding 20 sessions.')
        tk.Label(outer,textvariable=self.discovery_status,bg='#23263a',fg='#b8a3df',wraplength=1000,justify='left').pack(anchor='w',pady=(0,7))
        self.discovery_tree=self.tree(outer,['symbol','session','rvol','rvol50','avg_dollar_volume20','change_pct','close','volume','range_pct','scan_utc'])
        self.discovery_queue=queue.Queue();self.discovery_busy=False;self.discovery_rows={}
        self.discovery_refresh();self.after(250,self.discovery_poll)

    def run_diagnostics(self):
        """Execute the read-only diagnostic runner outside the GUI thread."""
        import subprocess
        runner=Path(__file__).resolve().parent/'raccoon_diagnostics.py'
        if not runner.is_file():
            messagebox.showerror('Diagnostics','raccoon_diagnostics.py is missing from this folder.');return
        self.discovery_status.set('Diagnostics running in background; no trading or database writes.')
        def worker():
            try:
                result=subprocess.run([sys.executable,str(runner),'--project',str(runner.parent)],
                                      capture_output=True,text=True,timeout=90)
                details=(result.stdout or result.stderr).strip()
                self.after(0,lambda: self._diagnostics_done(result.returncode,details))
            except Exception as exc:
                self.after(0,lambda msg=str(exc): messagebox.showerror('Diagnostics',msg))
        threading.Thread(target=worker,daemon=True).start()

    def _diagnostics_done(self,code,details):
        self.discovery_status.set('Diagnostics completed. '+details[-220:])
        if code==0:messagebox.showinfo('Diagnostics complete',details)
        else:messagebox.showwarning('Diagnostics need review',details or 'See diagnostic output.')

    def run_signal_audit(self):
        """Run independent read-only candle-quality audit in a worker."""
        runner=Path(__file__).resolve().parent/'signal_validation_lab.py'
        if not runner.is_file():
            messagebox.showerror('Signal audit','signal_validation_lab.py is missing.');return
        self.discovery_status.set('Historical candle audit running; no orders or database writes.')
        def worker():
            try:
                result=subprocess.run([sys.executable,str(runner),'--project',str(runner.parent)],
                                      capture_output=True,text=True,timeout=120)
                details=(result.stdout or result.stderr).strip()
                self.after(0,lambda: self._diagnostics_done(result.returncode,details))
            except Exception as exc:
                self.after(0,lambda msg=str(exc):messagebox.showerror('Signal audit',msg))
        threading.Thread(target=worker,daemon=True).start()

    def run_outcome_validation(self):
        """Launch read-only original-setup event study in a background worker."""
        runner=Path(__file__).resolve().parent/'setup_outcome_validation.py'
        if not runner.is_file():
            messagebox.showerror('Setup validation','setup_outcome_validation.py is missing.');return
        self.discovery_status.set('Setup outcome validation running; research data remains unchanged.')
        def worker():
            try:
                result=subprocess.run([sys.executable,str(runner),'--project',str(runner.parent)],
                                      capture_output=True,text=True,timeout=180)
                details=(result.stdout or result.stderr).strip()
                self.after(0,lambda:self._diagnostics_done(result.returncode,details))
            except Exception as exc:
                self.after(0,lambda msg=str(exc):messagebox.showerror('Setup validation',msg))
        threading.Thread(target=worker,daemon=True).start()

    def build_fundamentals(self):
        outer=tk.Frame(self.fund_frame,bg='#23263a');outer.pack(fill='both',expand=True,padx=12,pady=10)
        tk.Label(outer,text='PROFESSOR TRASH PANDA | SEC EVIDENCE LAB',bg='#23263a',fg='#d9c7ff',font=('Segoe UI',12,'bold')).pack(anchor='w')
        tk.Label(outer,text='SEC EDGAR filings and reported XBRL values. No automated buy ratings, no live news, no dilution inference without filing review.',bg='#23263a',fg='#b7b8cb',wraplength=950).pack(anchor='w',pady=(2,8))
        line=tk.Frame(outer,bg='#23263a');line.pack(fill='x')
        self.fund_ticker=tk.StringVar(value='UBER');self.fund_agent=tk.StringVar()
        tk.Label(line,text='Ticker',bg='#23263a',fg='white').pack(side='left')
        tk.Entry(line,textvariable=self.fund_ticker,width=10).pack(side='left',padx=5)
        self.button(line,'Load saved',self.fund_load).pack(side='left',padx=4)
        self.fund_fetch_btn=self.button(line,'Fetch SEC filings',self.fund_fetch,bg='#276653');self.fund_fetch_btn.pack(side='left',padx=4)
        tk.Label(outer,text='SEC contact User-Agent (required for fetch; not saved):',bg='#23263a',fg='#b7b8cb').pack(anchor='w',pady=(7,2))
        tk.Entry(outer,textvariable=self.fund_agent,bg='#343752',fg='white',insertbackground='white').pack(fill='x')
        self.fund_status=tk.StringVar(value='No SEC request made. Enter ticker and your contact User-Agent, then fetch.')
        tk.Label(outer,textvariable=self.fund_status,bg='#23263a',fg='#b8a3df',wraplength=900,justify='left').pack(anchor='w',pady=5)
        row=tk.Frame(outer,bg='#23263a');row.pack(fill='x',pady=(5,3))
        self.fund_category=tk.StringVar(value='Catalyst');self.fund_assessment=tk.StringVar(value='Unverified')
        ttk.Combobox(row,textvariable=self.fund_category,values=('Catalyst','Dilution','Cash flow','Debt','Financial condition','Other'),width=19,state='readonly').pack(side='left',padx=3)
        ttk.Combobox(row,textvariable=self.fund_assessment,values=('Unverified','Supported','Concern','Needs review'),width=17,state='readonly').pack(side='left',padx=3)
        self.fund_source=tk.StringVar()
        tk.Entry(row,textvariable=self.fund_source,width=45).pack(side='left',fill='x',expand=True,padx=3)
        tk.Label(outer,text='Evidence note (source URL above; saved independently of Swing Desk):',bg='#23263a',fg='#b7b8cb').pack(anchor='w')
        self.fund_note=tk.Text(outer,height=3,bg='#343752',fg='white',insertbackground='white',wrap='word');self.fund_note.pack(fill='x')
        self.button(outer,'Save evidence note',self.fund_save_note,bg='#276653').pack(anchor='w',pady=4)
        self.fund_view=tk.Text(outer,bg='#343752',fg='#f2f1fb',insertbackground='white',wrap='word',height=11)
        self.fund_view.pack(fill='both',expand=True,pady=4)
        self.fund_view.insert('1.0','No saved SEC snapshot loaded. SEC figures may be stale or period-incomparable; inspect linked filings.')
        self.fund_queue=queue.Queue();self.after(250,self.fund_poll)

    def fund_fetch(self):
        ticker=self.fund_ticker.get().strip().upper();agent=self.fund_agent.get().strip()
        if not agent or '@' not in agent:
            messagebox.showinfo('SEC contact','Enter a contact User-Agent such as RaccoonRadar/1.5 email@example.com.');return
        self.fund_fetch_btn.config(state='disabled');self.fund_status.set('Fetching public SEC data; network access and SEC limits apply...')
        def worker():
            try:
                from fundamental_intelligence import fetch,save_snapshot
                data=fetch(ticker,agent);save_snapshot(data);self.fund_queue.put(('ok',data))
            except Exception as exc:self.fund_queue.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def fund_poll(self):
        try:
            while True:
                status,value=self.fund_queue.get_nowait();self.fund_fetch_btn.config(state='normal')
                if status=='ok':self.fund_show(value)
                else:self.fund_status.set('SEC request failed: '+value)
        except queue.Empty:pass
        self.after(250,self.fund_poll)

    def fund_load(self):
        from fundamental_intelligence import latest
        data=latest(self.fund_ticker.get())
        if data:self.fund_show(data)
        else:self.fund_status.set('No locally saved SEC snapshot for this ticker.')

    def fund_show(self,data):
        self.fund_status.set(f"{data['company']} ({data['ticker']}) | CIK {data['cik']} | snapshot {data['fetched_utc']} UTC | SEC sourced, not independently verified")
        lines=['REPORTED SEC COMPANYFACTS — DO NOT COMPARE DIFFERENT PERIODS AS IF EQUIVALENT','']
        for label,x in data['metrics'].items():
            if not x:lines.append(label+': Not reported in selected taxonomy');continue
            val=x['value']; formatted=f'{val:,.0f}' if isinstance(val,(int,float)) else str(val)
            lines.append(f"{label}: {formatted} | period end {x.get('end','?')} | filed {x.get('filed','?')} | {x.get('form','?')}")
        lines.extend(['','RECENT SEC FILINGS (clickable URL can be copied):'])
        for x in data['filings']:lines.append(f"{x['filed']} {x['form']}  {x['url']}")
        lines.extend(['','DATA SOURCE: '+data['sources']['companyfacts'],'CAUTION: No automatic cash runway, dilution rating, or catalyst verification. Review original filings.','', 'SAVED EVIDENCE NOTES:'])
        from fundamental_intelligence import list_notes
        for stamp,cat,assessment,url,note in list_notes(data['ticker']):lines.append(f'{stamp} | {cat} | {assessment} | {note} | {url}')
        self.fund_view.delete('1.0','end');self.fund_view.insert('1.0','\n'.join(lines))

    def fund_save_note(self):
        from fundamental_intelligence import add_note
        try:
            add_note(self.fund_ticker.get(),self.fund_category.get(),self.fund_assessment.get(),self.fund_source.get(),self.fund_note.get('1.0','end-1c'))
            self.fund_note.delete('1.0','end')
            self.fund_status.set('Evidence note saved in raccoon_fundamentals.sqlite3.')
            self.fund_load()
        except Exception as exc:messagebox.showerror('Evidence note',str(exc))

    def discovery_scan(self):
        if self.discovery_busy:return
        self.discovery_busy=True;self.discovery_button.config(state='disabled')
        self.discovery_status.set('Scanning historical daily candles through local Moomoo OpenD...')
        def worker():
            try:
                from volume_discovery import scan_moomoo,save_results
                def progress(i,n,t):self.discovery_queue.put(('progress',i,n,t))
                rows,errors=scan_moomoo(progress=progress)
                if rows:save_results(rows)
                self.discovery_queue.put(('complete',rows,errors))
            except Exception as exc:self.discovery_queue.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def discovery_poll(self):
        try:
            while True:
                item=self.discovery_queue.get_nowait()
                if item[0]=='progress':self.discovery_status.set(f'Scanning {item[1]}/{item[2]}: {item[3]} (OpenD quotas may apply)')
                else:
                    self.discovery_busy=False;self.discovery_button.config(state='normal')
                    if item[0]=='error':self.discovery_status.set('Scan failed: '+item[1]);messagebox.showerror('Volume discovery',item[1])
                    else:
                        rows,errors=item[1],item[2]
                        self.discovery_refresh()
                        self.discovery_status.set(f'{len(rows)} tickers analyzed; {len(errors)} unavailable or insufficient. Ranked by daily relative volume. RVOL50 may be n/a. Dollar volume is historical approximation; no options liquidity verification.')
                        if errors:messagebox.showwarning('Partial scan',f'{len(errors)} tickers could not be analyzed. First examples: '+', '.join(errors[:5]))
        except queue.Empty:pass
        self.after(250,self.discovery_poll)

    def discovery_refresh(self):
        from volume_discovery import list_results
        rows=list_results();self.discovery_rows={str(r['id']):r for r in rows}
        for item in self.discovery_tree.get_children():self.discovery_tree.delete(item)
        for r in rows:
            self.discovery_tree.insert('','end',iid=str(r['id']),values=(r['symbol'],r['session'],f"{r['rvol']:.2f}x",f"{r['rvol50']:.2f}x" if r.get('rvol50') is not None else 'n/a',f"${r['avg_dollar_volume20']/1e6:,.1f}M" if r.get('avg_dollar_volume20') is not None else 'n/a',f"{r['change_pct']:+.2f}%" if r['change_pct'] is not None else 'n/a',f"{r['close']:.2f}",f"{r['volume']:,.0f}",f"{r['range_pct']:.2f}%",r['scan_utc']))

    def discovery_promote(self):
        selected=self.discovery_tree.selection()
        if not selected:messagebox.showinfo('Choose a ticker','Select a discovery row first.');return
        r=self.discovery_rows.get(selected[0])
        if not r:return
        self.swing_clear()
        self.swing_vars['ticker'].set(r['symbol'])
        self.swing_vars['source'].set(f"Volume discovery {r['session']}")
        self.swing_text['thesis'].insert('1.0',f"RESEARCH ONLY: {r['rvol']:.2f}x 20-session daily volume; underlying daily change {r['change_pct']:+.2f}% on {r['session']}. Verify price structure, filings, catalysts, options liquidity and current quotes before forming a thesis.")
        self.swing_text['liquidity'].insert('1.0','Underlying volume observed. Options volume, bid/ask, open interest and quote freshness NOT checked.')
        self.tabs.select(self.swing_frame)
        self.note.set('Discovery loaded into UNSAVED swing case. Review and click Save case if useful.')

    def discovery_save(self):
        """Save a selected discovery directly as an undecided manual research case."""
        selected=self.discovery_tree.selection()
        if not selected:
            messagebox.showinfo('Choose a ticker','Select a discovery row first.')
            return
        r=self.discovery_rows.get(selected[0])
        if not r:return
        from swing_watchlist import save_case, FIELDS
        values={k:'' for k in FIELDS}
        values.update(ticker=r['symbol'],direction='Undecided',status='Investigating',
                      source=f"Volume discovery {r['session']}",
                      thesis=f"RESEARCH ONLY: {r['rvol']:.2f}x 20-session daily volume; underlying daily change {r['change_pct']:+.2f}% on {r['session']}. Verify price structure, filings, catalysts, options liquidity and current quotes before forming a thesis.",
                      liquidity='Underlying volume observed. Options volume, bid/ask, open interest and quote freshness NOT checked.')
        try:
            save_case(values)
            self.swing_refresh()
            self.tabs.select(self.swing_frame)
            self.note.set(f"Saved {r['symbol']} as an undecided research case. Select it in the Swing Desk to add notes. No trade placed.")
            messagebox.showinfo('Research case saved',f"{r['symbol']} saved to the Swing Opportunity Desk. This is a research idea, not a trade.")
        except Exception as exc:messagebox.showerror('Could not save case',str(exc))

    def swing_refresh(self):
        from swing_watchlist import list_cases
        for item in self.swing_tree.get_children():self.swing_tree.delete(item)
        for r in list_cases():
            self.swing_tree.insert('', 'end',iid=str(r['id']),values=[r.get(k,'') for k in ('id','ticker','direction','status','updated_utc','source','thesis')])

    def swing_clear(self):
        self.swing_case_id=None
        for k,v in self.swing_vars.items():v.set('Undecided' if k=='direction' else 'Investigating' if k=='status' else '')
        for widget in self.swing_text.values():widget.delete('1.0','end')
        self.swing_tree.selection_remove(self.swing_tree.selection())

    def swing_select(self,event=None):
        selection=self.swing_tree.selection()
        if not selection:return
        from swing_watchlist import list_cases
        case=next((r for r in list_cases() if str(r['id'])==selection[0]),None)
        if not case:return
        self.swing_case_id=case['id']
        for k,v in self.swing_vars.items():v.set(case[k])
        for k,widget in self.swing_text.items():widget.delete('1.0','end');widget.insert('1.0',case[k])

    def swing_save(self):
        from swing_watchlist import save_case
        values={k:v.get() for k,v in self.swing_vars.items()}
        values.update({k:v.get('1.0','end-1c') for k,v in self.swing_text.items()})
        try:
            save_case(values,self.swing_case_id)
            self.swing_refresh();self.note.set('Swing case saved locally. These are manual research notes, not live market signals.')
            messagebox.showinfo('Research case saved','Swing research case saved to the local database. No order placed.')
        except Exception as exc:messagebox.showerror('Swing case error',str(exc))

    def swing_export(self):
        from swing_watchlist import export_csv
        destination=filedialog.asksaveasfilename(title='Export swing cases',defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if destination:
            try:export_csv(destination);messagebox.showinfo('Export complete','Swing case CSV exported.')
            except Exception as exc:messagebox.showerror('Export error',str(exc))

    def tile(self, parent, name, value, column):
        frame = tk.Frame(parent, bg='#24263b', padx=10, pady=5)
        frame.grid(row=0, column=column, sticky='nsew', padx=3)
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(frame, text=name, bg='#24263b', fg='#aaa8c4', font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        label = tk.Label(frame, text=value, bg='#24263b', fg='#f1ecff', font=('Segoe UI', 12, 'bold'))
        label.pack(anchor='w', pady=(2,0))
        return label

    def button(self, parent, text, command, bg='#54417d'):
        return tk.Button(parent, text=text, command=command, bg=bg, fg='white', activebackground='#745ba6', activeforeground='white', relief='flat', padx=10, pady=6, font=('Segoe UI', 9, 'bold'), cursor='hand2')

    def tree(self, parent, cols, fixed_height=None):
        container = tk.Frame(parent, bg='#23263a')
        if fixed_height is not None:
            container.pack(fill='x', expand=False, pady=(5, 2))
            container.configure(height=fixed_height)
            container.pack_propagate(False)
        else:
            container.pack(fill='both', expand=True)
        tree = ttk.Treeview(container, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c.replace('_',' ').title())
            tree.column(c, width=145 if c in ('bar_time_et','entry','exit','contract') else 115, minwidth=70)
        vs = ttk.Scrollbar(container, orient='vertical', command=tree.yview)
        hs = ttk.Scrollbar(container, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0,column=0,sticky='nsew'); vs.grid(row=0,column=1,sticky='ns'); hs.grid(row=1,column=0,sticky='ew')
        container.grid_rowconfigure(0,weight=1); container.grid_columnconfigure(0,weight=1)
        return tree

    def read_csv(self, path):
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError('The CSV has no header row.')
            rows = list(reader)
        return rows, reader.fieldnames

    def load_price_action(self):
        path = filedialog.askopenfilename(title='Choose OHLCV candles CSV (sample included)', filetypes=[('CSV files','*.csv')])
        if not path: return
        try:
            self.last_ohlcv = self.read_csv(path)[0]
            self.persist_history(self.last_ohlcv)
            self.detective_events = []
            self.filtered_events = []
            rows = analyze(self.last_ohlcv)
            if not rows: raise ValueError('No valid OHLCV candles found.')
            self.fill(self.price_tree, rows)
            self.tabs.select(self.price_frame)
            self.note.set(f'Analyzed {len(rows)} candle observations from {path}. Historical/sample candles; no true order-book or volume-delta data.')
        except Exception as exc:
            messagebox.showerror('Could not analyze candle CSV', str(exc))

    def fetch_candles(self):
        """Fetch completed 1m SPY/QQQ bars from OpenD, without order APIs."""
        if self.candle_busy:
            self.note.set('A candle fetch is already in progress.')
            return
        self.candle_busy = True
        self.note.set('Connecting to OpenD 127.0.0.1:11111 to retrieve completed 1-minute candles...')
        threading.Thread(target=self._fetch_candles_worker, daemon=True).start()

    def _fetch_candles_worker(self):
        q = None
        try:
            from moomoo import OpenQuoteContext, RET_OK, KLType
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo('America/New_York'))
            # Weekends use Friday. Exchange holidays may require manually selecting a previous date.
            session = now.date()
            while session.weekday() >= 5:
                session -= timedelta(days=1)
            day = session.isoformat()
            q = OpenQuoteContext(host='127.0.0.1', port=11111)
            combined = []
            latest = {}
            for symbol in ('US.SPY','US.QQQ'):
                ret, data, _ = q.request_history_kline(symbol, start=day, end=day,
                                                       ktype=KLType.K_1M, max_count=1000)
                if ret != RET_OK or not hasattr(data, 'iterrows'):
                    raise RuntimeError(f'{symbol} historical candles unavailable: {str(data)[:180]}')
                for _, bar in data.iterrows():
                    stamp = str(bar.get('time_key',''))
                    try:
                        bt = datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
                    if not (9 <= bt.hour <= 15) or (bt.hour == 9 and bt.minute < 30):
                        continue
                    if bt.date() == now.date() and bt >= now.replace(tzinfo=None, second=0, microsecond=0):
                        continue  # no incomplete current candle
                    record = {'time':stamp, 'symbol':symbol}
                    try:
                        for field in ('open','high','low','close','volume'):
                            record[field] = float(bar[field])
                    except (KeyError, ValueError, TypeError):
                        continue
                    combined.append(record)
                    latest[symbol] = max(latest.get(symbol, stamp),stamp)
            combined.sort(key=lambda x:(x['time'],x['symbol']))
            if not combined:
                raise RuntimeError(f'No completed SPY/QQQ candles returned for {day}. Market may be closed or data may be unavailable.')
            rows = analyze(combined)
            self.candle_queue.put(('success', rows, latest, day, now.isoformat(timespec='seconds'), combined))
        except Exception as exc:
            self.candle_queue.put(('error',str(exc)))
        finally:
            if q is not None:
                try: q.close()
                except Exception: pass

    def process_candle_events(self):
        try:
            while True:
                try: item = self.candle_queue.get_nowait()
                except queue.Empty: break
                self.candle_busy = False
                if item[0] == 'error':
                    self.note.set('OpenD candle fetch failed: '+item[1]+' â€” No live data assumed.')
                    self.status.config(text='DATA UNAVAILABLE')
                elif item[0] == 'range_success':
                    _, rows, raw_candles, sessions, failures, fetched = item
                    self.last_ohlcv = raw_candles
                    self.persist_history(raw_candles)
                    self.detective_events = []
                    self.filtered_events = []
                    self.fill(self.price_tree, rows)
                    self.tabs.select(self.price_frame)
                    self.last_candle_ts = max(r['time'] for r in raw_candles)
                    self.last_fetch_at = fetched
                    self.status.config(text='HISTORICAL RANGE')
                    self.note.set(f'Loaded {len(raw_candles)} candles across {len(sessions)} sessions ({sessions[0]} to {sessions[-1]}). Latest {self.last_candle_ts} ET. {len(failures)} unavailable symbol-days. Snapshot only, NOT live. Click Setup detective.')
                else:
                    _, rows, latest, day, fetched, raw_candles = item
                    self.last_ohlcv = raw_candles
                    self.persist_history(raw_candles)
                    self.detective_events = []
                    self.filtered_events = []
                    self.fill(self.price_tree, rows)
                    self.tabs.select(self.price_frame)
                    newest = max(latest.values()) if latest else 'unknown'
                    self.last_candle_ts = newest
                    self.last_fetch_at = fetched
                    self.status.config(text='HISTORICAL CANDLES')
                    self.note.set(f'OpenD returned {len(rows)} completed SPY/QQQ candles for {day}. Latest bar: {newest} ET; fetched: {fetched}. Snapshot only, NOT streaming/live.')
                    self.refresh_intelligence()
        finally:
            self.after(350, self.process_candle_events)

    def run_detective(self):
        if not self.last_ohlcv:
            messagebox.showinfo('Load candles first', 'Click Fetch OpenD candles or Analyze candle CSV first.')
            return
        try:
            self.detective_events = detect(self.last_ohlcv)
            self.validation_events=[]
            from performance_intelligence import nonoverlap, daily_breakdown, consistency
            self.filtered_events = nonoverlap(self.detective_events, 5) if self.deoverlap.get() else list(self.detective_events)
            results = summary(self.filtered_events)
            display=[]
            for row in results:
                display.append({k: ('—' if v is None else v) for k,v in row.items()})
            self.fill(self.detective_tree, display)
            self.fill(self.period_tree, self.period_summaries(self.filtered_events))
            self.fill(self.daily_tree, daily_breakdown(self.filtered_events))
            self.fill(self.consistency_tree, consistency(self.filtered_events))
            self.tabs.select(self.detective_frame)
            self.note.set(f'Performance Lab: {len(self.detective_events)} raw events; {len(self.filtered_events)} analyzed ({"5-minute per-symbol/setup spacing" if self.deoverlap.get() else "overlap allowed"}). {len(set(e["time"][:10] for e in self.filtered_events))} sessions with events. Daily + consistency tabs ready. ETF close-to-close ONLY, not option returns. Results are exploratory; zero moves count as non-wins.')
        except Exception as exc:
            messagebox.showerror('Setup Detective error',str(exc))

    def persist_history(self, candles):
        try:
            from strategy_validation import store_candles
            store_candles(candles)
        except Exception as exc:
            messagebox.showwarning('History storage failed',f'Candles are loaded but were NOT saved to SQLite: {exc}')

    def load_saved_history(self):
        try:
            from strategy_validation import load_candles
            candles=load_candles()
            if not candles:
                messagebox.showinfo('No history','No saved candles yet. Fetch a date range first.');return
            self.last_ohlcv=candles
            self.detective_events=[];self.filtered_events=[];self.validation_events=[]
            self.fill(self.price_tree,analyze(candles))
            self.status.config(text='SAVED HISTORY')
            self.note.set(f'Loaded {len(candles)} unique saved candles across {len(set(r["time"][:10] for r in candles))} sessions. Click Setup detective, then Run validation.')
            self.tabs.select(self.price_frame)
            self.refresh_intelligence()
        except Exception as exc: messagebox.showerror('History load error',str(exc))

    def run_validation(self):
        if not self.last_ohlcv:
            messagebox.showinfo('No candles','Fetch candles or load saved history first.');return
        try:
            from strategy_validation import strict_spacing, validate, weekdays
            # Recompute from loaded candles; do not rely on old filtered events.
            events=strict_spacing(detect(self.last_ohlcv),5)
            self.validation_events=events
            rows,info=validate(events)
            self.fill(self.validation_tree,rows)
            weekday_rows=weekdays(events)
            self.fill(self.weekday_tree,weekday_rows)
            from validation_intelligence import rolling_holdout, daily_outcomes
            self.rolling_rows, rolling_info = rolling_holdout(events)
            self.daily_validation_rows = daily_outcomes(events)
            self.fill(self.rolling_tree,self.rolling_rows)
            self.fill(self.day_validation_tree,self.daily_validation_rows)
            from research_journal import record_run
            self.latest_run_id=record_run(self.last_ohlcv,events,rows,weekday_rows,info)
            self.refresh_journal()
            self.tabs.select(self.validation_frame)
            self.note.set(f'Validation run #{self.latest_run_id} saved. {len(events)} strictly spaced events. {info} ETF moves only; no options P/L. Weekday results are descriptive, not predictions.')
        except Exception as exc: messagebox.showerror('Validation failed',str(exc))

    def export_research(self):
        """Export loaded candles, individual event outcomes, and summary tables.

        Read-only; no account data, broker orders, or network calls.
        """
        if not self.last_ohlcv:
            messagebox.showinfo('No research data', 'Fetch a date range or load candle CSV first.')
            return
        if not self.detective_events:
            messagebox.showinfo('Run Setup detective', 'Click Setup detective before exporting research.')
            return
        destination = filedialog.asksaveasfilename(
            title='Save Raccoon Radar research export',
            defaultextension='.zip',
            initialfile='raccoon_research_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.zip',
            filetypes=[('ZIP archive', '*.zip')])
        if not destination:
            return
        try:
            from setup_detective import summary
            from performance_intelligence import daily_breakdown, consistency
            from collections import Counter
            raw = self.detective_events
            analyzed = self.filtered_events
            # Identify retained observations by their position in the raw event list.
            # This preserves repeated events even if identical dictionaries exist.
            remaining = Counter(tuple(sorted(e.items())) for e in analyzed)
            labeled = []
            for event in raw:
                key = tuple(sorted(event.items()))
                kept = remaining[key] > 0
                if kept:
                    remaining[key] -= 1
                labeled.append({**event, 'analyzed': 'yes' if kept else 'no'})
            metadata = {
                'app_version': '1.5.4',
                'generated_at_local': datetime.now().isoformat(timespec='seconds'),
                'source': 'loaded candle CSV or historical OpenD snapshot (see application status)',
                'latest_candle_et': self.last_candle_ts,
                'fetch_timestamp': self.last_fetch_at,
                'candle_count': len(self.last_ohlcv),
                'sessions': sorted(set(str(r.get('time', ''))[:10] for r in self.last_ohlcv)),
                'raw_events': len(raw), 'analyzed_events': len(analyzed),
                'deoverlap_5_min_enabled': bool(self.deoverlap.get()),
                'methodology': 'ETF close-to-close directional percent moves at 1/3/5 minutes; missing future bars excluded per horizon; 5-minute greedy cooldown per symbol/setup when enabled; other overlapping events remain. Not option returns, fill simulations, or independent trades.'
            }
            def csv_bytes(rows, fields=None):
                output = io.StringIO(newline='')
                fields = fields or list(dict.fromkeys(k for row in rows for k in row))
                writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)
                return output.getvalue().encode('utf-8-sig')
            with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('metadata.json', json.dumps(metadata, indent=2))
                z.writestr('candles.csv', csv_bytes(self.last_ohlcv, ['time','symbol','open','high','low','close','volume']))
                z.writestr('events_all.csv', csv_bytes(labeled, ['time','symbol','setup','direction','entry_close','1m_%','3m_%','5m_%','analyzed']))
                z.writestr('events_analyzed.csv', csv_bytes(analyzed, ['time','symbol','setup','direction','entry_close','1m_%','3m_%','5m_%']))
                z.writestr('setup_summary.csv', csv_bytes(summary(analyzed)))
                z.writestr('time_of_day.csv', csv_bytes(self.period_summaries(analyzed)))
                z.writestr('daily_breakdown.csv', csv_bytes(daily_breakdown(analyzed)))
                z.writestr('consistency.csv', csv_bytes(consistency(analyzed)))
                if self.validation_events:
                    from strategy_validation import validate, weekdays
                    vr,_=validate(self.validation_events)
                    z.writestr('validation_holdout.csv',csv_bytes(vr))
                    z.writestr('weekday_study.csv',csv_bytes(weekdays(self.validation_events)))
                    from validation_intelligence import rolling_holdout,daily_outcomes
                    z.writestr('rolling_validation.csv',csv_bytes(rolling_holdout(self.validation_events)[0]))
                    z.writestr('day_level_outcomes.csv',csv_bytes(daily_outcomes(self.validation_events)))
                from research_journal import export_json
                z.writestr('research_journal.json',json.dumps(export_json(),indent=2))
                z.writestr('README.txt', 'Raccoon Radar research export\nHistorical ETF price-action study only. No options fills, slippage, spread, fees, or validated trading edge.\n')
            self.note.set(f'Exported {len(self.last_ohlcv)} candles and {len(analyzed)} analyzed events to {destination}')
            messagebox.showinfo('Export complete', f'Research ZIP saved to:\n{destination}\n\nUpload this ZIP to ChatGPT for analysis.')
        except Exception as exc:
            messagebox.showerror('Export failed', str(exc))

    def build_journal(self):
        bar=tk.Frame(self.journal_frame,bg='#23263a');bar.pack(fill='x',padx=12,pady=8)
        self.button(bar,'Refresh journal',self.refresh_journal).pack(side='left',padx=(0,8))
        self.button(bar,'Add hypothesis / finding',self.add_journal_note,bg='#276653').pack(side='left',padx=(0,8))
        tk.Label(bar,text='Entries are append-only; assessments are snapshots, not predictions.',bg='#23263a',fg='#b8a3df').pack(side='left')
        tk.Label(self.journal_frame,text='VALIDATION RUNS',bg='#23263a',fg='white').pack(anchor='w',padx=12)
        self.runs_tree=self.tree(self.journal_frame,['id','recorded_utc','candle_count','event_count','date_first','date_last','candle_hash'])
        tk.Label(self.journal_frame,text='RESEARCH NOTES (latest first)',bg='#23263a',fg='white').pack(anchor='w',padx=12)
        self.notes_tree=self.tree(self.journal_frame,['id','recorded_utc','assessment','hypothesis','evidence','run_id'])
        self.refresh_journal()

    def refresh_journal(self):
        try:
            from research_journal import get_runs,get_notes
            self.fill(self.runs_tree,get_runs())
            self.fill(self.notes_tree,get_notes())
        except Exception as exc: messagebox.showerror('Journal error',str(exc))

    def add_journal_note(self):
        from tkinter import simpledialog
        hypothesis=simpledialog.askstring('Research hypothesis','What hypothesis or finding should we record?',parent=self)
        if not hypothesis:return
        options=['Untested','Under investigation','Supported in holdout','Not supported','Inconclusive']
        status=simpledialog.askstring('Assessment','Assessment: '+', '.join(options),initialvalue='Untested',parent=self)
        if status is None:return
        if status not in options:
            messagebox.showerror('Invalid assessment','Choose one of: '+', '.join(options));return
        evidence=simpledialog.askstring('Evidence / caveats','Evidence, limitations, or reason for assessment (optional):',parent=self)
        if evidence is None:return
        try:
            from research_journal import record_note
            record_note(hypothesis,status,evidence,self.latest_run_id)
            self.refresh_journal();self.tabs.select(self.journal_frame)
        except Exception as exc:messagebox.showerror('Journal error',str(exc))

    def export_archive(self):
        from strategy_validation import DB_PATH
        from research_journal import export_json
        destination=filedialog.asksaveasfilename(title='Save portable research archive',defaultextension='.zip',initialfile='raccoon_archive_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip',filetypes=[('ZIP archive','*.zip')])
        if not destination:return
        try:
            import sqlite3
            # Online backup gives a consistent snapshot even if database is in use.
            from tempfile import TemporaryDirectory
            with TemporaryDirectory() as temp:
                snapshot=Path(temp)/'raccoon_history.sqlite3'
                from research_journal import initialize
                initialize()
                from contextlib import closing
                with closing(sqlite3.connect(DB_PATH)) as source, closing(sqlite3.connect(snapshot)) as backup:
                    source.backup(backup)
                with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
                    z.write(snapshot,'raccoon_history.sqlite3')
                    from swing_watchlist import initialize as init_swing, DB_PATH as swing_db
                    init_swing()
                    swing_snapshot=Path(temp)/'raccoon_swing.sqlite3'
                    with closing(sqlite3.connect(swing_db)) as source, closing(sqlite3.connect(swing_snapshot)) as backup:
                        source.backup(backup)
                    z.write(swing_snapshot,'raccoon_swing.sqlite3')
                    from volume_discovery import initialize as init_discovery, DB_PATH as discovery_db
                    init_discovery()
                    discovery_snapshot=Path(temp)/'raccoon_discovery.sqlite3'
                    with closing(sqlite3.connect(discovery_db)) as source, closing(sqlite3.connect(discovery_snapshot)) as backup:
                        source.backup(backup)
                    z.write(discovery_snapshot,'raccoon_discovery.sqlite3')
                    z.writestr('research_journal.json',json.dumps(export_json(snapshot),indent=2))
                    z.writestr('METHODOLOGY.txt','Raccoon Radar v1.3\nSwing watchlist entries are manually entered and unverified.\nRead-only SPY/QQQ ETF research. No options P&L.\nStrict 5-minute per-symbol spacing; same-timestamp setup ties alphabetical.\n09:40-11:30 ET; last 2 observed sessions holdout. This is a fixed chronological holdout, NOT rolling walk-forward.\nReusing a viewed holdout for tuning invalidates its untouched status.\nRolling evaluation uses expanding train >=10 observed sessions, disjoint 5-session evaluation blocks; retrospective, not pristine holdout.\nDay-level min/max are realized 3m close-to-close directional returns, NOT intrabar adverse excursion.\nSPY/QQQ and sessions may be correlated. No causal or predictive claim.\n')
                    for filename in ('strategy_validation.py','setup_detective.py','price_action_engine.py','performance_intelligence.py','research_journal.py','validation_intelligence.py','swing_watchlist.py','volume_discovery.py'):
                        z.write(Path(__file__).resolve().parent/filename,'source/'+filename)
            messagebox.showinfo('Archive exported',f'Portable archive saved to:\n{destination}\n\nContains all stored candles, journal entries, validation snapshots and methodology.')
        except Exception as exc:messagebox.showerror('Archive error',str(exc))

    def period_summaries(self, events):
        from collections import defaultdict
        from setup_detective import summary
        grouped = defaultdict(list)
        for event in events:
            t = datetime.strptime(event['time'], '%Y-%m-%d %H:%M:%S')
            period = '09:30-10:29' if t.hour == 9 or (t.hour == 10 and t.minute < 30) else ('10:30-11:29' if t.hour == 10 or (t.hour == 11 and t.minute < 30) else ('11:30-13:29' if t.hour in (11,12) or (t.hour == 13 and t.minute < 30) else '13:30-15:59'))
            grouped[period].append(event)
        result=[]
        for period, records in sorted(grouped.items()):
            for item in summary(records):
                result.append(dict(symbol=item['symbol'], period=period, **{k: ('—' if v is None else v) for k,v in item.items() if k!='symbol'}))
        return result

    def fetch_range(self):
        if self.candle_busy:
            self.note.set('A candle fetch is already in progress.'); return
        try:
            start=datetime.strptime(self.range_start.get().strip(), '%Y-%m-%d').date()
            end=datetime.strptime(self.range_end.get().strip(), '%Y-%m-%d').date()
            from zoneinfo import ZoneInfo
            today=datetime.now(ZoneInfo('America/New_York')).date()
            if start>end: raise ValueError('Start date must be on or before end date.')
            if end>=today: raise ValueError('Use completed past dates only; end date must be before today ET.')
            days=(end-start).days+1
            if days>21: raise ValueError('Limit each request to 21 calendar days to avoid excessive OpenD requests.')
        except ValueError as exc:
            messagebox.showerror('Date range',str(exc));return
        self.candle_busy=True
        self.note.set(f'Fetching historical candles {start} through {end} from OpenD; please wait...')
        threading.Thread(target=self._fetch_range_worker,args=(start,end),daemon=True).start()

    def _fetch_range_worker(self,start,end):
        q=None
        try:
            from moomoo import OpenQuoteContext, RET_OK, KLType
            from zoneinfo import ZoneInfo
            now=datetime.now(ZoneInfo('America/New_York'))
            q=OpenQuoteContext(host='127.0.0.1',port=11111)
            combined=[]; sessions=[]; failures=[]
            day=start
            while day<=end:
                if day.weekday()<5:
                    date=day.isoformat(); day_rows=[]; ok=True
                    for symbol in ('US.SPY','US.QQQ'):
                        ret,data,_=q.request_history_kline(symbol,start=date,end=date,ktype=KLType.K_1M,max_count=1000)
                        if ret!=RET_OK or not hasattr(data,'iterrows'):
                            failures.append(f'{date} {symbol}: {str(data)[:80]}');ok=False;break
                        for _,bar in data.iterrows():
                            stamp=str(bar.get('time_key',''))
                            try: bt=datetime.strptime(stamp,'%Y-%m-%d %H:%M:%S')
                            except ValueError:continue
                            if bt.date()!=day or not ((bt.hour==9 and bt.minute>=30) or (10<=bt.hour<=15)):continue
                            try:record=dict(time=stamp,symbol=symbol,**{k:float(bar[k]) for k in ('open','high','low','close','volume')})
                            except (KeyError,ValueError,TypeError):continue
                            day_rows.append(record)
                    if ok and day_rows:
                        combined.extend(day_rows);sessions.append(date)
                day+=timedelta(days=1)
            combined.sort(key=lambda r:(r['time'],r['symbol']))
            if not combined: raise RuntimeError('No usable historical candles. '+('; '.join(failures[:2]) if failures else 'Check selected dates and OpenD history permissions.'))
            self.candle_queue.put(('range_success',analyze(combined),combined,sessions,failures,now.isoformat(timespec='seconds')))
        except Exception as exc:self.candle_queue.put(('error',str(exc)))
        finally:
            if q is not None:
                try:q.close()
                except Exception:pass

    def _refresh_signal_labels(self, rows=None, error=None):
        from datetime import timezone
        from scanner_reliability import evaluate_signals
        if rows is not None:
            self.signal_rows = list(rows)
        if error is not None:
            self.signal_rows = []
        # No reviewed scanner-source/availability binding or freshness policy yet.
        # Keep raw rows in the table; do not promote their text into verified bias.
        self.signal_evidence = evaluate_signals(
            getattr(self, 'signal_rows', []), now=datetime.now(timezone.utc))
        for symbol, label in [('SPY', self.spy_label), ('QQQ', self.qqq_label)]:
            label.config(text=self.signal_evidence[symbol]['display'])

    def load_csv(self):
        path = filedialog.askopenfilename(title='Choose raccoon_radar_log.csv', filetypes=[('CSV files','*.csv')])
        if not path: return
        try:
            rows, headers = self.read_csv(path)
            if 'symbol' not in headers or 'bias' not in headers:
                raise ValueError('Expected signal CSV with symbol and bias columns.')
            self.csv_path = path
            self.last_mtimes[path] = Path(path).stat().st_mtime_ns
            self.fill(self.signal_tree, rows)
            self.rows_label.config(text=str(len(rows)))
            self._refresh_signal_labels(rows)
            self.note.set(f'Loaded {len(rows)} recorded signal rows from {path}. Static snapshot; bias source/availability/freshness UNVERIFIED, not a live feed.')
            self.tabs.select(self.signals_frame)
        except Exception as exc:
            self._refresh_signal_labels(error=str(exc))
            messagebox.showerror('Could not load signal CSV',str(exc))

    def load_trade_csv(self):
        path = filedialog.askopenfilename(title='Choose shadow trade journal CSV', filetypes=[('CSV files','*.csv')])
        if not path: return
        try:
            rows, headers = self.read_csv(path)
            if 'contract' not in headers or 'pnl' not in headers:
                raise ValueError('Expected shadow journal CSV with contract and pnl columns.')
            self.trade_path = path
            self.last_mtimes[path] = Path(path).stat().st_mtime_ns
            self.fill(self.trade_tree, rows)
            self.note.set(f'Loaded {len(rows)} historical/synthetic shadow-trade rows from {path}. Verify whether your source is sample data.')
            self.tabs.select(self.trades_frame)
        except Exception as exc:
            messagebox.showerror('Could not load trade CSV',str(exc))

    def fill(self, tree, rows):
        tree.delete(*tree.get_children())
        for row in rows[-5000:]:
            tree.insert('', 'end', values=[str(row.get(c,''))[:120] for c in tree['columns']])

    def start(self):
        if not (self.csv_path or self.trade_path):
            messagebox.showinfo('Choose a file', 'Load a signal or trade CSV first.')
            return
        self.active = True
        self.status.config(text='CSV AUTO-REFRESH')
        self.note.set('Watching loaded CSV files every 5 seconds. This does NOT start or stop the scanner.')
        self.poll_files(force=True)

    def poll(self):
        try:
            if self.active:
                self.poll_files()
        finally:
            self.after(self.refresh_ms, self.poll)

    def poll_files(self, force=False):
        for path, kind in ((self.csv_path, 'signal'), (self.trade_path, 'trade')):
            if not path:
                continue
            try:
                mtime = Path(path).stat().st_mtime_ns
                if not force and mtime == self.last_mtimes.get(path):
                    if kind == 'signal':
                        self._refresh_signal_labels()
                    continue
                rows, headers = self.read_csv(path)
                if kind == 'signal':
                    if not {'symbol', 'bias'}.issubset(headers):
                        raise ValueError('Signal CSV is missing symbol or bias')
                    self.fill(self.signal_tree, rows)
                    self.rows_label.config(text=str(len(rows)))
                    self._refresh_signal_labels(rows)
                else:
                    if not {'contract', 'pnl'}.issubset(headers):
                        raise ValueError('Trade CSV is missing contract or pnl')
                    self.fill(self.trade_tree, rows)
                self.last_mtimes[path] = mtime
                self.note.set(f'Updated {kind} CSV: {len(rows)} rows. Source: {path}' +
                              (' | Bias evidence UNVERIFIED; raw snapshot only.' if kind == 'signal' else ''))
            except Exception as exc:
                if kind == 'signal':
                    self._refresh_signal_labels(error=str(exc))
                self.status.config(text='CSV READ ERROR')
                self.note.set(f'Could not refresh {kind} CSV: {exc}. Retrying; no data invented.')

    def choose_scanner(self):
        path = filedialog.askopenfilename(title='Choose your existing raccoon_radar_v3.py', filetypes=[('Python scripts', '*.py')])
        if path:
            self.scanner_path = Path(path)
            self.note.set(f'Scanner selected: {path}. No scanner has started yet.')

    def find_scanner(self):
        if self.scanner_path and self.scanner_path.is_file():
            return self.scanner_path
        downloads = Path.home() / 'Downloads'
        candidates = [downloads / 'raccoon_radar_v3.py', downloads / 'raccoon_radar_v3' / 'raccoon_radar_v3.py']
        return next((p for p in candidates if p.is_file()), None)

    def start_scanner(self):
        if self.scanner_proc is not None and self.scanner_proc.poll() is None:
            self.note.set('Scanner is already running. No duplicate launched.')
            return
        path = self.find_scanner()
        if path is None:
            messagebox.showinfo('Scanner not found', 'Click Choose scanner .py and select your existing raccoon_radar_v3.py file. No files were changed.')
            return
        # v0.3 intentionally only launches our reviewed, read-only scanner v3.
        if path.name.lower() != 'raccoon_radar_v3.py':
            messagebox.showerror('Wrong script', 'Only raccoon_radar_v3.py is supported in this read-only release.')
            return
        try:
            kwargs = {'cwd': str(path.parent), 'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT,
                      'text': True, 'bufsize': 1}
            if sys.platform == 'win32':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            self.scanner_proc = subprocess.Popen([sys.executable, '-u', str(path), '--watch'], **kwargs)
            self.scanner_path = path
            self.scanner_errors = 0
            self.scanner_label.config(text='SCANNER: RUNNING', fg='#34d399')
            self.status.config(text='SCANNER RUNNING')
            self.note.set('Scanner process launched; checking for OpenD data. No trading orders.')
            log = path.parent / 'raccoon_radar_log.csv'
            if log.exists():
                self.csv_path = str(log)
                self.active = True
                self.poll_files(force=True)
            threading.Thread(target=self.read_scanner_output, args=(self.scanner_proc,), daemon=True).start()
        except Exception as exc:
            self.scanner_proc = None
            self.scanner_label.config(text='SCANNER: START ERROR', fg='#fb7185')
            messagebox.showerror('Could not start scanner', str(exc))

    def read_scanner_output(self, proc):
        try:
            for line in proc.stdout:
                if line.strip():
                    self.scanner_events.put(('line', line.strip()))
        except Exception as exc:
            self.scanner_events.put(('line', f'Could not read scanner output: {exc}'))
        finally:
            self.scanner_events.put(('exit', proc))

    def process_scanner_events(self):
        try:
            for _ in range(100):
                try:
                    kind, value = self.scanner_events.get_nowait()
                except queue.Empty:
                    break
                if kind == 'line':
                    line = value
                    if 'OpenD connection error' in line or 'unavailable (' in line:
                        self.scanner_errors += 1
                        self.scanner_label.config(text='SCANNER: DATA ERROR', fg='#fb7185')
                    elif 'Logged ' in line and self.scanner_proc and self.scanner_proc.poll() is None:
                        self.scanner_errors = 0
                        self.scanner_label.config(text='SCANNER: RUNNING', fg='#34d399')
                        log = self.scanner_path.parent / 'raccoon_radar_log.csv'
                        if log.exists():
                            self.csv_path = str(log)
                            self.active = True
                            self.poll_files(force=True)
                    self.note.set('Scanner: ' + line[:200])
                elif kind == 'exit' and value is self.scanner_proc:
                    code = value.poll()
                    self.scanner_label.config(text='SCANNER: STOPPED' if code == 0 else f'SCANNER: EXITED ({code})', fg='#b8a3df' if code == 0 else '#fb7185')
                    self.status.config(text='OFFLINE / STOPPED')
        finally:
            self.after(250, self.process_scanner_events)

    def stop_scanner(self):
        proc = self.scanner_proc
        if proc is None or proc.poll() is not None:
            self.scanner_label.config(text='SCANNER: STOPPED', fg='#b8a3df')
            self.note.set('Scanner is not running.')
            return
        try:
            proc.terminate()
            self.scanner_label.config(text='SCANNER: STOPPINGâ€¦', fg='#fbbf24')
            self.note.set('Stop requested for the scanner process started by this dashboard.')
        except Exception as exc:
            messagebox.showerror('Stop failed', str(exc))

    def on_close(self):
        proc = self.scanner_proc
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Never leave a scanner process launched by the UI running after close.
                proc.kill()
            except Exception:
                pass
        self.destroy()

    def stop(self):
        self.active = False
        self.status.config(text='OFFLINE / STOPPED')
        self.note.set('CSV auto-refresh stopped. This does NOT stop any separate scanner process.')

if __name__ == '__main__':
    Dashboard().mainloop()
