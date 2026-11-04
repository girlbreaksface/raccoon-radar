# Offline automation foundation

## Decision log — 2026-11-04

Repository and active PRs were inspected before implementation. Main has only
the baseline validation workflow; #61 already contains the guarded root suite,
isolated feed/reconciliation runners and synthetic adapter. #62–#68 are separate
development proposals. This PR stacks on #61 without modifying those branches,
adding another simulator, integrating broker code or claiming their tests.

Decision: reuse those existing runners and the exact 88-case evidence verifier.
The evidence verifier compares newly computed deterministic cases with the
committed baseline; failures must be investigated, never regenerated away.
Run all four suites even after an earlier failure, with separate logs, exit codes,
hashes and source inventory. Each runner executes once. Empty discovery already
fails in the guarded root runner. Guard limitations remain those documented in
offline_checks.py; this is cooperative Python isolation, not a security boundary.

Decision: publish readiness.json with six consolidated engineering blocker
categories derived from repository preflight and research documents. These are
not a claim that the exact historical Phase 25 gate names were recovered. All six
remain HOLD regardless of synthetic results. Recording/paper/merge/deployment
remain HOLD, live NO-GO, orders DISABLED. This file is an informational report,
not an execution interlock or permission token. No approval or waiver input exists.
The historical 224/224 assertions and 1500/1500 cycles remain USER_REPORTED_NOT_REPO_CI.
Actual suite counts are in logs, scoped to this checkout and environment.

Decision: retry only a fixed pinned timezone-wheel download, at most once after
three seconds, on explicit DNS/connection/read-timeout messages. Installation,
tests, evidence mismatches, unknown failures, timeouts and safety failures are
never retried. A final download failure stays failed. No broker/capture retry is
introduced. The timezone package is installed from the downloaded wheel without
network access. Workflow permissions are read-only plus the artifact service;
there are no PR comments, email, issues, scheduled reports or notification hooks.
GitHub account-level workflow notification preferences remain user-controlled.

## Use and evidence

CI runs on PRs, main pushes, this development branch and manual dispatch on
Windows/Linux with Python 3.11/3.12. It uploads separate 30-day evidence artifacts
even when a test fails. Setup/download failures remain visible in Actions logs;
missing evidence is an error, never a passing readiness result. No PR secrets,
provider SDK, market data, default databases or GUI are needed.

For local reproduction with Python 3.11+ and timezone data installed:

```text
python -B automation_foundation.py --output work/my-unique-evidence
```

Choose a fresh output directory each time. Existing evidence is never overwritten.
readiness.json includes Python/OS, CI context, checkout SHA, PR head SHA and source
hashes. CI checks the normal PR merge checkout; this does not merge the PR.
Local reports identify ci=false and do not establish hosted Linux verification.
Logs contain only offline fixture diagnostics; never upload private capture files.

Routine failures remain in CI/evidence for engineering follow-up. This workflow
does not autonomously repair code, merge, deploy, trade or send approval requests.
Only a concrete action outside existing authorization should prompt the owner.
No branch protection setting is changed; required-check enforcement needs a
separate repository-owner decision. Successful checks cannot authorize a release.

Rollback: close this draft PR or revert its added files and the work/ ignore rule.
No data/schema migration or calculation/risk-limit changes are involved.
