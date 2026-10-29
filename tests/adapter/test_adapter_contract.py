"""SPECIFICATION CHARACTERIZATION ONLY; no OpenD client or production adapter."""
import ast
import copy
from datetime import datetime,timedelta,timezone
import hashlib
from importlib import resources,metadata
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock
from zoneinfo import ZoneInfo
import pandas as pd

from contract_oracle import characterize,instant,local_instant,supported_precision,knowledge_upper_bound

FIXTURES=Path(__file__).with_name("fixtures")
HASHES={"pr29_scanner_reliability.py.txt":"bfedd03ac70a5291329a82fa98d9de52bfd8d23d62c0e74f395534c6fc359e7d",
        "pr31_successor.py.txt":"5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29",
        "v3_scanner.py.txt":"28bcd08df43b93f4f19818975d470cdc592c72a49d29fb71027d74e04d69eb0d"}


def setUpModule():
    def audit(event,args):
        if event.startswith(("socket.","subprocess.","sqlite3.")):
            raise PermissionError("Specification tests forbid network/process/SQLite operations")
        if event=="import" and args[0].split(".")[0] in ("moomoo","futu"):
            raise PermissionError("No provider SDK import authorized")
    sys.addaudithook(audit)


def pinned(name,function_only=None):
    path=FIXTURES/name; data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=HASHES[name]: raise AssertionError("Pinned source changed")
    namespace={"__file__":str(path),"__name__":"synthetic_pinned_fixture"}
    tree=ast.parse(data.decode("utf-8"))
    if function_only:
        tree=ast.Module(body=[next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function_only)],type_ignores=[])
    exec(compile(tree,str(path),"exec"),namespace)
    return namespace


def bundle(count=1):
    opening=datetime(2026,10,23,9,30,tzinfo=timezone.utc)
    rows=[]
    for i in range(count):
        t=opening+timedelta(minutes=i)
        rows.append(dict(symbol="SPY",raw_stamp=t.isoformat(),revision_id=f"SYNTHETIC-{i}",
            available_at=(t+timedelta(minutes=1,seconds=1)).isoformat(),availability_basis="SYNTHETIC_CAPTURE",
            completed=True,finality="FINAL",units="USD_SHARES",adjustment="SYNTHETIC_FIXED",
            open=100+i,high=102+i,low=99+i,close=101+i,volume=100))
    context=dict(synthetic=True,symbol="SPY",source_evidence="SYNTHETIC_SOURCE_ONLY",
        mapping="START",mapping_evidence="SYNTHETIC_MAPPING_ONLY",calendar_evidence="SYNTHETIC_CALENDAR_ONLY",
        open=opening.isoformat(),close=(opening+timedelta(hours=6)).isoformat(),
        watermark=(opening+timedelta(minutes=count)).isoformat(),
        capture_committed=True,capture_hash_valid=True,pagination_complete=True,clock_trusted=True,
        max_event_age=120,max_knowledge_age=120,max_delivery_lag=30)
    context["source_scope"]={k:"SYNTHETIC_ONLY" for k in
        ("endpoint","sdk","opend","interval","timezone","session_flags","adjustment","entitlement","units")}
    context["mapping_scope"]=copy.deepcopy(context["source_scope"])
    cutoff=(opening+timedelta(minutes=count+1)).isoformat()
    return rows,context,cutoff


