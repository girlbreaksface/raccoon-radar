"""Local-only OpenD reachability preflight; no broker SDK or market-data requests.

Usage (on the Windows machine running OpenD):
    python -B tools/opend_local_preflight.py

Checks only TCP connect to 127.0.0.1:11111. Does not authenticate, subscribe,
request quotes, read callbacks, write files, or use trading endpoints.
"""
import socket

HOST = "127.0.0.1"
PORT = 11111
TIMEOUT_SECONDS = 2

def check_local_opend():
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT_SECONDS):
            return True
    except (OSError, TimeoutError):
        return False

def main():
    if check_local_opend():
        print("LOCAL_PORT_REACHABLE: OpenD candidate listening on 127.0.0.1:11111")
        print("NOT_VERIFIED: process identity, SDK handshake, SPY/QQQ entitlements,")
        print("NOT_VERIFIED: timestamps, quote provenance, retention rights")
    else:
        print("LOCAL_PORT_UNREACHABLE: no TCP listener reachable on 127.0.0.1:11111")
        print("Check OpenD running, local port configuration and firewall.")
    print("NO_QUOTES_REQUESTED; NO_CALLBACKS_RECORDED; NO_ORDERS")

if __name__ == "__main__":
    main()
