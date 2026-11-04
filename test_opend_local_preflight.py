"""Offline tests for localhost-only OpenD reachability preflight."""
import unittest
from unittest.mock import patch
from tools.opend_local_preflight import check_local_opend

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

if __name__ == "__main__":
    unittest.main()
