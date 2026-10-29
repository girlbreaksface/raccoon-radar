# H-014 verification return — 2026-10-29T04:45:16Z

Scope: human-approved isolated synthetic-only visual journal development/testing.
[Draft PR27](https://github.com/girlbreaksface/raccoon-radar/pull/27) is stacked on
PR26 a374038bc10298e2aa14b238153c7674322a66d4, not an authorized merge.
PR24 calculator 092d7addbbbc56f369c1c53226ed6b82fa3e6dc4 remains separate.

## Exact test identities

Test-first commit197f029d10e4c56d1a477e61c460e98ef36fa930,
controller-test blob2a91cb917991baaa4ed80ebcbefbe8b883177650.
Local initial focused discovery fails with one import error:
ModuleNotFoundError: No module named ledger_ui_controller. This demonstrates
the missing implementation, not 17 independent observed failures.
After implementation: all17 controller/worker tests pass; unchanged39 journal tests pass.

[CI40819414632](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40819414632)
tests head955cdb6700b86caa16cf49b50eeddf5252d9b579 at actual synthetic merge checkout
a3f21127cd0a190925f77687eb795973d20701cb into unchanged PR26 base.
Both job logs and completed statuses were read:
- [Windows3.11.9 job123268107633](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40819414632/job/123268107633):69baseline PASS,56journal/controller PASS,compile PASS,Tk smoke PASS.
- [Ubuntu3.11.17 job123268107846](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40819414632/job/123268107846):same; Tk uses Xvfb.
OS-inapplicable smoke steps are conditionally skipped; no test assertions are skipped or weakened.
Total125 methods per OS across two suites plus a separate window smoke, not cumulative
direction/replay/calculator validation.

Local Windows3.12.14: same69+56 PASS, compilation PASS, own-window smoke PASS.
Smoke invokes actual widgets for startup/no store, queued entry, partial exit, correction,
historical view/write disabling, pinned export, backup, visible invalid-input error and close.
Synthetic partial exit: remaining2, realized19.99000000 before correction; screenshot
after correction shows9.99000000. These are fictional accounting observations, not market returns.
No provider, real history, real records, production DB or historical study used.

## Preservation and reconciliation

Unchanged backend blobs:
- manual_ledger.py:cfdefdc7100f78bbe5cea582a4bd86844dfb66c5
- manual_ledger_cli.py:5eca01c3cfe10ca2d9f61d8f5cadca74ed15b72e
- tests/ledger/test_manual_ledger.py:40a5d8ee5cb2a05841c8ef54d00d108a7c0882c0

Local copied bytes match these Git blobs. Compare to PR26 shows only new controller,
standalone window, tests, docs and nine additional CI lines; no backend/calculator/dashboard
changes. PR13/14/19/20/21/22/23/24/25/26 heads all read unchanged and unmerged.
PR19 head16bd05f5d694d7d2d472ff3d9ddf218ba32c0cad;
handoff blob09e826b23f7fde82d16bab7c4a102ed91b2b4503;
knowledge index blob6427019f678a58b67a63b3994df6009539904fb4.
Shared branch is protected from edits; return is a new-branch record and PR19 comment.

## Screenshot and review limits

Own-window screenshot generated locally, visually inspected; first DPI-misaligned/clipped
attempt was replaced by a correctly bounded screenshot after explicit Windows DPI awareness
in the smoke capture. Final PNG SHA256:
ea621e9076ce1673e626e653dd814217aa6793ff9ed32bcfc7c56e9e4a2161a2.
Local artifact: .sprint/h014-ledger-ui/ui-synthetic.png (not uploaded to GitHub).
The screenshot shows plaintext/synthetic warnings, partially closed fictional position,
exact repository P&L and visible rejected fractional-quantity error. It is not user acceptance.

Internal review is non-independent. Plaintext/ACL/path swapping/exclusive recovery limits,
in-memory-only pending intent on hard crash, large-display/DPI/accessibility/native-dialog
coverage, CLI-only restore/dependent batch corrections remain.
Recovery ownership is asserted, not proven; raw capture is not a verified backup.
No real-use, existing-app integration, independent sign-off, deployment or merge approval.
See [workflow and limitations](../../LEDGER_UI_H014.md).

## Final code follow-up — 2026-10-29T04:47Z

Windows visual inspection established a scaling mismatch between the initial launcher
and DPI-aware smoke capture. Commits3a0a29f2d4abf1b70145817838c730ff9a684325 and
bdbe7aee2e8a5e1b14ee85c2f4ee85ecd37cbaa7 make both call the same prepare_display
before Tk construction; no accounting/storage changes. The earlier successful run
remains original evidence, not silently relabeled as this revision.

[CI40819628047](https://github.com/girlbreaksface/raccoon-radar/actions/runs/40819628047)
tests code headbdbe7aee2e8a5e1b14ee85c2f4ee85ecd37cbaa7 at
ddab940da4faa9847f0bea4327721a5d6f835534 against unchanged PR26 base.
Windows job123268795870 and Ubuntu job123268796090 both completed SUCCESS:
69baseline +56journal/controller PASS, compile PASS, actual Tk smoke PASS.
Logs and statuses read. Local Windows same56 PASS, compile and Tk smoke PASS after
this change; unchanged baseline previously69 PASS. No extra baseline rerun was needed
for the isolated display-bootstrap change. Screenshot above retains its original
hash and capture identity; new smoke uses equivalent display setup.

Latest source blobs: manual_ledger_ui.py a19df33954631f133b9ef6ebd62de3cec2191793;
tests/ledger_gui_smoke.py 44d164c617a578210076dec9e54222dc54b34da2.
Final evidence-only commit is tested separately and returned in the PR19 completion comment.
