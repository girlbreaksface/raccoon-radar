# Shared engineering handoff

Shared record for the user's coding agent, ChatGPT, and human maintainers. Read this before continuing work; update it after each handoff through a separate documentation PR. Git history preserves prior snapshots. This document does not schedule agents, deliver messages automatically, grant approvals, or authorize merges.

## Scope and working agreement

- This handoff setup is documentation only. Do not modify or merge PRs #13, #14, #17, or #18 as part of it.
- Do not change trading functionality, calculations, thresholds, ingestion, GUI, provider connections, database schemas, or research data. Never enable order execution.
- Follow [contributor instructions](../AGENTS.md), [release checks](OFFLINE_RELEASE_CHECKS.md), and [roadmap](DEVELOPMENT_ROADMAP.md). Their older status/test-count paragraphs are historical; verify current commits rather than copying them as current facts.
- Coding agent: implement only separately authorized work, record exact commits, evidence, limitations, and questions here. ChatGPT: inspect the pinned diff/evidence and record recommendations with their basis. Human maintainer: resolve decisions, identify an independent reviewer, and explicitly authorize merges separately.
- Agent review is not independent maintainer approval. No reviewer username has been established by this handoff. Do not invent one or treat repository ownership as independent review.
- Before editing, fetch the latest document and its blob SHA. If another writer advances it, reread and reconcile; do not overwrite their entries. Preserve earlier decisions as superseded entries with a reason.
- Use full 40-character SHAs and UTC observation timestamps. Link evidence to its commit. A changed head, base, or test configuration invalidates carried-forward readiness until rechecked.
- Share this file's GitHub link with each participant in their own chat. Each participant must explicitly read it when resuming; no background synchronization is implied. Keep secrets and private datasets out of handoff text.

## Observed snapshot — 2026-10-27 12:58 UTC

Repository: girlbreaksface/raccoon-radar. Main: `b0ad02dc996b00406e7da08fb33b6382f658ea40`.
Read-only GitHub API inspection confirmed the following heads, bases, workflow conclusions, and absence of submitted reviews/requested reviewers. This is a snapshot, not an approval or a new code review.

