# Decision log — November 5, 2026

Reviewed the finished VWAP/EMA and multi-milestone chats before continuing.
GitHub open-stack inspection confirms #72 → #73 → #74 → #75 → #76 remain
draft, with unchanged heads de684940, 60f3dc64, 5a24864c, aacc102d and 4dcd1a6e.
All 22 checks on #72/#73 and all 26 checks on #74/#75/#76 currently succeed.
Four foundation artifacts per #73–#76 remain available; metadata is not a
substitute for downloading and verifying the archive contents.

## Reproduced gap and decision

`foundation_check` previously skipped a log or artifact whenever its reference
was absent. A report with current source hashes and ten PASS/zero-exit rows,
but no evidence files at all, was accepted. A regression failed before the fix.

Require every suite's canonical log filename and hash and every artifact-producing
suite's canonical JSON filename and hash. Share the artifact-suite inventory
with the producer. Keep existing byte-hash and directory containment checks.
Tests exercise every missing reference/hash, wrong filenames, changed bytes,
missing files and a complete synthetic integrity fixture. This establishes
completeness and integrity only, not independent execution or authenticity.

No provider or broker calls are needed for this repair. Earlier actual read-only
observations remain historical observations: two terminal orders without a local
baseline, no positions, unavailable paper historical fills. They do not establish
complete fill/fee lineage. No new history or baseline is inferred.

## Remaining gates

Provider finality/mapping/corrections and original availability remain unverified.
Risk production integration, external receipt custody, overnight baseline and
hardware durability remain unqualified. Historical quote rights and actual data
are absent; proposed chronological dates are not verified untouched holdout.
No empirical edge is claimed. Existing research variants and PR branches are
preserved; close this added draft to roll back this isolated repair.

Paper HOLD; recording HOLD; live NO-GO; orders DISABLED;
merge/deployment HOLD. No orders, account mutations, risk increases or purchases.
