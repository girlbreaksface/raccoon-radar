"""Invented stream identities; no provider qualification or eligible bars."""
from dataclasses import FrozenInstanceError, replace
import itertools
import unittest

from feed_isolation import Identity, Observation, isolate


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.identity = Identity('SYNTHETIC', 'fake-provider', 'fake-endpoint',
                                 'fake-schema-v1', 'NASDAQ_ONLY', 'RTH',
                                 'K_1M', 'QFQ', '2024-03-11', 'fake-factor-v1')
        self.a = Observation(self.identity, 'US.SPY', '2024-03-11 10:00:00',
                             1, b'raw-a')
        self.b = replace(self.a, sequence=2, raw=b'raw-b')

    def run_gate(self, observations=..., identity=..., **kwargs):
        return isolate((self.a, self.b) if observations is ... else observations,
                       self.identity if identity is ... else identity,
                       synthetic=True, **kwargs)

    def test_matching_stream_retains_every_observation_without_promotion(self):
        result = self.run_gate()
        self.assertEqual(result.compatibility, 'COMPATIBLE')
        self.assertEqual(result.observations, (self.a, self.b))
        self.assertEqual(result.reasons, ())
        self.assertEqual((result.status, result.finality, result.completeness),
                         ('DATA_BLOCKED', 'UNKNOWN', 'NOT_ESTABLISHED'))

    def test_each_identity_dimension_mismatch_blocks_whole_batch(self):
        for field in self.identity.__dataclass_fields__:
            with self.subTest(field=field):
                other = replace(self.identity, **{field: 'different'})
                result = self.run_gate((self.a, replace(self.b, identity=other)))
                self.assertEqual(result.compatibility, 'BLOCKED')
                self.assertEqual(result.observations, ())
                self.assertTrue(result.reasons)

    def test_unknown_or_malformed_expected_identity_blocks(self):
        for field in self.identity.__dataclass_fields__:
            for value in (None, '', ' ', 'UNKNOWN', 'UNVERIFIED', 'NOT_ESTABLISHED',
                          'unknown', 1, [], ' padded '):
                with self.subTest(field=field, value=value):
                    result = self.run_gate(identity=replace(self.identity, **{field: value}))
                    self.assertEqual(result.observations, ())
                    self.assertEqual(result.compatibility, 'BLOCKED')

    def test_identically_unknown_identities_never_establish_compatibility(self):
        unknown = replace(self.identity, adjustment_version='UNKNOWN')
        result = self.run_gate((replace(self.a, identity=unknown),), identity=unknown)
        self.assertEqual(result.compatibility, 'BLOCKED')
        self.assertEqual(result.observations, ())

    def test_no_normalization_or_same_enum_shortcut(self):
        for changes in ({'endpoint': 'history'}, {'coverage': 'CONSOLIDATED'},
                        {'adjustment_anchor': '2024-03-12'},
                        {'adjustment_version': 'fake-factor-v2'},
                        {'coverage': 'nasdaq_only'}):
            result = self.run_gate((replace(self.a, identity=replace(self.identity, **changes)),))
            self.assertEqual(result.compatibility, 'BLOCKED')

    def test_input_order_cannot_choose_which_incompatible_feed_wins(self):
        other = replace(self.b, identity=replace(self.identity, endpoint='history'))
        results = [self.run_gate(order) for order in itertools.permutations((self.a, other))]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0].observations, ())

    def test_no_dedup_sort_revision_selection_or_timestamp_shift(self):
        qqq = replace(self.a, symbol='US.QQQ', source_label='2024-03-11 16:00:00')
        raw = (self.b, qqq, self.a, self.a)
        self.assertEqual(self.run_gate(raw).observations, raw)

    def test_foreign_mode_and_missing_opt_in_block(self):
        self.assertEqual(isolate((self.a,), self.identity).compatibility, 'BLOCKED')
        for flag in (1, 'yes', None):
            self.assertEqual(isolate((self.a,), self.identity, synthetic=flag).compatibility,
                             'BLOCKED')
        live = replace(self.identity, mode='LIVE')
        self.assertEqual(self.run_gate((replace(self.a, identity=live),), identity=live).compatibility,
                         'BLOCKED')

    def test_malformed_rows_fail_closed_without_partial_output(self):
        for row in (None, {}, self.identity,
                    replace(self.a, identity={}), replace(self.a, symbol='US.IWM'),
                    replace(self.a, source_label=''), replace(self.a, sequence=True),
                    replace(self.a, sequence=0), replace(self.a, raw=bytearray(b'x')),
                    replace(self.a, raw=b'')):
            with self.subTest(row=row):
                self.assertEqual(self.run_gate((self.a, row)).observations, ())
                self.assertEqual(self.run_gate((self.a, row)).compatibility, 'BLOCKED')

    def test_bounded_immutable_typed_inputs(self):
        for rows in ([], {}, None, (), (self.a,)*5001):
            self.assertEqual(self.run_gate(rows).compatibility, 'BLOCKED')
        self.assertEqual(self.run_gate((replace(self.a, raw=b'x'*65537),)).compatibility,
                         'BLOCKED')

    def test_frozen_output_input_and_determinism(self):
        result = self.run_gate()
        self.assertEqual(result, self.run_gate())
        self.assertEqual(self.a.raw, b'raw-a')
        for obj, field, value in ((self.a, 'raw', b'new'),
                                  (self.identity, 'coverage', 'new'),
                                  (result, 'observations', ())):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, value)

    def test_invalid_identity_type_blocks(self):
        self.assertEqual(isolate((self.a,), {}, synthetic=True).compatibility, 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
