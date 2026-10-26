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
        self.title('ðŸ¦ Raccoon Radar | Research Dashboard v1.0')
        self.geometry('1190x760')
        self.minsize(940, 600)
        self.configure(bg='#151724')
        self.active = False
        self.scanner_proc = None
        self.scanner_path = None
        self.scanner_events = queue.Queue()
        self.scanner_errors = 0
        self.csv_path = None
        self.trade_path = None
        self.last_mtimes = {}
        self.refresh_ms = 5000
        self.candle_queue = queue.Queue()
        self.candle_busy = False
        self.live_candles = False
        self.last_ohlcv = []
        self.validation_events = []
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
        top = tk.Frame(self, bg='#151724'); top.pack(fill='x', padx=22, pady=(22, 8))
        tk.Label(top, text='ðŸ¦ RACCOON RADAR', bg='#151724', fg='#f4efff', font=('Segoe UI', 24, 'bold')).pack(side='left')
        tk.Label(top, text='v1.0  |  VALIDATION LAB  |  NO ORDERS', bg='#151724', fg='#b8a3df', font=('Segoe UI', 10, 'bold')).pack(side='right')
        tk.Label(self, text='A visual home for your SPY / QQQ research. Load your existing CSV to inspect recorded observations.', bg='#151724', fg='#b7b8cb', font=('Segoe UI', 11)).pack(anchor='w', padx=24, pady=(0, 15))
        strip = tk.Frame(self, bg='#151724'); strip.pack(fill='x', padx=20)
        self.status = self.tile(strip, 'MODE', 'OFFLINE / IDLE', 0)
        self.rows_label = self.tile(strip, 'ROWS LOADED', '0', 1)
        self.spy_label = self.tile(strip, 'SPY LATEST BIAS', 'â€”', 2)
        self.qqq_label = self.tile(strip, 'QQQ LATEST BIAS', 'â€”', 3)
        scanner_controls = tk.Frame(self, bg='#151724'); scanner_controls.pack(fill='x', padx=23, pady=(8,0))
        self.scanner_label = tk.Label(scanner_controls, text='SCANNER: STOPPED', bg='#151724', fg='#b8a3df', font=('Segoe UI', 10, 'bold'))
        self.scanner_label.pack(side='left', padx=(0,15))
        self.button(scanner_controls, 'Start scanner', self.start_scanner, bg='#276653').pack(side='left', padx=(0,10))
        self.button(scanner_controls, 'Stop scanner', self.stop_scanner, bg='#703f57').pack(side='left', padx=(0,10))
        self.button(scanner_controls, 'Choose scanner .py', self.choose_scanner).pack(side='left')
        controls = tk.Frame(self, bg='#151724'); controls.pack(fill='x', padx=23, pady=(9,3))
        self.button(controls, 'Analyze candle CSV', self.load_price_action, bg='#37547a').pack(side='left', padx=(0,8))
        self.button(controls, 'Fetch latest session', self.fetch_candles, bg='#276653').pack(side='left', padx=(0,8))
        self.button(controls, 'Setup detective', self.run_detective, bg='#37547a').pack(side='left', padx=(0,8))
        self.button(controls, 'Load signal CSV', self.load_csv).pack(side='left', padx=(0,8))
        self.button(controls, 'Load trade journal', self.load_trade_csv).pack(side='left')
        range_controls = tk.Frame(self, bg='#151724'); range_controls.pack(fill='x', padx=23, pady=(2,10))
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
        tk.Label(validation_controls,text='Window ET: 09:40–11:30  |  Holdout: last 2 sessions  |  Strict 5m symbol spacing',bg='#151724',fg='#b8a3df').pack(side='left')
        self.note = tk.StringVar(value='Scanner is stopped. This app may launch the existing read-only Moomoo scanner; no order APIs are used.')
        tk.Label(self, textvariable=self.note, bg='#151724', fg='#b8a3df', font=('Segoe UI', 10), wraplength=990, justify='left').pack(anchor='w', padx=24, pady=(0,10))
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill='both', expand=True, padx=22, pady=(0,18))
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
        self.signal_tree = self.tree(self.signals_frame, ['bar_time_et','symbol','close','bias','volume_ratio','pattern'])
        self.trade_tree = self.tree(self.trades_frame, ['entry','symbol','contract','side','exit','pnl','reason'])
        self.price_tree = self.tree(self.price_frame, ['time','symbol','close','auction_proxy','setup','range_ratio','volume_ratio'])
        self.detective_tree = self.tree(self.detective_frame, ['symbol','setup','events','1m_n','1m_winrate','1m_avg','3m_n','3m_winrate','3m_avg','5m_n','5m_winrate','5m_avg'])
        self.period_tree = self.tree(self.period_frame, ['symbol','period','setup','events','1m_n','1m_winrate','1m_avg','3m_n','3m_winrate','3m_avg','5m_n','5m_winrate','5m_avg'])
        self.daily_tree = self.tree(self.daily_frame, ['day','symbol','setup','events','sample','1m_n','1m_winrate','1m_avg','3m_n','3m_winrate','3m_avg','5m_n','5m_winrate','5m_avg'])
        self.consistency_tree = self.tree(self.consistency_frame, ['symbol','setup','events','sessions','positive_days_3m','days_with_3m','3m_daily_avg','3m_winrate','sample','warning'])
        self.validation_tree=self.tree(self.validation_frame,['symbol','setup','train_n','train_days','train_win_%','train_avg_%','test_n','test_days','test_win_%','test_avg_%','warning'])
        self.weekday_tree=self.tree(self.weekday_frame,['symbol','setup','weekday','events','sessions','win_%','avg_%','warning'])
        foot = tk.Label(self, text='Research only. Candle proxies are exploratory, not validated signals. Option stops and daily limits cannot guarantee fills or maximum losses.', bg='#151724', fg='#8d90a9', font=('Segoe UI', 9))
        foot.pack(pady=(0,14))

    def tile(self, parent, name, value, column):
        frame = tk.Frame(parent, bg='#24263b', padx=17, pady=14)
        frame.grid(row=0, column=column, sticky='nsew', padx=4)
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(frame, text=name, bg='#24263b', fg='#aaa8c4', font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        label = tk.Label(frame, text=value, bg='#24263b', fg='#f1ecff', font=('Segoe UI', 15, 'bold'))
        label.pack(anchor='w', pady=(8,0))
        return label

    def button(self, parent, text, command, bg='#54417d'):
        return tk.Button(parent, text=text, command=command, bg=bg, fg='white', activebackground='#745ba6', activeforeground='white', relief='flat', padx=14, pady=9, font=('Segoe UI', 10, 'bold'), cursor='hand2')

    def tree(self, parent, cols):
        container = tk.Frame(parent, bg='#23263a'); container.pack(fill='both', expand=True)
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
                display.append({k: ('â€”' if v is None else v) for k,v in row.items()})
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
            self.fill(self.weekday_tree,weekdays(events))
            self.tabs.select(self.validation_frame)
            self.note.set(f'Validation: {len(events)} strictly spaced events. {info} ETF moves only; no options P/L. Weekday results are descriptive, not predictions.')
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
                'app_version': '1.0',
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
                z.writestr('README.txt', 'Raccoon Radar research export\nHistorical ETF price-action study only. No options fills, slippage, spread, fees, or validated trading edge.\n')
            self.note.set(f'Exported {len(self.last_ohlcv)} candles and {len(analyzed)} analyzed events to {destination}')
            messagebox.showinfo('Export complete', f'Research ZIP saved to:\n{destination}\n\nUpload this ZIP to ChatGPT for analysis.')
        except Exception as exc:
            messagebox.showerror('Export failed', str(exc))

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
                result.append(dict(symbol=item['symbol'], period=period, **{k: ('â€”' if v is None else v) for k,v in item.items() if k!='symbol'}))
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
            for sym, label in [('SPY',self.spy_label),('QQQ',self.qqq_label)]:
                matches = [r for r in rows if sym in r.get('symbol','').upper()]
                label.config(text=(matches[-1].get('bias') or 'â€”') if matches else 'â€”')
            self.note.set(f'Loaded {len(rows)} recorded signal rows from {path}. This is a static snapshot, not a live feed.')
            self.tabs.select(self.signals_frame)
        except Exception as exc:
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
                    continue
                rows, headers = self.read_csv(path)
                if kind == 'signal':
                    if not {'symbol', 'bias'}.issubset(headers):
                        raise ValueError('Signal CSV is missing symbol or bias')
                    self.fill(self.signal_tree, rows)
                    self.rows_label.config(text=str(len(rows)))
                    for sym, label in [('SPY', self.spy_label), ('QQQ', self.qqq_label)]:
                        matches = [r for r in rows if sym in r.get('symbol', '').upper()]
                        label.config(text=(matches[-1].get('bias') or 'â€”') if matches else 'â€”')
                else:
                    if not {'contract', 'pnl'}.issubset(headers):
                        raise ValueError('Trade CSV is missing contract or pnl')
                    self.fill(self.trade_tree, rows)
                self.last_mtimes[path] = mtime
                self.note.set(f'Updated {kind} CSV: {len(rows)} rows. Source: {path}')
            except Exception as exc:
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

