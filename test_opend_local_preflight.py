"""Offline tests for localhost-only OpenD reachability preflight."""
import errno
from importlib.metadata import PackageNotFoundError
import unittest
from unittest.mock import patch
from tools.opend_local_preflight import Diagnostic, check_local_opend, diagnose_opend

class LocalPreflightTests(unittest.TestCase):
    def test_connect_success_closes_socket(self):
        class FakeSocket:
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with patch("tools.opend_local_preflight.socket.create_connection", return_value=FakeSocket()) as connect:
            self.assertTrue(check_local_opend())
            connect.assert_called_once_with(("127.0.0.1", 11111), timeout=2)

    def test_connection_failure_is_not_reported_as_success(self):
        with patch("tools.opend_local_preflight.socket.create_connection", side_effect=OSError("closed")):
            self.assertFalse(check_local_opend())

    @patch("tools.opend_local_preflight.version", return_value="1.2.3")
    @patch("tools.opend_local_preflight.socket.create_connection")
    def test_reachable_reports_sdk_and_closes_socket(self, connect, version):
        result = diagnose_opend(12345)
        self.assertIsInstance(result, Diagnostic)
        self.assertEqual(result.status, "REACHABLE")
        self.assertEqual(result.sdk_version, "1.2.3")
        self.assertIn("handshake unverified", result.describe())
        connect.assert_called_once_with(("127.0.0.1", 12345), timeout=2)
        connect.return_value.__exit__.assert_called_once()
        version.assert_called_once_with("moomoo-api")

    @patch("tools.opend_local_preflight.version", side_effect=PackageNotFoundError)
    @patch("tools.opend_local_preflight.socket.create_connection")
    def test_faults_and_missing_sdk(self, connect, version):
        for error, expected in ((ConnectionRefusedError(errno.ECONNREFUSED, "refused"), "REFUSED"),
                                (TimeoutError("slow"), "TIMEOUT"),
                                (OSError(errno.EACCES, "blocked"), "SOCKET_ERROR")):
            with self.subTest(status=expected):
                connect.side_effect = error
                result = diagnose_opend()
                self.assertEqual(result.status, expected)
                self.assertIsNone(result.sdk_version)
                self.assertIn("Market data unverified", result.describe())

    @patch("tools.opend_local_preflight.socket.create_connection")
    def test_invalid_ports_are_rejected_before_connecting(self, connect):
        for port in (0, -1, 65536, "remote"):
            with self.assertRaises(ValueError):
                diagnose_opend(port)
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
