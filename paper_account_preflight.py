"""Read-only localhost paper-account discovery. No unlock or order operations.

Run explicitly in the isolated environment: python -B paper_account_preflight.py
Only redacted account metadata is emitted. SDK imports are lazy for offline CI.
"""
import hashlib
import json
from importlib.metadata import version


def inspect_accounts(sdk):
    context = sdk.OpenSecTradeContext(filter_trdmarket=sdk.TrdMarket.US,
        host='127.0.0.1', port=11111, security_firm=sdk.SecurityFirm.FUTUINC)
    try:
        code, frame = context.get_acc_list()
        if code != sdk.RET_OK:
            # Provider error strings can contain account details; do not log them.
            return {'status': 'ACCOUNT_QUERY_FAILED', 'paper_accounts': []}
        rows = frame.to_dict('records')
        accounts, eligible_ids = [], []
        for row in rows:
            if (row.get('trd_env') != sdk.TrdEnv.SIMULATE
                    or row.get('sim_acc_type') != sdk.SimAccType.STOCK_AND_OPTION
                    or row.get('acc_status') != sdk.TrdAccStatus.ACTIVE
                    or sdk.TrdMarket.US not in row.get('trdmarket_auth', [])):
                continue
            account = row.get('acc_id')
            if type(account) is not int or account <= 0:
                continue
            eligible_ids.append(account)
            accounts.append({'account_fingerprint': hashlib.sha256(
                ('raccoon-paper-account:' + str(account)).encode()).hexdigest(),
                'environment': 'SIMULATE', 'type': 'STOCK_AND_OPTION',
                'market': 'US', 'status': 'ACTIVE'})
        result = {'status': 'PAPER_ACCOUNT_FOUND' if len(accounts) == 1 else
                'AMBIGUOUS_PAPER_ACCOUNTS' if accounts else 'NO_ELIGIBLE_PAPER_ACCOUNT',
                'paper_accounts': accounts}
        if len(accounts) == 1:
            result['paper_state'] = {}
            for name in ('position_list_query', 'order_list_query'):
                ret, data = getattr(context, name)(trd_env=sdk.TrdEnv.SIMULATE,
                    acc_id=eligible_ids[0], refresh_cache=True)
                result['paper_state'][name] = {'available': ret == sdk.RET_OK,
                    'row_count': len(data) if ret == sdk.RET_OK else None}
        return result
    finally:
        context.close()


def main():
    import moomoo
    result = inspect_accounts(moomoo)
    result.update(sdk_version=version('moomoo-api'), integration='HOLD',
                  live_trading='NO-GO', orders='DISABLED',
                  external_paper_orders='REVIEW_REQUIRED')
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
