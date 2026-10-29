"""Synthetic successor contracts; no SDK, real source, research store or orders."""
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock


def fixture(symbol="SPY"):
    start=datetime(2026,10,23,9,30,tzinfo=timezone.utc)
    rows=[]; intervals=[]
    for i in range(35):
        t=start+timedelta(minutes=i)
        raw=t.strftime("%Y-%m-%d %H:%M:%S")
        rows.append(dict(symbol=symbol,time=raw,open=100+i,high=102+i,low=99+i,
                         close=101+i,volume=100,source_sha256="a"*64))
        intervals.append(dict(raw_stamp=raw,start=t.isoformat(),end=(t+timedelta(minutes=1)).isoformat(),
            available_at=(t+timedelta(minutes=1,seconds=1)).isoformat(),completed=True,finality="FINAL"))
    contract={k:"SYNTHETIC TEST AUTHORITY" for k in ("source_authority","mapping_authority",
        "calendar_authority","availability_authority","completion_authority","finality_authority")}
    contract.update(source_sha256="a"*64,exchange_timezone="UTC",intervals=intervals)
    return rows,contract


class SuccessorTests(unittest.TestCase):
    def evaluate(self,rows=None,contract=None,**changes):
        from raccoon_scanner_successor import assess
        data,evidence=fixture()
        options=dict(now=datetime(2026,10,23,10,6,tzinfo=timezone.utc),session="2026-10-23",
                     contract=evidence if contract is None else contract,policy=dict(max_age_seconds=120),
                     pagination_complete=True,synthetic=True)
        options.update(changes)
        return assess("SPY",data if rows is None else rows,**options)

    def test_missing_authorities_fail_closed_no_guessed_policy(self):
        for field in ("source_authority","mapping_authority","calendar_authority","availability_authority",
                      "completion_authority","finality_authority"):
            rows,c=fixture(); c[field]=""
            result=self.evaluate(rows,c)
            self.assertFalse(result["eligible"])
            self.assertIsNone(result["bias"])
        self.assertFalse(self.evaluate(policy=None)["eligible"])
        self.assertFalse(self.evaluate(contract={})["eligible"])

    def test_valid_synthetic_contract_deterministic_immutable_finite(self):
        rows,c=fixture(); before=copy.deepcopy((rows,c))
        first=self.evaluate(rows,c); second=self.evaluate(rows,c)
        self.assertEqual(first,second)
        self.assertEqual((rows,c),before)
        self.assertTrue(first["eligible"])
        self.assertEqual(first["bias"],"BULLISH")
        self.assertEqual(first["action"],"WAIT")
        json.dumps(first,allow_nan=False)

    def test_ema_and_proxy_match_independent_reference_arithmetic(self):
        result=self.evaluate(); obs=result["observations"]
        rows,_=fixture(); e9=e21=float(rows[0]["close"])
        for row in rows[1:]:
            e9=.2*row["close"]+.8*e9
            e21=(2/22)*row["close"]+(20/22)*e21
        self.assertAlmostEqual(float(obs["ema9"]),e9,places=9)
        self.assertAlmostEqual(float(obs["ema21"]),e21,places=9)
        self.assertEqual(Decimal(obs["relative_volume"]),Decimal(1))
        proxy=sum((Decimal(r["high"])+Decimal(r["low"])+Decimal(r["close"]))/3 for r in rows)/35
        self.assertAlmostEqual(float(obs["hlc3_volume_weighted_proxy"]),float(proxy),places=9)
        self.assertIn("NOT_TRADE_LEVEL_VWAP",obs["limitations"])

    def test_duplicates_fail_before_indicators_not_change_ema(self):
        rows,c=fixture(); rows.append(copy.deepcopy(rows[-1]))
        result=self.evaluate(rows,c)
        self.assertIn("DUPLICATE_RAW_STAMP",result["reasons"])
        self.assertFalse(result["eligible"])
        self.assertIsNone(result["observations"])

    def test_missing_wrong_session_invalid_nonfinite_and_source_mismatch(self):
        for changes in (dict(close=float("inf")),dict(volume=float("nan")),dict(low=999),
                        dict(close=0),dict(volume=-1),dict(source_sha256="b"*64),
                        dict(time="2026-10-22 09:30:00")):
            rows,c=fixture(); rows[-1].update(changes)
            self.assertFalse(self.evaluate(rows,c)["eligible"])
        rows,c=fixture(); del rows[10]
        self.assertIn("MISSING_EXPECTED_INTERVAL",self.evaluate(rows,c)["reasons"])

    def test_stale_future_delayed_unfinished_and_unknown_finality_block(self):
        self.assertIn("STALE",self.evaluate(now=datetime(2026,10,23,12,tzinfo=timezone.utc))["reasons"])
        for changes in (dict(completed=False),dict(finality="UNKNOWN"),
                        dict(available_at="2026-10-24T10:00:00Z"),
                        dict(end="2026-10-24T10:00:00Z")):
            rows,c=fixture(); c["intervals"][-1].update(changes)
            self.assertFalse(self.evaluate(rows,c)["eligible"])

    def test_partial_page_and_symbol_error_block_with_explicit_reasons(self):
        self.assertIn("PAGINATION_INCOMPLETE",self.evaluate(pagination_complete=False)["reasons"])
        self.assertIn("PROVIDER_ERROR",self.evaluate(provider_error="SYNTHETIC FAILURE")["reasons"])
        self.assertIn("NO_ROWS",self.evaluate(rows=[])["reasons"])

    def test_1600_not_silently_filtered_or_shifted_requires_explicit_mapping(self):
        rows,c=fixture(); old=rows[-1]["time"]; rows[-1]["time"]="2026-10-23 16:00:00"
        self.assertIn("UNMAPPED_RAW_STAMP",self.evaluate(rows,c)["reasons"])
        self.assertEqual(rows[-1]["time"],"2026-10-23 16:00:00")
        self.assertEqual(c["intervals"][-1]["raw_stamp"],old)

    def test_naive_time_and_malformed_policy_and_non_synthetic_rejected(self):
        for policy in (None,{},dict(max_age_seconds=True),dict(max_age_seconds=float("inf")),dict(max_age_seconds=-1)):
            self.assertFalse(self.evaluate(policy=policy)["eligible"])
        with self.assertRaises(ValueError): self.evaluate(now=datetime(2026,10,23))
        with self.assertRaises(ValueError): self.evaluate(synthetic=False)

    def test_input_order_independent_and_per_symbol_isolation(self):
        rows,c=fixture(); other,_=fixture("QQQ")
        result=self.evaluate(list(reversed(rows))+other,c)
        original=self.evaluate(rows,c)
        self.assertNotEqual(result.pop("raw_sha256"),original.pop("raw_sha256"))
        self.assertEqual(result,original)  # Signals stable; raw evidence keeps original order.

    def test_mixed_data_has_no_directional_candidate(self):
        rows,c=fixture()
        for row in rows: row.update(open=100,high=101,low=99,close=100)
        result=self.evaluate(rows,c)
        self.assertFalse(result["eligible"])
        self.assertIn("NO_DIRECTIONAL_CONJUNCTION",result["reasons"])

    def test_extreme_finite_volumes_do_not_produce_infinite_output(self):
        rows,c=fixture()
        for row in rows: row["volume"]=5e-324
        rows[-1]["volume"]=1e308
        result=self.evaluate(rows,c)
        self.assertTrue(result["eligible"])
        self.assertTrue(Decimal(result["observations"]["relative_volume"]).is_finite())
        json.dumps(result,allow_nan=False)

    def test_result_keeps_complete_contract_and_policy_evidence(self):
        result=self.evaluate()
        self.assertIn("contract_evidence",result)
        self.assertIn("policy_evidence",result)
        self.assertIn("SYNTHETIC TEST AUTHORITY",json.dumps(result["contract_evidence"]))

    def test_explicit_synthetic_1600_mapping_is_preserved_without_filter(self):
        rows,c=fixture(); start=datetime(2026,10,23,15,26,tzinfo=timezone.utc)
        for i,(row,item) in enumerate(zip(rows,c["intervals"])):
            t=start+timedelta(minutes=i)
            row["time"]=item["raw_stamp"]=t.strftime("%Y-%m-%d %H:%M:%S")
            item.update(start=t.isoformat(),end=(t+timedelta(minutes=1)).isoformat(),
                        available_at=(t+timedelta(minutes=1,seconds=1)).isoformat())
        result=self.evaluate(rows,c,now=datetime(2026,10,23,16,2,tzinfo=timezone.utc))
        self.assertTrue(result["eligible"])
        self.assertEqual(rows[-1]["time"],"2026-10-23 16:00:00")
        self.assertEqual(result["observations"]["interval_end"],"2026-10-23T16:01:00+00:00")

    def test_contract_duplicate_or_overlapping_interval_rejected(self):
        rows,c=fixture(); c["intervals"][-1]["start"]=c["intervals"][-2]["start"]
        self.assertFalse(self.evaluate(rows,c)["eligible"])


