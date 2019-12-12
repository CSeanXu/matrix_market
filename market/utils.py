from collections import defaultdict
from enum import Enum

from django.conf import settings


class SymbolFormatEnum(Enum):
    UPPER_UNDERSCORE = 1
    LOWER_UNDERSCORE = 2
    LOWER = 3


def symbol_format_convert(s, from_format: SymbolFormatEnum, to_format: SymbolFormatEnum):
    if from_format is SymbolFormatEnum.UPPER_UNDERSCORE and to_format is SymbolFormatEnum.LOWER:
        return ''.join(s.split('_')).lower()
    elif (from_format is SymbolFormatEnum.LOWER and
          to_format in [SymbolFormatEnum.LOWER_UNDERSCORE, SymbolFormatEnum.UPPER_UNDERSCORE]):
        # it's unknown how many chars are there for quote currency
        # try all 3 possibilities
        base = None
        for cur_base in ['btc', 'eth', 'usdt']:
            if s.endswith(cur_base):
                base = cur_base
                break
        if base is not None:
            result = s[:len(s) - len(base)] + '_' + base
            return result if to_format is SymbolFormatEnum.LOWER_UNDERSCORE else result.upper()
        else:
            return None


def get_initial_price_mapping():
    _mapping = defaultdict(dict)

    _mapping["USDT"]["USD"] = settings.USDT_USD_EXCHANGE_RATE
    _mapping["USDT"]["AED"] = settings.USDT_AED_EXCHANGE_RATE

    _mapping["AED"]["USDT"] = 1 / settings.USDT_AED_EXCHANGE_RATE
    _mapping["USD"]["USDT"] = 1 / settings.USDT_USD_EXCHANGE_RATE

    return _mapping


def get_price(mapping, base, quote):
    p = mapping.get(quote, {}).get(base, None)

    if not p:
        for quote_currency, base_price_mapping in mapping.items():
            if base in base_price_mapping and quote in base_price_mapping:
                # print(f"{base} {quote} have same quote currency: {base}_{quote_currency} {quote}_{quote_currency}")
                # print(f"base_price_mapping[base] / base_price_mapping[quote] ==> {base_price_mapping[base]} / {base_price_mapping[quote]}")
                p = base_price_mapping[base] / base_price_mapping[quote]
                break

    return p
