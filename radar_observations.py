"""Append-only OpenD observation batches, reports and deterministic playback."""
import argparse
from collections import Counter
from contextlib import closing
from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

SYMBOLS = ("US.SPY", "US.QQQ")
TABLES = {"radar_observed_batches_v1", "radar_observed_polls_v1"}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(value.encode("utf-8")).hexdigest()


class ObservationStore:
    def __init__(self, path):
        self.path = Path(path).resolve()

    def append(self, snapshot, observed_at):
        """Store only the OpenD transport lane; synthetic replay has no call path here."""
        if observed_at.utcoffset() is None:
            raise ValueError("Observation timestamp needs an offset")
        value = deepcopy(snapshot)
        if value.get("synthetic") is True:
            raise ValueError("Synthetic data cannot enter the observation recorder")
        provenance = value.get("provenance", {})
        batches = {}
        for code, row in value.get("symbols", {}).items():
            if code not in SYMBOLS:
                raise ValueError("Unexpected observation symbol")
            if "raw_candles" in row:
                if provenance.get("source") != "MOOMOO_OPEND" or value.get("authenticated") is not True:
                    raise ValueError("Raw candles require authenticated OpenD provenance")
                payload = encoded(row.pop("raw_candles"))
                identity = digest(payload)
                batches[identity] = payload
                row["batch_sha256"] = identity
        value["observed_at"] = observed_at.isoformat()
        value["schema"] = "OPEND_OBSERVATION_V1"
        payload = encoded(value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=2)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            tables = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            if not tables:
                db.execute("CREATE TABLE radar_observed_batches_v1 (sha TEXT PRIMARY KEY, payload TEXT NOT NULL)")
                db.execute("""CREATE TABLE radar_observed_polls_v1 (
                    id INTEGER PRIMARY KEY, capture_day TEXT NOT NULL, sha TEXT NOT NULL, payload TEXT NOT NULL
                )""")
                db.execute("CREATE INDEX radar_observed_day_v1 ON radar_observed_polls_v1(capture_day, id)")
            elif tables != TABLES:
                raise ValueError("Select a dedicated observation file, separate from the paper journal")
            db.executemany("INSERT OR IGNORE INTO radar_observed_batches_v1 VALUES (?, ?)", batches.items())
            db.execute("INSERT INTO radar_observed_polls_v1(capture_day, sha, payload) VALUES (?, ?, ?)",
                       (observed_at.date().isoformat(), digest(payload), payload))

    def playback(self, day, *, include_candles=True):
        """Yield recorded poll decisions by insertion order, independent of wall time or provider."""
        cutoff = date.fromisoformat(day).isoformat()
        with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)) as db:
            for identity, payload in db.execute(
                    "SELECT sha, payload FROM radar_observed_polls_v1 WHERE capture_day = ? ORDER BY id",
                    (cutoff,)):
                if digest(payload) != identity:
                    raise ValueError("Recorded poll hash mismatch")
                value = json.loads(payload)
                if include_candles:
                    for row in value["symbols"].values():
                        batch = row.get("batch_sha256")
                        if batch:
                            found = db.execute("SELECT payload FROM radar_observed_batches_v1 WHERE sha = ?",
                                               (batch,)).fetchone()
                            if found is None or digest(found[0]) != batch:
                                raise ValueError("Recorded candle batch missing or changed")
                            row["raw_candles"] = json.loads(found[0])
                yield value


def observation_report(polls):
    report = {"polls": 0, "session": Counter(), "decisions": Counter(), "wait_reasons": Counter(),
              "candle_errors": Counter(), "connection_transitions": Counter(), "option_rejections": Counter()}
    for poll in polls:
        report["polls"] += 1
        report["session"][poll.get("session", "unknown")] += 1
        if poll.get("transition"):
            report["connection_transitions"][poll["transition"]] += 1
        for code in SYMBOLS:
            row = poll.get("symbols", {}).get(code, {})
            decision = row.get("action", "WAIT")
            report["decisions"][f"{code} {decision}"] += 1
            if decision == "WAIT":
                reasons = row.get("reason") or poll.get("status", "missing observation")
                report["wait_reasons"].update(reasons.split("; "))
            if row.get("candle_error"):
                report["candle_errors"][row["candle_error"]] += 1
            options = row.get("options", {})
            report["option_rejections"].update(options.get("rejected", {}))
            report["option_rejections"].update(options.get("book_errors", {}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("report", "playback"))
    parser.add_argument("file", type=Path)
    parser.add_argument("date", help="Eastern capture date, YYYY-MM-DD")
    args = parser.parse_args()
    polls = ObservationStore(args.file).playback(args.date, include_candles=args.mode == "playback")
    try:
        if args.mode == "report":
            print(json.dumps(observation_report(polls), sort_keys=True, indent=2))
        else:
            for poll in polls:
                print(encoded(poll))
    except (ValueError, sqlite3.Error) as exc:
        parser.exit(1, f"Recorder unavailable: {exc}\n")


if __name__ == "__main__":
    main()