class ContractExamples(unittest.TestCase):
    def test_network_and_database_guards_block_before_access(self):
        import socket,sqlite3
        with self.assertRaises(PermissionError): socket.socket()
        with self.assertRaises(PermissionError): sqlite3.connect(":memory:")
    def result(self,rows=None,context=None,cutoff=None):
        r,c,t=bundle()
        return characterize(r if rows is None else rows,c if context is None else context,
                            cutoff=t if cutoff is None else cutoff,zone=timezone.utc)

    def test_synthetic_example_is_deterministic_and_inputs_unchanged(self):
        rows,c,t=bundle(); before=copy.deepcopy((rows,c))
        first=self.result(rows,c,t)
        self.assertTrue(first["eligible"])
        self.assertEqual(first,self.result(rows,c,t))
        self.assertEqual((rows,c),before)

    def test_missing_mapping_source_calendar_and_clock_fail_closed(self):
        for key in ("mapping_evidence","source_evidence","calendar_evidence","clock_trusted"):
            rows,c,t=bundle(); c[key]=None
            self.assertFalse(self.result(rows,c,t)["eligible"])

    def test_missing_version_or_mismatched_endpoint_scope_blocks(self):
        for changes in (dict(sdk=""),dict(endpoint="DIFFERENT_SYNTHETIC_ENDPOINT")):
            rows,c,t=bundle(); c["source_scope"].update(changes)
            self.assertFalse(self.result(rows,c,t)["eligible"])

    def test_real_data_is_not_authorized_by_synthetic_contract(self):
        rows,c,t=bundle(); c["synthetic"]=False
        self.assertIn("REAL_DATA_NOT_AUTHORIZED",self.result(rows,c,t)["reasons"])

    def test_fetch_timestamp_not_historical_availability(self):
        rows,c,t=bundle(); rows[0].update(availability_basis="FETCH_TIME_ONLY")
        self.assertIn("AVAILABILITY_UNKNOWN",self.result(rows,c,t)["reasons"])

    def test_unknown_availability_blocks_instead_of_assumed_interval_end(self):
        rows,c,t=bundle(); rows[0]["available_at"]=None
        self.assertIn("AVAILABILITY_UNKNOWN",self.result(rows,c,t)["reasons"])

    def test_old_bar_new_receipt_cannot_reset_event_freshness(self):
        rows,c,t=bundle(); rows[0]["available_at"]="2026-10-23T12:00:00Z"
        result=self.result(rows,c,"2026-10-23T12:00:01Z")
        self.assertIn("STALE_MAX_EVENT_AGE",result["reasons"])
        self.assertIn("LATE_DELIVERY",result["reasons"])

    def test_future_revision_filtered_before_invalid_payload_inspection(self):
        rows,c,t=bundle(); first=self.result(rows,c,t)
        late={**rows[0],"revision_id":"SYNTHETIC-LATE","available_at":"2026-10-23T12:00:00Z",
              "close":float("inf")}
        result=self.result(rows+[late],c,t)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["frame_hash"],first["frame_hash"])
        self.assertNotEqual(result["bundle_hash"],first["bundle_hash"])
        self.assertEqual(result["excluded"],["SYNTHETIC-LATE"])

    def test_conflicting_known_revision_has_no_last_row_wins(self):
        rows,c,t=bundle(); rows.append({**rows[0],"revision_id":"SYNTHETIC-OTHER","close":100})
        result=self.result(rows,c,t)
        self.assertIn("CONFLICTING_OR_DUPLICATE_REVISION",result["reasons"])
        self.assertIsNone(result["frame"])

    def test_identical_retry_not_coalesced_without_reviewed_identity_policy(self):
        rows,c,t=bundle()
        self.assertIn("CONFLICTING_OR_DUPLICATE_REVISION",self.result(rows+copy.deepcopy(rows),c,t)["reasons"])

    def test_knowledge_age_policy_is_independent_of_event_age(self):
        rows,c,t=bundle(); c["max_knowledge_age"]=30
        result=self.result(rows,c,t)
        self.assertIn("STALE_MAX_KNOWLEDGE_AGE",result["reasons"])
        self.assertNotIn("STALE_MAX_EVENT_AGE",result["reasons"])

    def test_interior_tail_and_whole_symbol_gaps_are_not_fabricated(self):
        rows,c,t=bundle(3)
        for selected in (rows[:1]+rows[2:],rows[:2],[]):
            result=self.result(selected,c,t)
            self.assertIn("EXPECTED_GRID_GAP_OR_EXTRA",result["reasons"])
            self.assertIsNone(result["frame"])

    def test_partial_symbol_failure_does_not_certify_counterpart(self):
        rows,c,t=bundle(); spy=self.result(rows,c,t)
        c["symbol"]="QQQ"; c["pagination_complete"]=False
        qqq=self.result(rows,c,t)
        self.assertTrue(spy["eligible"])
        self.assertFalse(qqq["eligible"])

    def test_provisional_completed_bar_remains_blocked_by_pr31_profile(self):
        rows,c,t=bundle(); rows[0]["finality"]="PROVISIONAL"
        result=self.result(rows,c,t)
        self.assertIn("CONSUMER_FINALITY_BLOCKED",result["reasons"])
        self.assertTrue(rows[0]["completed"])

    def test_interval_elapsed_is_not_completion_evidence(self):
        rows,c,t=bundle(); rows[0]["completed"]=False
        self.assertIn("COMPLETION_UNVERIFIED",self.result(rows,c,t)["reasons"])

    def test_1600_and_early_close_depend_on_explicit_mapping(self):
        for end in ("2026-10-23T16:00:00Z","2026-10-23T13:00:00Z"):
            rows,c,t=bundle(); closing=instant(end)
            c.update(open=(closing-timedelta(minutes=1)).isoformat(),close=end,watermark=end)
            rows[0].update(raw_stamp=end,available_at=(closing+timedelta(seconds=1)).isoformat())
            c["mapping"]="END"
            self.assertTrue(self.result(rows,c,(closing+timedelta(minutes=1)).isoformat())["eligible"])
            c["mapping"]="START"
            self.assertIn("OUTSIDE_SESSION",self.result(rows,c,(closing+timedelta(minutes=1)).isoformat())["reasons"])
            self.assertEqual(rows[0]["raw_stamp"],end)

    def test_holiday_has_no_weekday_fallback(self):
        rows,c,t=bundle(); c["holiday"]=True
        self.assertIn("MARKET_CLOSED",self.result(rows,c,t)["reasons"])

    def test_crash_or_bad_capture_manifest_never_publishes_frame(self):
        for changes in (dict(capture_committed=False),dict(capture_hash_valid=False)):
            rows,c,t=bundle(); c.update(changes)
            self.assertIsNone(self.result(rows,c,t)["frame"])

    def test_unknown_freshness_policy_not_invented(self):
        for name in ("max_event_age","max_knowledge_age","max_delivery_lag"):
            rows,c,t=bundle(); del c[name]
            self.assertIn("FRESHNESS_POLICY_UNREVIEWED",self.result(rows,c,t)["reasons"])

    def test_unit_adjustment_and_bad_ohlcv_block(self):
        for changes in (dict(units="UNKNOWN"),dict(adjustment="UNKNOWN"),dict(low=999),dict(volume=float("nan"))):
            rows,c,t=bundle(); rows[0].update(changes)
            self.assertFalse(self.result(rows,c,t)["eligible"])


