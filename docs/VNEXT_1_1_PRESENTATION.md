# Raccoon Radar vNext 1.1 — presentation-only preview

This separate workstation presents PR #37's immutable, precomputed synthetic replay.
Parent: `cee98fb094842921a5a0fcd8764cfaf1c444b803` on `feat/synthetic-replay-viewer`.
The new draft PR targets that branch. It does not retarget or change PR #37.

## Launch on Windows

Use a separate checkout of this draft branch; do not copy it over an installed dashboard.
With Python 3.11 or newer including Tk installed, open a terminal in the checkout:

```powershell
py -3.11 -B raccoon_radar_vnext_1_1.py --scenario conflict --minute 35
```

If using another Python version with Tk, use `python -B` instead of `py -3.11 -B`.
No packages, provider SDK, OpenD, credentials, input files, or market connection are needed.
The original `raccoon_replay_viewer.py` entry point remains available unchanged.

## Controls and interpretation

- Choose one of seven fictional scenarios. Previous/Next, Left/Right arrows, and the
  slider select a precomputed minute. Buttons disable at the first/last step.
- SPY and QQQ have equal prominent cards. Green BULLISH, red BEARISH, amber
  blocked/no-candidate states also have explicit text labels.
- Pair status is the original engine value. CONFLICT explicitly says that the symbols
  disagree and no combined direction is inferred.
- Technical details, Diagnostics, and Evidence each open on demand. Selecting the open
  section again collapses it. Evidence includes original full-precision visible consumer
  values and input/run/decision identities. Post-cutoff raw observations are not displayed.
- Use the vertical page scrollbar when the desktop is too small to show every panel.
- Cards round labels to two decimals for magnitudes >= 10 and four below 10. The
  immutable replay result and detailed evidence keep original precision. Unavailable
  values remain UNAVAILABLE; they are never rendered as zero.

SYNTHETIC ONLY, FINAL-only, NO ORDERS, all actions WAIT, and the PR31 first-close
EMA seed / 35-bar profile remain visible. HLC3 is a candle-weighted proxy, not trade-level
VWAP. This is not PR18 study validation, provider verification, or evidence of an edge.

## Offline verification

```powershell
python -B offline_checks.py
python -m compileall -q .
python -B vnext_gui_smoke.py
```

The guarded runner discovers the existing 156 tests plus two presentation tests. It
blocks network and restricts SQLite tests to temporary synthetic stores. The Tk smoke
runner is explicit and separate: it checks seven scenarios, conflict/provisional states,
full-precision evidence, collapsible panels, disabled text, slider/buttons, bounds,
resizing, callback errors, and result immutability. It needs a Windows desktop with Tk.
The new CI workflow runs guarded checks and compilation on Windows/Linux Python 3.11,
plus Tk widget smoke on Windows. Linux GUI rendering is not claimed.

## Scope and rollback

Only new presentation code, presentation tests, a dedicated CI workflow, and this
guide are added. No existing source, fixture, test, workflow, source pin, calculation,
data semantics, scenario result, finality rule, original dashboard, research store, or
production path changes. All scenarios are calculated before Tk widgets exist;
callbacks select immutable results and render only. Close this preview to stop it;
launch the original entry point to return to the prior viewer. Nothing is merged,
deployed, or connected to a real provider.
