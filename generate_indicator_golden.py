"""Independent rational closed-form oracle; never imports production calculations.

EMA = seed*q**k + alpha*sum(close[j]*q**(last-j)).
Exact Fraction arithmetic, no recursive EMA update. Output is a reviewed static fixture.
"""
from fractions import Fraction as F
import json
from pathlib import Path


def golden():
    output = {}
    for count in (101, 120, 405):
        closes = [F(101+i%7) for i in range(count)]
        result = {}
        for n in (9, 21):
            q = F(n-1, n+1)
            value = sum(closes[:n])/n*q**(count-n) + (1-q)*sum(
                closes[j]*q**(count-1-j) for j in range(n, count))
            result['ema'+str(n)] = [str(value.numerator), str(value.denominator)]
        indices = range(390, count) if count == 405 else range(count)
        prices = [(F(302+3*(i%7), 3), F(1+i%11)) for i in indices]
        vwap = sum(p*v for p,v in prices)/sum(v for p,v in prices)
        result['vwap'] = [str(vwap.numerator), str(vwap.denominator)]
        output[str(count)] = result
    return output


if __name__ == '__main__':
    destination = Path(__file__).parent / 'fixtures' / 'production_indicator_golden.json'
    destination.parent.mkdir(exist_ok=True)
    with destination.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(golden(), indent=2, sort_keys=True)+'\n')
