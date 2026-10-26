RACCOON RADAR v1.4.1 LAYOUT PATCH

Fix: Swing Desk table now has bounded height so case editor and Save case controls remain visible.
Added: Save selected as research case button on Volume Discovery tab.
Preserved: all original modules, SQLite schema, and read-only/no-orders behavior.

INSTALL: Close app. BACK UP entire existing Raccoon Cave App folder first. Extract this ZIP to a NEW folder alongside your existing v1.4 installation. Copy your existing raccoon_history.sqlite3, raccoon_swing.sqlite3, raccoon_discovery.sqlite3 (and any other project databases) from your existing App folder into the new extracted folder; do not replace your original database files. Start using: py raccoon_dashboard_v1_2.py

NOTE: This patch was syntax-checked, not GUI-tested on Windows. The source filename remains raccoon_dashboard_v1_2.py for compatibility.
