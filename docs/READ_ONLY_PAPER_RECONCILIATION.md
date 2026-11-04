# Read-only paper-account reconciliation dry run

## Decision log — 2026-11-04

Base: #70 at 54fbbe457ec3f6829629d1c5b39a4338d9ab5606. Inspected open #65–#70
before implementation. #66/#67 already have account discovery and a separately
reviewed historical connectivity pilot. Their order-capable modules are not
imported, copied or invoked here. Neither source branch is modified or merged.
The prior preflight reports eligibility and row counts; this module additionally
compares quantities, order status/fill state, explicit expectations and two reads.

User authorization covers this read-only dry run. It does not enable any order
submission. paper_account_reconciliation.py has no submit, modify, cancel,
unlock, flatten, retry, quote-subscription or background strategy operation.
It creates only the SDK context needed for account/state queries. The context
is local to the function and is closed on success or failure. A close failure is
itself HOLD. No dashboard, database, user research file or risk setting is changed.

## Reviewed provider contract

Official moomoo v10.12 documentation reviewed for this implementation:

- [Account list](https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-acc-list.html): US STOCK_AND_OPTION SIMULATE account classification and market permissions.
- [Positions](https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-position-list.html): quantity and available quantity, explicit account/environment selection and refresh behavior.
- [Orders](https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-order-list.html): open orders and closed orders retained in its recent window; it is not a complete historical fill ledger.
- [Order statuses](https://openapi.moomoo.com/moomoo-api-doc/en/trade/trade.html): pending, partial-fill and terminal classifications. Unknown/deprecated transitions are conservatively unresolved.

The query defaults select a real environment/default account; this code always
passes SIMULATE, an explicit positive verified account ID and refresh_cache=True
for positions/orders. It never uses account-index selection or live fallback.
The reviewed local optional SDK version is moomoo-api 10.12.7208. CI neither
installs nor imports it. An unsupported/missing SDK yields sanitized startup HOLD
evidence; no automatic installation or permissions change is attempted.

## Collection and comparison contract

Require exactly one active eligible US SIMULATE STOCK_AND_OPTION account.
Reject duplicate/conflicting IDs and malformed permissions. A supplied expected
account fingerprint must match. Recheck the account classification before each
position/order read and after the pair. Two refreshed pairs must have identical
normalized required fields. The cooperative 30-second window is checked between
SDK calls. It cannot preempt a blocked native/SDK call or close; the local task
also uses an external 60-second process watchdog. No read is automatically retried.
There are only two position and two order requests, not polling loops.

Reject duplicates, missing fields, nonfinite/negative or contradictory quantities,
sellable quantity above holdings, unsupported securities/position sides and
unrecognized order states. Provider row-level account/environment fields, when
present, must agree; absent row fields rely on the explicit query scope and
account revalidation. Numeric canonicalization preserves quantity precision even
if the surrounding Decimal context changes. Zero-quantity LONG rows normalize
away only after validation; a short/unsupported row is never silently dropped.

Expected state is an explicit JSON baseline with schema
paper-account-reconciliation-v1, positions and orders arrays. Positions require
code, qty, can_sell_qty and position_side=LONG. Orders require order_id, code,
qty, dealt_qty, trd_side and order_status. Optional account_fingerprint pins the
prior account; optional provenance is hashed with the input. No implicit user
database or journal discovery occurs in the library. Unknown/extra/missing order
IDs, changed status/fills or position differences remain HOLD. Pending orders,
nonflat/frozen holdings and failed orders also remain HOLD even if expected.

Without a baseline the comparison is explicitly DECLARED_EMPTY_BASELINE. It
cannot be presented as independently reconciled local accounting. Even
MATCHED_BASELINE does not authorize execution or prove an atomic snapshot,
complete history, current market/risk conditions, fee accuracy or provider truth.
Two equal reads can miss intermediate changes or shared provider errors. Missing
historical orders are never invented or treated as zero fills. This is not a
restart-safe strategy gateway or a cancel-race/partial-fill recovery controller.

## Evidence, privacy and tests

Reports contain fixed reason codes, required-field snapshot hashes, counts,
query method trace, source/expectation hashes, close confirmation and disabled
execution gates. CLI reports include UTC observation time and SDK version.
Raw account/order IDs, symbols/position rows and provider error strings are not
exported. Account fingerprints and hashes remain potentially linkable: real
reports and raw SDK logs stay local; none are committed or uploaded to CI.
Hashes establish byte consistency, not authentication or a complete audit ledger.
CLI reserves output exclusively before importing/connecting; existing evidence
is never overwritten. SDK startup failures also produce a sanitized HOLD report.

paper_reconciliation_checks.py runs sixteen deterministic fake-only scenarios,
including account ambiguity/reclassification, scope isolation, nonflat/pending/
partial states, unknown statuses, missing expected orders, malformed quantities,
query errors, drifting state and cleanup failure. Fakes reject any unsupported
method. Tests assert the exact explicit account/environment read arguments and
the absence of mutation calls. The parent automation runner rejects missing or
forged artifacts, including removed scenarios or readiness edits with repaired
hashes. Regression PASS means expected failure handling was observed, not that a
blocked fake scenario or real account became execution-ready.

```text
python -B automation_foundation.py --output work/a-new-ci-evidence-directory
python -B paper_account_reconciliation.py --read-only --expectations work/private-expectations.json --output work/a-new-private-report.json
```

The second command explicitly contacts the existing localhost OpenD service.
Use only in an authorized read-only session and with the reviewed SDK already
installed. Its output parent must exist. SDK logs may contain private metadata;
keep them local. This task redirects SDK log storage into its ignored work area.
It does not restart/reconfigure OpenD or install anything.

## Local operational findings

Located the existing localhost OpenD listener and installed reviewed SDK. Built
an explicit private baseline from the earlier pilot's retained intent/acknowledgment
journals and final reconciliation record. Verified every entry-journal hash and
parent link using its actual empty-string chain root; preserved originals. The
separate exit-recovery journal has no hash chain and is labeled accordingly;
these are local prior records, not externally authenticated history.

The read-only dry run matched that account and baseline in two consecutive
required-field observations: zero nonzero positions, two terminal orders, zero
pending orders. Context closure confirmed. No new order, amendment, cancellation,
unlock or market-data request occurred. This verifies a bounded current-state
comparison only. Exact code/CI references and current validation results are in
this PR description; private identifiers and raw records are excluded.

All six engineering/paper gates remain HOLD; live NO-GO; orders DISABLED;
merge/deployment HOLD. Reconciliation has made partial progress but integrated
execution/restart/recovery assurance is still absent. Phase 25 reported counts
remain distinct from repo-verified synthetic CI. No approval is requested.

Rollback closes this separate PR or reverts its files; there is no schema/data
migration and no external state to undo from these read-only queries.
