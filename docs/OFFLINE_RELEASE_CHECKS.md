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
Eight new synthetic tests were written before the guard existed. They verify actual API calls: temporary transactions succeed; an existing external synthetic DB is denied before opening and its hash stays unchanged; an external path is not created; blank/noncanonical URI database names cannot bypass the policy; canonical mode=ro URIs work only inside the temporary root and reject writes; localhost OpenD connects and DNS are denied before network access; child-process launch is denied; normal and exceptional exits disable the scoped guard. No production file/service is used.

Local Windows/Python 3.12.14: all 18 branch tests pass via ordinary discovery AND the guarded runner; compilation succeeds. Existing Windows/Linux Python 3.11 CI runs this same guarded command. Results and links are recorded in the PR. Other open PR tests remain separate, and should also be checked together before release. Source hashes reflect exact source bytes in the tested checkout, including line-ending differences; preserve the CI log and commit identity together.

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
