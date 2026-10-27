# H-005 engineering readiness and risk review — documentation only
Recorded-at UTC: 2026-10-27 16:27:54 UTC; coding agent. Direct human authorization: “Yes of course” in the current coding chat after explicit request to begin [H-005](https://github.com/girlbreaksface/raccoon-radar/pull/19#issuecomment-6447454582). Status RETURNED_FOR_REVIEW, not acceptance or implementation permission.
Read starting PR #19 head f723f24be8353e7be1d77aaa0da4ab0b95ae65f5; handoff blob f99f68f93cfe99c7cec8a479d4bda1ea24cf8328; knowledge index 109e2c4434fbce15a3a4f8908f6e78fb755f9856 and linked records. Re-fetch latest blobs before writes. This is a manual session, not proof of a scheduled run.

## Deliverables
1. [Dependency and blocker map](dependency-blocker-map.md).
2. [Independent #13 reviewer packet](pr13-reviewer-packet.md).
3. [Read-only test coverage audit](test-coverage-gaps.md).
4. [Design-only paper readiness checklist](paper-readiness-design.md).
5. [Proposed implementation roadmap and next-step alternatives](implementation-roadmap.md).

Nothing here implements/tests code, opens stores, acquires market data, calls a provider/broker, executes replay/studies/simulated trades, retargets or merges. Future live-alert observation, paper execution and live trading are DISTINCT milestones with separate permissions; none is ready/authorized. No source or empirical edge established.

## Pin and CI provenance observed in H-005
| Artifact | Head/main SHA | Actual previous CI checkout | Run / per-platform count |
|---|---|---|---|
| main | b0ad02dc996b00406e7da08fb33b6382f658ea40 | b0ad02dc996b00406e7da08fb33b6382f658ea40 | 40496261547 / 69 |
| #13 | 6e7d1a8804b14aba9d08302bc5db48f31b0706ae | d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4 | 40504942948 / 97 |
| #14 | 328135f2695543cde96bb434aaa07201c51c0582 | a9f01f8c0b43697f9102e1424809645315b4fc64 | 40504949071 / 115 combined |
| #17 | 9224b7d7b0db02b56ce0f517c0ce5a4968c77fa3 | f406e7c8b8ab0da80d1fb3f663ad4ae3b6377d30 | 40504257980 / 69 baseline |
| #18 | eb683559a0ab685503627612ab22aa16a77066ed | 0b4535418ef8f36e2398d0836e59f6b93bb1cc39 | 40507854048 / 69 baseline |
| #19 starting head | f723f24be8353e7be1d77aaa0da4ab0b95ae65f5 | f9c0d05976c3c76737c28662a4d6817f2a984eed | 40516659710 / 69 baseline |

All six recorded runs' Windows/Ubuntu jobs were re-read completed/success; checkout, Python version and count re-extracted from job logs during H-005. Windows Python 3.11.9, Ubuntu 3.11.17; compilation plus guarded offline runner. No local test or study rerun. These are HISTORICAL CI executions re-inspected, not new execution evidence for unimplemented designs or the eventual H-005 head.
- [run 40496261547, validate (windows-latest), job 122162355888](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40496261547/job/122162355888): checkout b0ad02dc996b00406e7da08fb33b6382f658ea40, Python 3.11.9, 69 tests, success.
- [run 40496261547, validate (ubuntu-latest), job 122162356093](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40496261547/job/122162356093): checkout b0ad02dc996b00406e7da08fb33b6382f658ea40, Python 3.11.17, 69 tests, success.
- [run 40504942948, validate (ubuntu-latest), job 122191737325](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948/job/122191737325): checkout d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4, Python 3.11.17, 97 tests, success.
- [run 40504942948, validate (windows-latest), job 122191738058](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504942948/job/122191738058): checkout d1be5dcf7193bfacaa4bb6a53b72c8a1a3b82fd4, Python 3.11.9, 97 tests, success.
- [run 40504949071, validate (windows-latest), job 122191756215](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071/job/122191756215): checkout a9f01f8c0b43697f9102e1424809645315b4fc64, Python 3.11.9, 115 tests, success.
- [run 40504949071, validate (ubuntu-latest), job 122191756711](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504949071/job/122191756711): checkout a9f01f8c0b43697f9102e1424809645315b4fc64, Python 3.11.17, 115 tests, success.
- [run 40504257980, validate (windows-latest), job 122189410997](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980/job/122189410997): checkout f406e7c8b8ab0da80d1fb3f663ad4ae3b6377d30, Python 3.11.9, 69 tests, success.
- [run 40504257980, validate (ubuntu-latest), job 122189411592](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40504257980/job/122189411592): checkout f406e7c8b8ab0da80d1fb3f663ad4ae3b6377d30, Python 3.11.17, 69 tests, success.
- [run 40507854048, validate (windows-latest), job 122201680355](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40507854048/job/122201680355): checkout 0b4535418ef8f36e2398d0836e59f6b93bb1cc39, Python 3.11.9, 69 tests, success.
- [run 40507854048, validate (ubuntu-latest), job 122201680855](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40507854048/job/122201680855): checkout 0b4535418ef8f36e2398d0836e59f6b93bb1cc39, Python 3.11.17, 69 tests, success.
- [run 40516659710, validate (windows-latest), job 122232155030](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40516659710/job/122232155030): checkout f9c0d05976c3c76737c28662a4d6817f2a984eed, Python 3.11.9, 69 tests, success.
- [run 40516659710, validate (ubuntu-latest), job 122232155484](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40516659710/job/122232155484): checkout f9c0d05976c3c76737c28662a4d6817f2a984eed, Python 3.11.17, 69 tests, success.

#14 remains stacked against research/deterministic-direction-engine. PR metadata reports earlier base 286eb9b1e7071ebbc83a125dc1062e4723efcad1; actual tested merge logs combine pinned current #13 + #14. No head drift observed at intake. #13 submitted-review list empty. Reviewer identity/access/qualification UNKNOWN. New final documentation CI must be separately checked/pinned in PR #19; don't transfer earlier success.

## Inspected source identities and limits
- `direction_engine.py`: Git blob 09497b013d65aebaa9f77f47212079f35445b74b.
- `test_direction_engine.py`: Git blob 969d7c006ac22607d6c5fcb5d01e0bd7a3177795.
- `test_direction_math_review.py`: Git blob 799cf49b028da41660ebfece164b58e81c02a073.
- `direction_validation.py`: Git blob 4eeaa8c1fdb595134096fa5ac13f52f8ecf82392.
- `test_direction_validation.py`: Git blob 25a5904d8092cbf3525023909b7379274e3088ef.
- `test_direction_availability_review.py`: Git blob b9f13f2eb90a637fbb21fdd9abc1634c3e6e57b7.
- `test_candle_quality.py`: Git blob 246a20927cc49e7f3f9a5768be266aa8cf6ff3d5.
- `test_candle_ingestion_characterization.py`: Git blob 4a7f3139d7ae8324d6348fc866737befd803c484.
- `.github/workflows/python-validation.yml`: Git blob b3f906c82d8df4a7498819f402d744c7b5961bed.
Engine/test source pinned to #13; replay/test source pinned to #14; candle-quality/ingestion tests and workflow pinned to main. Source was read, not imported or executed. Test names/assertions establish inspected contract coverage; green jobs indicate those suites ran at specific checkouts, not full mathematical/market correctness.
#17/#18/C1/H-004 are design/derivation evidence, not implemented capabilities. Older AGENTS/assessment historical paragraphs still mention obsolete test counts/merge status; current pins above supersede those historical statuses without weakening contributor boundaries. No production/private research archive inspected.
