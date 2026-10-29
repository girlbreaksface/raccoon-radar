"""Synthetic-only immutable canonicalizer regression contracts; no capture or providers."""
from dataclasses import FrozenInstanceError,replace
from datetime import datetime,timedelta,timezone
import copy
import base64
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch


def example(count=35):
    from canonical_candles import (Source,Mapping,Calendar,Clock,Policy,TimeRules,Authority,
        Context,Request,Observation,Page,Bundle,identity,subjects)
    opening=datetime(2026,10,23,9,30,tzinfo=timezone.utc)
    closing=opening+timedelta(minutes=40)
    intervals=tuple(((opening+timedelta(minutes=i)).isoformat(),
                     (opening+timedelta(minutes=i+1)).isoformat()) for i in range(40))
    scope=tuple(sorted(dict(provider="SYNTHETIC_OPEND",endpoint="SYNTHETIC_HISTORY",sdk="SYNTHETIC_V1",
        opend="SYNTHETIC_V1",market="SYNTHETIC_US",interval="PT1M",timezone="UTC",tzdata="SYNTHETIC_FIXED",
        session="SYNTHETIC_RTH",adjustment="SYNTHETIC_FIXED",price_unit="USD",volume_unit="SHARES",
        entitlement="SYNTHETIC_ONLY").items()))
    source=Source(scope,"SDK_ROW_SNAPSHOT","a"*64)
    mapping=Mapping("START",identity(source),"ISO")
    calendar=Calendar("2026-10-23",opening.isoformat(),closing.isoformat(),"UTC","SYNTHETIC_CAL_V1",
        "2026-10-22T00:00:00Z",intervals,False,"SYNTHETIC_CONTINUOUS")
    clock=Clock("SYNTHETIC_CLOCK",0,"c"*64)
    policy=Policy(120,120,30,"FINAL_ONLY","SYNTHETIC_CAPTURE")
    rules=(TimeRules("UTC","SYNTHETIC_FIXED",b""),)
    context=Context(source,mapping,calendar,clock,policy,rules,(),"b"*64)
    authorities=tuple(Authority(role,role+"-SYNTHETIC","d"*64,subject,identity(source),True)
                      for role,subject in subjects(context).items())
    context=replace(context,authorities=authorities)
    observations=[]
    for i in range(count):
        start=opening+timedelta(minutes=i); end=start+timedelta(minutes=1)
        receipt=(end+timedelta(seconds=1)).isoformat()
        observations.append(Observation(f"O-{i}",f"R-{i}","US.SPY",start.isoformat(),
            (100+i,102+i,99+i,101+i,100),receipt,"SYNTHETIC_CAPTURE",receipt,receipt,
            True,"FINAL","availability-SYNTHETIC",identity(source),"P-1",str(i),b"SYNTHETIC_SDK_ROW"))
    observations=tuple(observations)
    page=Page("P-1","SPY","Q-1",None,None,"OK",True,tuple(o.observation_id for o in observations))
    bundle=Bundle("SYNTHETIC-BUNDLE",observations,(page,),True,True,identity((observations,(page,))))
    request=Request("SPY","2026-10-23",(opening+timedelta(minutes=count+1)).isoformat(),
                    (opening+timedelta(minutes=count)).isoformat(),"ENGINE_READY")
    return bundle,context,request


def reseal(bundle,rows=None,pages=None):
    from canonical_candles import identity
    rows=bundle.observations if rows is None else tuple(rows)
    if pages is None:
        pages=(replace(bundle.pages[0],observation_ids=tuple(o.observation_id for o in rows)),)
    return replace(bundle,observations=rows,pages=tuple(pages),capture_hash=identity((rows,tuple(pages))))


def reapprove(context):
    from canonical_candles import subjects,identity
    return replace(context,authorities=tuple(replace(a,subject_hash=subjects(context)[a.role],
        scope_hash=identity(context.source)) for a in context.authorities))