class PaginationTests(unittest.TestCase):
    def test_limits_and_first_page_are_explicit(self):
        from raccoon_scanner_successor import collect_pages
        for options in (dict(max_pages=0),dict(max_pages=True),dict(max_rows=-1)):
            with self.assertRaises(ValueError): collect_pages(Mock(),"SPY",{},**options)
        with self.assertRaises(ValueError): collect_pages(Mock(),"SPY",dict(page_req_key="late"))
    def test_complete_raw_pages_and_input_preservation(self):
        from raccoon_scanner_successor import collect_pages
        rows,_=fixture(); original=copy.deepcopy(rows)
        req=Mock(side_effect=[(0,rows[:20],"next"),(0,rows[20:],None)])
        result=collect_pages(req,"SPY",dict(start="SYNTHETIC"))
        self.assertTrue(result["complete"])
        self.assertEqual(result["rows"],rows)
        self.assertEqual(rows,original)
        self.assertEqual(req.call_args.kwargs["page_req_key"],"next")

    def test_error_repeat_exception_limit_and_bad_data_block(self):
        from raccoon_scanner_successor import collect_pages
        for replies,limit in [([(0,[{}],"x"),(1,"error",None)],10),
                              ([(0,[{}],"x"),(0,[],"x")],10),
                              ([(0,[{}],"x"),OSError("synthetic")],10),
                              ([(0,[{}],"x")],1), ([(0,"bad",None)],10)]:
            result=collect_pages(Mock(side_effect=replies),"SPY",{},max_pages=limit)
            self.assertFalse(result["complete"])
            self.assertTrue(result["reasons"])


