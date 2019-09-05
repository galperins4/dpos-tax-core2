from core.taxdb import TaxDB
from core.psql import DB
from core.price import Price
from reference import get_offset, get_timestamps
from util.config import use_network
from util.client import Client
import os.path
import time
import sys


if __name__ == "__main__":
    option = sys.argv[1]
    n = use_network(option)
    u = Client()
    client = u.get_client(n['port'])
    # check to see if tax.db exists, if not initialize db, etc
    if os.path.exists('tax.db') == False:
        taxdb = TaxDB(n['dbuser'])
        psql = DB(n['database'], n['dbuser'], n['dbpassword'])
        taxdb.setup()

        # setup initial delegates
        '''d = psql.get_delegates()
        addresses = [i[0] for i in d]
        '''
        delegates = []
        start = 1
        d = client.delegates.all()
        counter = d['meta']['pageCount']
        while start <= counter:
            delist = client.delegates.all(page=start)
            for j in delist['data']:
                delegates.append(j['address'])
            start += 1

        taxdb.update_delegates(delegates)

        # get prices
        p = Price()
        t = int(time.time())
        newEpoch = get_offset(n['epoch'])
        timestamps = get_timestamps(newEpoch, t)

        for i in timestamps:
            price = [p.get_market_price(i, n['ticker'])]
            taxdb.update_prices(price)
