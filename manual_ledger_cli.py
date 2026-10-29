"""Manual CLI for synthetic journal testing only. No dashboard/feed integration."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

from manual_ledger import Ledger, LedgerError, NOTICE, _load_json, _write


def main(argv=None):
    parser=argparse.ArgumentParser(description=NOTICE)
    sub=parser.add_subparsers(dest="action",required=True)
    create=sub.add_parser("create")
    create.add_argument("directory",type=Path)
    create.add_argument("--synthetic",action="store_true")
    template=sub.add_parser("template")
    template.add_argument("output",type=Path)
    record=sub.add_parser("record")
    record.add_argument("directory",type=Path)
    record.add_argument("request",type=Path)
    report=sub.add_parser("report")
    report.add_argument("directory",type=Path)
    report.add_argument("--sequence",type=int)
    export=sub.add_parser("export")
    export.add_argument("directory",type=Path)
    export.add_argument("destination",type=Path)
    export.add_argument("--sequence",type=int)
    backup=sub.add_parser("backup")
    backup.add_argument("directory",type=Path)
    backup.add_argument("destination",type=Path)
    restore=sub.add_parser("restore")
    restore.add_argument("backup",type=Path)
    restore.add_argument("destination",type=Path)
    restore.add_argument("--synthetic",action="store_true")
    recover=sub.add_parser("recover")
    recover.add_argument("directory",type=Path)
    recover.add_argument("--confirm-exclusive",action="store_true")
    args=parser.parse_args(argv)
    print(NOTICE,file=sys.stderr)
    try:
        if args.action=="create":
            ledger=Ledger.create(args.directory,synthetic=args.synthetic)
            result=dict(directory=str(ledger.path),synthetic_only=True)
        elif args.action=="template":
            if not args.output.is_absolute():
                raise LedgerError("Explicit absolute output filename required")
            payload=dict(command_id=str(uuid4()),fills=[dict(fill_id=str(uuid4()),
                revision_id=str(uuid4()),expected_revision=None,position_id=str(uuid4()),
                contract=dict(symbol="SYNTHETIC_SPY_CALL",underlying="SPY",
                    expiration="2030-12-20",strike="500",right="CALL",multiplier=100,
                    currency="USD",deliverable="STANDARD_100"),side="BUY_TO_OPEN",
                quantity=3,premium="1.00",fees="0.01",effective_at="2026-10-23T10:00:00-04:00",
                timezone="America/New_York",tie=0,reason="Synthetic example; edit before saving",
                tick="0.01",tick_authority="USER_ASSERTED",synthetic=True)])
            _write(args.output,(json.dumps(payload,indent=2,allow_nan=False)+"\n").encode())
            result=dict(request=str(args.output),notice="Synthetic example only; no fill recorded")
        elif args.action=="record":
            if not args.request.is_absolute() or args.request.stat().st_size>1000000:
                raise LedgerError("Explicit bounded JSON request file required")
            request=_load_json(args.request.read_text(encoding="utf-8"))
            if type(request) is not dict or set(request)!={"command_id","fills"}:
                raise LedgerError("Request requires exactly command_id and fills")
            result=Ledger.open(args.directory).apply(request["command_id"],request["fills"])
        elif args.action=="report":
            result=Ledger.open(args.directory,readonly=True).report(sequence=args.sequence)
        elif args.action=="export":
            result=dict(export=str(Ledger.open(args.directory,readonly=True).export(
                args.destination,sequence=args.sequence)),plaintext=True)
        elif args.action=="backup":
            result=dict(backup=str(Ledger.open(args.directory,readonly=True).backup(args.destination)),
                        plaintext=True)
        elif args.action=="restore":
            result=dict(directory=str(Ledger.restore(args.backup,args.destination,
                                                     synthetic=args.synthetic).path))
        else:
            result=dict(raw_capture=str(Ledger.recover(args.directory,
                                       confirm_exclusive=args.confirm_exclusive)))
        print(json.dumps(result,sort_keys=True,allow_nan=False))
        return 0
    except (LedgerError,OSError) as error:
        print(type(error).__name__+": "+str(error),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
