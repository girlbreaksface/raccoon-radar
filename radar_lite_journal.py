"""Dedicated SQLite journal for synthetic Radar Lite replay commands."""
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class ReplayRecord:
    id: int
    scenario: str
    initial_index: int
    fingerprint: str
    commands: tuple


class JournalError(RuntimeError):
    pass


class PaperJournal:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=1)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            tables = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            if not tables:
                db.execute("""CREATE TABLE radar_lite_replays_v1 (
                    id INTEGER PRIMARY KEY, scenario TEXT NOT NULL,
                    initial_index INTEGER NOT NULL, fingerprint TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )""")
                db.execute("""CREATE TABLE radar_lite_commands_v1 (
                    replay_id INTEGER NOT NULL, sequence INTEGER NOT NULL,
                    command TEXT NOT NULL, contract_index INTEGER,
                    entry_text TEXT, recorded_at TEXT NOT NULL,
                    PRIMARY KEY (replay_id, sequence)
                )""")
            elif tables != {"radar_lite_replays_v1", "radar_lite_commands_v1"}:
                raise JournalError("Select a dedicated Radar Lite journal file.")
            yield db

    def open_replay(self, scenario, initial_index, fingerprint, *, new=False):
        with self.transaction() as db:
            row = db.execute("""SELECT id, initial_index, fingerprint
                FROM radar_lite_replays_v1 WHERE scenario = ? ORDER BY id DESC LIMIT 1""",
                             (scenario,)).fetchone()
            if new or row is None:
                cursor = db.execute("""INSERT INTO radar_lite_replays_v1
                    (scenario, initial_index, fingerprint, created_at) VALUES (?, ?, ?, ?)""",
                    (scenario, initial_index, fingerprint, datetime.now(timezone.utc).isoformat()))
                return ReplayRecord(cursor.lastrowid, scenario, initial_index, fingerprint, ())
            replay_id, initial_index, saved_fingerprint = row
            if saved_fingerprint != fingerprint:
                raise JournalError("Replay data changed. Start a new replay to keep the old journal.")
            commands = tuple(db.execute("""SELECT sequence, command, contract_index, entry_text
                FROM radar_lite_commands_v1 WHERE replay_id = ? ORDER BY sequence""", (replay_id,)))
            return ReplayRecord(replay_id, scenario, initial_index, saved_fingerprint, commands)

    def append(self, replay_id, sequence, command, contract_index, entry_text):
        with self.transaction() as db:
            row = db.execute("""SELECT r.id, (SELECT MAX(c.sequence)
                FROM radar_lite_commands_v1 c WHERE c.replay_id = r.id)
                FROM radar_lite_replays_v1 r WHERE r.id = ? AND r.id = (
                    SELECT MAX(id) FROM radar_lite_replays_v1 WHERE scenario = r.scenario)""", (replay_id,)).fetchone()
            if row is None or (row[1] or 0) + 1 != sequence:
                raise JournalError("Journal changed in another window. Reopen Radar Lite to continue.")
            db.execute("""INSERT INTO radar_lite_commands_v1
                (replay_id, sequence, command, contract_index, entry_text, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (replay_id, sequence, command, contract_index, entry_text,
                 datetime.now(timezone.utc).isoformat()))

    def history(self):
        with self.transaction() as db:
            return tuple(db.execute("""SELECT r.id, r.scenario, c.entry_text
                FROM radar_lite_replays_v1 r
                JOIN radar_lite_commands_v1 c ON c.replay_id = r.id
                WHERE c.entry_text IS NOT NULL ORDER BY r.id DESC, c.sequence"""))