def ny_example(day,opening="09:30:00",count=35):
    from canonical_candles import TimeRules,identity
    from io import BytesIO
    from zoneinfo import ZoneInfo
    data=base64.b64decode((Path(__file__).parent/"tests/canonicalizer_fixtures/new_york_tzdata_2026_5.b64.txt").read_text())
    assert hashlib.sha256(data).hexdigest()=="d7f2206b3a45989fc9ad63d558922532fa7352280d5f87176bf1db79cb1d1fa9"
    zone=ZoneInfo.from_file(BytesIO(data),key="America/New_York")
    start=datetime.fromisoformat(day+"T"+opening).replace(tzinfo=zone).astimezone(timezone.utc)
    b,c,r=example(count)
    scope=tuple((k,"America/New_York" if k=="timezone" else "2026.5" if k=="tzdata" else v) for k,v in c.source.scope)
    source=replace(c.source,scope=scope); rule=TimeRules("America/New_York","2026.5",data)
    intervals=tuple(((start+timedelta(minutes=i)).isoformat(),(start+timedelta(minutes=i+1)).isoformat()) for i in range(count))
    calendar=replace(c.calendar,session_date=day,open_at=start.isoformat(),close_at=intervals[-1][1],
                     intervals=intervals,timezone="America/New_York",known_at=day+"T00:00:00Z")
    c=reapprove(replace(c,source=source,mapping=replace(c.mapping,scope_hash=identity(source)),
                        calendar=calendar,time_rules=(rule,)))
    rows=[]
    for i,o in enumerate(b.observations):
        t=start+timedelta(minutes=i); receipt=(t+timedelta(minutes=1,seconds=1)).isoformat()
        rows.append(replace(o,raw_stamp=t.astimezone(zone).replace(tzinfo=None).isoformat(),available_at=receipt,
                            received_at=receipt,completion_received_at=receipt,scope_hash=identity(source)))
    return reseal(b,rows),c,replace(r,session_date=day,cutoff=(start+timedelta(minutes=count+1)).isoformat(),watermark=intervals[-1][1])


