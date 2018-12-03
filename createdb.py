from core.taxdb import TaxDB
from core.psql import DB
from core.price import Price
from reference import get_offset, get_timestamps
from util.config import use_network
import os.path
import time


if __name__ == "__main__":

    n = use_network("ark")
    # check to see if tax.db exists, if not initialize db, etc
    if os.path.exists('tax.db') == False:
        taxdb = TaxDB(n['dbuser'])
        psql = DB(n['database'], n['dbuser'], n['dbpassword'])
        taxdb.setup()

        # setup initial delegates
        d = psql.get_delegates()
        addresses = [i[0] for i in d]
        taxdb.update_delegates(addresses)

        # get prices
        p = Price()
        t = int(time.time())
        newEpoch = get_offset(n['epoch'])
        timestamps = get_timestamps(newEpoch, t)

        for i in timestamps:
            price = [p.get_market_price(i, n['ticker'])]
            taxdb.update_prices(price)
