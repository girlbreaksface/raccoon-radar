"""Bounded synthetic bridge regressions. No SDK, host timezone, DB, capture or orders."""
import ast
from dataclasses import FrozenInstanceError,replace
from datetime import datetime,timedelta,timezone
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from canonical_candles import canonicalize,to_pr31_arguments,identity
from test_canonical_candles import example,ny_example,reapprove,reseal


def reference():
    path=Path(__file__).parent/"tests/canonicalizer_fixtures/pr31_successor.py.txt"
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=="5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29"
    namespace={"__file__":str(path),"__name__":"pinned_reference_fixture"}
    exec(compile(raw,str(path),"exec"),namespace)
    return namespace


class MemoryOnlyZone:
    def __new__(cls,*args,**kwargs): raise AssertionError("Host ZoneInfo constructor forbidden")
    from_file=ZoneInfo.from_file


class TimezoneBridgeTests(unittest.TestCase):
    def evaluate(self,b=None,c=None,r=None):
        from pinned_timezone_bridge import evaluate
        original=example()
        return evaluate(canonicalize(original[0] if b is None else b,
                                     original[1] if c is None else c,
                                     original[2] if r is None else r))

    def test_utc_exact_parity_with_unchanged_pinned_pr31(self):
        from pinned_timezone_bridge import consumer_dict
        report=canonicalize(*example())
        expected=reference()["assess"](**to_pr31_arguments(report))
        self.assertEqual(consumer_dict(self.evaluate()),expected)

    def test_new_york_eligible_without_host_rules_or_filesystem(self):
        from pinned_timezone_bridge import evaluate,consumer_dict
        report=canonicalize(*ny_example("2026-10-23"))
        with patch("canonical_candles.ZoneInfo",MemoryOnlyZone),patch("builtins.open",side_effect=AssertionError("I/O forbidden")):
            result=evaluate(report)
        self.assertTrue(result.eligible,result.reasons)
        self.assertEqual(consumer_dict(result)["bias"],"BULLISH")
        self.assertEqual(result.action,"WAIT")
        with self.assertRaises(ValueError): to_pr31_arguments(report)  # Protected old gate remains.

    def test_new_york_explicit_pinned_semantics_match_reference_with_injected_memory_zone(self):
        from pinned_timezone_bridge import consumer_dict
        from canonical_candles import _zone
        b,c,r=ny_example("2026-10-23")
        # Reference UTC builder is used solely to obtain identical argument structure;
        # explicit timezone is restored before invoking the pinned reference.
        from pinned_timezone_bridge import _arguments
        report=canonicalize(b,c,r)
        args=_arguments(report)
        original=reference(); original["ZoneInfo"]=lambda name:_zone(name,c)
        expected=original["assess"](**args)
        self.assertEqual(consumer_dict(self.evaluate(b,c,r)),expected)

    def test_dst_spring_and_fall_use_pinned_bytes(self):
        from pinned_timezone_bridge import evaluate,consumer_dict
        for day,hour in (("2026-03-06",14),("2026-03-09",13),("2026-10-30",13),("2026-11-02",14)):
            report=canonicalize(*ny_example(day))
            with patch("canonical_candles.ZoneInfo",MemoryOnlyZone): result=evaluate(report)
            self.assertTrue(result.eligible,result.reasons)
            self.assertEqual(datetime.fromisoformat(report.frame.candles[0].start).hour,hour)
            self.assertEqual(consumer_dict(result)["session"],day)

    def test_ambiguous_and_nonexistent_raw_times_never_reach_kernel(self):
        for day,raw in (("2026-03-08","2026-03-08T02:30:00"),("2026-11-01","2026-11-01T01:30:00")):
            b,c,r=ny_example(day); rows=list(b.observations); rows[0]=replace(rows[0],raw_stamp=raw)
            with patch("_pr31_pinned_kernel.assess",side_effect=AssertionError("Invalid frame forwarded")):
                result=self.evaluate(reseal(b,rows),c,r)
            self.assertFalse(result.eligible)

    def test_early_close_and_1600_end_labels_remain_separate_from_start_labels(self):
        for opening in ("12:25:00","15:25:00"):
            b,c,r=ny_example("2026-10-23",opening=opening)
            rows=tuple(replace(o,raw_stamp=(datetime.fromisoformat(o.raw_stamp)+timedelta(minutes=1)).isoformat()) for o in b.observations)
            end_context=reapprove(replace(c,mapping=replace(c.mapping,label="END")))
            valid=self.evaluate(reseal(b,rows),end_context,r)
            self.assertTrue(valid.eligible,valid.reasons)
            self.assertEqual(valid.canonical_report.frame.candles[-1].raw_stamp,rows[-1].raw_stamp)
            self.assertFalse(self.evaluate(reseal(b,rows),c,r).eligible)

    def test_fractional_availability_and_cutoff_do_not_round_early(self):
        b,c,r=ny_example("2026-10-23"); rows=list(b.observations)
        end=datetime.fromisoformat(c.calendar.close_at)
        receipt=(end+timedelta(seconds=1,microseconds=1)).isoformat()
        rows[-1]=replace(rows[-1],available_at=receipt,received_at=receipt,completion_received_at=receipt)
        self.assertFalse(self.evaluate(reseal(b,rows),c,replace(r,cutoff=(end+timedelta(seconds=1)).isoformat())).eligible)
        self.assertTrue(self.evaluate(reseal(b,rows),c,replace(r,cutoff=receipt)).eligible)

    def test_submicrosecond_precision_and_uncertainty_stay_blocked(self):
        b,c,r=ny_example("2026-10-23"); rows=list(b.observations)
        rows[0]=replace(rows[0],available_at="2026-10-23T13:31:01.0000001Z")
        self.assertFalse(self.evaluate(reseal(b,rows),c,r).eligible)
        uncertain=reapprove(replace(c,clock=replace(c.clock,uncertainty_seconds=0.0000001)))
        self.assertFalse(self.evaluate(b,uncertain,r).eligible)

    def test_post_cutoff_invalid_revision_does_not_change_feature_or_consumer_result(self):
        from pinned_timezone_bridge import consumer_dict
        b,c,r=ny_example("2026-10-23"); first=self.evaluate(b,c,r)
        late=replace(b.observations[-1],observation_id="LATE-O",revision_id="LATE-R",row_id="LATE-ROW",
            values=(float("inf"),None,"bad",True,0),raw_stamp="INVALID",available_at="2026-10-24T00:00:01Z",
            received_at="2026-10-24T00:00:01Z",completion_received_at="2026-10-24T00:00:01Z")
        later=self.evaluate(reseal(b,b.observations+(late,)),c,r)
        self.assertTrue(later.eligible,later.reasons)
        self.assertEqual(consumer_dict(first),consumer_dict(later))
        self.assertEqual(first.canonical_report.frame.frame_hash,later.canonical_report.frame.frame_hash)
        self.assertNotEqual(first.bridge_hash,later.bridge_hash)

    def test_unknown_available_and_visible_conflicting_revision_block(self):
        b,c,r=ny_example("2026-10-23")
        for changed in (replace(b.observations[-1],observation_id="NEW",row_id="NEW",available_at=None),
                        replace(b.observations[-1],observation_id="NEW",row_id="NEW",revision_id="REV-2")):
            self.assertFalse(self.evaluate(reseal(b,b.observations+(changed,)),c,r).eligible)

    def test_invalid_source_calendar_finality_and_clock_cannot_be_relaxed(self):
        b,c,r=ny_example("2026-10-23")
        cases=[(b,replace(c,authorities=()),r),
               (b,reapprove(replace(c,calendar=replace(c.calendar,known_at="2026-10-24T00:00:00Z"))),r),
               (b,reapprove(replace(c,clock=replace(c.clock,uncertainty_seconds=None))),r),
               (reseal(b,b.observations[:-1]+(replace(b.observations[-1],finality="UNKNOWN"),)),c,r)]
        for data,context,request in cases:
            with patch("_pr31_pinned_kernel.assess",side_effect=AssertionError("Invalid frame forwarded")):
                self.assertFalse(self.evaluate(data,context,request).eligible)

    def test_hostile_host_timezone_lookup_never_becomes_fallback_on_missing_rule(self):
        b,c,r=ny_example("2026-10-23")
        bad=reapprove(replace(c,time_rules=(replace(c.time_rules[0],data=b""),)))
        with patch("canonical_candles.ZoneInfo",MemoryOnlyZone):
            self.assertFalse(self.evaluate(b,bad,r).eligible)

    def test_unsupported_timezone_alias_is_not_silently_substituted(self):
        b,c,r=ny_example("2026-10-23")
        source=replace(c.source,scope=tuple((k,"US/Eastern" if k=="timezone" else v) for k,v in c.source.scope))
        c=reapprove(replace(c,source=source,mapping=replace(c.mapping,scope_hash=identity(source)),
            calendar=replace(c.calendar,timezone="US/Eastern"),time_rules=(replace(c.time_rules[0],name="US/Eastern"),)))
        rows=tuple(replace(o,scope_hash=identity(source)) for o in b.observations)
        report=canonicalize(reseal(b,rows),c,r)
        self.assertTrue(report.eligible,report.reasons)
        from pinned_timezone_bridge import evaluate
        self.assertIn("UNSUPPORTED_CONSUMER_TIMEZONE",evaluate(report).reasons)

    def test_offset_contradicting_pinned_dst_rules_blocks(self):
        b,c,r=ny_example("2026-10-23"); rows=list(b.observations)
        rows[0]=replace(rows[0],raw_stamp="2026-10-23T09:30:00-05:00")
        self.assertFalse(self.evaluate(reseal(b,rows),c,r).eligible)

    def test_nonfinite_or_contradictory_dependency_output_fails_closed(self):
        b,c,r=ny_example("2026-10-23")
        for output in (dict(synthetic=True,action="WAIT",eligible=True,bias="BULLISH",reasons=[],observations=dict(ema9=float("inf"))),
                       dict(synthetic=True,action="WAIT",eligible=True,bias="BULLISH",reasons=["INVALID_SOURCE"]),
                       dict(synthetic=True,action="WAIT",eligible=False,bias=None,reasons=[None,1,"bad"])):
            with self.subTest(output=output):
                with patch("_pr31_pinned_kernel.assess",return_value=output):
                    result=self.evaluate(b,c,r)
                self.assertFalse(result.eligible)
                self.assertIn("INVALID_CONSUMER_OUTPUT",result.reasons)

    def test_report_forgery_is_revalidated_before_kernel(self):
        from pinned_timezone_bridge import evaluate
        report=canonicalize(*ny_example("2026-10-23"))
        for forged in (replace(report,run_hash="0"*64),replace(report,bundle_hash="0"*64),
                       replace(report,reasons=("INVALID",))):
            with patch("_pr31_pinned_kernel.assess",side_effect=AssertionError("Forged report forwarded")):
                result=evaluate(forged)
            self.assertFalse(result.eligible)

    def test_outputs_immutable_and_explicit_copies_do_not_alias_lineage(self):
        from pinned_timezone_bridge import consumer_dict
        b,c,r=ny_example("2026-10-23"); before=copy.deepcopy((b,c,r)); result=self.evaluate(b,c,r)
        with self.assertRaises(FrozenInstanceError): result.eligible=False
        with self.assertRaises(FrozenInstanceError): result.consumer.items=()
        view=consumer_dict(result); view["bias"]="CORRUPTED"
        view["observations"]["ema9"]="bad"
        self.assertEqual(consumer_dict(result)["bias"],"BULLISH")
        self.assertEqual((b,c,r),before)

    def test_mixed_and_insufficient_warmup_are_not_trade_candidates(self):
        b,c,r=example(); rows=tuple(replace(o,values=(100,101,99,100,100)) for o in b.observations)
        result=self.evaluate(reseal(b,rows),c,r)
        self.assertFalse(result.eligible)
        self.assertIn("NO_DIRECTIONAL_CONJUNCTION",result.reasons)
        short=example(10)
        self.assertTrue(canonicalize(*short).eligible)
        self.assertFalse(self.evaluate(*short).eligible)

    def test_determinism_and_no_caller_global_mutation(self):
        b,c,r=ny_example("2026-10-23")
        self.assertEqual(self.evaluate(b,c,r),self.evaluate(b,c,r))
        self.assertIs(__import__("canonical_candles").ZoneInfo,ZoneInfo)


