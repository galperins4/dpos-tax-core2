#!/usr/bin/env python
import datetime
import requests
import time

class Price:
    def __init__(self):
        self.tsyms = 'USD,EUR'
        self.url = 'https://min-api.cryptocompare.com/data/pricehistorical'
        self.tick_convert = {'PRSN':'persona', 'XQR':'qredit', 'XPH':'phantom', 'BIND':'nos'}

    def get_market_price(self, ts, ticker):
        if ticker in ['XQR', 'PRSN', 'XPH', 'BIND']:
            output = self.coin_gecko(ts, ticker)         
        else:
            # set request params
            params = {"fsym": ticker,
                      "tsyms": self.tsyms,
                      "ts": ts}
            try:
                r = requests.get(self.url, params=params)
                output = [ts, r.json()[ticker]['USD'], r.json()[ticker]['EUR']]
            except:
                output = [ts, 0, 0]
    
        time.sleep(1)
        return output

    
    def coin_gecko(self, stamp, t):
        new_ticker = self.tick_convert[t]
        new_ts = datetime.datetime.fromtimestamp(stamp).strftime('%d-%m-%Y')
        url = 'https://api.coingecko.com/api/v3/coins/'+new_ticker+'/history?date='+new_ts
        
        try:
            r = requests.get(url)
            output = [stamp, r.json()['market_data']['current_price']['usd'], r.json()['market_data']['current_price']['eur']]
        except:
            output = [stamp, 0, 0]  

        return output
