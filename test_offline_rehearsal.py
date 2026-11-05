import copy
import json
from pathlib import Path
import tempfile
import unittest
from offline_rehearsal import evidence, rehearsal, validate_evidence
from unified_readiness import certify, foundation_check
from durable_daily_risk import digest
from broker_history_provenance import probe
from test_paper_account_reconciliation import fake_sdk


class RehearsalTests(unittest.TestCase):
    def test_full_portfolio_restart_and_independent_pnl(self):
        r=rehearsal()
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['risk']['realized_cents'],str(2*(2400-2000-2*65)))
        self.assertEqual(r['risk']['trades'],2)
        self.assertEqual(r['risk']['positions'],{})
        self.assertEqual(r['reconciliation']['reasons'],[])
        self.assertTrue(all(s['restart_receipt']['count']>0 for s in r['stages']))

    def test_negative_paths_and_determinism(self):
        for s in ('gap','stale','mismatch'):
            r=rehearsal(s)
            self.assertEqual(r['status'],'BLOCKED')
            self.assertEqual(r,rehearsal(s))
        self.assertIn('MISSING_EXPECTED_ORDER',rehearsal('mismatch')['reconciliation']['reasons'])

    def test_rehashed_tampering_cannot_pass(self):
        r=evidence(); r['reports']['baseline']['risk']['realized_cents']='999'
        r['report_hash']=digest(r['reports'])
        with self.assertRaises(ValueError): validate_evidence(r)

    def test_certification_never_releases_gates(self):
        r=certify()
        self.assertEqual(r['report_hash'],digest({k:v for k,v in r.items() if k!='report_hash'}))
        self.assertEqual(r['status'],'HOLD'); self.assertEqual(r['orders'],'DISABLED')
        self.assertTrue(all(g['status']=='HOLD' for g in r['gates']))

    def test_missing_or_tampered_foundation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            with self.assertRaises(FileNotFoundError): foundation_check(p)
            (p/'readiness.json').write_text(json.dumps({'source_sha256':{}}))
            with self.assertRaises(ValueError): foundation_check(p)

    def test_foundation_cannot_omit_all_hashed_evidence(self):
        from automation_foundation import COMMANDS
        from unified_readiness import sources
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            report = dict(source_sha256=sources(), environment={},
                repository_verification={k:dict(status='PASS', exit_code=0) for k in COMMANDS})
            (p/'readiness.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError): foundation_check(p)

    def test_foundation_requires_each_expected_file_and_hash(self):
        from automation_foundation import COMMANDS, ARTIFACT_SUITES
        from unified_readiness import sources, file_hash
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            rows = {}
            for key in COMMANDS:
                row = dict(status='PASS', exit_code=0)
                kinds = {'log': '.txt'}
                if key in ARTIFACT_SUITES: kinds['artifact'] = '.json'
                for kind, suffix in kinds.items():
                    path = p/(key+suffix)
                    path.write_text('synthetic integrity fixture')
                    row[kind], row[kind+'_sha256'] = path.name, file_hash(path)
                rows[key] = row
            report = dict(source_sha256=sources(), environment={}, repository_verification=rows)
            def check(value):
                (p/'readiness.json').write_text(json.dumps(value))
                return foundation_check(p)
            self.assertEqual(check(report)['status'], 'PASS')
            for key, row in rows.items():
                for field in ('log', 'log_sha256', *(['artifact', 'artifact_sha256'] if key in ARTIFACT_SUITES else [])):
                    bad = copy.deepcopy(report)
                    del bad['repository_verification'][key][field]
                    with self.subTest(key=key, field=field), self.assertRaises(ValueError): check(bad)
            for value in ('../root.txt', 'feed.txt', '/root.txt'):
                bad = copy.deepcopy(report)
                bad['repository_verification']['root']['log'] = value
                with self.assertRaises(ValueError): check(bad)
            (p/'root.txt').write_text('changed')
            with self.assertRaises(ValueError): check(report)
            (p/'root.txt').unlink()
            with self.assertRaises(FileNotFoundError): check(report)

    def test_broker_probe_mismatch_cannot_call_history(self):
        sdk,calls=fake_sdk()
        r=probe(sdk,'0'*64,'2026-11-04','2026-11-05')
        self.assertIn('QUERY_OR_SCOPE_UNVERIFIED',r['reasons'])
        self.assertEqual(r['query_trace'],['get_acc_list'])
        self.assertTrue(r['close_confirmed'])


if __name__=='__main__': unittest.main()