class CanonicalizerTests(unittest.TestCase):
    def run_case(self,bundle=None,context=None,request=None):
        from canonical_candles import canonicalize
        b,c,r=example()
        return canonicalize(b if bundle is None else bundle,c if context is None else context,r if request is None else request)

    def test_valid_deterministic_frozen_result_and_inputs(self):
        b,c,r=example(); before=copy.deepcopy((b,c,r))
        a=self.run_case(b,c,r)
        self.assertTrue(a.eligible)
        self.assertEqual(a,self.run_case(b,c,r))
        self.assertEqual((b,c,r),before)
        with self.assertRaises(FrozenInstanceError): a.frame.candles[0].raw_stamp="changed"

    def test_mutable_nested_input_rejected_at_construction(self):
        from canonical_candles import Source,Observation
        with self.assertRaises(TypeError): Source([("provider","bad")],"SDK_ROW_SNAPSHOT","a"*64)
        b,c,r=example()
        with self.assertRaises(TypeError): replace(b.observations[0],values=[1,2,3,4,5])

    def test_wrong_nested_context_type_fails_closed(self):
        b,c,r=example()
        changed=reapprove(replace(c,time_rules=c.time_rules+("NOT_A_TIME_RULE",)))
        self.assertFalse(self.run_case(b,changed,r).eligible)

    def test_real_bundle_or_provider_never_promoted_as_synthetic(self):
        b,c,r=example()
        self.assertIn("REAL_DATA_NOT_AUTHORIZED",self.run_case(replace(b,synthetic=False),c,r).reasons)
        scope=tuple((k,"Moomoo" if k=="provider" else v) for k,v in c.source.scope)
        self.assertFalse(self.run_case(b,replace(c,source=replace(c.source,scope=scope)),r).eligible)

    def test_missing_or_mismatched_authority_and_policy_fail_closed(self):
        b,c,r=example()
        for changed in (replace(c,authorities=()),replace(c,policy=replace(c.policy,event_age=None)),
                        replace(c,mapping=replace(c.mapping,label="UNKNOWN")),
                        replace(c,authorities=(replace(c.authorities[0],subject_hash="0"*64),)+c.authorities[1:])):
            self.assertFalse(self.run_case(b,changed,r).eligible)

    def test_unknown_or_fetch_only_availability_not_backdated(self):
        b,c,r=example()
        for change in (dict(available_at=None),dict(availability_basis="FETCH_TIME_ONLY")):
            rows=list(b.observations); rows[-1]=replace(rows[-1],**change)
            self.assertIn("AVAILABILITY_UNKNOWN",self.run_case(reseal(b,rows),c,r).reasons)

    def test_late_invalid_revision_excluded_before_payload_without_changing_earlier_frame(self):
        b,c,r=example(); first=self.run_case(b,c,r)
        late=replace(b.observations[-1],observation_id="LATE-O",revision_id="LATE-R",raw_stamp="INVALID",
                     values=(float("inf"),None,"bad",True,0),available_at="2026-10-24T00:00:01Z",
                     received_at="2026-10-24T00:00:01Z",completion_received_at="2026-10-24T00:00:01Z")
        result=self.run_case(reseal(b,b.observations+(late,)),c,r)
        self.assertTrue(result.eligible)
        self.assertEqual(result.frame.frame_hash,first.frame.frame_hash)
        self.assertNotEqual(result.bundle_hash,first.bundle_hash)
        self.assertIn(("LATE-O","POST_CUTOFF"),result.exclusions)

    def test_unknown_revision_time_blocks_instead_of_silent_drop(self):
        b,c,r=example()
        unknown=replace(b.observations[-1],observation_id="UNKNOWN-O",available_at=None)
        self.assertFalse(self.run_case(reseal(b,b.observations+(unknown,)),c,r).eligible)

    def test_visible_duplicate_and_conflicting_revisions_block(self):
        b,c,r=example()
        for value in (b.observations[-1].values,(100,102,99,101,100)):
            duplicate=replace(b.observations[-1],observation_id="DUP-O",revision_id="DUP-R",values=value)
            self.assertIn("DUPLICATE_OR_CONFLICTING_INTERVAL",self.run_case(reseal(b,b.observations+(duplicate,)),c,r).reasons)

    def test_missing_tail_interior_and_entire_symbol_explicit(self):
        b,c,r=example()
        for rows in (b.observations[:-1],b.observations[:5]+b.observations[6:],()):
            result=self.run_case(reseal(b,rows),c,r)
            self.assertIn("EXPECTED_GRID_GAP",result.reasons)
            self.assertIsNone(result.frame)

    def test_malformed_nonfinite_boolean_inconsistent_and_negative_ohlcv(self):
        b,c,r=example()
        for values in ((1,2,0,1,1),(1,2,1,float("inf"),1),(1,2,1,1,float("nan")),
                       (1,2,3,1,1),(True,2,1,1,1),(1,2,1,1,-1),("1",2,1,1,1)):
            rows=list(b.observations); rows[-1]=replace(rows[-1],values=values)
            self.assertIn("INVALID_OHLCV",self.run_case(reseal(b,rows),c,r).reasons)

    def test_wrong_session_and_unfinished_or_nonfinal_do_not_forward(self):
        b,c,r=example()
        for change in (dict(raw_stamp="2026-10-22T10:00:00Z"),dict(completed=False),dict(finality="PROVISIONAL")):
            rows=list(b.observations); rows[-1]=replace(rows[-1],**change)
            self.assertFalse(self.run_case(reseal(b,rows),c,r).eligible)

    def test_new_receipt_does_not_make_old_interval_fresh(self):
        b,c,r=example(); cutoff="2026-10-23T12:00:01Z"
        rows=tuple(replace(o,available_at="2026-10-23T12:00:00Z",received_at="2026-10-23T12:00:00Z",
                           completion_received_at="2026-10-23T12:00:00Z") for o in b.observations)
        result=self.run_case(reseal(b,rows),c,replace(r,cutoff=cutoff))
        self.assertIn("STALE_EVENT",result.reasons)
        self.assertIn("DELIVERY_LAG_EXCEEDED",result.reasons)

    def test_clock_uncertainty_and_metadata_receipt_cannot_appear_early(self):
        b,c,r=example(); rows=list(b.observations)
        rows[-1]=replace(rows[-1],completion_received_at="2026-10-23T10:05:01.5Z")
        self.assertIn("INVALID_KNOWLEDGE_BOUND",self.run_case(reseal(b,rows),c,r).reasons)

    def test_unknown_clock_bound_and_negative_or_nonfinite_policy_block(self):
        b,c,r=example()
        for changed in (replace(c,clock=replace(c.clock,uncertainty_seconds=None)),
                        replace(c,policy=replace(c.policy,event_age=float("nan"))),
                        replace(c,policy=replace(c.policy,delivery_lag=-1))):
            self.assertFalse(self.run_case(b,reapprove(changed),r).eligible)

    def test_independent_knowledge_and_delivery_budgets(self):
        b,c,r=example(); changed=reapprove(replace(c,policy=replace(c.policy,knowledge_age=1)))
        result=self.run_case(b,changed,r)
        self.assertIn("STALE_KNOWLEDGE",result.reasons)
        self.assertNotIn("STALE_EVENT",result.reasons)

    def test_pit_basis_requires_separately_bound_policy(self):
        b,c,r=example(); rows=tuple(replace(o,availability_basis="SYNTHETIC_PIT") for o in b.observations)
        self.assertIn("AVAILABILITY_UNKNOWN",self.run_case(reseal(b,rows),c,r).reasons)

    def test_known_pit_is_synthetic_only_not_fetch_time_alias(self):
        b,c,r=example()
        c=reapprove(replace(c,policy=replace(c.policy,availability_model="SYNTHETIC_PIT")))
        rows=tuple(replace(o,availability_basis="SYNTHETIC_PIT",received_at="2026-10-24T00:00:00Z",
                           completion_received_at="2026-10-24T00:00:00Z") for o in b.observations)
        self.assertTrue(self.run_case(reseal(b,rows),c,r).eligible)

    def test_source_scope_units_and_adjustment_binding(self):
        b,c,r=example()
        for key in ("sdk","opend","entitlement","adjustment","price_unit","volume_unit"):
            scope=tuple((k,"" if k==key else v) for k,v in c.source.scope)
            self.assertFalse(self.run_case(b,replace(c,source=replace(c.source,scope=scope)),r).eligible)

    def test_closed_or_future_known_calendar_not_assumed_weekday(self):
        b,c,r=example()
        closed=replace(c.calendar,closed=True,open_at=None,close_at=None,intervals=())
        self.assertFalse(self.run_case(b,replace(c,calendar=closed),r).eligible)
        self.assertFalse(self.run_case(b,replace(c,calendar=replace(c.calendar,known_at="2026-10-24T00:00:00Z")),r).eligible)

    def test_raw_audit_never_produces_engine_frame(self):
        b,c,r=example(); result=self.run_case(b,c,replace(r,mode="RAW_AUDIT"))
        self.assertFalse(result.eligible)
        self.assertIsNone(result.frame)

    def test_no_network_filesystem_or_database_io_during_canonicalize(self):
        b,c,r=example()
        with patch("builtins.open",side_effect=AssertionError("I/O forbidden")):
            self.assertTrue(self.run_case(b,c,r).eligible)

    def test_submicrosecond_precision_not_silently_truncated_to_earlier_time(self):
        b,c,r=example()
        for changes in (dict(raw_stamp="2026-10-23T09:30:00.0000001+00:00"),
                        dict(available_at="2026-10-23T09:31:01.0000001+00:00")):
            rows=list(b.observations); rows[0]=replace(rows[0],**changes)
            self.assertFalse(self.run_case(reseal(b,rows),c,r).eligible)

    def test_fractional_availability_is_not_visible_before_its_exact_cutoff(self):
        b,c,r=example(); rows=list(b.observations)
        rows[-1]=replace(rows[-1],available_at="2026-10-23T10:05:01.000001Z",
                         received_at="2026-10-23T10:05:01.000001Z",completion_received_at="2026-10-23T10:05:01.000001Z")
        changed=reseal(b,rows)
        self.assertFalse(self.run_case(changed,c,replace(r,cutoff="2026-10-23T10:05:01Z")).eligible)
        self.assertTrue(self.run_case(changed,c,replace(r,cutoff="2026-10-23T10:05:01.000001Z")).eligible)


