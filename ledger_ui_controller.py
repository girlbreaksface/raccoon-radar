"""Synthetic journal presentation state. Accounting belongs exclusively to Ledger."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from queue import Queue
import re
from uuid import uuid4

from manual_ledger import Ledger, LedgerError


def example_form():
    return dict(underlying="SPY", right="CALL", expiration="2030-12-20",
                strike="500", side="BUY_TO_OPEN", quantity="1", premium="1.00",
                fees="0.00", effective_at="2026-10-23T10:00:00-04:00",
                timezone="America/New_York", tie="0", reason="", tick="0.01")


class WorkQueue:
    """Serial operations; completion callbacks enqueue data and never touch Tk."""
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.events = Queue()
        self.busy = False
        self.closed = False

    def start(self, operation):
        if self.busy or self.closed:
            raise LedgerError("Operation already pending or window closed")
        self.busy = True
        def run():
            try:
                event = dict(ok=True, result=operation(), error=None)
            except Exception as exc:
                event = dict(ok=False, result=None, error=f"{type(exc).__name__}: {exc}")
            self.events.put(event)
        self.executor.submit(run)

    def take(self, timeout=0):
        event = self.events.get(timeout=timeout)
        self.busy = False
        return event

    def close(self):
        if self.busy:
            return False
        self.executor.shutdown(wait=True)
        self.closed = True
        return True


class LedgerController:
    def __init__(self):
        self.repository = self.snapshot = self.pending = None
        self.view_sequence = None
        self.new_position()

    def new_position(self):
        self.selection = self.correction = None
        return example_form()

    def _no_pending(self):
        if self.pending:
            raise LedgerError("Resolve pending command by retry, reload or explicit abandon")

    def _editable(self):
        self._no_pending()
        if self.repository is None or self.view_sequence is not None:
            raise LedgerError("Select an existing store's Latest view before editing")

    def _switch(self, factory):
        self._no_pending()
        self.repository = self.snapshot = None
        self.view_sequence = None
        self.new_position()
        repo = factory()
        snapshot = repo.report()
        self.repository, self.snapshot = repo, snapshot
        return snapshot

    def create_store(self, path):
        return self._switch(lambda: Ledger.create(path, synthetic=True))

    def open_store(self, path):
        return self._switch(lambda: Ledger.open(path))

    def recover_store(self, path, *, confirmed=False):
        self._no_pending()
        if not confirmed:
            raise LedgerError("Exclusive ownership confirmation required")
        self.repository = self.snapshot = None
        self.new_position()
        return Ledger.recover(path, confirm_exclusive=True)

    def reload(self):
        if self.repository is None:
            raise LedgerError("No open synthetic store")
        latest = self.repository.report()
        if self.pending:
            for command in latest["commands"]:
                if command["command_id"] == self.pending["command_id"]:
                    if command["request"]["fills"] != self.pending["fills"]:
                        raise LedgerError("Pending command receipt mismatch")
                    self.pending = None
                    self.new_position()
                    break
        self.snapshot = (latest if self.view_sequence is None else
                         self.repository.report(sequence=self.view_sequence))
        return self.snapshot

    def set_sequence(self, sequence):
        self._no_pending()
        if self.repository is None:
            raise LedgerError("No open store")
        snapshot = self.repository.report(sequence=sequence)
        self.view_sequence, self.snapshot = sequence, snapshot
        self.new_position()
        return snapshot

    def _raw(self, fill_id):
        for command in reversed(self.snapshot["commands"]):
            for fill in reversed(command["request"]["fills"]):
                if fill["fill_id"] == fill_id and not fill.get("void"):
                    return deepcopy(fill)
        raise LedgerError("Original fill not available")

    def _form(self, raw):
        result = {key: str(raw[key]) for key in example_form() if key in raw}
        result.update({key: str(raw["contract"][key]) for key in
                       ("underlying", "right", "expiration", "strike")})
        result["tick"] = raw["tick"] or ""
        result["reason"] = ""
        return result

    def select_position(self, position_id):
        self._editable()
        revision = next((r for r in self.snapshot["revisions"]
                         if r["position_id"] == position_id), None)
        if revision is None:
            raise LedgerError("Unknown position")
        self.selection = self._raw(revision["fill_id"])
        self.correction = None
        result = self._form(self.selection)
        result["side"] = "SELL_TO_CLOSE"
        return result

    def _head(self, revision_id):
        heads = {r["fill_id"]: r for r in self.snapshot["revisions"]}
        found = next((r for r in heads.values() if r["revision_id"] == revision_id), None)
        if found is None:
            raise LedgerError("Select the current revision in Latest view")
        return found

    def load_correction(self, revision_id):
        self._editable()
        revision = self._head(revision_id)
        self.selection = self._raw(revision["fill_id"])
        self.correction = revision
        return self._form(self.selection)

    def submit_form(self, form):
        self._editable()
        values = {key: str(form[key]).strip() for key in example_form()}
        for key in ("quantity", "tie"):
            if not re.fullmatch(r"[0-9]+", values[key]):
                raise LedgerError(f"{key} must be an integer")
        if not values["reason"]:
            raise LedgerError("A reason is required")
        identity = ("underlying", "right", "expiration", "strike")
        if self.selection:
            if any(values[key] != str(self.selection["contract"][key]) for key in identity):
                raise LedgerError("Existing contract identity cannot be edited")
            contract = deepcopy(self.selection["contract"])
            position_id = self.selection["position_id"]
        else:
            contract = {key: values[key] for key in identity}
            contract.update(symbol="SYNTHETIC_" + uuid4().hex.upper(),
                            multiplier=100, currency="USD", deliverable="STANDARD_100")
            position_id = str(uuid4())
        raw = {key: values[key] for key in
               ("side", "premium", "fees", "effective_at", "timezone", "reason")}
        raw.update(quantity=int(values["quantity"]), tie=int(values["tie"]),
                   fill_id=self.correction["fill_id"] if self.correction else str(uuid4()),
                   revision_id=str(uuid4()), expected_revision=(
                       self.correction["revision_id"] if self.correction else None),
                   position_id=position_id, contract=contract, synthetic=True,
                   tick=values["tick"] or None,
                   tick_authority="USER_ASSERTED" if values["tick"] else "UNKNOWN")
        self.pending = dict(command_id=str(uuid4()), fills=[raw])
        return self.retry_pending()

    def retry_pending(self):
        if not self.pending:
            raise LedgerError("No pending command")
        receipt = self.repository.apply(self.pending["command_id"], deepcopy(self.pending["fills"]))
        snapshot = self.repository.report()
        self.snapshot, self.pending = snapshot, None
        self.new_position()
        return receipt

    def abandon_pending(self, *, confirmed=False):
        if not confirmed:
            raise LedgerError("Explicit abandonment confirmation required")
        self.reload()  # Reconcile any successful commit first; never delete history.
        self.pending = None
        self.new_position()

    def void_revision(self, revision_id, reason, *, confirmed=False):
        self._editable()
        if not confirmed or not reason.strip():
            raise LedgerError("Confirmation and reason required")
        head = self._head(revision_id)
        self.pending = dict(command_id=str(uuid4()), fills=[dict(
            fill_id=head["fill_id"], revision_id=str(uuid4()),
            expected_revision=revision_id, void=True, reason=reason, synthetic=True)])
        return self.retry_pending()

    def export(self, path):
        self._no_pending()
        if self.snapshot is None:
            raise LedgerError("No displayed snapshot")
        return self.repository.export(path, sequence=self.snapshot["snapshot_sequence"])

    def backup(self, path):
        self._editable()
        target = self.repository.backup(path)
        return dict(path=str(target), sequence=Ledger.open(target, readonly=True).report()["snapshot_sequence"])
