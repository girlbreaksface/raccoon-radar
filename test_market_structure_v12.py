"""v1.2 synthetic structural contracts; no real records, providers or trade outcomes."""
import ast
import copy
from dataclasses import FrozenInstanceError, replace
from decimal import getcontext, localcontext, ROUND_DOWN
from datetime import datetime, timedelta
import json
from pathlib import Path
import unittest

from canonical_candles import identity
from market_structure_v12_scenarios import scenario, reseal


def api():
    import market_structure_v12 as module
    return module


def replay_case(name, config=None, symbol="SPY"):
    module=api()
    bundle,context,requests=scenario(name,symbol)
    previous=None
    outputs=[]
    for request in requests:
        result=module.assess(bundle,context,request,config=config or module.Config(),previous=previous,synthetic=True)
        outputs.append(result)
        previous=result.tracker
    return outputs


class StructureTests(unittest.TestCase):
    def test_both_reversals_require_later_retest_and_confirmation(self):
        for name,direction,trend in (("bullish_reversal","BULLISH","BEARISH"),("bearish_reversal","BEARISH","BULLISH")):
            with self.subTest(name=name):
                results=replay_case(name)
                self.assertEqual(results[12].decision.classification,"REVERSAL_WATCH")
                self.assertEqual(results[13].decision.stage,"AWAITING_RETEST")
                self.assertIsNone(results[13].decision.direction)
                final=results[-1].decision
                self.assertEqual(final.classification,"CONFIRMED_STRUCTURAL_REVERSAL")
                self.assertEqual(final.direction,direction)
                self.assertEqual(final.prior_trend,trend)
                self.assertEqual(final.action,"WAIT")

    def test_mirror_preserves_structural_status_and_reflects_boundaries(self):
        a,b=replay_case("bullish_reversal"),replay_case("bearish_reversal")
        self.assertEqual([x.decision.classification for x in a],[x.decision.classification for x in b])
        from decimal import Decimal
        self.assertEqual(Decimal(a[-1].decision.support)+Decimal(b[-1].decision.resistance),20000)
        self.assertEqual(Decimal(a[-1].decision.resistance)+Decimal(b[-1].decision.support),20000)

    def test_continuation_both_directions(self):
        for name,direction in (("bullish_continuation","BULLISH"),("bearish_continuation","BEARISH")):
            final=replay_case(name)[-1].decision
            self.assertEqual(final.classification,"TREND_CONTINUATION")
            self.assertEqual(final.direction,direction)

    def test_false_breakouts_both_directions(self):
        for name in ("bullish_false_breakout","bearish_false_breakout"):
            final=replay_case(name)[-1].decision
            self.assertEqual(final.classification,"FAILED_REVERSAL")
            self.assertIn("BREAKOUT_REENTERED_RANGE",final.reasons)
            self.assertIsNone(final.direction)

    def test_failed_retests_both_directions(self):
        for name in ("bullish_failed_retest","bearish_failed_retest"):
            final=replay_case(name)[-1].decision
            self.assertEqual(final.classification,"FAILED_REVERSAL")
            self.assertIn("FAILED_RETEST",final.reasons)

    def test_invalidation_does_not_erase_earlier_confirmation(self):
        for name in ("bullish_invalidated","bearish_invalidated"):
            results=replay_case(name)
            self.assertEqual(results[-2].decision.classification,"CONFIRMED_STRUCTURAL_REVERSAL")
            final=results[-1]
            self.assertEqual(final.decision.classification,"INVALIDATED_SETUP")
            self.assertIn("CONFIRMED_REVERSAL_INVALIDATED",final.decision.reasons)
            self.assertEqual(final.tracker.history[-2],results[-2].decision)
            kinds=[event.kind for event in final.tracker.events]
            self.assertIn("CONFIRMED_STRUCTURAL_REVERSAL",kinds)
            self.assertIn("INVALIDATED_SETUP",kinds)

    def test_prolonged_range_exact_age_then_expiry(self):
        results=replay_case("prolonged")
        self.assertEqual(results[-2].decision.classification,"REVERSAL_WATCH")
        self.assertEqual(results[-1].decision.classification,"INVALIDATED_SETUP")
        self.assertIn("CONSOLIDATION_EXPIRED",results[-1].decision.reasons)

    def test_retest_timeout_not_unlimited_wait(self):
        results=replay_case("retest_timeout")
        self.assertEqual(results[-2].decision.classification,"REVERSAL_WATCH")
        self.assertEqual(results[-1].decision.classification,"FAILED_REVERSAL")
        self.assertIn("RETEST_TIMEOUT",results[-1].decision.reasons)

    def test_wick_only_does_not_confirm_and_two_sided_is_ambiguous(self):
        wick=replay_case("wick_only")[-1].decision
        self.assertEqual(wick.classification,"REVERSAL_WATCH")
        self.assertIn("WICK_ONLY_NO_CLOSE_BREAKOUT",wick.reasons)
        ambiguous=replay_case("two_sided")[-1].decision
        self.assertEqual(ambiguous.classification,"INVALIDATED_SETUP")
        self.assertIn("AMBIGUOUS_TWO_SIDED_EXCURSION",ambiguous.reasons)

    def test_insufficient_warmup_weak_trend_and_volatility(self):
        for name,reason in (("not_ready","INSUFFICIENT_STRUCTURE_WARMUP"),
                            ("weak_trend","NO_ESTABLISHED_TREND"),
                            ("no_contraction","VOLATILITY_NOT_CONTRACTED")):
            final=replay_case(name)[-1].decision
            self.assertEqual(final.classification,"INSUFFICIENT_EVIDENCE")
            self.assertIn(reason,final.reasons)

    def test_range_bounds_freeze_during_breakout_and_retest(self):
        results=replay_case("bullish_reversal")
        self.assertEqual({r.decision.support for r in results[12:]},{"9260"})
        self.assertEqual({r.decision.resistance for r in results[12:]},{"9340"})
        self.assertEqual(len({r.decision.setup_id for r in results[12:]}),1)

    def test_exact_breakout_equality_is_not_a_breakout(self):
        module=api()
        bundle,context,requests=scenario()
        state=replay_case("bullish_reversal")[12].tracker
        rows=list(bundle.observations)
        rows[13]=replace(rows[13],values=(9340,9350,9330,9348,100))
        changed=reseal(bundle,rows)
        result=module.assess(changed,context,requests[13],previous=state,synthetic=True)
        self.assertEqual(result.decision.classification,"REVERSAL_WATCH")
        self.assertEqual(result.decision.stage,"CONSOLIDATING")
        self.assertIsNone(result.decision.direction)

    def test_configuration_is_explicit_bounded_and_not_float(self):
        module=api()
        for changes in (dict(trend_bars=True),dict(consolidation_bars=2),dict(min_move="NaN"),
                        dict(max_contraction="1.1"),dict(min_move=0.02),dict(min_touches=6),
                        dict(max_range_bars=4),dict(confirmation_closes=1),dict(retest_fraction="-0.1")):
            with self.subTest(changes=changes):
                with self.assertRaises((ValueError,TypeError)):
                    replay_case("bullish_reversal",replace(module.Config(),**changes))

    def test_threshold_config_can_reject_same_unoptimized_fixture(self):
        module=api()
        narrow=replay_case("bullish_reversal",replace(module.Config(),max_width="0.0001"))[-1].decision
        self.assertEqual(narrow.classification,"INSUFFICIENT_EVIDENCE")
        self.assertIn("RANGE_TOO_WIDE",narrow.reasons)

    def test_config_context_symbol_and_seal_changes_reject_state_reuse(self):
        module=api()
        b,c,requests=scenario()
        state=replay_case("bullish_reversal")[12].tracker
        bad_cases=(
            dict(config=replace(module.Config(),min_move="0.02"),previous=state),
            dict(context=replace(c,implementation_hash="f"*64),previous=state),
            dict(previous=replace(state,seal="0"*64)),
            dict(request=replace(requests[13],symbol="QQQ"),previous=state),
        )
        for changes in bad_cases:
            options=dict(context=c,request=requests[13],config=module.Config(),previous=state)
            options.update(changes)
            with self.assertRaises(ValueError):
                module.assess(b,synthetic=True,**options)

    def test_nonincreasing_cutoff_cannot_overwrite_history(self):
        module=api()
        b,c,requests=scenario()
        state=replay_case("bullish_reversal")[12].tracker
        for request in (requests[12],requests[11]):
            with self.assertRaises(ValueError):
                module.assess(b,c,request,previous=state,synthetic=True)

    def test_data_quality_failures_never_create_confirmed_state(self):
        reasons={"gap":"EXPECTED_GRID_GAP","provisional":"FINALITY_UNVERIFIED","partial":"PARTIAL_SOURCE",
                 "unknown":"AVAILABILITY_UNKNOWN","duplicate":"DUPLICATE_OR_CONFLICTING_INTERVAL",
                 "incomplete":"COMPLETION_UNVERIFIED","invalid":"INVALID_OHLCV"}
        for name,reason in reasons.items():
            with self.subTest(name=name):
                final=replay_case(name)[-1].decision
                self.assertEqual(final.classification,"INSUFFICIENT_EVIDENCE")
                self.assertEqual(final.data_status,"BLOCKED")
                self.assertIn(reason,final.reasons)
                self.assertIsNone(final.direction)
                self.assertIsNone(final.support)

    def test_real_markers_and_untyped_call_reject(self):
        module=api()
        b,c,requests=scenario()
        for flag in (False,None,1,"true"):
            with self.assertRaises(ValueError):
                module.assess(b,c,requests[-1],synthetic=flag)
        with self.assertRaises(TypeError):
            module.assess({},c,requests[-1],synthetic=True)
        with self.assertRaises(ValueError):
            module.assess(replace(b,synthetic=False),c,requests[-1],synthetic=True)

    def test_prefix_revision_change_blocks_without_repainting(self):
        module=api()
        b,c,requests=scenario()
        prior=replay_case("bullish_reversal")[12]
        rows=list(b.observations)
        rows[0]=replace(rows[0],revision_id="CORRECTED",values=(10010,10090,9930,10010,100))
        result=module.assess(reseal(b,rows),c,requests[13],previous=prior.tracker,synthetic=True)
        self.assertIn("PREFIX_REVISION_CHANGED",result.decision.reasons)
        self.assertEqual(result.tracker.history[:-1],prior.tracker.history)
        self.assertEqual(result.tracker.candles,prior.tracker.candles)
        self.assertEqual(result.decision.data_status,"BLOCKED")

    def test_known_later_invalid_revision_does_not_repaint_prefix(self):
        module=api()
        b,c,requests=scenario()
        original=module.assess(b,c,requests[12],synthetic=True)
        late=replace(b.observations[0],observation_id="LATE",revision_id="LATE",row_id="LATE",
            raw_stamp="BAD",values=(float("inf"),None,True,0,0),
            available_at="2026-10-24T00:00:00Z",received_at="2026-10-24T00:00:00Z",
            completion_received_at="2026-10-24T00:00:00Z")
        changed=module.assess(reseal(b,b.observations+(late,)),c,requests[12],synthetic=True)
        self.assertEqual(original.decision,changed.decision)
        self.assertEqual(original.tracker,changed.tracker)
        self.assertNotEqual(original.audit_hash,changed.audit_hash)

    def test_fractional_receipt_does_not_admit_the_bar_early(self):
        module=api()
        b,c,requests=scenario()
        rows=list(b.observations)
        received=(datetime.fromisoformat(rows[-1].available_at)+timedelta(microseconds=1)).isoformat()
        rows[-1]=replace(rows[-1],available_at=received,received_at=received,completion_received_at=received)
        b=reseal(b,rows)
        early=module.assess(b,c,requests[-1],synthetic=True)
        late=module.assess(b,c,replace(requests[-1],cutoff=received),previous=early.tracker,synthetic=True)
        self.assertEqual(early.decision.data_status,"BLOCKED")
        self.assertEqual(late.decision.classification,"CONFIRMED_STRUCTURAL_REVERSAL")

    def test_batch_events_use_knowledge_cutoff_not_backdated_bar_time(self):
        module=api()
        b,c,requests=scenario()
        result=module.assess(b,c,requests[-1],synthetic=True)
        self.assertTrue(result.tracker.events)
        self.assertTrue(all(e.observed_at==requests[-1].cutoff for e in result.tracker.events))
        self.assertTrue(all(e.trigger_interval_end<e.observed_at for e in result.tracker.events))

    def test_deep_immutability_and_determinism(self):
        module=api()
        b,c,requests=scenario()
        before=copy.deepcopy((b,c,requests))
        first=module.assess(b,c,requests[-1],synthetic=True)
        second=module.assess(b,c,requests[-1],synthetic=True)
        self.assertEqual(first,second)
        self.assertEqual((b,c,requests),before)
        with self.assertRaises(FrozenInstanceError):
            first.decision.classification="BULLISH"
        with self.assertRaises(FrozenInstanceError):
            first.tracker.events=()

    def test_decimal_context_is_isolated_and_outputs_strict_json(self):
        from dataclasses import asdict
        module=api()
        first=replay_case("bullish_reversal")[-1]
        original=repr(getcontext())
        with localcontext() as ctx:
            ctx.prec=5
            ctx.rounding=ROUND_DOWN
            second=replay_case("bullish_reversal")[-1]
        self.assertEqual(first,second)
        self.assertEqual(repr(getcontext()),original)
        json.dumps(asdict(first.decision),allow_nan=False)

    def test_independent_conflicting_symbols_and_invalid_peer(self):
        module=api()
        left=replay_case("bullish_reversal",symbol="SPY")[-1].decision
        right=replay_case("bearish_reversal",symbol="QQQ")[-1].decision
        before=copy.deepcopy((left,right))
        pair=module.compare(left,right)
        self.assertEqual(pair.state,"CONFLICT")
        self.assertEqual(pair.directions,("BULLISH","BEARISH"))
        self.assertEqual((left,right),before)
        bad=replay_case("provisional",symbol="QQQ")[-1].decision
        self.assertEqual(module.compare(left,bad).state,"PEER_DATA_UNAVAILABLE")

    def test_pair_alignment_and_state_seal_required(self):
        module=api()
        left=replay_case("bullish_reversal",symbol="SPY")[-1].decision
        right=replay_case("bullish_reversal",symbol="QQQ")[-1].decision
        self.assertEqual(module.compare(left,right).state,"AGREEMENT_BULLISH")
        with self.assertRaises(ValueError):
            module.compare(left,replace(right,at="2026-10-24T00:00:00Z"))
        with self.assertRaises(ValueError):
            module.compare(left,left)

    def test_no_import_or_modification_of_old_ema_replay_or_production(self):
        module=api()
        tree=ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        names={n.names[0].name.split(".")[0] if isinstance(n,ast.Import) else (n.module or "").split(".")[0]
               for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))}
        self.assertFalse(names & {"synthetic_replay","pinned_timezone_bridge","raccoon_scanner_successor",
                                 "moomoo","futu","sqlite3","socket","pathlib","tkinter","subprocess","os"})
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="open"
                             for n in ast.walk(tree)))

    def test_zero_range_and_zero_volatility_report_unavailable_ratios(self):
        module=api()
        b,c,requests=scenario()
        rows=tuple(replace(row,values=(10000,10000,10000,10000,100)) for row in b.observations)
        result=module.assess(reseal(b,rows),c,requests[12],synthetic=True)
        stats=dict(result.decision.measurements)
        self.assertIsNone(stats["contraction_ratio"])
        self.assertIsNone(stats["range_drift_fraction"])
        self.assertNotIn("Infinity",repr(result.decision))
        self.assertIn("ZERO_WIDTH_RANGE",result.decision.reasons)

    def test_raw_audit_mode_has_explicit_block_reason(self):
        module=api()
        b,c,requests=scenario()
        result=module.assess(b,c,replace(requests[-1],mode="RAW_AUDIT"),synthetic=True)
        self.assertEqual(result.decision.data_status,"BLOCKED")
        self.assertIn("ENGINE_READY_REQUEST_REQUIRED",result.decision.reasons)

    def test_tracker_and_decision_bind_model_version(self):
        module=api()
        b,c,requests=scenario()
        prior=module.assess(b,c,requests[12],synthetic=True)
        self.assertEqual(prior.tracker.version,module.VERSION)
        self.assertEqual(prior.decision.version,module.VERSION)
        older=replace(prior.tracker,version="OLDER_MODEL")
        older=replace(older,seal=module._tracker_seal(older))
        with self.assertRaises(ValueError):
            module.assess(b,c,requests[13],previous=older,synthetic=True)

    def test_inclusive_trend_move_threshold_is_not_rounded(self):
        module=api()
        exact=replace(module.Config(),min_move="0.07",min_efficiency="1")
        above=replace(module.Config(),min_move="0.070000000001")
        for name in ("bullish_reversal","bearish_reversal"):
            self.assertEqual(replay_case(name,exact)[12].decision.classification,"REVERSAL_WATCH")
            self.assertIn("NO_ESTABLISHED_TREND",replay_case(name,above)[12].decision.reasons)

    def test_retest_at_deadline_is_allowed(self):
        module=api()
        b,c,requests=scenario("retest_timeout")
        rows=list(b.observations)
        rows[17]=replace(rows[17],values=(9370,9410,9330,9390,100))
        b=reseal(b,rows)
        prior=None
        for request in requests[:18]:
            result=module.assess(b,c,request,previous=prior,synthetic=True)
            prior=result.tracker
        self.assertEqual(result.decision.classification,"CONFIRMED_STRUCTURAL_REVERSAL")

    def test_confirmation_closes_must_be_consecutive(self):
        module=api()
        b,c,requests=scenario("bullish_invalidated")
        rows=list(b.observations)
        rows[14]=replace(rows[14],values=(9340,9350,9330,9344,100))
        rows[15]=replace(rows[15],values=(9370,9410,9330,9390,100))
        result=module.assess(reseal(b,rows),c,requests[-1],synthetic=True)
        self.assertEqual(result.decision.classification,"REVERSAL_WATCH")
        self.assertIsNone(result.decision.direction)

    def test_invalidation_tolerance_equality_is_not_crossed(self):
        module=api()
        for name,price in (("bullish_invalidated",9324),("bearish_invalidated",10676)):
            b,c,requests=scenario(name)
            rows=list(b.observations)
            rows[-1]=replace(rows[-1],values=(price,price+20,price-20,price,100))
            result=module.assess(reseal(b,rows),c,requests[-1],synthetic=True)
            self.assertEqual(result.decision.classification,"CONFIRMED_STRUCTURAL_REVERSAL")

    def test_price_overlap_is_a_real_consolidation_requirement(self):
        module=api()
        b,c,requests=scenario()
        rows=list(b.observations)
        for i in range(5):
            price=9300+i*12
            rows[8+i]=replace(rows[8+i],values=(price,price+4,price-4,price,100))
        result=module.assess(reseal(b,rows),c,requests[12],synthetic=True)
        self.assertIn("PRICE_STRUCTURE_NOT_OVERLAPPING",result.decision.reasons)
        self.assertEqual(result.decision.classification,"INSUFFICIENT_EVIDENCE")

    def test_all_nine_direction_pairs_keep_independent_classifications(self):
        module=api()
        decisions={}
        for symbol in ("SPY","QQQ"):
            for direction,name in (("BULLISH","bullish_reversal"),("BEARISH","bearish_reversal"),
                                   (None,"bullish_reversal")):
                b,c,requests=scenario(name,symbol)
                if direction is None:
                    rows=list(b.observations)
                    for index in (13,14):
                        rows[index]=replace(rows[index],values=(9300,9340,9260,9300,100))
                    b=reseal(b,rows)
                decisions[symbol,direction]=module.assess(b,c,requests[-1],synthetic=True).decision
        for left in ("BULLISH","BEARISH",None):
            for right in ("BULLISH","BEARISH",None):
                pair=module.compare(decisions["SPY",left],decisions["QQQ",right])
                expected=("NO_CONFIRMED_DIRECTION" if left is None and right is None else
                    "SINGLE_DIRECTION" if left is None or right is None else
                    "AGREEMENT_"+left if left==right else "CONFLICT")
                self.assertEqual(pair.state,expected)
                self.assertEqual(pair.directions,(left,right))

    def test_impossible_confirmation_deadline_is_rejected(self):
        module=api()
        with self.assertRaises(ValueError):
            replay_case("bullish_reversal",replace(module.Config(),confirmation_closes=10,max_retest_bars=4))

    def test_decimal_default_traps_cannot_change_research_behavior(self):
        import decimal
        expected=replay_case("bullish_reversal")[-1]
        original=decimal.DefaultContext.traps[decimal.Inexact]
        try:
            decimal.DefaultContext.traps[decimal.Inexact]=True
            actual=replay_case("bullish_reversal")[-1]
        finally:
            decimal.DefaultContext.traps[decimal.Inexact]=original
        self.assertEqual(expected,actual)
