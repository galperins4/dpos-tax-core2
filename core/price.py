#!/usr/bin/env python
import requests
import time

class Price:
    def __init__(self):
        self.tsyms = 'USD,EUR'
        self.url = 'https://min-api.cryptocompare.com/data/pricehistorical'

    def get_market_price(self, ts, ticker):
        # set request params
        params = {"fsym": ticker,
                  "tsyms": self.tsyms,
                  "ts": ts}

        try:
            r = requests.get(self.url, params=params)
            output = [ts, r.json()[ticker]['USD'], r.json()[ticker]['EUR']]
        except:
            output = [ts, 0, 0]
    
        time.sleep(0.25)

        return output
