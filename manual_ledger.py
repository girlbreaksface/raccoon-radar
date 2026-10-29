"""Synthetic-only manual journal draft. No research DB, provider, quotes or orders.

Explicit NEW directories only. This is a cooperative local-file boundary, not an
OS filesystem sandbox. Plaintext records/backups/exports; never use real records.
"""
import csv
import hashlib
from importlib import metadata, resources
import json
import os
from pathlib import Path
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from functools import lru_cache
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

SCALE = 100000000
FEE_SCALE = SCALE // 100
APPLICATION_ID = 0x524C4447
VERSION = 1
POLICY = "synthetic-fifo-v1"
TZ_VERSION = "2026.5"
DB = "ledger.sqlite3"
MARKER = "ledger-identity.json"
NOTICE = "SYNTHETIC DRAFT ONLY. Plaintext local files. No real records, quotes or orders."
REVISION_FIELDS = ("fill_id", "revision_id", "predecessor", "position_id", "contract",
                   "side", "quantity", "premium_units", "fee_cents", "effective_at_utc",
                   "entered_time", "timezone", "fold", "tie", "reason", "tick_units",
                   "tick_authority", "warnings", "synthetic", "voided",
                   "recorded_sequence", "ordinal", "recorded_at_utc")
ALLOCATION_FIELDS = ("position_id", "entry_fill_id", "exit_fill_id", "quantity",
                     "entry_fee_cents", "exit_fee_cents", "gross_usd", "net_usd",
                     "net_display_usd", "effective_at_utc")

class LedgerError(ValueError):
    pass

class RecoveryRequired(LedgerError):
    pass

def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",",":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise LedgerError("Invalid JSON value") from error

def _hash(value):
    return hashlib.sha256(value).hexdigest()

def _load_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise LedgerError("Duplicate JSON field")
            result[key]=value
        return result
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(LedgerError("Nonfinite JSON")))
    except (ValueError, TypeError) as error:
        raise LedgerError("Invalid JSON") from error

def _id(value):
    if type(value) is not str:
        raise LedgerError("Explicit UUID required")
    try:
        if str(UUID(value)) != value: raise ValueError()
    except ValueError as error:
        raise LedgerError("Canonical UUID required") from error
    return value

def _text(value, limit=4096):
    if type(value) is not str or not value.strip() or len(value)>limit or "\0" in value:
        raise LedgerError("Invalid bounded text")
    return value

def _units(value, places, maximum=1000000):
    if (type(value) is not str or len(value)>32 or
            re.fullmatch(r"[0-9]+(?:\.[0-9]{1,"+str(places)+r"})?",value) is None):
        raise LedgerError("Plain nonnegative decimal required")
    whole, _, fractional=value.partition(".")
    amount=int(whole)*10**places+int((fractional+"0"*places)[:places])
    if amount>maximum*10**places: raise LedgerError("Amount exceeds draft limit")
    return amount

def _usd(units):
    sign="-" if units<0 else ""
    amount=abs(units)
    return f"{sign}{amount//SCALE}.{amount%SCALE:08d}"

