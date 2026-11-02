# Raccoon Radar consolidated readiness audit

Audited November 2, 2026. Frozen target: `6c3acba2f22d582cbe9102d9e9aea3f12b31b62d`.

**Decision: GO for guarded offline synthetic research. HOLD for merge. NO-GO for production feed integration, completed-candle claims, trading signals and live orders.** This audit grants no live capture authority.

## Frozen scope and dependency chain

| Layer | Exact commit | GitHub state |
| --- | --- | --- |
| Reconciliation foundation | `838851a3cfd248b19bd0a2a590a7bf55756eaed2` | Audit lower boundary |
| [Draft #43](https://github.com/girlbreaksface/raccoon-radar/pull/43) | `fb38c328c57cb2d819adaaa706d6eaf8ceb082bb` | Open, draft, unmerged |
| [Draft #44](https://github.com/girlbreaksface/raccoon-radar/pull/44) | `99ed196ae60b5894816fefe8c414f0007bea6e43` | Open, draft, unmerged |
| [Draft #45](https://github.com/girlbreaksface/raccoon-radar/pull/45) | `b73740402be823837b4dc8835ad25696f5bc2fe1` | Open, draft, unmerged |
| [Draft #47](https://github.com/girlbreaksface/raccoon-radar/pull/47) | `d151a0aceff4641a539db062cfa5048ee4c4ec8d` | Open, draft, unmerged |
| [Draft #48](https://github.com/girlbreaksface/raccoon-radar/pull/48) | `6c3acba2f22d582cbe9102d9e9aea3f12b31b62d` | Open, draft, unmerged |

GitHub base SHAs equal each preceding head. Local Git ancestry checks pass for every adjacent pair. The range contains 11 commits, preserved with their parents in `commit-history.txt`. #43's body still names older head b890c65; its actual API head is fb38c32. The frozen metadata is authoritative for this audit; historical prose and old CI counts were not used as current-head evidence.

The cumulative diff contains 25 added files / 2,485 lines: one isolated CI workflow and the feed-contract research modules, tests and documentation. Existing root application files, detectors, thresholds, stores, reconciliation implementation and vendor comparator are unchanged relative to the foundation. The foundation itself and earlier proposals are dependencies, not newly certified production implementations. `cumulative.diff` preserves the complete reviewed range.

## Cumulative review and safety findings

Reviewed the added eligibility model, journal writer/verifier, opt-in OpenD runner, replay, quality summary, revision-impact analyzer, field-path audit, reference regressions, seven synthetic test modules, workflow and explanatory documents.

- The typed fake eligibility model accepts only SYNTHETIC mode and produces MOCK_READY rather than live-ready output. Missing authority, unhealthy state, revision graph ambiguity, provisional/uncommitted successors, missing intervals and invalid OHLCV block selection. It is a trusted-fixture model, not an untrusted live adapter.
- The journal exclusively creates evidence, preserves SDK-serialized payload bytes and source labels, and acknowledges only after flush/fsync. Full seals, hashes, bounds, safety metadata and chronology are checked before cutoffs. This preserves serialization bytes, not original network packets. Hash chains detect inconsistent changes; they do not authenticate the provider or prevent a deliberate complete reseal.
- Replay verifies and decodes the full sealed capture before selecting inclusive receipt sequence/time cutoffs. Later corruption or decode failure blocks even an empty or earlier selected prefix. Grouping uses exact symbol/label keys; latest means receipt/row order. No timestamp shift, candle fabrication or finality promotion is introduced.
- Quality statistics describe receipts and decoded field changes; they do not infer missing candles or session coverage. Revision impact requires nested prefixes. Field paths distinguish absence from null, count intermediate excursions/reversions, and retain exact sequence/row evidence. Baselines exclude earlier excursions; newly observed groups explicitly lack a baseline.
- Exports use exclusive creation and carry source provenance. Detached copies prevent mutation of one returned view from rewriting another. I/O failure can still leave a partial newly created export; consumers must parse/validate it. Exclusivity is not atomic publication.
- All analytical outputs retain PROVISIONAL / UNKNOWN / DATA_BLOCKED and completeness NOT_ESTABLISHED. Real protobuf decoding also needs separately installed pinned schema dependencies; injected decoders in tests are trusted synthetic fixtures, not schema certification.
- The standalone live runner remains executable only through explicit invocation; it is not wired into the dashboard or detector. Inspected code limits quote scope, subscription, queue, time and payloads, disables reconnect and closes on failure. These behaviors were exercised only with fakes here. The worker can be invoked directly without the supervisor, and the runner lacks expiring authority enforcement; it must not be treated as an approved live service. Recorded SDK source hashes are not an allowlist for every dependency.
- OfflineGuard blocks audited Python network operations, subprocess creation and non-temporary SQLite connections. It is not an OS isolation mechanism and does not prohibit arbitrary native activity or file writes. No existing research database was opened or modified by this audit.

No newly observed behavioral defect requires a code change for the authorized offline scope. The cumulative whitespace check reports one cosmetic extra blank line at `research/feed_contract/test_quality_report.py:86`; it does not pass cleanly. Earlier incremental whitespace claims do not cover this cumulative range. No new PR was necessary; the audited head remains unchanged.

## Clean local reproduction

A new local clone was created from the existing object repository with `--no-hardlinks`, checked out detached at the frozen target, and verified clean. No untracked captures, databases or previous environment were copied. A fresh Python 3.12.10 virtual environment with system packages disabled installed only `tzdata==2025.2` beyond pip. Both moomoo and google/protobuf are absent. No provider credentials were supplied or read by the audit commands; tests used fakes and disposable synthetic stores under OfflineGuard. Dependency installation used the package index before tests; this was not a provider connection.

| Command (from checkout, using fresh environment Python) | Result |
| --- | --- |
| `python -I -B research/feed_contract/run_checks.py` | 85 tests PASS, 2.009 seconds |
| `python -I -B research/reconciliation/run_checks.py` | 54 tests PASS, 4.183 seconds |
| `python -B research/reconciliation/verify_evidence.py` | Exact 88 synthetic variants reproduced |
| `python -I -B offline_checks.py` | 158 tests PASS, 86.432 seconds |
| AST parse of every Python source | 78 files PASS; no bytecode required |
| `git diff --check 838851a3cfd248b19bd0a2a590a7bf55756eaed2 HEAD` | Cosmetic blank-line finding above |
| `git status --porcelain` | Clean before and after verification |

The feed suite's 85 executions include nine inherited ReplayTests rerun by ImpactTests; this is 76 distinct test methods, not 85 independent behaviors. Suite totals are separate scopes and are not added to counts on main. The broader tests include expensive scenario repetitions, not market trials.

An exploratory `python -I -B research/reconciliation/verify_evidence.py` failed with ModuleNotFoundError for `compare`, because isolated mode removes its script directory from import search. The documented command without `-I` reproduced evidence exactly. Both logs are retained. This is a command compatibility limitation, not evidence mismatch. `reproduce.ps1` uses documented entry points and checks the frozen SHA and clean checkout; supply an SDK-free Python environment with tzdata 2025.2. Linux and Python 3.11 validation here rely on CI, not a local run. No local GUI or actual SDK/native test was performed.

## Exact-head CI

Fresh GitHub API reads confirm four completed successful workflows associated with target head 6c3acba and all ten jobs successful:

| Workflow | Jobs | Evidence |
| --- | --- | --- |
| Feed contract | Ubuntu/Windows x Python 3.11/3.12, four successes | [41491012811](https://github.com/girlbreaksface/raccoon-radar/actions/runs/41491012811) |
| Python validation | Ubuntu/Windows, two successes | [41491012876](https://github.com/girlbreaksface/raccoon-radar/actions/runs/41491012876) |
| Presentation | Ubuntu/Windows, two successes | [41491012896](https://github.com/girlbreaksface/raccoon-radar/actions/runs/41491012896) |
| Reconciliation | Ubuntu/Windows, two successes | [41491012809](https://github.com/girlbreaksface/raccoon-radar/actions/runs/41491012809) |

Windows Tk smoke succeeded; Linux Tk smoke was skipped as configured. Independently inspected Windows feed 3.12 job 125433683086 and Python job 125433682611 logs confirm 85 feed / 54 reconciliation / 88 variants and 158 broader tests, respectively.

Checkout nuance: these PR workflows tested temporary merge commit `f443b9be1fbf3cf62fed98d1d10b63ef061efe30`, parents d151a0a and 6c3acba. Its tree `d001d9a189a2c359663ceb614cbd71dde87be471` matches the audited head tree exactly. This validates source-tree equivalence; it does not imply a merge occurred. CI installs unpinned tzdata and uses moving action tags/runners, so historical CI environment reproduction is not bit-for-bit guaranteed. Run/job snapshots are retained in the artifacts.

## Evidence and unresolved requirements

`frozen-baseline-manifest.json` records all 119 tracked files with Git blob IDs, SHA-256 of exact committed content and SHA-256 of actual checkout bytes (line endings can differ). It records the tree, ancestry, commands and environment. The included committed synthetic evidence is verifiably reproduced; its file hash is in the inventory. `SHA256SUMS.txt` hashes the delivered artifacts. These hashes freeze bytes, not provider truth or authenticity.

Private capture was deliberately not accessed or rehashed. Its evidence_hashes is null in the manifest. The previously reported 1,143 observations, six groups, revision 386/388 and 42/36/0 field counts are historical claims, not independently reverified results of this audit. Expected private hashes embedded in existing reference scripts are not evidence that the underlying files were verified today. No private raw receipts or full capture reports are included.

[Issue #46](https://github.com/girlbreaksface/raccoon-radar/issues/46) remains open, with no comments/provider response at inspection. Minute boundary meaning, revision/correction guarantees, permanent finality, adjustment factors/version anchors and related provider facts remain unresolved. Existing provider review documents are historical scoped findings; this audit did not refresh external provider documentation or establish new contract facts. Independent clock accuracy, feed coverage/delay, entitlement/retention authority, authoritative exchange calendar and completed-candle completeness remain unestablished. S0 detector integration, multi-episode/pair logic, causal outcomes/censoring and untouched evaluation evidence remain unfinished as documented in the recommendation. No predictive edge or executable-return claim is supported.

## GO / NO-GO matrix

| Proposed activity | Decision | Required boundary or next gate |
| --- | --- | --- |
| Guarded synthetic offline research/reproduction | GO | Frozen source, synthetic fixtures, temporary stores, preserve blocked labels |
| Offline review of authorized sealed evidence | Conditional GO | Separate approved schema environment and local read-only evidence; private regression not rerun here |
| Merge stacked work into main | HOLD | Owner review/approval of whole dependency chain; no merge authorized by this audit |
| New live OpenD capture | NO-GO in this task | Explicit new scoped authority and reviewed runtime/supervision prerequisites |
| Production feed/dashboard/detector integration | NO-GO | Resolve provider/authority/calendar/clock/completeness and operational gaps; meaningful integration evidence |
| Treat observations as FINAL/completed candles | NO-GO | Endpoint/version-scoped independent or provider evidence; issue #46 remains open |
| Predictive signals, live orders or trading | NO-GO | No strategy validation or execution readiness established |
| Deploy or email provider | NO-GO in this task | Explicitly outside authorized actions |

Completed only the consolidated audit and local artifacts. No repository changes, new PR, merge, deployment, provider email, OpenD connection, order or trade occurred.
