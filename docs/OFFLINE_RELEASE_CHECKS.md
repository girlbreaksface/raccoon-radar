# Offline verification and release readiness

## Repeatable offline command
Run `python -B offline_checks.py` from a checkout. The runner:
1. AST-parses and SHA-256 inventories every top-level Python source without importing dashboards.
2. Prints Python, platform, SQLite versions and source hashes to stdout.
3. Installs a Python audit guard BEFORE test discovery and directs tempfile fixtures into one disposable root.
4. Runs every discovered test_*.py and exits nonzero for source failures, no tests or failing tests.

The guard rejects SQLite outside that root (including default project stores), noncanonical/writable URI or empty SQLite filenames, Python-audited socket operations except socket creation, urllib requests, and common child-process launch events. :memory: and explicitly rooted temporary databases remain permitted. Resolve-based containment rejects path escapes. Source inputs are never repaired or normalized. Ordinary pytest/unittest commands do not activate this guard; CI now uses the guarded command on Windows and Linux/Python 3.11.

This is an accidental-side-effect detector, NOT a hostile-code sandbox. Native extensions, ctypes, raw filesystem writes and mechanisms without Python audit events are outside its guarantees. It does not protect arbitrary files, validate semantic correctness, ban all third-party side effects, or replace the contributor rules. Do not deliberately exercise user paths just because they are blocked. Audit hooks cannot be removed; each context disables its hook on exit. Use the CLI in a fresh process for release checks.

## Evidence
Eight initial synthetic tests were written before the guard existed; nine additional SQL-escape regression tests were added after reproducing the ATTACH/VACUUM bypass. They verify actual API calls: temporary transactions succeed; an existing external synthetic DB is denied before opening and its hash stays unchanged; an external path is not created; blank/noncanonical URI database names cannot bypass the policy; canonical mode=ro URIs work only inside the temporary root and reject writes; localhost OpenD connects and DNS are denied before network access; child-process launch is denied; normal and exceptional exits disable the scoped guard. No production file/service is used.

Local Windows/Python 3.12.14: the initial 27-test snapshot against main 342c7389 pass via ordinary discovery AND the guarded runner; compilation succeeds. Existing Windows/Linux Python 3.11 CI runs this same guarded command. Results and links are recorded in the PR. Other open PR tests remain separate, and should also be checked together before release. Source hashes reflect exact source bytes in the tested checkout, including line-ending differences; preserve the CI log and commit identity together.

## Release checklist (all items need evidence)
- Record reviewed commit SHA, runtime/source manifest, CI links and exact commands.
- Run guarded offline checks on Windows and Linux; review test count and branch differences. A green branch with fewer tests does not cover unmerged PRs.
- Review each calculation change against a fixed hypothesis, evidence and regression tests; absent provider evidence remains UNVERIFIED.
- Confirm PRs contain no production DBs, migrations, credentials, raw-history rewrites or execution APIs.
- Check declared timestamp bounds, missing/duplicate/invalid data, per-symbol/session freshness and remaining ingestion limitations.
- Verify a complete all-store backup/restore plan on disposable copies before any separately approved persistence change. Existing archive implementation omits fundamentals; passing offline checks does not resolve that.
- Test GUI layout, shutdown and error delivery on Windows with fakes/disposable fixtures; unit tests alone do not establish desktop/provider interoperability.
- Treat OpenD timestamp verification as separate quote-only empirical research with immutable provenance. Never infer semantics or trading edge from synthetic fixtures.
- Preserve old source/data and a rollback path; require approval before merging/releasing. No automatic merge, live execution or migration is part of this command.

Outstanding: independently documented provider semantics; ingestion 16:00 and incomplete-bar policy; hidden DB initialization/upserts; complete archive manifests; broader calendar/early-close/DST evidence; real GUI smoke testing. No version-number increase substitutes for these checks.

## SQL-level bypass correction
The original connect-only policy was insufficient: an allowed connection could ATTACH an external synthetic database and VACUUM INTO an external synthetic file without a new Python connect audit event. Both escapes were reproduced in disposable fixtures before the fix. No production store was used.

The corrected runner wraps managed sqlite3.connect calls, validates initial paths through audit hooks, then installs a SQLite authorizer after connection initialization. Unwrapped aliases (including _sqlite3.connect) are rejected while guarded. Custom factories are rejected because their constructors could execute SQL before authorizer installation. This uses [Python's authorizer API](https://docs.python.org/3.11/library/sqlite3.html#sqlite3.Connection.set_authorizer) and [SQLite semantic action codes](https://www.sqlite.org/c3ref/c_alter_table.html), rather than fragile SQL keyword matching.

The conservative policy denies ALL SQLITE_ATTACH/DETACH operations, including in-root and :memory: attachments. This also denies tested VACUUM/VACUUM INTO internal attachments; [VACUUM INTO accepts SQL filename expressions](https://www.sqlite.org/lang_vacuum.html), so parameter/expression variants are tested. Virtual-table creation/drop, SQL load_extension/readfile/writefile names, extension-loading APIs and directory-changing PRAGMAs are blocked. Temporary storage is set to memory and SQL attempts to switch it to disk are denied. Ordinary CRUD, schema creation, read-only temporary URIs and backup between managed fixtures still work. Some legitimate maintenance SQL is intentionally unavailable in offline tests.

Nine additional tests verify: existing external fixture hash unchanged after denied attachment; literal/parameter/expression/script attachments create no files; VACUUM INTO variants create no files; an existing empty external file stays empty; nesting and connection lifetime retain SQL policy; raw aliases and custom factories cannot skip installation; directory/extension/file-function/virtual-table attempts are denied before callbacks; and ordinary transactions/backup remain available.

Protection scope is precise: newly managed Python sqlite3 connections opened after guard entry, while callers cooperate with the policy. Start before discovery and connection creation. Pre-existing unguarded handles, deliberately replacing an authorizer, arbitrary user-defined functions/native extensions, direct file APIs, malicious Python, custom SQLite VFS, hard-link aliases, filesystem races and other unaudited mechanisms are outside the guarantee. Connection objects may not be shared with untrusted code. This is NOT a general filesystem sandbox or a safe arbitrary-SQL service. Use OS isolation and disposable data for untrusted code.

Local Windows/Python 3.12.14: The initial 27-test snapshot against main 342c7389 passes through the guarded runner. After main advanced to 0d9015cc with #8/#10 merged, the refreshed 34-test branch-compatible suite also passes. A combined disposable overlay of main plus #1/#6/#8/#9/#10/#11 passes 69 tests locally. These do not imply all proposals are merged. Refreshed Windows/Linux Python 3.11 CI results are recorded in the PR.