def _cents(units):
    return (1 if units>=0 else -1)*((abs(units)+FEE_SCALE//2)//FEE_SCALE)

def _display(units):
    cents=_cents(units)
    return ("-" if cents<0 else "")+f"{abs(cents)//100}.{abs(cents)%100:02d}"

@lru_cache(maxsize=1)
def _eastern():
    try:
        if metadata.version("tzdata") != TZ_VERSION:
            raise LedgerError("Install exact journal tzdata dependency")
        with resources.files("tzdata.zoneinfo").joinpath("America/New_York").open("rb") as source:
            return ZoneInfo.from_file(source,key="America/New_York")
    except (ImportError, OSError, metadata.PackageNotFoundError) as error:
        raise LedgerError("Pinned timezone data unavailable; no offset fallback") from error

def _stamp(text, zone):
    if type(text) is not str or len(text)>40 or zone not in ("America/New_York","UTC"):
        raise LedgerError("Explicit aware time and supported timezone required")
    try:
        value=datetime.fromisoformat(text.replace("Z","+00:00"))
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError()
        local=value.astimezone(_eastern() if zone=="America/New_York" else timezone.utc)
        if (local.replace(tzinfo=None)!=value.replace(tzinfo=None)
                or local.utcoffset()!=value.utcoffset()):
            raise ValueError()
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00","Z"),local.fold
    except (ValueError, OverflowError) as error:
        raise LedgerError("Nonexistent/ambiguous or inconsistent offset/timezone") from error

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00","Z")

def _contract(raw):
    if type(raw) is not dict or set(raw)!={"symbol","underlying","expiration","strike","right",
                                         "multiplier","currency","deliverable"}:
        raise LedgerError("Complete synthetic standard contract required")
    if (type(raw["symbol"]) is not str or
        re.fullmatch(r"SYNTHETIC_[A-Z0-9_]{1,100}",raw["symbol"]) is None or
        raw["underlying"] not in ("SPY","QQQ") or raw["right"] not in ("CALL","PUT") or
        type(raw["multiplier"]) is not int or raw["multiplier"]!=100 or
        raw["currency"]!="USD" or raw["deliverable"]!="STANDARD_100"):
        raise LedgerError("Only synthetic SPY/QQQ USD standard100 long options supported")
    try:
        expiration=date.fromisoformat(raw["expiration"])
        if expiration.isoformat()!=raw["expiration"]: raise ValueError()
    except (ValueError,TypeError) as error:
        raise LedgerError("Invalid expiration date") from error
    strike=_units(raw["strike"],8)
    if strike<=0: raise LedgerError("Positive strike required")
    return {**raw,"strike":strike}

def _normalize(raw, previous):
    if type(raw) is not dict or raw.get("synthetic") is not True:
        raise LedgerError("Synthetic records only")
    common={"fill_id","revision_id","expected_revision","reason","synthetic"}
    fill_id, revision_id = _id(raw.get("fill_id")),_id(raw.get("revision_id"))
    expected=raw.get("expected_revision")
    if expected is not None: _id(expected)
    if (previous["revision_id"] if previous else None)!=expected:
        raise LedgerError("Stale/missing predecessor; no last-write-wins")
    reason=_text(raw.get("reason"))
    if raw.get("void") is True:
        if previous is None or set(raw)!=common|{"void"}:
            raise LedgerError("Void requires existing fill and explicit minimal command")
        return {**{k:v for k,v in previous.items() if k not in
                   ("recorded_sequence","recorded_at_utc","ordinal")},
                "revision_id":revision_id,"predecessor":expected,"voided":True,"reason":reason}
    required=common|{"position_id","contract","side","quantity","premium","fees",
                     "effective_at","timezone","tie","tick","tick_authority"}
    if set(raw)!=required: raise LedgerError("Missing or unknown fill fields")
    position=_id(raw["position_id"])
    terms=_contract(raw["contract"])
    if previous and (previous["position_id"]!=position or previous["contract"]!=terms):
        raise LedgerError("Position/contract identities cannot be corrected in place")
    quantity=raw["quantity"]
    if type(quantity) is not int or not 1<=quantity<=100000:
        raise LedgerError("Quantity must be whole contracts1..100000")
    side=raw["side"]
    if side not in ("BUY_TO_OPEN","SELL_TO_CLOSE","MANUAL_ZERO_CLOSE"):
        raise LedgerError("Unsupported manual side")
    premium=_units(raw["premium"],8)
    fees=_units(raw["fees"],2,100000000)
    if (side=="BUY_TO_OPEN" and premium==0 or
        side=="SELL_TO_CLOSE" and premium==0 or side=="MANUAL_ZERO_CLOSE" and premium!=0):
        raise LedgerError("Zero close must be explicit MANUAL_ZERO_CLOSE")
    effective,fold=_stamp(raw["effective_at"],raw["timezone"])
    if type(raw["tie"]) is not int or not 0<=raw["tie"]<=1000000:
        raise LedgerError("Explicit nonnegative tie sequence required")
    if raw["tick_authority"] not in ("UNKNOWN","USER_ASSERTED"):
        raise LedgerError("No verified tick authority in synthetic draft")
    tick=None if raw["tick"] is None else _units(raw["tick"],8)
    if tick is not None and tick<=0: raise LedgerError("Positive reference tick required")
    warnings=["UNVERIFIED_TICK_AUTHORITY"]
    if tick and premium%tick: warnings.append("OFF_REFERENCE_TICK")
    local=datetime.fromisoformat(effective.replace("Z","+00:00")).astimezone(_eastern())
    if local.date().isoformat()>terms["expiration"]: warnings.append("AFTER_EXPIRATION_DATE_UNVERIFIED")
    return dict(fill_id=fill_id,revision_id=revision_id,predecessor=expected,
                position_id=position,contract=terms,side=side,quantity=quantity,
                premium_units=premium,fee_cents=fees,effective_at_utc=effective,
                entered_time=raw["effective_at"],timezone=raw["timezone"],fold=fold,
                tie=raw["tie"],reason=reason,tick_units=tick,
                tick_authority=raw["tick_authority"],warnings=warnings,
                synthetic=True,voided=False)

def _project(records,positions,sequence,ledger_id):
    latest={}
    for row in records:
        prior=latest.get(row["fill_id"])
        if row["predecessor"]!=(prior["revision_id"] if prior else None):
            raise LedgerError("Broken correction chain")
        latest[row["fill_id"]]=row
    active=[v for v in latest.values() if not v["voided"]]
    allocations=[]; statuses=[]
    for position,terms in positions.items():
        rows=sorted((r for r in active if r["position_id"]==position),
                    key=lambda r:(r["effective_at_utc"],r["tie"]))
        if len({(r["effective_at_utc"],r["tie"]) for r in rows})!=len(rows):
            raise LedgerError("Ambiguous equal-time fill ordering")
        lots=[]; remaining=closed=0; had_flat=False
        for row in rows:
            if row["contract"]!=terms: raise LedgerError("Contract mismatch")
            if row["side"]=="BUY_TO_OPEN":
                if had_flat: raise LedgerError("New cycle after flat requires new position")
                remaining+=row["quantity"]
                if remaining>100000: raise LedgerError("Open position quantity exceeds limit")
                lots.append(dict(row=row,closed=0))
                continue
            if row["quantity"]>remaining: raise LedgerError("Oversell/negative inventory prefix")
            consumed=0
            for lot in lots:
                opening=lot["row"]
                available=opening["quantity"]-lot["closed"]
                matched=min(available,row["quantity"]-consumed)
                if not matched: continue
                before=lot["closed"]; after=before+matched
                entry_fee=(opening["fee_cents"]*after//opening["quantity"]-
                           opening["fee_cents"]*before//opening["quantity"])
                exit_fee=(row["fee_cents"]*(consumed+matched)//row["quantity"]-
                          row["fee_cents"]*consumed//row["quantity"])
                gross=(row["premium_units"]-opening["premium_units"])*100*matched
                net=gross-(entry_fee+exit_fee)*FEE_SCALE
                allocations.append(dict(position_id=position,entry_fill_id=opening["fill_id"],
                    exit_fill_id=row["fill_id"],quantity=matched,entry_fee_cents=entry_fee,
                    exit_fee_cents=exit_fee,gross_usd=_usd(gross),net_usd=_usd(net),
                    net_display_usd=_display(net),effective_at_utc=row["effective_at_utc"]))
                lot["closed"]=after; consumed+=matched
                if consumed==row["quantity"]: break
            remaining-=row["quantity"]; closed+=row["quantity"]
            had_flat=remaining==0
        subset=[a for a in allocations if a["position_id"]==position]
        total=sum(_signed_units(a["net_usd"]) for a in subset)
        history=any(r["position_id"]==position for r in records)
        status=("VOIDED" if history else "EMPTY") if not rows else (
                "CLOSED" if not remaining else "PARTIALLY_CLOSED" if closed else "OPEN")
        unrecognized=sum(l["row"]["fee_cents"]-
                         l["row"]["fee_cents"]*l["closed"]//l["row"]["quantity"] for l in lots)
        statuses.append(dict(position_id=position,contract=terms,status=status,remaining=remaining,
                             closed_quantity=closed,unrecognized_entry_fee_cents=unrecognized,
                             realized_usd=_usd(total)))
    summaries={kind:{} for kind in ("daily","weekly","monthly")}
    for row in allocations:
        local=datetime.fromisoformat(row["effective_at_utc"].replace("Z","+00:00")).astimezone(_eastern())
        iso=local.isocalendar()
        keys={"daily":local.date().isoformat(),"weekly":f"{iso.year}-W{iso.week:02d}",
              "monthly":local.strftime("%Y-%m")}
        for kind,key in keys.items():
            group=summaries[kind].setdefault(key,[])
            group.append(row)
    for kind,groups in summaries.items():
        for key,rows in list(groups.items()):
            net=sum(_signed_units(r["net_usd"]) for r in rows)
            groups[key]=dict(net_usd=_usd(net),net_display_usd=_display(net),
                            gross_usd=_usd(sum(_signed_units(r["gross_usd"]) for r in rows)),
                            entry_fee_cents=sum(r["entry_fee_cents"] for r in rows),
                            exit_fee_cents=sum(r["exit_fee_cents"] for r in rows),
                            allocation_count=len(rows),exit_fill_count=len({r["exit_fill_id"] for r in rows}),
                            closed_contracts=sum(r["quantity"] for r in rows),
                            rounding_difference_cents=_cents(net)-sum(_cents(_signed_units(r["net_usd"])) for r in rows))
    return dict(ledger_id=ledger_id,synthetic_only=True,policy=POLICY,tzdata_version=TZ_VERSION,
                reporting_timezone="America/New_York",snapshot_sequence=sequence,
                active_fills=active,revisions=records,positions=statuses,
                allocations=allocations,summaries=summaries,
                limitations=[NOTICE,"Manual assertions; not broker/tax/market evidence.",
                             "Summaries use exit-effective civil dates, not exchange sessions."])

def _signed_units(value):
    return (-1 if value.startswith("-") else 1)*_units(value.lstrip("-"),8,10**30)

SCHEMA = """
CREATE TABLE meta(singleton INTEGER PRIMARY KEY CHECK(singleton=1), body TEXT NOT NULL);
CREATE TABLE positions(position_id TEXT PRIMARY KEY, contract TEXT NOT NULL);
CREATE TABLE commands(seq INTEGER PRIMARY KEY AUTOINCREMENT, command_id TEXT NOT NULL UNIQUE,
 request TEXT NOT NULL, request_hash TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE TABLE revisions(revision_id TEXT PRIMARY KEY, fill_id TEXT NOT NULL,
 command_seq INTEGER NOT NULL REFERENCES commands(seq), ordinal INTEGER NOT NULL,
 predecessor TEXT UNIQUE REFERENCES revisions(revision_id), payload TEXT NOT NULL,
 payload_hash TEXT NOT NULL, UNIQUE(command_seq,ordinal), UNIQUE(command_seq,fill_id));
"""
for _table in ("meta","positions","commands","revisions"):
    for _action in ("UPDATE","DELETE"):
        SCHEMA+=f"CREATE TRIGGER protect_{_table}_{_action} BEFORE {_action} ON {_table} BEGIN SELECT RAISE(ABORT,'append only'); END;\n"

def _schema_hash(connection):
    rows=connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
    return _hash(_json(rows).encode())

def _identity(path):
    if path.is_symlink(): raise LedgerError("Symbolic links are not supported")
    info=path.stat()
    if info.st_nlink!=1: raise LedgerError("Hard links are not supported")
    return [info.st_dev,info.st_ino]

def _directory(path, *, new=False):
    path=Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise LedgerError("Explicit absolute directory required")
    for part in (path,*path.parents):
        if part.is_symlink(): raise LedgerError("Symlink path components are not supported")
    if new:
        if not path.parent.is_dir(): raise LedgerError("Parent directory must already exist")
        path.mkdir(mode=0o700,exist_ok=False)
    if not path.is_dir(): raise LedgerError("Existing Ledger directory required; Open never creates")
    return path

def _write(path,data):
    with path.open("xb") as output:
        output.write(data); output.flush(); os.fsync(output.fileno())

def _marker(path,ledger_id,kind,schema_hash,**extra):
    value=dict(format="RACCOON_SYNTHETIC_LEDGER",version=VERSION,policy=POLICY,
               ledger_id=ledger_id,kind=kind,synthetic_only=True,
               file_identity=_identity(path/DB),schema_hash=schema_hash,
               schema_code_hash=_hash(SCHEMA.encode()),**extra)
    _write(path/MARKER,(_json(value)+"\n").encode())
    return value

def _check(path, *, sidecars=True):
    path=_directory(path)
    try:
        if (path/MARKER).is_symlink() or (path/MARKER).stat().st_size>10000:
            raise LedgerError("Invalid identity marker")
        marker=_load_json((path/MARKER).read_text(encoding="utf-8"))
        if (marker["format"]!="RACCOON_SYNTHETIC_LEDGER" or marker["version"]!=VERSION or
            marker["synthetic_only"] is not True or marker["policy"]!=POLICY or
            marker["kind"] not in ("STORE","BACKUP") or
            marker["schema_code_hash"]!=_hash(SCHEMA.encode()) or
            marker["file_identity"]!=_identity(path/DB)):
            raise LedgerError("Wrong store identity/version; no migration")
        _id(marker["ledger_id"])
        if marker["kind"]=="BACKUP" and marker.get("db_sha256")!=_hash((path/DB).read_bytes()):
            raise LedgerError("Backup hash mismatch")
        if sidecars:
            for suffix in ("-journal","-wal","-shm"):
                extra=path/(DB+suffix)
                if extra.exists() and (suffix!="-journal" or extra.stat().st_size):
                    raise RecoveryRequired("Sidecar present; close writer or explicitly recover known Ledger")
        return path,marker
    except (OSError,KeyError,TypeError) as error:
        raise LedgerError("Missing/invalid Ledger identity; no initialization") from error

def _authorizer(action,first,second,database,trigger):
    if action in (sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH,sqlite3.SQLITE_CREATE_VTABLE,
                  sqlite3.SQLITE_DROP_VTABLE):
        return sqlite3.SQLITE_DENY
    if action==sqlite3.SQLITE_FUNCTION and (second or "").lower() in ("load_extension","readfile","writefile"):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK

@contextmanager
def _connection(path,mode="ro"):
    connection=None
    try:
        connection=sqlite3.connect((path/DB).as_uri()+"?mode="+mode,uri=True,timeout=0.25)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA synchronous=FULL")
        connection.set_authorizer(_authorizer)
        yield connection
    except sqlite3.Error as error:
        raise LedgerError("SQLite operation rejected/failed; store preserved") from error
    finally:
        if connection is not None: connection.close()

def _validate(connection,marker):
    if (connection.execute("PRAGMA application_id").fetchone()[0]!=APPLICATION_ID or
        connection.execute("PRAGMA user_version").fetchone()[0]!=VERSION or
        _schema_hash(connection)!=marker["schema_hash"]):
        raise LedgerError("Schema identity/version mismatch; no migration")
    if connection.execute("PRAGMA quick_check").fetchall()!=[("ok",)]:
        raise LedgerError("Integrity check failed")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise LedgerError("Foreign key check failed")
    info=_load_json(connection.execute("SELECT body FROM meta WHERE singleton=1").fetchone()[0])
    if (info.get("ledger_id")!=marker["ledger_id"] or info.get("synthetic_only") is not True or
        info.get("tzdata_version")!=TZ_VERSION or info.get("policy")!=POLICY):
        raise LedgerError("Ledger metadata mismatch")
    _eastern()
    return info

def _records(connection,sequence):
    records=[]
    query=("SELECT r.revision_id,r.fill_id,r.predecessor,r.payload,r.payload_hash,"
           "r.command_seq,r.ordinal,c.recorded_at FROM revisions r JOIN commands c "
           "ON c.seq=r.command_seq WHERE c.seq<=? ORDER BY c.seq,r.ordinal")
    for revision,fill_id,previous,payload,digest,seq,ordinal,recorded in connection.execute(query,(sequence,)):
        if _hash(payload.encode())!=digest: raise LedgerError("Revision hash mismatch")
        body=_load_json(payload)
        if (body["revision_id"]!=revision or body["fill_id"]!=fill_id or
            body["predecessor"]!=previous or body.get("synthetic") is not True):
            raise LedgerError("Revision metadata mismatch")
        records.append({**body,"recorded_sequence":seq,"ordinal":ordinal,"recorded_at_utc":recorded})
    for request,digest in connection.execute("SELECT request,request_hash FROM commands WHERE seq<=?",(sequence,)):
        if _hash(request.encode())!=digest: raise LedgerError("Command hash mismatch")
    return records

class Ledger:
    def __init__(self,path,readonly):
        self.path=path
        self.readonly=readonly

    @classmethod
    def create(cls,directory,*,synthetic=False):
        if synthetic is not True: raise LedgerError("Only explicit synthetic stores are allowed")
        _eastern()
        path=_directory(directory,new=True)
        _write(path/DB,b"")
        ledger_id=str(uuid4())
        with _connection(path,"rw") as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.executescript("BEGIN IMMEDIATE;\n"+SCHEMA)
            db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            db.execute(f"PRAGMA user_version={VERSION}")
            db.execute("INSERT INTO meta VALUES(1,?)",(_json(dict(ledger_id=ledger_id,
                       synthetic_only=True,policy=POLICY,tzdata_version=TZ_VERSION,created_utc=_now())),))
            db.commit()
            signature=_schema_hash(db)
        _marker(path,ledger_id,"STORE",signature)
        return cls.open(path)

    @classmethod
    def open(cls,directory,*,readonly=False):
        path,marker=_check(directory)
        if marker["kind"]=="BACKUP" and not readonly:
            raise LedgerError("Backups are read-only; restore to a NEW directory")
        with _connection(path) as db:
            _validate(db,marker)
        return cls(path,readonly)

    def apply(self,command_id,fills,*,_fault=None):
        if self.readonly: raise LedgerError("Read-only Ledger")
        _id(command_id)
        if type(fills) is not list or not 1<=len(fills)<=100:
            raise LedgerError("Bounded nonempty command batch required")
        request=_json(dict(synthetic=True,fills=fills))
        if len(request)>1000000: raise LedgerError("Command exceeds draft size limit")
        digest=_hash(request.encode())
        path,marker=_check(self.path)
        if marker["kind"]!="STORE": raise LedgerError("Not a writable store")
        with _connection(path,"rw") as db:
            _validate(db,marker)
            try:
                db.execute("BEGIN IMMEDIATE")
                receipt=db.execute("SELECT seq,request_hash,recorded_at FROM commands WHERE command_id=?",(command_id,)).fetchone()
                if receipt:
                    if receipt[1]!=digest: raise LedgerError("Idempotency key reused with different payload")
                    db.rollback()
                    return dict(sequence=receipt[0],command_id=command_id,recorded_at_utc=receipt[2])
                current_seq=db.execute("SELECT COALESCE(MAX(seq),0) FROM commands").fetchone()[0]
                old=_records(db,current_seq)
                if len(old)+len(fills)>10000: raise LedgerError("Synthetic draft record cap reached")
                latest={r["fill_id"]:r for r in old}
                if any(type(r) is not dict for r in fills):
                    raise LedgerError("Fill records must be mappings")
                fill_ids = [_id(r.get("fill_id")) for r in fills]
                if len(set(fill_ids))!=len(fills):
                    raise LedgerError("One revision per logical fill per command")
                new=[_normalize(r,latest.get(r.get("fill_id"))) for r in fills]
                positions={p:_load_json(c) for p,c in db.execute("SELECT position_id,contract FROM positions ORDER BY rowid")}
                for row in new:
                    position=row["position_id"]; terms=row["contract"]
                    if position in positions and positions[position]!=terms: raise LedgerError("Immutable position contract")
                    if any(c["symbol"]==terms["symbol"] and c!=terms for c in positions.values()):
                        raise LedgerError("Conflicting synthetic contract symbol")
                    if position not in positions:
                        db.execute("INSERT INTO positions VALUES(?,?)",(position,_json(terms)))
                        positions[position]=terms
                recorded=_now()
                seq=db.execute("INSERT INTO commands(command_id,request,request_hash,recorded_at) VALUES(?,?,?,?)",
                               (command_id,request,digest,recorded)).lastrowid
                if _fault: _fault("after_command")
                candidate=old+[{**r,"recorded_sequence":seq,"recorded_at_utc":recorded,"ordinal":i}
                               for i,r in enumerate(new)]
                _project(candidate,positions,seq,marker["ledger_id"])
                for i,row in enumerate(new):
                    payload=_json(row)
                    db.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?,?)",
                               (row["revision_id"],row["fill_id"],seq,i,row["predecessor"],payload,_hash(payload.encode())))
                    if _fault: _fault("after_revision")
                if _fault: _fault("before_commit")
                db.commit()
            except BaseException:
                if db.in_transaction: db.rollback()
                raise
        if _fault: _fault("after_commit")
        return dict(sequence=seq,command_id=command_id,recorded_at_utc=recorded)

    def report(self,*,sequence=None):
        path,marker=_check(self.path)
        with _connection(path) as db:
            db.execute("BEGIN")
            _validate(db,marker)
            latest=db.execute("SELECT COALESCE(MAX(seq),0) FROM commands").fetchone()[0]
            if sequence is None: sequence=latest
            if (type(sequence) is not int or sequence<0 or sequence>latest or
                sequence and db.execute("SELECT 1 FROM commands WHERE seq=?",(sequence,)).fetchone() is None):
                raise LedgerError("Committed command sequence cutoff required")
            records=_records(db,sequence)
            visible_positions={r["position_id"] for r in records}
            positions={p:_load_json(c) for p,c in db.execute("SELECT position_id,contract FROM positions ORDER BY rowid")
                       if p in visible_positions}
            result = _project(records,positions,sequence,marker["ledger_id"])
            result["commands"] = [dict(sequence=seq,command_id=key,request=_load_json(raw),
                                       request_sha256=digest,recorded_at_utc=recorded)
                for seq,key,raw,digest,recorded in db.execute(
                    "SELECT seq,command_id,request,request_hash,recorded_at FROM commands WHERE seq<=? ORDER BY seq",
                    (sequence,))]
            return result

    def export(self,directory,*,sequence=None,_fault=None):
        report=self.report(sequence=sequence)
        target=_directory(directory,new=True)
        _write(target/"report.json",(_json(report)+"\n").encode())
        for name,rows in (("revisions.csv",report["revisions"]),("allocations.csv",report["allocations"])):
            fields = REVISION_FIELDS if name=="revisions.csv" else ALLOCATION_FIELDS
            with (target/name).open("x",encoding="utf-8",newline="") as output:
                writer=csv.DictWriter(output,fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    value={k:(v if k in ("gross_usd","net_usd","net_display_usd") else
                              _safe_csv(_json(v) if isinstance(v,(dict,list)) else v))
                           for k,v in row.items()}
                    writer.writerow(value)
                output.flush(); os.fsync(output.fileno())
        if _fault: _fault("before_export_complete")
        hashes={p.name:_hash(p.read_bytes()) for p in target.iterdir() if p.is_file()}
        manifest=dict(complete=True,synthetic_only=True,plaintext_warning=NOTICE,
                      snapshot_sequence=report["snapshot_sequence"],ledger_id=report["ledger_id"],
                      policy=POLICY,tzdata_version=TZ_VERSION,code_sha256=_hash(Path(__file__).read_bytes()),
                      python_version=__import__("sys").version,sqlite_version=sqlite3.sqlite_version,
                      sha256=hashes,created_utc=_now(),text_sanitizer="apostrophe-leading-formula-v1")
        _write(target/"manifest.json",(_json(manifest)+"\n").encode())
        return target

    def backup(self,directory):
        path,marker=_check(self.path)
        target=_directory(directory,new=True)
        _write(target/DB,b"")
        with _connection(path) as source, _connection(target,"rw") as destination:
            _validate(source,marker)
            source.execute("BEGIN")
            source.execute("SELECT seq FROM commands ORDER BY seq DESC LIMIT 1").fetchall()
            source.backup(destination)
            _validate(destination,marker)
        _marker(target,marker["ledger_id"],"BACKUP",marker["schema_hash"],
                db_sha256=_hash((target/DB).read_bytes()),created_utc=_now())
        return target

    @classmethod
    def restore(cls,backup,directory,*,synthetic=False):
        if synthetic is not True: raise LedgerError("Synthetic restore only")
        source_path,marker=_check(backup)
        if marker["kind"]!="BACKUP": raise LedgerError("Verified backup artifact required")
        cls.open(source_path,readonly=True).report()
        target=_directory(directory,new=True)
        _write(target/DB,b"")
        with _connection(source_path) as source, _connection(target,"rw") as destination:
            source.backup(destination)
            _validate(destination,marker)
        _marker(target,marker["ledger_id"],"STORE",marker["schema_hash"],restored_from_sha256=marker["db_sha256"])
        return cls.open(target)

    @classmethod
    def recover(cls,directory,*,confirm_exclusive=False):
        if confirm_exclusive is not True:
            raise LedgerError("Explicit exclusive ownership confirmation required")
        path,marker=_check(directory,sidecars=False)
        if marker["kind"]!="STORE": raise LedgerError("Recovery of writable synthetic store only")
        if any((path/(DB+s)).exists() for s in ("-wal","-shm")):
            raise LedgerError("WAL recovery unsupported; preserve files")
        archive=path/("recovery-before-"+str(uuid4()))
        archive.mkdir(mode=0o700)
        for name in (DB,MARKER,DB+"-journal"):
            if (path/name).exists(): _write(archive/name,(path/name).read_bytes())
        _write(archive/"raw-capture.json",(_json(dict(kind="RAW_CAPTURE_NOT_VERIFIED_BACKUP",
                    sha256={p.name:_hash(p.read_bytes()) for p in archive.iterdir()},created_utc=_now()))+"\n").encode())
        # Only an explicitly owned file with matching creation identity reaches RW.
        with _connection(path,"rw") as db:
            db.execute("BEGIN EXCLUSIVE")
            _validate(db,marker)
            # A killed pre-commit writer may leave a cold nonzero journal.
            # Let SQLite finalize it, never unlink a journal ourselves.
            db.execute(f"PRAGMA user_version={VERSION}")
            db.commit()
        cls.open(path).report()
        return archive

def _safe_csv(value):
    if isinstance(value,str) and value.lstrip().startswith(("=","+","-","@")):
        return "'"+value
    return value