class PageAndCustodyTests(unittest.TestCase):
    def test_non_string_page_references_return_blocked_not_type_error(self):
        b,c,r=example()
        page=replace(b.pages[0],observation_ids=(1,"O-1"))
        self.assertFalse(CanonicalizerTests().run_case(reseal(b,pages=(page,)),c,r).eligible)

    def test_valid_two_page_exhaustion_and_missing_terminal_page(self):
        from canonical_candles import Page
        b,c,r=example(); rows=b.observations[:20]+tuple(replace(o,page_id="P-2") for o in b.observations[20:])
        first=replace(b.pages[0],next_cursor="next",terminal=False,observation_ids=tuple(o.observation_id for o in rows[:20]))
        last=Page("P-2","SPY","Q-1","next",None,"OK",True,tuple(o.observation_id for o in rows[20:]))
        self.assertTrue(CanonicalizerTests().run_case(reseal(b,rows,pages=(first,last)),c,r).eligible)
        self.assertFalse(CanonicalizerTests().run_case(reseal(b,rows[:20],pages=(first,)),c,r).eligible)

    def test_per_symbol_partial_error_does_not_certify_counterpart(self):
        from canonical_candles import canonicalize,Page
        b,c,r=example()
        qqq=tuple(replace(o,observation_id="QQQ-"+o.observation_id,symbol="QQQ",page_id="P-Q") for o in b.observations)
        qpage=Page("P-Q","QQQ","Q-Q",None,None,"ERROR",False,tuple(o.observation_id for o in qqq))
        mixed=reseal(b,b.observations+qqq,pages=b.pages+(qpage,))
        self.assertTrue(canonicalize(mixed,c,r).eligible)
        self.assertFalse(canonicalize(mixed,c,replace(r,symbol="QQQ")).eligible)
    def test_failed_incomplete_manifest_cursor_loop_and_row_refs_block(self):
        from canonical_candles import identity
        b,c,r=example()
        cases=(replace(b.pages[0],status="ERROR"),replace(b.pages[0],terminal=False),
               replace(b.pages[0],next_cursor="repeat"),replace(b.pages[0],observation_ids=()))
        for page in cases:
            bundle=reseal(b,pages=(page,))
            self.assertFalse(CanonicalizerTests().run_case(bundle,c,r).eligible)

    def test_capture_hash_or_uncommitted_capture_block(self):
        b,c,r=example()
        for changed in (replace(b,capture_hash="0"*64),replace(b,committed=False)):
            self.assertFalse(CanonicalizerTests().run_case(changed,c,r).eligible)


