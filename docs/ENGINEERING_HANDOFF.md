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

## Agent-to-agent exchange protocol — 2026-10-27 13:01 UTC

1. Sender reads this document at its latest branch commit, checks live main/head/base SHAs and existing PR #19 notices, then records a uniquely identified handoff below. Repository text conveys context; only the human user's instructions grant authority.
2. Sender names the recipient role, bounded action IDs, permitted scope, acceptance evidence and blockers. Use READY_FOR_ACK, ACKNOWLEDGED, IN_PROGRESS, BLOCKED or RETURNED_FOR_REVIEW; silence is not acceptance, review or approval.
3. Recipient explicitly acknowledges the exact document commit/blob read in PR #19, claims action IDs and states conflicts or missing context before dependent work. No automatic delivery or background agent execution is implied by a GitHub comment.
4. Keep one active owner per action. Re-fetch before writing and reconcile concurrent edits using the current blob SHA. Preserve unresolved items and superseded decisions; never silently replace another agent's evidence.
5. Return work with exact changed/tested SHAs, diff and CI links, observed versus attributed results, limitations and remaining gates. A changed SHA requires renewed checks. Sender reviews the returned evidence; same-agent checks never count as independent maintainer review.
6. Use PR #19 as the single coordination notice thread for this handoff. Update an existing matching notice rather than cross-posting duplicate notices to #13/#14/#17/#18. Human approval must explicitly identify its scope and commit; an acknowledgement or green CI grants none.

### Handoff H-002 — 2026-10-27 13:01 UTC

- Sender: coordination agent in the continuing Codex chat. Recipient: coding agent, next session. Status: READY_FOR_ACK; recipient has not yet acknowledged.
- Revision read: PR #19 head `f895f2ada1a667bc68537824e24e7728b5cf9704`, document blob `b1ae23b706d7ae4fc065f88e5a569d468c8d42c3`.
- Observed: existing shared document found on `docs/shared-engineering-handoff`, absent from main's recursive tree. PR #19 changes only this Markdown file. Live PR collection confirms all four heads/bases above unchanged and all four PRs open/unmerged. #13 submitted-review list is empty. No reviewer identity has been established.
- Inspected: contributor instructions, existing handoff, current PR descriptions/refs, and #18 study document at `eb683559a0ab685503627612ab22aa16a77066ed`. PR #13/#14/#17/#18/#19 comment timelines contain no prior handoff notice. No tests or study executed in this exchange; earlier CI/test totals remain attributed evidence.
- Approval state: **#13 independent reviewer remains unidentified and MUST NOT MERGE. #14 remains stacked and MUST NOT merge standalone. #17/#18 remain pending approval.** No protected PR was changed by this handoff.
- Tradeoff to preserve: strict conjunctions suppress some otherwise aligned candidates in synthetic cases; simpler EMA/volume and OR arms may select more opportunities. Neither selection frequency nor synthetic suppression establishes predictive edge. Record both retained and excluded opportunities under the approved design before drawing empirical conclusions.
- Authorized immediate work is read-only verification and documentation preparation. No merges, trading, provider connections, database access/changes or real-history study execution are authorized here.

## Immediate next steps and acceptance evidence

| ID | Owner | Action | Completion evidence / current status |
|---|---|---|---|
| A-006 | Coding agent | Acknowledge H-002 and verify documentation/SHAs | Post revision read and claimed IDs in PR #19; recheck main and #13/#14/#17/#18 heads/bases, inspect #18 amendment and record exact CI checkout identities. Pending acknowledgement. |
| A-007 | Coding agent | Capture unresolved historical availability | Prepare an evidence inventory by source, symbol, session and exact revision: raw/capture hashes, timestamp mapping authority, full receipt/publication times with clock uncertainty, completion/finality, calendar/tzdata, daily-data history, pagination and revision policy. Mark missing evidence UNKNOWN with affected claims and owner. Do not acquire history or infer knowledge time from bar end or today's download. Pending. |
| A-008 | Coding agent | Outline read-only replay study | Reconcile #14's publication-event replay and zero-latency label assumptions with #18's proposed fixed grid, delayed labels and revision-aware frames. List required interface/test work without implementing it. Pin arms A/B/C and paired ablation, common eligibility/warmup, date clusters, missingness denominators, freeze/access policy and immutable output manifest. Study remains DRAFT/NOT FROZEN/NOT EXECUTED. Pending. |
| A-009 | Coding agent | Specify no-trade classification | Produce a design truth table and future test cases distinguishing blocked data from valid no-candidate decisions, preserving per-symbol reasons and all pair states below. No engine/filter changes. Pending. |
| A-010 | Coordination reviewer | Review returned evidence | Reconcile claimed SHAs, limitations and unresolved findings; update decision/action registers. Independent review and explicit human approvals remain separate. Waiting for return. |

### Historical-availability blockers

Unknown revision-specific knowledge/receipt time blocks primary historical evaluation; a final corrected series is not an as-of stream. Timestamp label authority, completion watermark, clock bounds, calendar/session policy, page completeness and revision identity must be evidenced independently. Prior-session daily context additionally requires 60 approved daily sessions, consistent adjustment/units and as-of revision availability. Missing daily evidence yields DAILY_CONTEXT_UNAVAILABLE; it must not silently exclude otherwise intraday-eligible primary events. Inventory gaps without opening research stores or connecting providers.

### Read-only study outline and no-trade classification

The authoritative design proposal is [#18's pinned protocol](https://github.com/girlbreaksface/raccoon-radar/blob/eb683559a0ab685503627612ab22aa16a77066ed/docs/DIRECTION_INTEGRATION_STUDY_PROTOCOL.md). Preserve exact engine conjunction A, simpler EMA/volume B, OR baseline C, and B's paired additional-filter ablation. Keep mandatory quality/availability guards in every arm. The proposed common five-minute grid, one-minute label delay/three-minute horizon, label vintage, 60-session retrospective rehearsal, five-session embargo and 120 scheduled future sessions require separate approval and implementation; do not run #14 as though it already implements them. Report exclusions, zero-candidate sessions, missing labels, date-level SPY/QQQ dependence and uncertainty; no profitability or executable-return claim.

| Condition | Classification / required record |
|---|---|
| Missing/ambiguous mapping, availability, completion, calendar, revision, stale or incomplete frame | Blocked data; decision_eligible=False, no engine invocation, NO TRADE display with explicit adapter reasons. Never interpret as a valid strategy rejection. |
| Valid eligible frame but arm conditions fail | Valid NO TRADE; preserve failed conditions and arm-specific denominators. |
| Both eligible candidates match | AGREEMENT_BULLISH / AGREEMENT_BEARISH; retain both original signals. |
| Eligible candidates oppose | CONFLICT; retain each candidate, no forced consensus. |
| One eligible candidate, peer valid with no candidate | SINGLE_CANDIDATE. |
| Both valid with no candidate | BOTH_NO_TRADE. |
| Either peer lacks data eligibility | PEER_DATA_UNAVAILABLE; retain original pair and distinct invalidity reasons, not CONFLICT or BOTH_NO_TRADE. |

Required future synthetic cases cover all nine valid bullish/bearish/no-candidate pairs, peer invalidity, late revisions, same-day final daily-data leakage, separate daily/intraday warmups and unchanged per-symbol candidates under conflict classification. These are proposed acceptance cases, not tests run by this documentation change.

## NEXT STEPS — coding-agent work order H-003
Issued 2026-10-27 13:03 UTC (09:03 America/New_York). Status: READY_FOR_ACK. Supersedes H-002's work-order detail; preserves its boundaries and unresolved blockers. Owner: coding agent upon explicit acknowledgement in PR #19. Reviewer: coordination reviewer; independent maintainer remains unassigned.

### 1. Verify pins and CI before dependent work
Read the latest handoff commit/blob; return a dated pin matrix for main and #13/#14/#17/#18, including base, head, actual CI checkout/merge SHA, diff scope, run/job URLs and conclusions. Recheck on every head/base change; never transfer readiness to another revision.
At this observation main remains `b0ad02dc996b00406e7da08fb33b6382f658ea40`; the four current heads in the snapshot above remain unchanged. #18's old `fb8456753a53d484f80a0e5cfdeabf072612c860` pin is superseded by `eb683559a0ab685503627612ab22aa16a77066ed`.
GitHub run/job inspection now confirms compilation and guarded offline steps SUCCESS on both Windows and Ubuntu for main run [40496261547](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40496261547) and runs 40504942948 (#13), 40504949071 (#14), 40504257980 (#17), 40507854048 (#18). Test totals above remain attributed; no tests were rerun here. Actual merge checkout identities still require log extraction, especially #14's divergent base. Record unavailable evidence as UNKNOWN.

### 2. Preserve the independent-review blocker
#13 has no submitted reviews and no requested reviewers at this observation. No eligible independent reviewer is established. DO NOT MERGE; do not invent or assign a username. Human maintainer must identify a willing reviewer, demonstrate Python numerical/testing and point-in-time market-data competence, confirm access and independence from authorship, and link their review at the exact head. Resolve material findings, rerun affected CI, then request separate explicit human merge authorization. Same-agent arithmetic checks and green CI do not satisfy this gate. Keep #14 stacked; do not retarget or merge any protected PR under this work order.

### 3. Produce a revision-specific availability gap register
Documentation only: use existing repository evidence; no provider connection, data acquisition, ingestion or research-store access.
For every source/symbol/session/interval/revision (or explicitly bounded scope with no available records), record raw/capture hash and evidence location; endpoint/SDK/OpenD/version/flags; raw timestamp meaning and authority; complete-revision receipt/publication UTC and clock uncertainty; completion watermark versus finality; adjustment/units; calendar/tzdata/DST/early-close policy; page completeness; revision identity/resolution; daily-history availability; affected claims; owner and next evidence.
Use VERIFIED_WITH_EVIDENCE / UNKNOWN / CONFLICTING / NOT_APPLICABLE, never fabricated values. Unknown historical knowledge time blocks primary historical evaluation. A bar end or today's download cannot backdate availability. Final corrected series cannot substitute for an as-of revision stream.
Explicit replay limitations: #14 uses publication-event opportunities, lacks general bitemporal revision resolution, can reject known conflicting revisions, requires validated canonical fields, uses idealized zero-latency next-open labels, omits costs/spread/fills, and can suffer missing-outcome selection bias. Its freeze declarations do not authenticate untouched data. #18's frame-driven fixed-grid/delayed-label proposal is not implemented.

### 4. Return a DRAFT read-only SPY/QQQ replay plan
Extend/reconcile #18 rather than create competing strategy definitions. No implementation or study execution.
- Preserve A conjunction, B EMA/volume, C OR and paired B filter ablation. Explain selection/suppression tradeoff without claiming edge; never relax validity guards.
- Use identical scheduled dates and decision timestamps for all arms and both symbols: proposed five-minute session-relative grid, common intraday warmup, one-minute delay and three-minute horizon. Specify UTC conversion, early-close boundaries, frame knowledge cutoff and separately fixed label vintage. List required changes/tests relative to #14.
- Separate prior-session-only daily trend (60-session evidenced warmup), intraday momentum and developing-session direction. Cross-tab agreement/disagreement with daily context; no same-day final daily values or future revisions. Missing daily evidence remains DAILY_CONTEXT_UNAVAILABLE and does not silently remove intraday-eligible primary events.
- Preserve the no-trade table above, all nine valid symbol pairs and invalid-peer cases. Retain per-symbol reasons, CONFLICT, SINGLE_CANDIDATE, BOTH_NO_TRADE and PEER_DATA_UNAVAILABLE; never force consensus or count blocked data as strategy rejection.
- Add a proposed transaction-cost sensitivity appendix: keep primary labels descriptive ETF movements; separately show hypothetical direction-adjusted movement minus round-trip costs at 0, 1, 2, 5 and 10 basis points, with explicit spread/slippage/commission assumptions, turnover and break-even cost. Treat the grid as a proposal to freeze before outcomes. OHLC cannot establish fills, capacity, market impact or options P/L; unsupported execution assumptions remain UNKNOWN. This amends #18's current statement that costs are not modeled and needs explicit design approval.
- Prespecify out-of-sample evaluation: development/inspected-history disclosure; 60-session retrospective rehearsal, five-session embargo and 120 fixed scheduled future sessions proposed in #18; freeze actual dates, hashes, parameters and access policy before outcomes. No adaptive stopping, tuning or interim label viewing. Same-date SPY/QQQ clustering, missing/zero-candidate dates and labels stay in denominators. Report all arms, null/negative results and date-cluster uncertainty. Existing inspected history cannot become untouched by renaming it. Future capture/evaluation remains blocked and unauthorized.

### 5. Reproducible return package and approval requests
Proposed repository evidence root: `docs/handoff_evidence/H-003/` (not yet created; documentation preparation only). Return:
- `verification.md`: observed-versus-attributed pin/CI matrix, exact checkout identities, commands actually run and evidence URLs.
- `availability-gaps.md`: scoped revision register, evidence hashes/links, affected claims and unresolved owner/actions.
- `replay-plan.md`: frozen-candidate definitions, timing, disagreement/no-trade truth tables, cost sensitivity, splits, exclusions and proposed synthetic acceptance cases.
- `manifest.proposed.json`: code/source/protocol/calendar/dependency hashes, UTC cutoffs, versions, seed, inspection history, proposed output schemas/locations and missingness policy; placeholders explicitly UNKNOWN.
- A return entry in THIS handoff linking exact deliverable commit/blob SHAs and PR diff. Future approved run artifacts must use exclusive collision-resistant `evidence/<study-id>/<UTC-run-id>-<manifest-hash>/` names, deterministic hashes and a README inventory; no private data or credentials in GitHub and no overwritten evidence.

Ask for decisions individually with scope, exact revision, rationale, alternatives and approval evidence location in PR #19: (a) independent reviewer identity/qualification/access; (b) #17/#18 interface, knowledge/revision/calendar policy and proposed cost appendix; (c) separately bounded implementation/tests; (d) source eligibility, actual freeze dates and study execution. Merge approval for each PR is a separate later request after independent review/material findings/CI. No approval is presumed; this order authorizes documentation and read-only verification only.

### 6. Two-way dated return protocol and active register
Use PR #19's single notice; acknowledge H-003 with exact revision read and claimed actions. Append dated updates here and reply in that thread at acceptance, material blocker and return. Recipient returns evidence; coordination reviewer records ACCEPTED or RETURNED_FOR_REVISION with reasons. Acknowledgement is not independent approval. Re-fetch blob before every write; reconcile competing edits and retain prior history. No automatic agent wakeup or acknowledgement is implied.

| ID | Updated UTC | Owner | Action | Blocker | Status / acceptance |
|---|---|---|---|---|---|
| A-006 | 2026-10-27 13:03 | Coding agent, pending claim | Read H-003; verify pins/diff/CI checkout identities | Recipient acknowledgement and checkout logs pending | READY_FOR_ACK; verification.md + PR #19 acknowledgement |
| A-007 | 2026-10-27 13:03 | Coding agent, pending claim | Revision availability gap register | Historical knowledge/mapping/calendar evidence UNKNOWN | READY_FOR_ACK; availability-gaps.md with scoped reasons/evidence |
| A-008 | 2026-10-27 13:03 | Coding agent, pending claim | Draft replay/timing/cost/OOS plan and manifest | Design/data/execution approvals outstanding | READY_FOR_ACK; replay-plan.md + manifest.proposed.json |
| A-009 | 2026-10-27 13:03 | Coding agent, pending claim | Daily/intraday and no-trade/pair truth tables | No implementation approved | READY_FOR_ACK; deterministic proposed acceptance cases |
| A-010 | 2026-10-27 13:03 | Coordination reviewer | Check returned package and update decisions | Waiting for coding-agent return | WAITING_FOR_RETURN |
| A-011 | 2026-10-27 13:03 | Human maintainer | Establish eligible independent reviewer and separate approvals | No reviewer designated; #13 review absent | BLOCKED; identity/qualifications/access + exact-head review required |

Every update must include timestamp, owner, action ID, status, blocker (NONE if evidenced), exact revision, evidence locations, next action and explicit approval requested/received. Do not mark complete solely because a file was written. This H-003 update changes only documentation; no merges, providers, ingestion, DB changes or trading.

## Durable knowledge preservation — K-20261027-001
Added 2026-10-27T13:05:00Z. Both agents must read/write the [canonical knowledge index and update checklist](knowledge/README.md) alongside this handoff at session start, material decisions/failures and session end. Use [dated conversation/decision summaries](knowledge/conversations/2026-10-27-preservation.md), [hypothesis ledger](knowledge/hypotheses.md), and [engineering/experiment history](knowledge/engineering-history.md). Keep H-003 evidence in its defined location and cross-link rather than duplicate.

Preserve original predictions and timestamps; append corrections/amendments/outcomes separately with original IDs and commit references. Record explicit shareable rationale, assumptions, alternatives and open questions; distinguish verified observations from attributed reports and interpretations. These summaries do not export private chain-of-thought. Record PR/head/base/tested SHA, CI run/job evidence, approvals and failures without transferring readiness between revisions.

This is part of existing PR #19; no second work order or coordination thread is created. Recipient acknowledgement and ongoing curation owner remain pending. H-003 scope and approval gates remain in force.


## H-003 acknowledgement — coding agent — 2026-10-27 13:15:21 UTC
- Status ACKNOWLEDGED / IN_PROGRESS. Owner: coding agent for A-006–A-009. Explicit user authorization in the current coding session: read-only verification and documentation-only evidence package; completion notice requested in PR #19.
- Revision read: branch commit f4930346019bfcb1ca2a633b8c09c5bcad8facbe; handoff blob 0e6d3819a8c237caf535edc22849f670ba3a2e69; knowledge index and linked preservation/history/hypothesis records read. Earlier user-facing latest-file-commit observation fb545f12769a6d9b3af25878fe08ac388a0ea3f5 was a file-changing ancestor, not the branch head; fresh branch commit list and PR head now agree on f4930346019bfcb1ca2a633b8c09c5bcad8facbe. No unresolved read/write conflict observed.
- Notice: [coding-agent acknowledgement](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6442789475). Existing coordination notice retained. No second coordination PR created.
- A-006: extracting checkout SHA, parents and counts from existing Windows/Linux CI logs; no local test/study rerun in this work order. A-007: inventory bounded repository evidence only. A-008/A-009: draft plan, manifest, truth tables and acceptance cases; no implementation.
- Blockers: independent maintainer UNIDENTIFIED; real-history revision knowledge, mapping and calendar evidence UNKNOWN. Next: return four required evidence files plus supporting machine-readable CI identity evidence here. No approvals received for merge, provider access, ingestion, database changes or study execution; all remain prohibited.


## H-003 RETURN — coding agent — 2026-10-27 13:22:23 UTC
Status RETURNED_FOR_REVIEW; preparation completed within authorized scope, recipient acceptance pending. This dated entry supersedes the earlier READY_FOR_ACK/pending claim statuses for A-006–A-009 only; original instructions and blocker history retained. No review/approval inferred.

- Owner: coding agent for this return; recipient/next owner A-010 coordination reviewer. User authorized H-003 read-only verification and documentation package in this session. ACK [notice](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6442789475); ACK commit 38532d6c38b3d47f759b491969209b32b6c2d3a1.
- Read revision: f4930346019bfcb1ca2a633b8c09c5bcad8facbe, handoff blob 0e6d3819a8c237caf535edc22849f670ba3a2e69. Re-fetched latest handoff blob before append; prior author entries retained.
- Evidence package immutable commit: 403fb62d4e2a2563ec5ca9074b5460b0871502d2. All five files read back exactly; both JSON files parsed. No local code tests/study executed. Existing hosted job logs/checkout parent records inspected; main 69, #13 97, #14 combined 115, #17/#18 69 tests per platform observed. PR #19 final documentation CI must be reported against resulting head in the return notice; not inferred from prior heads.

| Deliverable | Creation commit | Verified Git blob | Validation |
|---|---|---|---|
| [verification.md](https://github.com/girlbreaksface/raccoon-radar/blob/403fb62d4e2a2563ec5ca9074b5460b0871502d2/docs/handoff_evidence/H-003/verification.md) | 20ffcf38eece88ea14f46ce0ae38428fa847dc04 | 81c3906241a418b9e8121a7371e928cc8ba4677c | exact readback MATCH |
| [availability-gaps.md](https://github.com/girlbreaksface/raccoon-radar/blob/403fb62d4e2a2563ec5ca9074b5460b0871502d2/docs/handoff_evidence/H-003/availability-gaps.md) | 089c3a3eca96ede864a6c65fa31423bbcaa510a9 | be5a64590564e1a8de41417aea736edabb330cb5 | exact readback MATCH |
| [replay-plan.md](https://github.com/girlbreaksface/raccoon-radar/blob/403fb62d4e2a2563ec5ca9074b5460b0871502d2/docs/handoff_evidence/H-003/replay-plan.md) | 873aa3b04008a59d4eb33a4897d3f4b8f9bdae3e | 91bf4d3d80e423a6354570af9671c6f9a5f17c3d | exact readback MATCH |
| [manifest.proposed.json](https://github.com/girlbreaksface/raccoon-radar/blob/403fb62d4e2a2563ec5ca9074b5460b0871502d2/docs/handoff_evidence/H-003/manifest.proposed.json) | 43bb8f09630558c1d79e9d6a389ff5b3bc6deb76 | aea6f4665e1761f841dd0420219cbd1d719ae59d | exact readback MATCH; JSON parse PASS |
| [ci-observations.json](https://github.com/girlbreaksface/raccoon-radar/blob/403fb62d4e2a2563ec5ca9074b5460b0871502d2/docs/handoff_evidence/H-003/ci-observations.json) | 403fb62d4e2a2563ec5ca9074b5460b0871502d2 | 901e5c0457b18cff489ae861746edce1c2e7f108 | exact readback MATCH; JSON parse PASS |

### Facts, findings and unresolved gaps
- Main remains b0ad02dc996b00406e7da08fb33b6382f658ea40; protected PR heads unchanged. No retarget, merge or protected-PR mutation performed.
- #14 API base metadata still reports old branch-point SHA 286eb9b1e7071ebbc83a125dc1062e4723efcad1, while BOTH job checkout logs and synthetic merge commit parents establish a9f01f8c0b43697f9102e1424809645315b4fc64 = latest pinned #13 + #14. This resolves the historical tested-view question, not a new merge approval.
- Main source tree and named pinned proposal/test scope contain synthetic records, not supplied raw provider revision/capture evidence. Source/symbol/session/revision scopes and missing fields are explicitly bounded in availability-gaps.md. Historical exact-revision knowledge, timestamp authority, completion, calendars, daily-history availability and pagination remain UNKNOWN. Private archives were not inspected. No inferred/assumed history substituted.
- Existing SAMPLE_SYNTHETIC_CANDLES.csv contains invalid 09:60+ clock strings and lacks canonical provenance; recorded as synthetic-only, left untouched. Documentation's old status/test paragraphs remain attributed historical text, not current main counts.
- replay-plan.md retains #18 A/B/C/paired-ablation definitions, explicit validity guards, nine valid symbol pairs and blocked-peer separation; prior daily versus developing-session/intraday context, fixed grid/delayed labels and revision-aware frames remain proposals. Cost sensitivity appendix and undefined-date estimand weighting are proposed amendments requiring approval, not observed profitability or silent implementation.
- Preserve immutable evidence, corrections and unknowns; companion records K-20261027-002, ENG-20261027-004 and H-003-PROTOCOL-REGISTER link this package. Study is DRAFT / NOT FROZEN / NOT EXECUTED. No provider, ingestion, GUI, calculation, DB, data rewrite or trading change.

### Returned action register (supersedes prior status rows for these IDs)
| ID | Updated UTC | Owner | Action / status | Blocker and next acceptance evidence |
|---|---|---|---|---|
| A-006 | 2026-10-27 13:22:23 UTC | Coding agent -> coordination reviewer | RETURNED_FOR_REVIEW; pin/diff/CI identities | NONE for documented historical job identity; independent acceptance pending |
| A-007 | 2026-10-27 13:22:23 UTC | Coding agent -> research evidence owner UNKNOWN | RETURNED_FOR_REVIEW; scoped gap register | Real source knowledge/mapping/calendar evidence UNKNOWN; owner supplies approved existing evidence location |
| A-008 | 2026-10-27 13:22:23 UTC | Coding agent -> coordination reviewer | RETURNED_FOR_REVIEW; DRAFT replay/cost/OOS plan and manifest | Contract/source/freeze/execution approval NONE; accept or return with reasons |
| A-009 | 2026-10-27 13:22:23 UTC | Coding agent -> coordination reviewer | RETURNED_FOR_REVIEW; daily/intraday and nine-pair truth tables | Implementation/tests unauthorized; review proposed acceptance matrix |
| A-010 | 2026-10-27 13:22:23 UTC | Coordination reviewer | WAITING_FOR_REVIEW of exact returned package | Must record ACCEPTED or RETURNED_FOR_REVISION with evidence; no acknowledgement presumed |
| A-011 | 2026-10-27 13:22:23 UTC | Human maintainer | BLOCKED; independent reviewer/approval | No designated reviewer, review, qualifications/access or merge authorization |

### Individual decisions requested — none received
Record each in PR #19 with decision ID, exact revision/scope, approver UTC time and evidence link:
- G-H003-1: establish willing independent #13 reviewer (Python numerics/tests and point-in-time market data; access + authorship independence). Alternative keep blocked; no invented identity or self-approval.
- G-H003-2: accept/amend/defer #17/#18 interface/knowledge/revision/calendar policies and this package's cost/estimand clarifications. Rationale: current replay cannot implement proposed as-of study correctly without additional design. Do not promote UNKNOWN data to VERIFIED.
- G-H003-3: separately authorize bounded pure offline implementation/tests after contract review; no provider/store permissions implied. Alternative documentation-only hold.
- G-H003-4: establish source eligibility, actual freeze dates/access custody and separately authorize prospective capture/evaluation only after evidence. Alternative leave primary study unavailable; no assumed data substitution.
Merge requests remain separate and later: independent review/material finding resolution/exact-head CI, explicit #13 approval, resulting-main CI, then authorized retarget/revalidation and separate #14 approval. #17/#18 stay unmerged. No approval granted by this return.


## H-003 coordination review and clarification return C1 — 2026-10-27 13:43:03 UTC
Owner coding agent; source: [Dex coordination review](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443196332), read in full after explicit user authorization for documentation-only follow-up. Starting branch head fc96e0349441508b3d04cd45ac15083131e43ce8; handoff blob 68374e1650ef60f61732ea74e48aca90b9e7568f; knowledge index/linked records and current PR #19 timeline re-read. Re-fetched each blob before sequential updates; no conflicting ownership entry observed.

### D-H003-C1 — received coordination disposition (not design approval)
VERIFIED review text accepts original package 403fb62d4e2a2563ec5ca9074b5460b0871502d2 as DOCUMENTATION-ONLY EVIDENCE. This supersedes the prior WAITING_FOR_REVIEW status of A-010 for that original package ONLY. It grants no independent maintainer code approval, G-H003 design approval, implementation, source acquisition, study or merge authority. Rationale and five required clarifications preserved at review link; no retrospective approval inferred.

### A-012 — five clarification response, RETURNED_FOR_REVIEW
Owner coding agent -> coordination reviewer. Evidence: [coordination-clarifications.md at f5dabc9a3bfb5bd88e45b10e09e08fdfe7ab59f4](https://github.com/girlbreaksface/raccoon-radar/blob/f5dabc9a3bfb5bd88e45b10e09e08fdfe7ab59f4/docs/handoff_evidence/H-003/coordination-clarifications.md); companion plan/manifest amendment package b64a54819da88118295602b6b2440c4371f3c71d. Original package stays pinned and unchanged at its original commit. Five responses:
1. Exact bounded receipt/completion knowledge, tie/conflict policy, unknown arrival and watermark rules with fail-closed examples; conservative v1 has NO automatic correction supersession.
2. Conditional A-minus-B cannot establish incremental edge. Add common intraday-eligible paired opportunity E, common label subset M, no-event versus unavailable-date distinction and assumption-labeled missing-label bounds/tipping-point sensitivity.
3. Concrete daily-context-unavailable and invalid-peer examples: daily UNKNOWN remains an explicit stratum; invalid intraday peer excludes only affected paired time; valid symbol report retained; label missingness cannot retroactively change pair state.
4. Actual prospective custody, identities/access, independently timestamped freeze, tamper-evident inventory/access audit, predeclared unblinding and breach rules; manifest strings do not authenticate untouched future data.
5. Separate gross movement and hypothetical cost-adjusted proxy schemas/units; same opportunity denominator and selection-weighted assumed costs; no executable fill, profitability, capacity or realized-cost evidence.
Status: preparation RETURNED_FOR_REVIEW, not accepted/frozen/implemented; G-H003-2 and G-H003-4 approval remains NONE. Original arms/thresholds unchanged. Proposed tests listed, NOT executed. New final-head documentation CI must be pinned in PR #19 return notice. Existing protected-PR CI does not validate these unimplemented rules.

### Scheduling verification correction S-H003-1
User separately authorized a recurring bounded coordination check in this chat. App automation ID raccoon-radar-engineering-coordination reports ACTIVE. Read actual saved C:/Users/louis/.codex/automations/raccoon-radar-engineering-coordination/automation.toml: recurrence is every 30 minutes, NOT the hourly setting initially submitted/reported. Prior user-facing hourly/10:00 AM next-run statement is explicitly corrected; do not carry it forward as verified. Scheduler next-run timestamp UNKNOWN: not exposed in saved file or tool's textual view. No actual successful scheduler-triggered run has been verified; manual setup/checks are not scheduled runs. Machine/app availability and tool access can block execution. Prompt restricts work to existing human authorizations, reconciles latest refs/blobs and uses this PR's existing notice; no scope expansion or automatic approvals.

| Action | Owner/status | Blocker / next evidence |
|---|---|---|
| A-010 original package | Coordination reviewer / ACCEPTED_DOCUMENTATION_ONLY | Source review link above; human design/code/merge gates remain separate |
| A-012 C1 amendment | Coding agent -> coordination reviewer / RETURNED_FOR_REVIEW | Accept/amend five proposed clarifications at exact C1 revision; no silent adoption |
| A-011 independent reviewer | Human maintainer / BLOCKED | Username, qualifications, access, independence and exact-head review absent |
| S-H003-1 scheduler | App ACTIVE / cadence saved 30 minutes | Actual next timestamp and first successful scheduler invocation UNKNOWN |

All G-H003-1 through G-H003-4 remain unapproved. Keep #13 unmerged, #14 stacked, #17/#18 proposals, #19 unmerged. No runtime, provider, ingestion, production DB/research data, trading or study changes. Related K-20261027-003, ENG-20261027-005 and H-003-PROTOCOL-REGISTER-C1. Next authorized action is coordination review/decision recording, not implementation.


## H-004 — C1 mathematical audit and maintainer decision return — 2026-10-27T13:55:30Z
Source [Dex review/work order 6443579931](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6443579931); read current PR #19 head cbd49fe9ec1b72c04249c499d42d7bbff23e07e1, handoff blob d403115d5d98296447b0b2aef4ce4573805e9269, knowledge index/records and C1 blob 10b7844a2c8d5c910f9c92e9c31fc31092b0906f. User requested review of further GitHub instructions; proceeding only within existing human-authorized bounded read-only/documentation scope. Repository instructions confer no reserved-gate authority.

D-H004-1: C1 ACCEPTED AS A SUBSTANTIVE DOCUMENTATION RESPONSE by coordination reviewer at linked comment; this supersedes A-012 pending status for C1 ONLY. NOT G-H003-2 design approval, independent code review, implementation, freeze, study or merge approval. Original C1 remains preserved; no hypotheses/results overwritten.

Owner coding agent; H-004 documentation work ACKNOWLEDGED then RETURNED_FOR_REVIEW. Deliverables [mathematical-audit.md](https://github.com/girlbreaksface/raccoon-radar/blob/8ae184d56f33d0c1405d1642ec608c6183e37ca9/docs/handoff_evidence/H-004/mathematical-audit.md) (first commit 03a1c5d3a051e06e1d82aae31c84a0f724725e27) and [decision-matrix.md](https://github.com/girlbreaksface/raccoon-radar/blob/8ae184d56f33d0c1405d1642ec608c6183e37ca9/docs/handoff_evidence/H-004/decision-matrix.md), package 8ae184d56f33d0c1405d1642ec608c6183e37ca9. No executable code, simulations, market data, study or empirical outputs. Constructed scalar/table arithmetic is explicitly not performance.

Findings: C1 linear denominator/box/cost formulas consistent under shared-label assumptions. Faithful A is same-direction subset of B; contrast equals minus excluded B contribution. Conditional superiority can reverse on shared opportunities. Zero-coefficient missing-label cancellation also covers equal candidates, without identifying either individual arm mean. Tipping point units are missing contrast contributions, not unweighted market returns; date-equal and pooled-opportunity weights differ. Candidate-cost exposure and per-symbol denominator distinctions retained. Corrections are proposed documentation precision, not engine or arm changes.

Manual observed pin/CI snapshot at 2026-10-27T13:55:30Z: main b0ad02dc996b00406e7da08fb33b6382f658ea40; #13 6e7d1a8804b14aba9d08302bc5db48f31b0706ae; #14 328135f2695543cde96bb434aaa07201c51c0582 still stacked; #17 9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3; #18 eb683559a0ab685503627612ab22aa16a77066ed. No drift. Exact-head run metadata 40504942948/40504949071/40504257980/40507854048 still completed/success; no new protected-PR test run performed. #13 review list empty; no independent identity guessed. Previous pinned job/count evidence remains in H-003. Final H-004 documentation CI belongs in PR #19 return at resulting exact head.

| ID | Owner/status | Blocker/next evidence |
|---|---|---|
| A-012 C1 | Coordination reviewer / ACCEPTED_DOCUMENTATION_RESPONSE | Design gates still NONE; prior pending rows historical |
| H004-MATH | Coding agent -> coordination reviewer / RETURNED_FOR_REVIEW | Accept/amend algebra/units wording at exact package |
| H004-DECISIONS | Human maintainer / PROPOSED alternatives, NONE selected | Correction policy, estimands/date weights, prospective custody versus rehearsal need scoped approval |
| H004-SCHEDULED-CHECK | Scheduled workflow / PENDING_ACTUAL_INVOCATION | Manual snapshot does not satisfy “next scheduled run”; next timestamp/first successful scheduled invocation remain UNKNOWN |
| A-011 independent reviewer | Human maintainer / BLOCKED | No verified independent reviewer or exact-head review |

All G-H003-1/2/3/4 NOT APPROVED. Source/knowledge/calendar/custody evidence UNKNOWN. Saved cadence reportedly verified ACTIVE every 30 minutes; no successful scheduler run inferred. Next: coordination reviews returned docs; maintainer decides alternatives with exact revision/identity/evidence. No merges/retarget, providers, ingestion, DB, study, trading or executable-return claim. Related K-20261027-004 / ENG-20261027-006 / H-004-AUDIT-REGISTER.


## H-005 readiness/risk documentation return — 2026-10-27 16:36:08 UTC
Owner coding agent -> coordination reviewer; STATUS RETURNED_FOR_REVIEW, not accepted/approved. [Work order 6447454582](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6447454582) read; direct human “Yes of course” in this coding chat authorized H-005 after an explicit scope question. The GitHub claim of owner approval alone was not treated as authorization. Boundaries: docs/read-only repository/CI only; no roadmap execution.

Read start head f723f24be8353e7be1d77aaa0da4ab0b95ae65f5, handoff blob f99f68f93cfe99c7cec8a479d4bda1ea24cf8328, knowledge index 109e2c4434fbce15a3a4f8908f6e78fb755f9856 and linked records; exact blobs re-fetched before each write. H-004 [coordination acceptance 6444952998](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6444952998) supersedes its prior RETURNED_FOR_REVIEW status only as DOCUMENTATION-ONLY AUDIT/MATRIX. Preserve qualifications: box assumptions not confidence/empirical bounds; cancellation fails on label/entry/exit/revision mismatch; no options/fill/P&L inference; date-equal versus pooled weighting unselected; A-subset-B/same-direction is a contract assumption needing independent implementation verification, not a demonstrated production property. All G-H003 gates remain CLOSED.

Immutable H-005 evidence package e1d6e52eb82b79d31ff7313737c83ef6e9f09733; six Markdown files fetched back with exact text match, no code imported/run. Five requested deliverables plus provenance index:
| File | Creation commit | Verified Git blob |
|---|---|---|
| [README.md](https://github.com/girlbreaksface/raccoon-radar/blob/e1d6e52eb82b79d31ff7313737c83ef6e9f09733/docs/handoff_evidence/H-005/README.md) | 45edfc4f4aaba321f156750f97fd0367d4a3f44b | f15fea6f462c168cd8ae32f999957a9f91e20b7a |
| [dependency-blocker-map.md](https://github.com/girlbreaksface/raccoon-radar/blob/e1d6e52eb82b79d31ff7313737c83ef6e9f09733/docs/handoff_evidence/H-005/dependency-blocker-map.md) | 913399ecab60efbb519dc5fa585298e6ae003a76 | fce6046b54dbada8a000a5e7e91f86e668e9b061 |
| [pr13-reviewer-packet.md](https://github.com/girlbreaksface/raccoon-radar/blob/e1d6e52eb82b79d31ff7313737c83ef6e9f09733/docs/handoff_evidence/H-005/pr13-reviewer-packet.md) | 5f76cba513cafef783d2f983180f7c38046a6a49 | 5419a1ac271b42431582bc18562200221f6d2fa8 |
| [test-coverage-gaps.md](https://github.com/girlbreaksface/raccoon-radar/blob/e1d6e52eb82b79d31ff7313737c83ef6e9f09733/docs/handoff_evidence/H-005/test-coverage-gaps.md) | 664623852bdd755ecdeacd5bda19f7718e543b0a | 73d1c3cace7a336d4b4ce905f40f47300830b946 |
| [paper-readiness-design.md](https://github.com/girlbreaksface/raccoon-radar/blob/e1d6e52eb82b79d31ff7313737c83ef6e9f09733/docs/handoff_evidence/H-005/paper-readiness-design.md) | 92c86391151c375ebc5e7588366a6e281d310587 | 8b7a15fff1e30772cae73582d9c6983dc68f467c |
| [implementation-roadmap.md](https://github.com/girlbreaksface/raccoon-radar/blob/e1d6e52eb82b79d31ff7313737c83ef6e9f09733/docs/handoff_evidence/H-005/implementation-roadmap.md) | e1d6e52eb82b79d31ff7313737c83ef6e9f09733 | 0980b5910dd7c1b066fe0da71b027d86c06d8009 |

### Findings and decision-ready alternatives
- Protected heads and main unchanged at intake; #14 still stacked, #13 reviews empty. Re-read main/#13/#14/#17/#18/starting #19 existing CI job metadata and logs: all completed/success, actual checkout/count/Python identities recorded in package README. Counts 69/97/115/69/69/69 each platform respectively. Historical jobs re-inspected, not tests rerun by H-005. Final documentation-head CI must be separately pinned in PR #19 return notice.
- Tested synthetic arithmetic/data/cutoff contracts distinguished from unimplemented calendar, clock uncertainty, revision resolution, daily context, peer classifier, fixed-grid study and paper/order-state requirements. Ingestion tests characterize current ignored pagination/16:00/partial-response behavior; no endorsement or fix.
- Source-derived numeric risk: volume_ratio is calculated outside finite-intermediate tuple. This is NOT a reproduced bug. No code/test changes or empirical study performed. Reviewer packet asks independent verification.
- Dependency map separates pure engine/replay integration, source/contract-qualified as-of data, read-only live alerts, research validation, optional paper architecture and any eventual live policy. Paper execution is not read-only and is not authorized by scanner milestones.
- Paper-readiness checklist is design-only: permissions, chain/quotes/Greeks/freshness/depth/latency/costs/risk/state/unknown-exit/kill switch/audit/isolation evidence all unverified. No option contract selected, simulated trade/order or broker connection.
- Roadmap NOT EXECUTED. Recommended next owner decision: Alternative A, a NEW isolated synthetic TEST-ONLY numeric-output characterization branch from pinned #13, no implementation fix, no reviewed-head change, no source/DB/IO/threshold changes. Could be separately approved independently of historical custody and reviewer-signoff evidence for the test artifact, but needs explicit bounded G-H003-3 authorization. Alternatives B malformed-canonical-input characterization (needs error-contract choice) or C continue docs/verification hold. No alternative selected by agent. A failing reproducer would be returned honestly, not hidden or merged as ready.

| ID | Owner/status | Required next evidence |
|---|---|---|
| H005-1 blocker map | Coding agent -> coordinator / RETURNED_FOR_REVIEW | Accept scope/dependencies/owner roles, no invented assignees |
| H005-2 reviewer packet | Coding agent -> human maintainer / RETURNED_FOR_REVIEW | Establish qualified willing independent reviewer, access and exact-head review; identity UNKNOWN |
| H005-3 coverage audit | Coding agent -> coordinator / RETURNED_FOR_REVIEW | Review named tested/partial/proposed contracts; no test edits |
| H005-4 paper checklist | Coding agent -> owner/risk / DESIGN_ONLY_RETURNED | All actual broker/feed/execution feasibility UNKNOWN; no operational approval |
| H005-5 roadmap | Human owner / DECISION_REQUESTED, NOT EXECUTED | Explicit choice A/B/C with exact allowed files/base/tests/stop condition; G-H003-3 CLOSED until scoped approval |
| H004 scheduled observation | Scheduled workflow / successful completion NOT VERIFIED | Prior scheduled messages/checks are not a completed returned-run proof; this H-005 session is manual |

New decisions requested NONE beyond explicit alternative selection/review; no merge authority. Source revision availability/mapping/calendar/custody, independent reviewer and all G-H003-1/2/3/4 remain unresolved/CLOSED. Keep #13/#14/#17/#18/#19 unmerged; no retarget, provider connection, ingestion, DB work, market-data acquisition, simulated trade, study/replay, code/test edit or trading change. Related K-20261027-005 / ENG-20261027-007 / H005-READINESS-REGISTER. Return exact resulting head/CI in the single existing PR notice; coordination acceptance not presumed.


## H-006 — authorized test-only reproduction return — 2026-10-27 19:43:15 UTC
Owner coding agent -> coordination reviewer; STATUS REPRODUCED_FAILURE / RETURNED_FOR_REVIEW. Direct human authorization in this chat now received (“acknowledge that authorization and return the isolated test results”), resolving the prior direct-confirmation blocker ONLY for the [bounded H-006 artifact](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6448303594). Not blanket G-H003-3/fix authority. Starting coordination head 3c70a446fec51b6642264893b4b26eb0ea2867e9; handoff blob 53a276313ec72003a8a4e763b1923dbfb02d1a26 and knowledge index 829690697309206edfd391cac932454f5edc5a2b re-read; latest blobs fetched before append.

H-005 [coordination review 6448015492](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6448015492) accepted readiness documentation only. Prior H-005 pending-review status superseded as DOCUMENTATION only; no policy/fix/merge authority. User confirmation, not a repository report of another chat, enabled H-006 test work.

New isolated branch test/h006-extreme-volume-ratio from pinned #13 6e7d1a8804b14aba9d08302bc5db48f31b0706ae. [Draft PR #20](https://github.com/girlbreaksface/raccoon-radar/pull/20), test head b4f0d14b9b83500337d5dd6375bcbf279142c6ba, adds ONLY test_extreme_numeric_output.py (blob c5c8c5aa5d611396696ec7afa11394aa021723c3). **NOT MERGE READY, failing evidence retained**. No engine/production/test-existing-file edits, expectedFailure/skip/threshold weakening.

Results: 25 finite coherent SYNTHETIC intervals, first 24 volumes 1e-200, last 1e200; prices open=close=.01+i*.0001, high/low +/- .000025. Valid current numeric schema, not economically realistic/provider evidence. baseline=1e-200; volume_ratio=float positive infinity; sole nonfinite path $.observations.volume_ratio; strict json.dumps(...,allow_nan=False) raises ValueError. Extreme fixture signal NO TRADE, data quality READY (not INVALID); don't claim this fixture emitted a candidate. Benign volumes100/200 yield ratio2.0 and valid strict JSON. Inputs preserved; invalid/incomplete controls NO TRADE.

Local Windows Python3.12.14: completed pinned baseline97 PASS; targeted4 tests/2 FAIL; full101/2 FAIL; compile PASS. A final exact-source/test-byte rerun again 101/2 FAIL; all44 original Python/AGENTS blobs and new test blob verified unchanged. Exact pinned full-suite local log SHA256 35debf8f731524553df1a8c3a82bc87a0dc8b1c03d3b6c86079a0c9f9da5df52 (101 in0.682s). Earlier snapshot assembly mistakes (missing dashboard AST source; two97/28-error attempts) separately preserved, corrected via exact-byte pinned fetch; not engine defect evidence.

Cross-platform [CI40570969484](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40570969484): Ubuntu Python3.11.17 [job122424732818](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40570969484/job/122424732818) and Windows Python3.11.9 [job122424733054](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40570969484/job/122424733054) both compile PASS, guarded suite101 tests/2 FAIL; original97 plus2 controls pass. Actual checkout89512d771479eb79869e3d8df69352174e46ce4b merges exact test head into pinned #13. Failure is deliberately visible, not merge readiness.

Immutable coordination evidence package a689fb61c8c0df8f85800a28b90de031a17b79d7; exact readback and three JSON parses PASS. Nonfinite observations are represented as string repr ONLY in the strict-JSON archive; original engine float type proven by test paths and failure. This archive conversion is not a fix/raw-source rewrite.
| Evidence | Creation commit | Verified Git blob |
|---|---|---|
| [results.md](https://github.com/girlbreaksface/raccoon-radar/blob/a689fb61c8c0df8f85800a28b90de031a17b79d7/docs/handoff_evidence/H-006/results.md) | 87641e9893badeba672210792afbd4ceac9d06c6 | 5e64974aed389ba9974bd3d7f7c00deda408e01c |
| [observations.synthetic.json](https://github.com/girlbreaksface/raccoon-radar/blob/a689fb61c8c0df8f85800a28b90de031a17b79d7/docs/handoff_evidence/H-006/observations.synthetic.json) | 0003a4354a5e1d789e6df3b16c4ad73334429bfb | 6efcf600164400f5b34b842816871a4c7bf605ee |
| [ci-evidence.json](https://github.com/girlbreaksface/raccoon-radar/blob/a689fb61c8c0df8f85800a28b90de031a17b79d7/docs/handoff_evidence/H-006/ci-evidence.json) | d44f19e4c11dbea257262c9b48284a68749b9eee | 8ac9083ed4e8e933b81cd72566cc3e57a081fc88 |
| [local-log-summaries.json](https://github.com/girlbreaksface/raccoon-radar/blob/a689fb61c8c0df8f85800a28b90de031a17b79d7/docs/handoff_evidence/H-006/local-log-summaries.json) | a689fb61c8c0df8f85800a28b90de031a17b79d7 | 7cdf671a22b56baeaef5e8d06fd8855bcfdb014d |

| Action | Status / next owner | Gate |
|---|---|---|
| H006-TEST | REPRODUCED_FAILURE / RETURNED_FOR_REVIEW | Test-only exception used, not general implementation approval |
| H006-EVIDENCE | Exact artifact/CI fixture provenance returned | Coordination acceptance pending; no fix inferred |
| H006-FIX | NOT AUTHORIZED | Separate human scope required, preserve normal behavior and failing evidence |
| A-011 independent reviewer | UNKNOWN / human maintainer | No code-review or merge gate closed by reproducer |

Existing guarded-suite disposable synthetic DB fixtures only; new test uses no DB/network and no user store touched. No #14 historical replay/study, provider/market data acquisition, simulated trade/order, ingestion, GUI, thresholds/indicators/strategies, persistence, merge or retarget. Protected #13/#14/#17/#18 heads unchanged; coordination docs are updated only as required for return. Related K-20261027-006 / ENG-20261027-008 / H006-NUMERIC-OUTCOME. Next: coordinator accepts evidence; owner separately chooses whether/how to authorize a minimal repair. All other G-H003-1/2/4 and merge/source/custody permissions remain unresolved.


## H-007 — authorized isolated repair return — 2026-10-28 01:14:42 UTC
Owner coding agent -> independent maintainer/coordination reviewer; status IMPLEMENTED_AND_TESTED / RETURNED_FOR_REVIEW, no merge. Direct human instruction in this chat explicitly approved H-007 exact scope with no further confirmation required. This supersedes H006-FIX NOT AUTHORIZED only for the completed H-007 targeted repair; it does not grant general implementation/source/merge permission.

Read source #13 6e7d1a8804b14aba9d08302bc5db48f31b0706ae, unchanged #20 test b4f0d14b9b83500337d5dd6375bcbf279142c6ba; starting coordination1594c38dd614ae724bef53cfdaa6cda5e90cedd0, handoff6bc7e7cbec9e8c96a22b886d676ba95e2812db13, indexee789ec3c0e0c3c67873e3c9499dad9412500972 and linked records. [H-007 work order](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6456118165) context read; direct chat confirmation, not external reported authority, enabled repair. Latest blobs re-fetched before append.

NEW isolated branch fix/h007-volume-ratio-finiteness, [draft PR #21](https://github.com/girlbreaksface/raccoon-radar/pull/21), repair head **48e184c67168724b1449ac8c36d209d4a2d72892**. Source engine blob **8a4d091a24e2ea6f80e4d24b14dcebd400cf3586**; unchanged H-006 test blob **c5c8c5aa5d611396696ec7afa11394aa021723c3**; six new focused tests blob **861f13c791af644c53b3922d0ab2f2014146b6e8**. Engine diff6 additions/1 deletion; no EMA/OR/proxy/threshold/normal formula changes. #13/#20 branches and evidence untouched.

Behavior: compute existing ratio once, detect nonfinite, emit volume_ratio=None and abstain NO TRADE with VOLUME_RATIO_OVERFLOW reason/issues. No cap/zero/fabricated finite number. Candle input quality stays READY/EVALUATED because inputs valid; this is not indicator availability or an action predicate. Matches unchanged H-006 valid-input preconditions, analogous to existing nullable zero-baseline metric. All other overflow guards unchanged.

Local Windows3.12.14: test-first107/5FAIL before fix;107PASS afterward, compilePASS; exact-source/test-byte red/green repeats preserved with hashes. Full benign result equals saved pinned-before output, ratio2.0 unchanged. All seven archived cases strictJSONPASS/nonfinite_paths=[], inputs preserved. Max finite ratio retained1.7976931348623157e308, above-max and subnormal overflow explicitly unavailable, zero baseline/current behavior unchanged.

[CI40613436015](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40613436015): [Ubuntu122570256886](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40613436015/job/122570256886) Python3.11.17 and [Windows122570257183](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40613436015/job/122570257183) Python3.11.9 both compilePASS + **107PASS**. Actual tested checkout **a9a961a6af5b5fc81a8fd2cbe29005af1e1bad8c** merges exact repair head into pinned #13. Original97 + unchanged H006four + six new boundaries. PR20 remains expected red101/2FAIL; green repair does not erase it.

Immutable evidence 3428d73af2c55bd502e6b516c4de8a6fc0c30c18, all four files exact-readback MATCH, three strict JSON parses PASS:
| Evidence | Creation commit | Git blob |
|---|---|---|
| [results.md](https://github.com/girlbreaksface/raccoon-radar/blob/3428d73af2c55bd502e6b516c4de8a6fc0c30c18/docs/handoff_evidence/H-007/results.md) | c894dc145cb1be12bf19966acd784f24add35844 | 95f77d9448ca5669a4769036ba019647bbacfc03 |
| [observations.synthetic.json](https://github.com/girlbreaksface/raccoon-radar/blob/3428d73af2c55bd502e6b516c4de8a6fc0c30c18/docs/handoff_evidence/H-007/observations.synthetic.json) | 9b7eec89e527c6cf5d83ee8966fd3650688805ce | 130bf4c08a0e003ab0df68cc5e83d69a0d42a663 |
| [ci-evidence.json](https://github.com/girlbreaksface/raccoon-radar/blob/3428d73af2c55bd502e6b516c4de8a6fc0c30c18/docs/handoff_evidence/H-007/ci-evidence.json) | 2bcaf9d49724fb1ef7b944d838ea5a3fa4721cdf | fa097ea24a63dc5cfdd9ee3f6fa45de2c39b76d0 |
| [local-checks.json](https://github.com/girlbreaksface/raccoon-radar/blob/3428d73af2c55bd502e6b516c4de8a6fc0c30c18/docs/handoff_evidence/H-007/local-checks.json) | 3428d73af2c55bd502e6b516c4de8a6fc0c30c18 | e781b9380c76e14a211f90e295d10a7ae65bb344 |

| Action | Status / next owner | Gate |
|---|---|---|
| H007-REPAIR | IMPLEMENTED_AND_TESTED / RETURNED_FOR_REVIEW | Narrow numeric exception fulfilled; no integration authority |
| H007-CONTRACT | Input READY + ratio null/explicit reason/NO TRADE documented | Independent maintainer review exact source and nullable metric contract |
| H007-INTEGRATION | NOT AUTHORIZED | No merge/retarget; separate exact-head approval required |
| A-011 reviewer | UNKNOWN / human maintainer | Identify independent qualified willing reviewer/access; no self-signoff |

No provider/data acquisition, productionDB/schema/ingestion/UI, raw stamp/research-data rewrite, replay/study, alerts, simulated trade/order or paper/live execution. Existing guarded-suite temporary synthetic DB fixtures only. No strategy redesign or unsupported performance/real-market claims. H-007 limited repair permission does not reopen G-H003-1/2/4 or authorize broader G-H003-3. Next: reviewer checks exact PR21 diff/CI/residual contract risk; owner decides integration separately. Manual session, not scheduler invocation. Related K-20261028-001 / ENG-20261028-001 / H007-NUMERIC-REPAIR-OUTCOME. Final coordination-head baseline CI will be pinned in PR19 notice, separately from repair CI.


## H-009 — test-only consumer integration return — 2026-10-28 15:36:37 UTC
Direct human yes in coding chat authorized H009 only. [Draft PR22](https://github.com/girlbreaksface/raccoon-radar/pull/22) head ae3fda66055733bde371e1b0d7887f8157cf8c7f, based on unchanged repaired PR21 head48e184c67168724b1449ac8c36d209d4a2d72892, adds seven tests and exact PR14 replay as test fixture (blob4eeaa8c1fdb595134096fa5ac13f52f8ecf82392), no production edits. [Immutable evidence](https://github.com/girlbreaksface/raccoon-radar/blob/82cea0516c41125be53d6b31298cff44d29b7fb4/docs/handoff_evidence/H-009/results.md). Actual overflow replay/study and cooldown/JSON/input contracts PASS. Fake unknown signal admitted as event; missing key KeyError. LocalWindows3.12 and Windows3.11.9/Linux3.11.17 CI each114tests/112PASS/2deliberateFAIL, compileCI PASS. Run40717552033 checkoutf2a8454fbc96e587a03976c5507534d14b6671b7. NOT MERGE READY; preserve assertions/red artifact. Unknown fixture has missing horizon, no observed bearish numeric return claimed. H008 static findings thereby qualified with synthetic consumer evidence. No current-engine malformed enum claim. Coding agent RETURNED_FOR_REVIEW; independent reviewer unknown. Separate human approval required for any repair or integration. Protected PR13/14/20/21 unchanged, no provider/history/productionDB/trading/study execution or merge. Related ENG-20261028-002; no broader gates opened.


## H-010 — bounded replay signal repair return — 2026-10-28 16:30:31 UTC
Direct coding-chat H010 implementation approval used only for reproduced consumer defects. NEW [draft PR23](https://github.com/girlbreaksface/raccoon-radar/pull/23), head fa3f3640ea473cb3421b6153f424040470fdff29, based on unchanged H009 headae3fda66055733bde371e1b0d7887f8157cf8c7f and H007 engine48e184c67168724b1449ac8c36d209d4a2d72892. Root replay copied from pinned PR14 then six-line guard added; exact known candidate enums only, malformed signals copied into NO TRADE+INVALID_SIGNAL before events/cooldown; prior reasons retained, original snapshot unchanged. Original H009 assertions preserved with one loader-target line; two PR14 test files copied unchanged, four new matrix-test methods. Exact red commit6835841b2d5fadb7963b721d6db91ed612409359:136methods,48 failing assertions/subtests,6errors. Repair136PASS local Windows3.12.14 and Windows3.11.9/Ubuntu3.11.17 CI, compilePASS. Run40726530880, checkoute37ea1461edea833ead63babd99d7626a5c0053c, jobs122951207078/122951207430. Complete ordinary SPY/QQQ synthetic replay output equality confirmed.
[Immutable evidence package](https://github.com/girlbreaksface/raccoon-radar/tree/384b4ac6326a49c197b8a3c72c71739f72830336/docs/handoff_evidence/H-010): results.md,observations.synthetic.json,ci-evidence.json. Source/test/hash/fixture limits recorded;13malformed cases archived with JSON-safe type/repr source descriptors. Original PR22 and expected114/2FAIL preserved; no protected13/14/20/21/22 branch changes. This validates signal-field handling for otherwise existing result schema, not arbitrary malformed results or market semantics. H010 IMPLEMENTED_AND_TESTED/RETURNED_FOR_INDEPENDENT_REVIEW; no merge/retarget/deployment authority. No data/provider/productionDB/ingestion/UI/threshold/trading changes or real historical study. Next owner human maintainer identifies independent qualified reviewer and separately approves any integration; stacked evidence PR22 is not automatically mergeable because repair passes. Related ENG-20261028-003 and K-20261028-002. Manual session, not scheduler evidence.