class TimeCharacterization(unittest.TestCase):
    def test_clock_uncertainty_and_completion_metadata_delay_not_backdated(self):
        end=instant("2026-10-23T10:00:00Z")
        received=end+timedelta(milliseconds=100)
        metadata_time=end+timedelta(milliseconds=800)
        upper=knowledge_upper_bound(received,metadata_time,end,500)
        self.assertEqual(upper,end+timedelta(milliseconds=1300))
        with self.assertRaises(ValueError): knowledge_upper_bound(received,metadata_time,end,None)

    def zone(self):
        self.assertEqual(metadata.version("tzdata"),"2026.5")
        with resources.files("tzdata").joinpath("zoneinfo/America/New_York").open("rb") as f:
            return ZoneInfo.from_file(f,key="America/New_York")

    def test_bundled_dst_offsets_not_exchange_calendar_verification(self):
        zone=self.zone()
        self.assertEqual(local_instant("2026-03-06 09:30:00",zone).hour,14)
        self.assertEqual(local_instant("2026-03-09 09:30:00",zone).hour,13)
        self.assertEqual(local_instant("2026-10-30 09:30:00",zone).hour,13)
        self.assertEqual(local_instant("2026-11-02 09:30:00",zone).hour,14)

    def test_ambiguous_and_nonexistent_naive_local_times_block(self):
        zone=self.zone()
        for value in ("2026-03-08 02:30:00","2026-11-01 01:30:00"):
            with self.assertRaises(ValueError): local_instant(value,zone)

    def test_fractional_availability_rounds_up_cutoff_down(self):
        available=instant("2026-10-23T10:00:00.100001Z")
        cutoff=instant("2026-10-23T10:00:00.999999Z")
        up,down=supported_precision(available,cutoff)
        self.assertGreater(up,down)
        self.assertGreaterEqual(up,available)
        self.assertLessEqual(down,cutoff)


