# Paper-only validation gate

Integration HOLD. Live trading NO-GO. External paper orders REVIEW REQUIRED.

This proposal extends draft PR #61 at a81e0710a319890a321834968f0b03d262f52bd9,
stacked on PR #60 (6576d49). It does not integrate either proposal into main.

## Architecture inspected

The existing Tk dashboard owns research stores and lazy OpenD quote access.
The synthetic path is separate: fictional demo -> canonical candles -> pinned
timezone/replay kernel -> paper signal engine -> fixture adapter -> pure options
simulator. No broker object, account, credentials, endpoint or order transport is
accepted by that path. PR #61 also adds a separate TCP-only localhost preflight;
this rehearsal never calls it. Reachability would not prove broker identity.

The adapter requires immutable typed fixtures and explicit synthetic=True.
The simulator requires matching signal/right, chronological session quotes,
stable contract binding, finite positive uncrossed prices and a maximum quote age.
It uses ask plus slippage for entries, bid minus slippage for exits, includes fees
in P/L, caps entry premium at $30, permits three entries per session, blocks
overlapping exposure per symbol and latches data/profile entry blocks.

## Reproducible offline evidence

Run `python -B offline_checks.py` for guarded regression discovery, then
`python -B paper_only_validation.py` for a JSON rehearsal report on stdout.
Preserve each report under a new exclusive filename; never overwrite evidence.
The report includes Python/platform, source SHA256 inventory, scenario outcomes,
input/run hashes, hash-linked ledgers, unresolved positions and disabled controls.
BUY/SELL ledger rows are fictional accounting events only.

The rehearsal fixes eight fictional cases and validates deterministic output,
expected events, ledger continuity and disabled orders under OfflineGuard.
The guard is a Python audit aid, not an OS security boundary; it prevents the
normal network/subprocess/foreign SQLite paths described in offline_checks.py.
The full suite includes separate daily limit, slippage/fee, leakage and data-block
regressions. No user research database or UI needs to be opened.

## Limits and next review gate

Synthetic fixture labeling is a caller assertion, not authenticated provenance.
The UTC session is fictional. No provider timestamp, entitlement, retention,
exchange calendar, real options contract, actual spread or fill is validated.
Stop triggers do not cap loss through gaps; the $30 premium cap excludes fees.
There is no portfolio/daily dollar loss stop, broker kill switch, restart-safe
idempotency/reconciliation, forced session close or external paper-order path.
Open positions remain explicit, and missing fresh marks remain unknown.

Before any external paper submission, prepare a separate reviewed proposal with
the exact broker sandbox endpoint/account attestation, SDK version, paper-only
credentials, instrument allowlist, quantity/notional/exposure/loss limits, stop
switch, session/quote rules, durable intent IDs, timeout/retry reconciliation,
partial-fill/cancel handling and redacted audit records. Use fakes first. Review
the exact proposed paper order and obtain user authorization before sending it.
No live endpoint fallback, account unlock, merge, deployment or purchase is allowed.
