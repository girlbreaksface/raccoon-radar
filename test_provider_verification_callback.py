"""Execute actual worker methods with fake SDK/clock/paths; no GUI or OpenD."""
import ast
import json
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch


def dashboard_method(name):
    source = Path(__file__).with_name("raccoon_dashboard_v1_5_14.py")
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    dashboard = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                     and n.name == "Dashboard")
    method = next(n for n in dashboard.body if isinstance(n, ast.FunctionDef)
                  and n.name == name)
    namespace = {"datetime": datetime, "__file__": str(source)}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"),
         namespace)
    return namespace[name], namespace


class ProviderVerificationErrorTests(unittest.TestCase):
    def setUp(self):
        self.worker, self.namespace = dashboard_method("_verify_provider_worker")
        self.callbacks = []
        self.messages = []
        self.dashboard = types.SimpleNamespace(
            after=lambda delay, callback: self.callbacks.append(callback),
            _opening_feed_done=self.messages.append, candle_busy=True)
        self.sdk = types.ModuleType("moomoo")
        self.sdk.RET_OK = 0
        self.sdk.KLType = types.SimpleNamespace(K_1M="synthetic-minute")
        self.sdk.AuType = types.SimpleNamespace(QFQ="synthetic-adjustment")
        self.context = Mock()
        self.context.request_history_kline.return_value = (1, "synthetic unavailable", None)
        self.context.get_cur_kline.return_value = (1, "synthetic unavailable")
        self.sdk.OpenQuoteContext = Mock(return_value=self.context)
        self.zones = types.ModuleType("zoneinfo")
        self.zones.ZoneInfo = lambda name: timezone.utc
        self.sdk_patch = patch.dict("sys.modules",
                                    {"moomoo": self.sdk, "zoneinfo": self.zones})
        self.sdk_patch.start()
        self.addCleanup(self.sdk_patch.stop)

    def drain_after_worker_returns(self):
        # Emulate Tk dispatch after Python has cleared the except variable.
        self.worker(self.dashboard)
        for callback in self.callbacks:
            callback()
        self.assertFalse(self.dashboard.candle_busy)

    def test_context_error_survives_deferred_dispatch(self):
        self.sdk.OpenQuoteContext.side_effect = RuntimeError("synthetic connect failure")
        self.drain_after_worker_returns()
        self.assertEqual(self.messages, [
            "Provider verification failed: RuntimeError: synthetic connect failure"])
        self.context.close.assert_not_called()

    def test_report_error_is_delivered_and_context_closed(self):
        self.namespace["Path"] = Mock(side_effect=OSError("synthetic output failure"))
        self.drain_after_worker_returns()
        self.assertEqual(self.messages, [
            "Provider verification failed: OSError: synthetic output failure"])
        self.context.close.assert_called_once_with()

    def test_read_only_summary_success_still_dispatches(self):
        output = Mock()
        output.resolve.return_value = output
        output.parent = output
        output.__truediv__ = Mock(return_value=output)
        self.namespace["Path"] = Mock(return_value=output)
        self.drain_after_worker_returns()
        report = json.loads(output.write_text.call_args.args[0])
        self.assertTrue(report["read_only"])
        self.assertTrue(report["no_database_writes"])
        self.assertTrue(report["no_timestamp_shift"])
        self.assertIn("No candles modified.", self.messages[0])
        self.context.close.assert_called_once_with()

    def test_busy_request_does_not_start_another_worker(self):
        method, namespace = dashboard_method("verify_provider_candles")
        namespace["threading"] = Mock()
        self.dashboard.note = Mock()
        method(self.dashboard)
        namespace["threading"].Thread.assert_not_called()
        self.dashboard.note.set.assert_called_once_with(
            "Another candle request is in progress.")


if __name__ == "__main__":
    unittest.main()
