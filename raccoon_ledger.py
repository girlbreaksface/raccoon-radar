"""Manual long-option premium references. Pure Decimal arithmetic, no IO or feeds."""
import re
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, localcontext

CENT = Decimal("0.01")
NOTICE = ("REFERENCE LEVELS ONLY. Manual long-option estimate; no automatic stops, "
          "orders or alerts. Actual fills may differ. Standard 100 multiplier; "
          "adjusted contracts unsupported.")


@dataclass(frozen=True)
class Reference:
    stop_premium: Decimal
    target_premium: Decimal
    entry_cost: Decimal
    stop_pnl: Decimal
    target_pnl: Decimal
    stop_change_percent: Decimal
    target_change_percent: Decimal


def _number(value, label, maximum, *, positive=True):
    if (type(value) is not str or len(value) > 32 or
            re.fullmatch(r"[0-9]+(?:\.[0-9]{1,8})?", value.strip()) is None):
        raise ValueError(label+" must be a plain finite decimal (up to 8 decimal places).")
    number = Decimal(value.strip())
    if number > Decimal(maximum) or (number <= 0 if positive else number < 0):
        raise ValueError(label+" is outside the supported range.")
    return number


def calculate(*, premium, contracts, stop_percent="15", target_percent="20",
              tick="0.01", entry_fees="0.00", exit_fees="0.00"):
    """Long premium only; both tick levels rounded toward entry, dollars to cents.

    Fees are total position dollars, not per contract; entry cost includes entry
    fees, while each hypothetical exit P&L subtracts both entry and exit fees.
    Percentages are input hypotheses, not recommendations or execution rules.
    """
    entry = _number(premium, "Premium", "1000000")
    if (type(contracts) is not str or len(contracts) > 6 or
            re.fullmatch(r"[1-9][0-9]*", contracts.strip()) is None or
            int(contracts.strip()) > 100000):
        raise ValueError("Contracts must be a whole number from 1 to 100000.")
    count = int(contracts.strip())
    stop = _number(stop_percent, "Stop percent", "99.99999999")
    target = _number(target_percent, "Target percent", "1000")
    increment = _number(tick, "Tick", "0.10")
    if increment not in (CENT, Decimal("0.05"), Decimal("0.10")):
        raise ValueError("Choose a manual tick of 0.01, 0.05 or 0.10.")
    fees = [_number(v, label, "100000000", positive=False)
            for v, label in ((entry_fees, "Entry fees"), (exit_fees, "Exit fees"))]
    with localcontext(Context(prec=50, rounding=ROUND_HALF_UP)):
        if any(v != v.quantize(CENT) for v in fees):
            raise ValueError("Fees must use whole cents.")
        if entry % increment:
            raise ValueError("Premium must be a multiple of the chosen manual tick.")
        raw_stop = entry * (1-stop/100)
        raw_target = entry * (1+target/100)
        stop_price = (raw_stop/increment).to_integral_value(rounding=ROUND_CEILING)*increment
        target_price = (raw_target/increment).to_integral_value(rounding=ROUND_FLOOR)*increment
        if not Decimal(0) < stop_price < entry < target_price:
            raise ValueError("Reference levels collapse at this tick; adjust percentages or tick.")
        money = lambda value: value.quantize(CENT, rounding=ROUND_HALF_UP)
        return Reference(
            money(stop_price), money(target_price), money(entry*100*count+fees[0]),
            money((stop_price-entry)*100*count-sum(fees)),
            money((target_price-entry)*100*count-sum(fees)),
            money((stop_price/entry-1)*100), money((target_price/entry-1)*100))


def _dollars(value, *, signed=False):
    prefix = "-" if value < 0 else "+" if signed and value > 0 else ""
    return prefix+"$"+format(value.copy_abs(), ",.2f")


def calculator_view(values):
    """Fresh display on every edit; invalid inputs cannot leave old levels visible."""
    view = dict(valid=False, stop="—", target="—", entry_cost="—", error="",
                notice=NOTICE,
                fee_basis="P&L includes entered total entry + exit fees. No spread/slippage model.")
    try:
        result = calculate(**values)
    except ValueError as error:
        view["error"] = str(error)
        return view
    view.update(valid=True, entry_cost=_dollars(result.entry_cost),
                stop=(_dollars(result.stop_premium)+"  ·  "+
                      format(result.stop_change_percent, "+.2f")+"%  ·  est. P&L "+
                      _dollars(result.stop_pnl, signed=True)),
                target=(_dollars(result.target_premium)+"  ·  "+
                        format(result.target_change_percent, "+.2f")+"%  ·  est. P&L "+
                        _dollars(result.target_pnl, signed=True)))
    return view
