# H-014 standalone synthetic Ledger UI draft

Run Python 3.11+ with Tk and `pip install -r requirements-ledger.txt`, then
`python -B manual_ledger_ui.py`. This separate window depends on PR26 at
a374038bc10298e2aa14b238153c7674322a66d4. It does not mount in Radar or import
PR24's calculator. No accounting code, calculator, dashboard or research store is changed.

## Safe workflow

Startup opens nothing. New explicitly chooses an existing parent and NEW subdirectory;
Open accepts only a recognized existing synthetic store and never creates a fallback.
All records are fictional SPY/QQQ standard-100 USD long calls/puts.
Fields use sample dates/prices; the operator must edit deliberately. Fees are total per fill;
premium is per share. Tick is UNKNOWN or USER_ASSERTED, never exchange-verified.

Record a simulated BUY_TO_OPEN. Select its position for partial SELL_TO_CLOSE or
explicit MANUAL_ZERO_CLOSE. Existing contract identity is locked. Positions and
Eastern daily/weekly/monthly summaries display Ledger's calculations.
Audit lists all revisions, reasons, predecessor links and original timestamps.
Correction/void append revisions; select only a current head in Latest.
Numbered sequence views preserve original reports and are read-only, even at the current cutoff.
Export pins the displayed sequence. Backup captures its own current committed sequence,
reported on completion, and requires Latest. Both require new exclusive directories.

Recovery is never automatic: close other processes, select the known synthetic store,
explicitly assert exclusive ownership, and read the raw-capture warning. Success returns
the capture path and leaves the store inactive; Open explicitly afterward. Restore and
atomic multi-fill corrections remain CLI functions. Dependent single-fill corrections
can be rejected; the UI does not bypass repository consistency checks.

## Failure and concurrency

One worker serializes local I/O. Only the main Tk thread renders queued results.
Errors retain their messages. Controls disable during work; closing waits for completion.
A failed save retains its original command UUID and exact payload. Retry uses that same
request; reload reconciles an already committed receipt. Explicit abandon first reconciles
history and discards only uncommitted intent, never committed data. Store switching and
editing are blocked while a request is unresolved.

Pending intent exists ONLY in process memory. Hard crashes lose that unsaved intent.
There is no automatic resubmission or startup opening. Inspect saved command history before
manual re-entry after a crash. This draft does not certify exactly-once user intent across
process loss. Concurrent external edits may make corrections stale; repository rejection
requires explicit reconciliation. Export and backup cutoffs can differ by design.

## Validation and limits

Test-first controller specification was committed before implementation; initial import
fails because the controller does not exist. Seventeen controller/worker tests exercise
the real API with explicit synthetic temporary stores. Existing 39 journal tests remain
unchanged; root offline suite remains 69 tests. A separate own-window Tk smoke uses
widget invocations for entry, partial exit, correction, history, export, backup and visible
invalid-input errors. CI runs that smoke on Windows and Linux/Xvfb, not real desktop user
acceptance on Linux. No providers or market history are involved.

All files, exports and backups are plaintext. Backend ACL/path-swap/exclusive-recovery,
resource-limit and power-loss limitations remain; this is not a general filesystem sandbox.
No real records, exchange tick verification, quotes, alerts, orders, historical study,
deployment or merge is authorized. Keyboard accessibility, multiple DPI/small screens,
native file dialogs and human usability need further review. The fixed initial minimum
window requires a sufficiently large display; tables scroll horizontally/vertically.
External-review waiver covers only isolated development/testing, not independent sign-off
or permission for real use/integration/merge.