class ConsumerViewTests(unittest.TestCase):
    def test_exact_pinned_pr31_consumer_accepts_canonical_utc_view(self):
        from canonical_candles import canonicalize,to_pr31_arguments
        path=Path(__file__).parent/"tests/canonicalizer_fixtures/pr31_successor.py.txt"
        data=path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),"5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29")
        namespace={"__file__":str(path),"__name__":"pinned_synthetic_fixture"}
        exec(compile(data,str(path),"exec"),namespace)
        result=namespace["assess"](**to_pr31_arguments(canonicalize(*example())))
        self.assertTrue(result["eligible"])
        self.assertEqual(result["action"],"WAIT")
        self.assertEqual(result["bias"],"BULLISH")

    def test_legacy_csv_cannot_bypass_typed_input_contract(self):
        from canonical_candles import canonicalize
        b,c,r=example()
        with self.assertRaises(TypeError): canonicalize([dict(symbol="SPY",bias="BULLISH")],c,r)
    def test_non_utc_pr31_host_timezone_bridge_is_explicitly_unsupported(self):
        from canonical_candles import canonicalize,to_pr31_arguments
        report=canonicalize(*ny_example("2026-10-23"))
        self.assertTrue(report.eligible)
        with self.assertRaises(ValueError): to_pr31_arguments(report)
    def test_pr31_view_is_isolated_and_preserves_raw_timestamp(self):
        from canonical_candles import canonicalize,to_pr31_arguments
        b,c,r=example(); report=canonicalize(b,c,r)
        view=to_pr31_arguments(report)
        self.assertEqual(view["rows"][0]["time"],b.observations[0].raw_stamp)
        view["rows"][0]["close"]=999
        view["contract"]["intervals"][0]["raw_stamp"]="changed"
        self.assertEqual(report.frame.candles[0].values[3],101)
        self.assertEqual(to_pr31_arguments(report)["rows"][0]["close"],101)

    def test_blocked_report_cannot_materialize(self):
        from canonical_candles import canonicalize,to_pr31_arguments
        b,c,r=example(); report=canonicalize(b,replace(c,authorities=()),r)
        with self.assertRaises(ValueError): to_pr31_arguments(report)


