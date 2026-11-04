"""One reviewed paper connectivity round trip. Never a strategy or live gateway.

Only the injected SDK SIMULATE environment is used, with an explicitly verified
account. No unlock, market orders, retry of submissions or background trading.
The caller must supply a fresh verified quote and an exclusively created journal.
"""
import hashlib
import json
import os

CONTRACT = 'US.SPY261105C777000'


def execute_pilot(sdk, context, journal_path, *, verified_quote, pause,
                  expected_fingerprint, reviewed=False, kill_switch=None):
    """Reviewed Nov 4 pilot only; .20 BUY, .01 close limit; at most two submissions.

    An uncertain submission consumes the exclusive journal; never rerun it.
    A remaining position/order requires manual paper-account reconciliation.
    verified_quote is a callable returning False on any stale/unknown input.
    kill_switch must return exactly False to permit entry. Missing/failed state
    blocks entry; an active switch does not veto the verified long-only close.
    This entry interlock does not monitor or cancel an already pending order.
    """
    def entry_enabled():
        # Missing, failed or non-boolean state never authorizes new exposure.
        try:
            return callable(kill_switch) and kill_switch() is False
        except Exception:
            return False

    if not entry_enabled():
        raise ValueError('Verified inactive kill switch required')
    if reviewed is not True or verified_quote() is not True:
        raise ValueError('Reviewed pilot and current verified quote required')
    if (type(expected_fingerprint) is not str or len(expected_fingerprint) != 64
            or any(c not in '0123456789abcdef' for c in expected_fingerprint)):
        raise ValueError('Explicit reviewed paper-account fingerprint required')
    code, frame = context.get_acc_list()
    if code != sdk.RET_OK:
        raise RuntimeError('Account query failed')
    eligible = [r for r in frame.to_dict('records')
        if r.get('trd_env') == sdk.TrdEnv.SIMULATE
        and r.get('sim_acc_type') == sdk.SimAccType.STOCK_AND_OPTION
        and r.get('acc_status') == sdk.TrdAccStatus.ACTIVE
        and sdk.TrdMarket.US in r.get('trdmarket_auth', [])
        and type(r.get('acc_id')) is int and r['acc_id'] > 0
        and hashlib.sha256(('raccoon-paper-account:' + str(r['acc_id'])).encode()).hexdigest() == expected_fingerprint]
    if len(eligible) != 1:
        raise ValueError('Exact active paper account required')
    account = eligible[0]['acc_id']
    kwargs = dict(trd_env=sdk.TrdEnv.SIMULATE, acc_id=account)

    def query(method, **extra):
        ret, data = getattr(context, method)(**kwargs, refresh_cache=True, **extra)
        if ret != sdk.RET_OK:
            raise RuntimeError('Paper reconciliation failed')
        return data.to_dict('records')

    if query('position_list_query') or query('order_list_query'):
        raise ValueError('Pilot requires an empty paper account')
    # Exclusive marker is durable before any externally visible submission.
    with open(journal_path, 'x', encoding='utf-8') as journal:
        parent = ''
        def log(state, **details):
            nonlocal parent
            row = dict(state=state, contract=CONTRACT, environment='SIMULATE',
                       account_fingerprint=expected_fingerprint, parent=parent, **details)
            parent = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            journal.write(json.dumps(dict(row, hash=parent), sort_keys=True) + '\n')
            journal.flush()
            os.fsync(journal.fileno())

        def submit(side, price):
            # Re-read account classification immediately before every submission.
            ret, rows = context.get_acc_list()
            matched = [] if ret != sdk.RET_OK else [
                r for r in rows.to_dict('records') if r.get('acc_id') == account]
            if (len(matched) != 1
                    or matched[0].get('trd_env') != sdk.TrdEnv.SIMULATE
                    or matched[0].get('acc_status') != sdk.TrdAccStatus.ACTIVE
                    or matched[0].get('sim_acc_type') != sdk.SimAccType.STOCK_AND_OPTION
                    or sdk.TrdMarket.US not in matched[0].get('trdmarket_auth', [])):
                raise RuntimeError('Paper account changed')
            if side == sdk.TrdSide.BUY and not entry_enabled():
                log('ENTRY_KILLED')
                raise RuntimeError('Kill switch blocked entry')
            log('SUBMIT_INTENT', side=side, price=price, quantity=1)
            ret, data = context.place_order(price=price, qty=1, code=CONTRACT,
                trd_side=side, order_type=sdk.OrderType.NORMAL, adjust_limit=0,
                time_in_force=sdk.TimeInForce.DAY, fill_outside_rth=False,
                remark='RRPAPER20261104', **kwargs)
            if ret != sdk.RET_OK:
                log('SUBMISSION_UNCERTAIN', side=side)
                raise RuntimeError('No retry: inspect paper account before further action')
            rows = data.to_dict('records')
            if len(rows) != 1 or not rows[0].get('order_id'):
                raise RuntimeError('Order acknowledgement ambiguous; no retry')
            order = str(rows[0]['order_id'])
            log('ACKNOWLEDGED', side=side, order_id=order)
            return order

        def wait(order):
            for _ in range(15):
                # Broker permits ten order queries per thirty seconds. Four
                # seconds also leaves headroom for final reconciliation.
                pause(4)
                rows = query('order_list_query', order_id=order)
                if len(rows) != 1:
                    raise RuntimeError('Order reconciliation ambiguous')
                row = rows[0]
                if row.get('order_status') == sdk.OrderStatus.FILLED_ALL and float(row.get('dealt_qty', 0)) == 1:
                    log('FILLED', order_id=order, price=str(row.get('dealt_avg_price')))
                    return True
            return False

        try:
            log('REVIEWED_PILOT', max_entry_premium=20, immediate_close=True)
            if verified_quote() is not True:
                raise ValueError('Quote expired before submission')
            entry = submit(sdk.TrdSide.BUY, .20)
            if not wait(entry):
                ret, _ = context.modify_order(sdk.ModifyOrderOp.CANCEL, entry,
                    qty=0, price=0, adjust_limit=0, **kwargs)
                log('ENTRY_CANCEL_REQUESTED', acknowledged=ret == sdk.RET_OK)
                # A late fill must be reconciled before deciding to close.
                rows = query('position_list_query', code=CONTRACT)
                if not rows:
                    log('ENTRY_UNFILLED_RECONCILE_REQUIRED')
                    return 'RECONCILE_REQUIRED'
            rows = query('position_list_query', code=CONTRACT)
            if len(rows) != 1 or float(rows[0].get('qty', 0)) != 1 or float(rows[0].get('can_sell_qty', 0)) != 1:
                raise RuntimeError('Expected exactly one sellable long paper contract')
            exit_order = submit(sdk.TrdSide.SELL, .01)
            if not wait(exit_order):
                log('EXIT_PENDING_REVIEW_REQUIRED', order_id=exit_order)
                return 'EXIT_PENDING'
            positions = query('position_list_query', code=CONTRACT)
            if any(float(r.get('qty', 0)) != 0 for r in positions):
                raise RuntimeError('Paper position remains after exit fill')
            log('ROUND_TRIP_COMPLETE', integration='HOLD', live_trading='NO-GO')
            return 'ROUND_TRIP_COMPLETE'
        except BaseException:
            log('HALTED_RECONCILE_REQUIRED')
            raise
