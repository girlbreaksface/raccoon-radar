"""Standalone CSV-only candle-quality report; no SQLite or provider access."""
import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

from candle_quality import audit_candles


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Explicit OHLCV CSV input")
    parser.add_argument("--expected-start", required=True, help="Inclusive raw stamp HH:MM")
    parser.add_argument("--expected-end", required=True, help="Inclusive raw stamp HH:MM")
    parser.add_argument("--output", type=Path, help="New JSON file only; default stdout")
    args = parser.parse_args(argv)
    try:
        if args.input.suffix.lower() != ".csv":
            raise ValueError("Input must be an explicit CSV file, not a research database")
        source = args.input.read_bytes()
        reader = csv.DictReader(io.StringIO(source.decode("utf-8-sig")), strict=True)
        fields = set(reader.fieldnames or ())
        needed = {"symbol", "open", "high", "low", "close", "volume"}
        if not needed <= fields or not fields.intersection({"time", "bar_time_et"}):
            raise ValueError("CSV needs symbol, time (or bar_time_et), open/high/low/close/volume")
        records = list(reader)
        audit = audit_candles(records, expected_start=args.expected_start,
                              expected_end=args.expected_end)
        status = ("NO_DATA" if not records else
                  "REVIEW" if audit["invalid_rows"] or
                  any(not session["quality_ok"] for session in audit["sessions"])
                  else "COVERAGE_MATCH")
        report = {
            "report_version": 1, "source_name": args.input.name,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "status": status, "audit": audit,
            "interpretation": "Caller-declared raw-stamp coverage only; provider semantics UNVERIFIED.",
        }
        serialized = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
        if args.output is None:
            print(serialized, end="")
        else:
            # Never replace evidence or the source, even if an identical name is chosen.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        return 0 if status == "COVERAGE_MATCH" else 2
    except (OSError, ValueError, csv.Error, UnicodeError) as exc:
        print(f"Report failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