class PinnedCompatibility(unittest.TestCase):
    def test_pr29_legacy_csv_remains_unverified(self):
        evaluate=pinned("pr29_scanner_reliability.py.txt")["evaluate_signals"]
        result=evaluate([dict(symbol="US.SPY",bias="BULLISH",bar_time_et="2026-10-23 10:00:00")],
                        now=instant("2026-10-23T10:01:00Z"))
        self.assertFalse(result["SPY"]["eligible"])
        self.assertEqual(result["SPY"]["display"],"UNVERIFIED")

    def test_pr29_recent_availability_does_not_refresh_old_event(self):
        evaluate=pinned("pr29_scanner_reliability.py.txt")["evaluate_signals"]
        row=dict(symbol="SPY",bias="BULLISH",source_sha256="a"*64,event_at="2026-10-23T09:30:00Z",available_at="2026-10-23T12:00:00Z")
        result=evaluate([row],now=instant("2026-10-23T12:00:01Z"),max_age_seconds=120,
                        evidence=dict(source_sha256="a"*64,authority="SYNTHETIC ONLY",availability_verified=True))
        self.assertIn("STALE_EVENT",result["SPY"]["reasons"])

    def test_pr30_v3_still_ignores_pagination_and_retains_stale_bias(self):
        namespace=pinned("v3_scanner.py.txt",function_only="analyze")
        namespace.update(pd=pd,RET_OK=0)
        # clock_time is the datetime.time CLASS in the original module.
        from datetime import time
        namespace.update(clock_time=time,ENTRY_START=time(9,40),ENTRY_END=time(11,30),KLType=types.SimpleNamespace(K_1M="SYNTHETIC"))
        rows,_,_=bundle(35)
        table=pd.DataFrame([{**{k:r[k] for k in ("open","high","low","close","volume")},
                             "time_key":r["raw_stamp"][:19].replace("T"," ")} for r in rows])
        q=Mock(); q.request_history_kline.return_value=(0,table,"IGNORED_CURSOR")
        result=namespace["analyze"](q,"US.SPY",instant("2026-10-23T12:00:00Z"))
        self.assertEqual(q.request_history_kline.call_count,1)
        self.assertFalse(result["fresh"])
        self.assertEqual(result["bias"],"BULLISH")
        self.assertEqual(result["action"],"WAIT")
        self.assertNotIn("moomoo",sys.modules)

    def test_pr31_accepts_unique_synthetic_frame_but_not_legacy_or_unknown_contract(self):
        assess=pinned("pr31_successor.py.txt")["assess"]
        rows,c,t=bundle(35)
        report=characterize(rows,c,cutoff=t,zone=timezone.utc)
        self.assertTrue(report["eligible"])
        raw=[dict(symbol="SPY",time=r["raw_stamp"],source_sha256="a"*64,
                  **{k:r[k] for k in ("open","high","low","close","volume")}) for r in rows]
        contract={name:"SYNTHETIC ONLY" for name in ("source_authority","mapping_authority","calendar_authority",
                   "availability_authority","completion_authority","finality_authority")}
        contract.update(source_sha256="a"*64,exchange_timezone="UTC",intervals=[dict(
            raw_stamp=r["raw_stamp"],start=r["start"],end=r["end"],available_at=r["available_at"],
            completed=True,finality="FINAL") for r in report["frame"]])
        result=assess("SPY",raw,now=instant(t),session="2026-10-23",contract=contract,
                      policy=dict(max_age_seconds=120),pagination_complete=True,synthetic=True)
        self.assertTrue(result["eligible"])
        blocked=assess("SPY",raw,now=instant(t),session="2026-10-23",contract={},
                       policy=None,pagination_complete=True,synthetic=True)
        self.assertFalse(blocked["eligible"])

    def test_pr29_and_pr31_pagination_error_contracts_not_silently_interchanged(self):
        for name,func,flag in (("pr29_scanner_reliability.py.txt","collect_pages","pagination_complete"),
                               ("pr31_successor.py.txt","collect_pages","complete")):
            collect=pinned(name)[func]
            for pages in ([(0,[{}],"x"),(1,"SYNTHETIC ERROR",None)],
                          [(0,[{}],"x"),(0,[],"x")]):
                result=collect(Mock(side_effect=pages),"SPY",{})
                self.assertFalse(result[flag])
                self.assertTrue(result["reasons"])


if __name__=="__main__": unittest.main()