class ExactKernelConformance(unittest.TestCase):
    def test_reference_ast_matches_except_explicit_resolver_injection(self):
        import _pr31_pinned_kernel as kernel
        path=Path(__file__).parent/"tests/canonicalizer_fixtures/pr31_successor.py.txt"
        data=path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),"5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29")
        old=ast.parse(data.decode("utf-8")); new=ast.parse(Path(kernel.__file__).read_text(encoding="utf-8-sig"))
        names=("_time","_symbol","_typed","_json","_hash","assess")
        class Resolver(ast.NodeTransformer):
            def visit_Name(self,node):
                return ast.copy_location(ast.Name(id="zone_factory",ctx=node.ctx),node) if node.id=="ZoneInfo" else node
        for name in names:
            original=copy.deepcopy(next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name))
            changed=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
            if name=="assess":
                original.args.kwonlyargs.append(ast.arg(arg="zone_factory"))
                original.args.kw_defaults.append(None)
                original=Resolver().visit(original)
            self.assertEqual(ast.dump(original,include_attributes=False),ast.dump(changed,include_attributes=False),name)
        for name in ("AUTHORITIES","NOTICE"):
            def value(tree):
                return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and
                    any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
            self.assertEqual(value(old),value(new),name)
        self.assertNotIn("ZoneInfo",kernel.__dict__)


if __name__=="__main__": unittest.main()
