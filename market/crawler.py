import datetime
import json
import logging
import random
from itertools import combinations

import requests
from django.conf import settings

from market.utils import symbol_format_convert, SymbolFormatEnum, get_price, get_initial_price_mapping

logger = logging.getLogger("django")


def _gen_open(high, low):
    return low + random.random() * (high - low)


def _gen_high(price):
    return price * (1 + random.choice([i / 100 for i in range(1, 9)]))


def _gen_low(price):
    return price * (1 - random.choice([i / 100 for i in range(1, 9)]))


def _gen_close(high, low):
    return low + random.random() * (high - low)


def _gen_volume(v):
    return random.random() * v


def _gen_bar(ti, ts):
    _, real_open, real_high, real_low, real_close, real_volume = ti
    fake_high = _gen_high(real_high)
    fake_low = _gen_low(real_low)
    fake_open = _gen_open(fake_high, fake_low)
    fake_close = _gen_close(fake_high, fake_low)
    fake_vol = _gen_volume(real_volume)
    rec = [ts, fake_open, fake_high, fake_low, fake_close, fake_vol]
    return json.dumps(rec)


def gen_bars(ticker):
    """
    :return: a list of 10 str s
    """

    now = datetime.datetime(*datetime.datetime.now().timetuple()[:4])

    _rec = []
    for i in range(10):
        ts = int(now.timestamp() * 1000)
        _rec.append(_gen_bar(ticker, ts))
        now -= datetime.timedelta(hours=1)
    return _rec


def format_ticker(j):
    r = {}

    if not j["status"] == "ok":
        return
    ts = j["ts"]
    data = j["data"]

    open_price_mapping = get_initial_price_mapping()
    high_price_mapping = get_initial_price_mapping()
    low_price_mapping = get_initial_price_mapping()
    close_price_mapping = get_initial_price_mapping()

    for d in data:
        _symbol = d["symbol"]
        _open = d["open"]
        _high = d["high"]
        _low = d["low"]
        _close = d["close"]
        _volume = d["vol"]

        symbol = symbol_format_convert(_symbol, SymbolFormatEnum.LOWER, SymbolFormatEnum.UPPER_UNDERSCORE)

        if symbol:
            base, quote = symbol.split("_")

            open_price_mapping[quote][base] = _open
            open_price_mapping[base][quote] = 1 / _open

            high_price_mapping[quote][base] = _high
            high_price_mapping[base][quote] = 1 / _high

            low_price_mapping[quote][base] = _low
            low_price_mapping[base][quote] = 1 / _low

            close_price_mapping[quote][base] = _close
            close_price_mapping[base][quote] = 1 / _close

    for comp in list(combinations(settings.TARGET_ASSETS, 2)):
        base, quote = comp

        open_price = get_price(open_price_mapping, base, quote)
        high_price = get_price(high_price_mapping, base, quote)
        low_price = get_price(low_price_mapping, base, quote)
        close_price = get_price(close_price_mapping, base, quote)

        logger.info(f"{base}_{quote}: {open_price}")

        ticker_data = [ts, open_price, high_price, low_price, close_price, 0]

        bars = gen_bars(ticker_data)

        symbol = f"{base}_{quote}"

        r.setdefault(symbol, {
            "symbol": symbol,
            "prices": json.dumps(ticker_data),
            "bars": bars,
        })

        # base <==> quote (base as quote)
        reversed_open_price = 1 / open_price
        reversed_high_price = 1 / high_price
        reversed_low_price = 1 / low_price
        reversed_close_price = 1 / close_price

        logger.info(f"{quote}_{base}: {reversed_open_price}")

        ticker_data = [ts, reversed_open_price, reversed_high_price, reversed_low_price, reversed_close_price, 0]

        bars = gen_bars(ticker_data)

        symbol = f"{quote}_{base}"

        r.setdefault(symbol, {
            "symbol": symbol,
            "prices": json.dumps(ticker_data),
            "bars": bars,
        })

    return filter_ticker(r)


def filter_ticker(collection):
    result = []
    for quote_currency, corresponding_base_currency in settings.REQUIRED_SYMBOL_INFO:
        tmp = {
            "quote_currency": quote_currency,
            "data": []
        }
        for base_currency in corresponding_base_currency:
            symbol = f"{base_currency}_{quote_currency}"
            data = collection[symbol]
            tmp["data"].append(data)
        result.append(tmp)
    return result


def crawl_ticker():
    try:
        resp = requests.get(settings.HUOBI_TICKER_URL)
        j = resp.json()

        return format_ticker(j)
    except Exception as e:
        logger.error(e)
        return None
