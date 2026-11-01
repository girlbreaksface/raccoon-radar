# Bounded raw SPY/QQQ capture validation

User authorized continued read-only capture validation on 2026-10-30 and explicitly confirmed API access and permission for local retention. The user performs OpenD login locally. This permits raw evidence capture, not strategy integration, trading, paid activation or deployment.

## Frozen bounds

- Local OpenD only: 127.0.0.1:11111; installed SDK and executable version10.11.7108. Executable SHA256 `3c2c5065c8f18dece54dc2c208317721a0c16821cfcd8fa21e45255faa38d738` is checked before connection. Relevant installed SDK sources and capture/journal code hashes are recorded.
- One TCP reachability probe, one quote context, one subscription request for US.SPY and US.QQQ K_1M, Session.RTH, extended_time=False, is_first_push=False. No history, recovery, fallback, account queries, trade context or order methods.
- 120 seconds after subscription, within a hard300-second supervised process lifetime including SDK startup/cleanup. No autonomous retry or reconnect. SDK private reconnect flag is restricted to this pinned build; source behavior reviewed, fake lifecycle tests cover the wrapper. Real disconnect behavior remains unverified until observed.
- At most5000 journal records,10MiB receipt journal,64KiB per serialized protobuf,128 queued callbacks,100 source stamps per receipt. Metadata/seal/log overhead is separate. No unbounded raw provider/account responses in reports.
- Stop on either symbol silent for over30seconds, disconnect/system notification, queue overflow, schema/symbol/interval violation, budget exhaustion, wall-clock rollback or wall-versus-monotonic divergence over250ms, write/fsync failure, or regular-hours time-window end. Wall-clock comparison cannot prove UTC accuracy. Holidays, early closes and halts are not certified by a weekday/time check.
- Exclusive new session directory under this chat's outputs/captures. No existing data, dashboard or databases opened for writes. Raw evidence stays local; only source code and sanitized validation results may be pushed.

## Evidence and eligibility

Capture records retain SDK protobuf serialization bytes, their SHA256 and source time_key strings without shifting or relabeling; these are not original network packet bytes. The protobuf retains original SDK field values including rehabType. Subscription offers no explicit adjustment argument: adjustment semantics remain unverified rather than being represented as unadjusted.

Each record includes UTC wall/monotonic receipt and journal times, local journal sequence, payload hash and hash-chain linkage. fsync completes before acknowledgement. A separately created seal covers record count/bytes/final hash; missing seals, truncation and edits block verification. This detects accidental edits, not adversarial rewriting; fsync does not establish power-loss guarantees or provider truth. Supervisor status is separate and must also be inspected.

Every record and summary says UNKNOWN finality and DATA_BLOCKED strategy status. As-of reads are receipt cutoffs plus journal sequence over a fully verified sealed journal, not source publication times or durable-commit-as-of snapshots. No decision engine consumes this output. Neither new bars, elapsed minutes nor repeated values establish FINAL. No historical data is represented as point-in-time.

The runner's raw-only wall-time session restriction is not an authoritative market calendar, entitlement monitor, gap detector or provider-completeness claim. Missing bars, stale source timestamps and source-time gaps cannot become eligible under this profile. Full typed/scoped expiring authorities, independent calendar/UTC-clock verification, timestamp mapping, revision lineage, source coverage/delay and completion/finality proof remain required for any engine use. The user access/retention attestation and a successful subscription are evidence of permission/subscription at that moment, not a provider license audit.

## Validation

OfflineGuard is installed before discovery. Existing24 contract tests plus23 capture/lifecycle tests exercise scope, immutable raw bytes, as-of prefix, seals, tamper/truncation, record/byte/payload/time/silence/clock limits, fsync failure, queue overflow, rejected subscriptions, disabled reconnect, cleanup including seal failure, version guard and watchdog kill. Fakes do not certify SDK or provider behavior. Windows/Linux Python3.11 CI is required; only timezone data is installed, never the provider SDK. No live connection occurs in CI. The app callback queue is bounded; internal SDK buffering is not certified by these tests.

Official reference: https://openapi.moomoo.com/moomoo-api-doc/en/quote/sub.html describes cached first pushes and RTH/session parameters; https://openapi.moomoo.com/moomoo-api-doc/en/quote/update-kl.html describes asynchronous callbacks and US Eastern time_key. Neither establishes the required FINAL contract.

Run from an already authenticated local installation, using its Python interpreter: `python -B research/feed_contract/opend_capture.py --supervise ABSOLUTE_NEW_DIRECTORY`. Verify summary and supervisor JSON together; abnormal termination is incomplete evidence, never a successful market-data validation. Raw data is excluded from Git.

## Local attempted capture outcome

On2026-10-30, user logged into OpenD locally and a127.0.0.1:11111 listener was observed. One supervised attempt used the installed Windows Python3.15 environment and matching SDK/OpenD10.11.7108. It stopped during SDK import: Windows Application Control blocked the native Crypto.Util._cpuid_c dependency (WinError4551). The worker returned1 without timeout. One TCP reachability probe had succeeded, but no quote context/subscription was created, no market records were received and no capture journal was opened. Subsequent code moves dependency import before the reachability probe so this failure requires no socket at all.

Attempted runner SHA256 `78731f7415f3f6f8e768e8c13b096e5b3d295af17b2f22101b15a0ad120928fe`; journal SHA256 `272945a0f40dd7a496aeb274ecae8f8e06937bb410e57b643ddf4dee59034427`. Supervisor result and dependency traceback remain local under outputs/captures, excluded from Git. No policy changes, installation workaround or alternate provider was attempted. This is blocked runtime evidence, not verified live capture. A working organization-approved SDK/native-dependency environment is the next prerequisite; then the same bounded raw-only run must be repeated. FINAL eligibility remains independently unresolved even if capture succeeds.