class EvidenceTests(unittest.TestCase):
    def test_existing_lock_is_not_stolen_or_deleted(self):
        from raccoon_scanner_successor import create_store,record_observation
        with tempfile.TemporaryDirectory() as temp:
            store=Path(temp).resolve()/"synthetic"; create_store(store,synthetic=True)
            lock=store/".writer-lock"; lock.write_bytes(b"SYNTHETIC OTHER OWNER")
            with self.assertRaises(FileExistsError): record_observation(store,dict(synthetic=True),raw_rows=[],recorded_at="2026-10-23T10:07:00Z")
            self.assertEqual(lock.read_bytes(),b"SYNTHETIC OTHER OWNER")

    def test_mismatched_observation_raw_hash_is_not_recorded(self):
        from raccoon_scanner_successor import create_store,record_observation
        with tempfile.TemporaryDirectory() as temp:
            store=Path(temp).resolve()/"synthetic"; create_store(store,synthetic=True)
            with self.assertRaises(ValueError): record_observation(store,dict(synthetic=True,raw_sha256="0"*64),
                raw_rows=[],recorded_at="2026-10-23T10:07:00Z")
            self.assertEqual(len(list(store.iterdir())),1)

    def test_forked_revision_does_not_overwrite_original_or_create_file(self):
        from raccoon_scanner_successor import create_store,record_observation
        with tempfile.TemporaryDirectory() as temp:
            store=Path(temp).resolve()/"synthetic"; create_store(store,synthetic=True)
            observation=dict(symbol="SPY",synthetic=True)
            first=record_observation(store,observation,raw_rows=[],recorded_at="2026-10-23T10:07:00Z")
            record_observation(store,observation,raw_rows=[],recorded_at="2026-10-23T10:08:00Z",supersedes=first["record_id"])
            before={p.name:p.read_bytes() for p in store.iterdir()}
            with self.assertRaises(ValueError): record_observation(store,observation,raw_rows=[],recorded_at="2026-10-23T10:09:00Z",supersedes=first["record_id"])
            self.assertEqual(before,{p.name:p.read_bytes() for p in store.iterdir()})

    def test_new_store_exclusive_records_and_revision_chain(self):
        from raccoon_scanner_successor import create_store,record_observation,read_records
        with tempfile.TemporaryDirectory() as temp:
            store=Path(temp).resolve()/"synthetic"
            create_store(store,synthetic=True)
            rows,c=fixture()
            first=record_observation(store,dict(symbol="SPY",synthetic=True),raw_rows=rows,
                recorded_at="2026-10-23T10:06:00Z")
            before={p.name:p.read_bytes() for p in store.iterdir()}
            second=record_observation(store,dict(symbol="SPY",synthetic=True),raw_rows=rows,
                recorded_at="2026-10-23T10:07:00Z",supersedes=first["record_id"])
            for name,data in before.items(): self.assertEqual((store/name).read_bytes(),data)
            self.assertNotEqual(first["record_id"],second["record_id"])
            records=read_records(store)
            self.assertEqual(len(records),2)
            self.assertEqual(records[-1]["supersedes"],first["record_id"])
            with self.assertRaises(FileExistsError): create_store(store,synthetic=True)

    def test_nonfinite_raw_evidence_strict_json_and_no_real_records(self):
        from raccoon_scanner_successor import create_store,record_observation,read_records
        with tempfile.TemporaryDirectory() as temp:
            store=Path(temp).resolve()/"synthetic"; create_store(store,synthetic=True)
            record_observation(store,dict(symbol="SPY",synthetic=True),raw_rows=[dict(time="raw",close=float("inf"))],
                recorded_at="2026-10-23T10:06:00Z")
            json.dumps(read_records(store),allow_nan=False)
            with self.assertRaises(ValueError): record_observation(store,dict(synthetic=False),raw_rows=[],recorded_at="2026-10-23T10:07:00Z")

    def test_foreign_path_invalid_revision_and_tampering_rejected(self):
        from raccoon_scanner_successor import create_store,record_observation,read_records
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve(); foreign=root/"foreign"; foreign.mkdir()
            with self.assertRaises(ValueError): read_records(foreign)
            store=root/"synthetic"; create_store(store,synthetic=True)
            with self.assertRaises(ValueError): record_observation(store,dict(synthetic=True),raw_rows=[],recorded_at="2026-10-23T10:07:00Z",supersedes="missing")
            result=record_observation(store,dict(synthetic=True),raw_rows=[],recorded_at="2026-10-23T10:07:00Z")
            (store/(result["record_id"]+".json")).write_text("{}",encoding="utf-8")
            with self.assertRaises(ValueError): read_records(store)


if __name__=="__main__": unittest.main()
