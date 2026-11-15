"""Read-only OpenD diagnostics for IPv4 loopback."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import errno
from importlib.metadata import PackageNotFoundError, version
import socket
from time import monotonic

HOST = "127.0.0.1"
PORT = 11111
TIMEOUT_SECONDS = 2


@dataclass(frozen=True)
class Diagnostic:
    port: int
    status: str
    checked_at: datetime
    elapsed_ms: int
    sdk_version: str | None
    error_code: int | None

    def describe(self):
        explanation = {
            "REACHABLE": "TCP listener reached. OpenD identity and handshake unverified.",
            "REFUSED": "Connection refused. Check whether OpenD is running and verify its configured port.",
            "TIMEOUT": "Connection timed out. Check the local firewall and OpenD settings.",
            "SOCKET_ERROR": f"Socket check failed (error {self.error_code}). Check local networking.",
        }[self.status]
        sdk = self.sdk_version or "not installed in this Python environment"
        return (f"{HOST}:{self.port} · {self.status} · {self.elapsed_ms} ms\n"
                f"{explanation}\n"
                f"Python moomoo-api: {sdk}\n"
                f"Checked {self.checked_at:%Y-%m-%d %H:%M:%S} UTC · Market data unverified")


def port_number(value):
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    return port


def _probe(port):
    began = monotonic()
    error_code = None
    try:
        with socket.create_connection((HOST, port), timeout=TIMEOUT_SECONDS):
            status = "REACHABLE"
    except OSError as exc:
        error_code = getattr(exc, "winerror", None) or exc.errno
        if isinstance(exc, ConnectionRefusedError) or error_code in (errno.ECONNREFUSED, 10061):
            status = "REFUSED"
        elif isinstance(exc, TimeoutError) or error_code in (errno.ETIMEDOUT, 10060):
            status = "TIMEOUT"
        else:
            status = "SOCKET_ERROR"
    return status, round((monotonic() - began) * 1000), error_code


def diagnose_opend(port=PORT):
    port = port_number(port)
    status, elapsed, error = _probe(port)
    checked = datetime.now(timezone.utc)
    try:
        sdk = version("moomoo-api")
    except PackageNotFoundError:
        sdk = None
    return Diagnostic(port, status, checked, elapsed, sdk, error)


def check_local_opend():
    """Compatibility wrapper for callers that only need TCP reachability."""
    return _probe(PORT)[0] == "REACHABLE"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=port_number, default=PORT)
    args = parser.parse_args()
    result = diagnose_opend(args.port)
    # ASCII output also works in Windows consoles with legacy encodings.
    print(result.describe().replace("·", "|"))
    print("NO_HANDSHAKE; NO_QUOTES_REQUESTED; NO_ORDERS")
    return 0 if result.status == "REACHABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
