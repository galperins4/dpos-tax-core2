#!/usr/bin/env python
from core.psql import DB
from core.taxdb import TaxDB
from core.price import Price
from util.config import use_network
import time
import sys


day = 86400

def get_offset(e):
    offset = 0
    while ((e+offset) % day) != 0:
        offset += 1

    return (e+offset)


def get_timestamps(first, ts):
    l = []

    while first <= ts:
        l.append(first)
        first += day

    return l

if __name__ == '__main__':
    option = sys.argv[1]
    n = use_network(option)
    psql = DB(n['database'], n['dbuser'], n['dbpassword'])
    taxdb = TaxDB(n['dbuser'])

    # update delegate list
    d = psql.get_delegates()
    addresses = [i[0] for i in d]
    taxdb.update_delegates(addresses)

    # pull prices from database and get last one
    db_prices = taxdb.get_prices().fetchall()
    newEpoch = db_prices[-1][0]

    # add new prices
    p = Price()
    t = int(time.time())

    timestamps = get_timestamps(newEpoch, t)

    for i in timestamps:
        price = [p.get_market_price(i, n['ticker'])]
        taxdb.update_prices(price)