| PR | Pinned current head | Base branch | State | CI evidence |
|---|---|---|---|---|
| [#13 Direction engine](https://github.com/girlbreaksface/raccoon-radar/pull/13) | `6e7d1a8804b14aba9d08302bc5db48f31b0706ae` | main | Open, not draft | [40504942948](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948), completed/success |
| [#14 Historical replay](https://github.com/girlbreaksface/raccoon-radar/pull/14) | `328135f2695543cde96bb434aaa07201c51c0582` | research/deterministic-direction-engine | Open, not draft | [40504949071](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071), completed/success |
| [#17 Adapter contract](https://github.com/girlbreaksface/raccoon-radar/pull/17) | `9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3` | main | Open, not draft | [40504257980](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980), completed/success |
| [#18 Interface/study design](https://github.com/girlbreaksface/raccoon-radar/pull/18) | `eb683559a0ab685503627612ab22aa16a77066ed` | main | Open, draft | [40507854048](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40507854048), completed/success |

All four have zero submitted reviews and zero requested reviewers at observation. Workflow run metadata was checked for each exact head; job logs and test totals were not independently rerun or audited during handoff setup. Existing PR descriptions report Windows/Linux Python 3.11 totals of 97 (#13), 115 cumulative (#14), and 69 baseline (#17/#18) per platform. Those counts are attributed reports, not new verification.

**Head drift:** the referenced conversation pinned #18 at `fb8456753a53d484f80a0e5cfdeabf072612c860`. Current #18 is `eb683559a0ab685503627612ab22aa16a77066ed`; its description reports a daily-context/conflicting-symbols design amendment. Earlier review must not be transferred to this head without inspecting the amendment.

**Stack dependency:** #14's current GitHub base SHA is `286eb9b1e7071ebbc83a125dc1062e4723efcad1`, while #13's head is `6e7d1a8804b14aba9d08302bc5db48f31b0706ae`. Its description reports testing against the latter. Record the actual checkout/merge SHA used by CI; do not infer cumulative compatibility merely from the target branch name.

## CI evidence and review gates

Existing [Python validation workflow](../.github/workflows/python-validation.yml) uses Python 3.11 on ubuntu-latest and windows-latest, compilation, then `python -B offline_checks.py`. Use the guarded runner and disposable synthetic fixtures; never launch dashboards or open user stores for inspection.

For every new verification record: UTC time, PR/head/base SHA, actual tested checkout or merge SHA, workflow/run/job URLs, OS/Python versions, commands, result/test count, evidence source, and limitations. Missing, stale, cancelled, or pending CI is not a pass. Passing baseline tests on documentation does not validate an unimplemented adapter or study.

- [ ] Exact current head and base rechecked; complete diff inspected and scope confirmed.
- [ ] Windows/Linux checks pass for the intended integration, with test inventory and evidence pinned.
- [ ] Independent maintainer identity and submitted review established; unresolved findings recorded.
- [ ] No source-store writes, raw-history rewrites, migrations, credentials, or order APIs.
- [ ] Provider semantics, revision-specific availability, calendar/session policy, and empirical claims have separate supporting evidence.
- [ ] Explicit human merge authorization recorded for the exact scope/commit; no automatic merge.

These boxes remain unchecked by this setup. Suggested sequence from prior review: independently review #13 first; only after separately authorized integration and resulting main CI, reassess #14's base/diff and rerun cumulative checks before its separate approval. #17/#18 remain design proposals; implementation and study execution require separate authorization. This sequence is a recommendation, not permission to act on the protected PRs.

## Decision register

| ID | Decision / question | Status | Owner | Evidence / rationale |
|---|---|---|---|---|
| D-001 | Use a versioned docs handoff on a separate branch/PR | Applied for setup; pending merge review | Handoff author / maintainer | Existing docs convention and AGENTS.md |
| D-002 | Preserve #13/#14/#17/#18 and trading functionality | Required boundary | All participants | User request |
| D-003 | Select independent maintainer and review exact heads | Unresolved | Human maintainer | No submitted reviews/requested reviewers observed; no username established |
| D-004 | Adapter/revision/calendar contracts and study execution | Pending separate review/authorization | Human maintainer | #17/#18 are proposals; CI alone does not approve contracts |

For new decisions add ID, UTC date, proposer, alternatives, selected rationale, approver/evidence link, affected SHAs, and superseded decision ID. Recommendations and approvals must have distinct statuses.

## Risks and unresolved assumptions

| ID | Risk / limitation | Consequence / gate | Owner / next evidence |
|---|---|---|---|
| R-001 | Same-agent review is not independent review | Readiness does not establish approval | Maintainer: identify eligible independent reviewer |
| R-002 | #18 head drift and #14 stacked-base divergence | Older review/CI claims may be misapplied | Reviewer: compare exact commits and tested merge |
| R-003 | Strict conjunctions can suppress candidates; synthetic tests establish no predictive edge | No profitability, execution-return, or options P/L claims | Research owner: separately approved empirical protocol |
| R-004 | General revision-stream resolution and historical availability remain limited | Block unsupported real-history evaluation | Adapter/research owner: revision-specific evidence |
| R-005 | Provider timestamp/calendar semantics and real GUI/SDK behavior not established by offline tests | Keep provider integration and semantic promotion gated | Maintainer: independent evidence |
| R-006 | Some inspection paths initialize/write stores; archives may omit fundamentals | Preserve research data and use guarded disposable fixtures | Coding agent: follow persistence/release guidance |

## Next actions

| ID | Action | Owner | Status / completion evidence |
|---|---|---|---|
| A-001 | Review and separately approve this documentation PR for integration | Human maintainer | Pending; no merge authorized |
| A-002 | Read this file at session start and record acknowledgement plus current snapshot SHA | Coding agent / ChatGPT | Pending next session |
| A-003 | Identify an independent maintainer reviewer without altering protected PRs in this task | Human maintainer | Pending; username and basis required |
| A-004 | Inspect #18 amendment and reconcile pinned review evidence | Next authorized reviewer | Pending read-only review |
| A-005 | Revalidate #13/#14 dependency and exact-head CI before any future integration decision | Next authorized reviewer | Pending; protected PRs unchanged |

## Reusable handoff entry

Copy this section for each exchange; retain prior entries in Git history and preserve unresolved items in the current tables.

### Handoff: <ID> — <UTC timestamp>

- Author/role and recipient/role:
- Goal and user-authorized scope:
- Document revision read (commit/blob SHA):
- Main SHA; PR links; head/base SHAs; actual tested checkout SHA:
- Changed files and behavior impact (or documentation only):
- Evidence inspected / commands actually run / OS and Python:
- CI run/job links, result, test count, and time:
- Facts observed versus reported claims versus recommendations:
- Decisions made, approver/evidence, superseded IDs:
- Risks, blockers, assumptions, and explicit non-validation:
- Review gates satisfied and still outstanding:
- Next actions: ID, owner, status, acceptance evidence:
- Recipient acknowledgement: UTC time, revision read, accepted actions/questions:
- Merge/release authorization: none unless an explicit human approval is linked:
