# H-003 / A-006 — pin, diff and CI verification
Recorded-at UTC: 2026-10-27 13:15:21 UTC. Owner: coding agent. Status: RETURNED_FOR_REVIEW; independent approval absent.
Read baseline handoff branch commit f4930346019bfcb1ca2a633b8c09c5bcad8facbe, blob 0e6d3819a8c237caf535edc22849f670ba3a2e69. Acknowledgement commit 38532d6c38b3d47f759b491969209b32b6c2d3a1. Scope is documentation/read-only GitHub verification; no study or local test rerun in this work order.

## Observed pin matrix
| Artifact | Head / main SHA | GitHub reported base SHA / ref | Actual tested checkout |
|---|---|---|---|
| main | b0ad02dc996b00406e7da08fb33b6382f658ea40 | NOT_APPLICABLE | b0ad02dc996b00406e7da08fb33b6382f658ea40 |
| [#13](https://github.com/girlbreaksface/raccoon-radar/pull/13) | 6e7d1a8804b14aba9d08302bc5db48f31b0706ae | b0ad02dc996b00406e7da08fb33b6382f658ea40 / main | d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4 |
| [#14](https://github.com/girlbreaksface/raccoon-radar/pull/14) | 328135f2695543cde96bb434aaa07201c51c0582 | 286eb9b1e7071ebbc83a125dc1062e4723efcad1 / research/deterministic-direction-engine | a9f01f8c0b43697f9102e1424809645315b4fc64 |
| [#17](https://github.com/girlbreaksface/raccoon-radar/pull/17) | 9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3 | b0ad02dc996b00406e7da08fb33b6382f658ea40 / main | f406e7c8b8ab0da80d1fb3f663ad4ae3b6377d30 |
| [#18](https://github.com/girlbreaksface/raccoon-radar/pull/18) | eb683559a0ab685503627612ab22aa16a77066ed | b0ad02dc996b00406e7da08fb33b6382f658ea40 / main | 0b4535418ef8f36e2398d0836e59f6b93bb1cc39 |

VERIFIED: API refs and current PR heads match H-003 pins. All four PRs are open/unmerged with empty submitted-review lists and requested-reviewer arrays. No independent reviewer identified; no identity assigned. No readiness/approval is transferred to a changed head.

## CI evidence independently inspected in this work order
Each row below: job status completed/success; compilation and guarded offline steps succeeded. Test totals are now observed from job logs, superseding their earlier attributed-only status for THESE jobs only.
| Run / artifact | Windows job / Python / tests | Ubuntu job / Python / tests |
|---|---|---|
| [40496261547](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40496261547) / main | [122162355888](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40496261547/job/122162355888) / 3.11.9 / 69 | [122162356093](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40496261547/job/122162356093) / 3.11.17 / 69 |
| [40504942948](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948) / #13 | [122191738058](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948/job/122191738058) / 3.11.9 / 97 | [122191737325](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948/job/122191737325) / 3.11.17 / 97 |
| [40504949071](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071) / #14 | [122191756215](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071/job/122191756215) / 3.11.9 / 115 | [122191756711](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071/job/122191756711) / 3.11.17 / 115 |
| [40504257980](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980) / #17 | [122189410997](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980/job/122189410997) / 3.11.9 / 69 | [122189411592](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980/job/122189411592) / 3.11.17 / 69 |
| [40507854048](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40507854048) / #18 | [122201680355](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40507854048/job/122201680355) / 3.11.9 / 69 | [122201680855](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40507854048/job/122201680855) / 3.11.17 / 69 |

Commands evidenced in CI: `python -m compileall -q .`; `python -B offline_checks.py`. These were executed by the recorded hosted jobs, NOT newly executed locally for H-003. Python patch versions differ (Windows 3.11.9, Ubuntu 3.11.17). SQLite versions: Windows 3.45.1, Ubuntu 3.46.1. Broad cross-platform behavior remains limited to these suites/runners.

[ci-observations.json](ci-observations.json) retains exact run/job IDs, repository head/base, checkout identities, source SHA256s reported by each platform and log excerpts. GitHub logs remain primary evidence and can expire; the selected immutable extracts are not a full log archive. No secret/private dataset material copied.

## Resolving #14 base ambiguity
Both checkout logs explicitly state: Merge 328135f2695543cde96bb434aaa07201c51c0582 into 6e7d1a8804b14aba9d08302bc5db48f31b0706ae. Fetched commit a9f01f8c0b43697f9102e1424809645315b4fc64 has those two parents, with tree 6043eaf49a9c7b0e22ace612f851ad0f25f5a8b4. Thus 115 tests cover the combined current engine/replay view. The PR API still reports earlier base SHA 286eb9b1e7071ebbc83a125dc1062e4723efcad1. This is a metadata discrepancy, not proof the old base was tested. Use the actual checkout and parent evidence; do not change branch ancestry under this order.

Other verified synthetic merge parents:
- d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4: main + #13.
- f406e7c8b8ab0da80d1fb3f663ad4ae3b6377d30: main + #17.
- 0b4535418ef8f36e2398d0836e59f6b93bb1cc39: main + current #18.
These synthetic CI commits are not merges into main.

## Diff scope and versioned source evidence
Fetched complete PR changed-file lists, patches and compare metadata. Comparisons are merge-base PR diffs, not assertions that #14 contains latest #13 on its branch.
- #13: `direction_engine.py`, `docs/DIRECTION_ENGINE.md`, `docs/DIRECTION_ENGINE_REVIEW.md`, `test_direction_engine.py`, `test_direction_math_review.py`.
- #14: `direction_validation.py`, `docs/DIRECTION_VALIDATION.md`, `docs/DIRECTION_VALIDATION_REVIEW.md`, `test_direction_availability_review.py`, `test_direction_validation.py`.
- #17: `docs/CANONICAL_COMPLETED_CANDLE_ADAPTER_DESIGN.md`, `docs/examples/canonical_adapter_blocked.proposed.json`.
- #18: `docs/DIRECTION_INTEGRATION_STUDY_PROTOCOL.md`.
No existing ingestion, dashboard, persistence or trading files appear in these diffs. #13 is ahead of current main; #14 diverges at 286eb9b1e7071ebbc83a125dc1062e4723efcad1. #17/#18 are documentation proposals, not implemented contracts.
Source Git blobs:
- engine: 09497b013d65aebaa9f77f47212079f35445b74b at #13 head.
- replay: 4eeaa8c1fdb595134096fa5ac13f52f8ecf82392 at #14 head.
- #17 design: 876b29be4aecb6fba95e3fa2fa395aab8a35a4fb.
- #18 protocol: e4f381a8fa8d8ed968e01bd501b7a95b763df38a.
- workflow: b3f906c82d8df4a7498819f402d744c7b5961bed on pinned main.
Git blob IDs identify repository bytes; platform checkout source SHA256s are preserved separately and are not interchangeable with Git SHA1 or with each other.

## Source and tool observations
Read-only operations: GitHub PR/commit/tree/file/review/job/log GETs and comparison reads; no GUI/provider/store inspection. Source-level review confirms engine math is outside GUI/persistence and replay separates as-of snapshots from labels; original regression evidence remains synthetic. No new general proof of leakage absence or mathematical completeness is claimed.

One attempted documentation lookup used docs/INGESTION_CHARACTERIZATION.md, which is absent; corrected via tree inventory to docs/CANDLE_INGESTION_CHARACTERIZATION.md. No file was created at the mistaken path. Earlier claimed latest-file commit fb545f12769a6d9b3af25878fe08ac388a0ea3f5 was an ancestor; fresh branch/PR/commit observations agreed on f4930346019bfcb1ca2a633b8c09c5bcad8facbe before H-003 writes.

## Still-blocked gates and next action
Independent maintainer review/qualification/access UNKNOWN; no merge authorization. Keep #13 unmerged and #14 stacked. Only after independently reviewed #13 receives explicit merge authorization may integration occur, followed by new main CI; retargeting #14 requires a new diff/check/test review and separate approval. #17/#18 approval, source eligibility, actual freeze dates and study execution remain separate. Owner A-010 coordination reviewer: reconcile returned evidence; A-011 human maintainer: establish reviewer and decide contracts. This package alone closes no human gate.