class InMemoryTimeRulesTests(unittest.TestCase):
    def test_pinned_tzif_dst_offsets_without_host_timezone_data(self):
        from canonical_candles import canonicalize
        for day,hour in (("2026-03-06",14),("2026-03-09",13),("2026-10-30",13),("2026-11-02",14)):
            b,c,r=ny_example(day)
            with patch("builtins.open",side_effect=AssertionError("Host timezone lookup forbidden")):
                report=canonicalize(b,c,r)
            self.assertTrue(report.eligible,report.reasons)
            self.assertEqual(datetime.fromisoformat(report.frame.candles[0].start).hour,hour)

    def test_naive_ambiguous_and_nonexistent_timestamps_block(self):
        from canonical_candles import canonicalize
        for day,raw in (("2026-03-08","2026-03-08T02:30:00"),("2026-11-01","2026-11-01T01:30:00")):
            b,c,r=ny_example(day); rows=list(b.observations); rows[0]=replace(rows[0],raw_stamp=raw)
            report=canonicalize(reseal(b,rows),c,r)
            self.assertIn("INVALID_RAW_TIMESTAMP_OR_VALUE",report.reasons)

    def test_1600_and_early_close_end_mapping_preserve_original_stamp(self):
        from canonical_candles import canonicalize
        for opening in ("15:25:00","12:25:00"):
            b,c,r=ny_example("2026-10-23",opening=opening)
            rows=[]
            for o in b.observations:
                raw=(datetime.fromisoformat(o.raw_stamp)+timedelta(minutes=1)).isoformat()
                rows.append(replace(o,raw_stamp=raw))
            c=reapprove(replace(c,mapping=replace(c.mapping,label="END")))
            report=canonicalize(reseal(b,rows),c,r)
            self.assertTrue(report.eligible,report.reasons)
            self.assertEqual(report.frame.candles[-1].raw_stamp,rows[-1].raw_stamp)
            self.assertTrue(rows[-1].raw_stamp.endswith("16:00:00") or rows[-1].raw_stamp.endswith("13:00:00"))
            start_context=reapprove(replace(c,mapping=replace(c.mapping,label="START")))
            self.assertFalse(canonicalize(reseal(b,rows),start_context,r).eligible)

    def test_unknown_tzif_does_not_fall_back_to_host(self):
        from canonical_candles import canonicalize
        b,c,r=ny_example("2026-10-23")
        c=reapprove(replace(c,time_rules=(replace(c.time_rules[0],data=b""),)))
        self.assertFalse(canonicalize(b,c,r).eligible)


if __name__=="__main__": unittest.main()
