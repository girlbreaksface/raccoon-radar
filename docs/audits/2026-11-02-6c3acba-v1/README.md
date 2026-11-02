# Frozen audit archive v1

Preserved November 2, 2026 for [draft PR #48](https://github.com/girlbreaksface/raccoon-radar/pull/48), audited head `6c3acba2f22d582cbe9102d9e9aea3f12b31b62d`, tree `d001d9a189a2c359663ceb614cbd71dde87be471`.

The 13 original audit artifacts are exact byte copies from the preceding audit chat's local outputs. They include the requested readiness report, frozen manifest, reproduction script and original checksum file, plus all 12 files named by that checksum file. No original content, line endings or historical statements were updated. PROVENANCE.json records source paths and the independent archival verification. The original report predates the documentation comment now present on [issue #46](https://github.com/girlbreaksface/raccoon-radar/issues/46#issuecomment-6584081282); preserve that historical wording rather than silently correcting it.

ARCHIVE-SHA256SUMS.txt covers every payload file, including the original SHA256SUMS.txt. It excludes itself to avoid a self-hash cycle. Verify after download using PowerShell from this folder:

```powershell
$ErrorActionPreference = 'Stop'
foreach ($line in Get-Content -LiteralPath ./ARCHIVE-SHA256SUMS.txt) {
    $expected, $name = $line -split '  ', 2
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $PWD $name)).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum mismatch: $name" }
}
'PASS: archive checksums'
```

The documentation PR stores these files without text conversion using a directory-local .gitattributes. Treat v1 as append-only evidence: any later correction belongs in a new archive version, with provenance linking to this one. Hashes establish byte consistency, not provider authenticity or finality. The original SHA256SUMS.txt itself is covered by the outer checksum list.

## Offline reproduction

Use a new, clean checkout detached at the full audited SHA, never this documentation branch. Fetching Git/dependencies needs ordinary network access; the test commands must not connect to OpenD. Do not launch the dashboard, live runner or reference regressions requiring private evidence.

```powershell
git clone https://github.com/girlbreaksface/raccoon-radar.git radar-reproduction
git -C radar-reproduction checkout --detach 6c3acba2f22d582cbe9102d9e9aea3f12b31b62d
py -3.12 -m venv audit-env
./audit-env/Scripts/python.exe -m pip install tzdata==2025.2
./audit-env/Scripts/python.exe -c "import sys, importlib.util, importlib.metadata; assert sys.version_info[:2] == (3,12); assert importlib.metadata.version('tzdata') == '2025.2'; assert importlib.util.find_spec('moomoo') is None; assert importlib.util.find_spec('google.protobuf') is None if importlib.util.find_spec('google') else True"
./reproduce.ps1 -Checkout ./radar-reproduction -Python (Resolve-Path ./audit-env/Scripts/python.exe).Path
```

Original local environment: Windows, Python 3.12.10, tzdata 2025.2; no moomoo/protobuf. The archived script checks moomoo absence and timezone availability but does not itself enforce the tzdata version or protobuf absence; the explicit preflight above supplies those checks. For the audit's exact command flags use the command table in readiness-audit.md: `-I -B` for the three suites, only `-B` for verify_evidence.py. The preserved script uses `-B` for all four entry points. The isolated-mode verify_evidence attempt failed due to its local import, as recorded in the original logs.

Expected historical results: 85 feed executions (76 distinct methods), 158 broader executions, 54 reconciliation executions and 88 exact synthetic variants. These are archived results, not new executions during preservation. The cumulative whitespace check has a recorded cosmetic EOF finding. Existing CI's moving dependencies/runners are not a bit-for-bit environment lock.

## Provider gate

PROVIDER-INQUIRY.md is an unsent support draft scoped to moomoo SDK/OpenD 10.11.7108. Its documentation references currently identify v10.12, so they must not be treated as a 10.11.7108 contract. No provider response is archived here. Retain a future response with date, case ID, responder, endpoint/version scope, exact answers and unresolved items in a new evidence version; review each claim before changing eligibility.

Status remains **PROVISIONAL / UNKNOWN / DATA_BLOCKED**, completeness **NOT_ESTABLISHED**. Offline synthetic research GO; merge HOLD; production integration and trading NO-GO. No live OpenD, trade, merge, deployment or provider email was performed by this archival task.
