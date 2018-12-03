#!/usr/bin/env python
import sqlite3
import threading

lock = threading.Lock()


class TaxDB:
    def __init__(self, u):
        self.connection = sqlite3.connect('/home/'+u+'/dpos-tax/tax.db')
        self.cursor = self.connection.cursor()

    def commit(self):
        return self.connection.commit()

    def execute(self, query, args=[]):
        try:
            lock.acquire(True)
            res = self.cursor.execute(query, args)
        finally:
            lock.release()

        return res

    def executemany(self, query, args):
        try:
            lock.acquire(True)
            res = self.cursor.executemany(query, args)
        finally:
            lock.release()

        return res

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def setup(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS prices (timestamp int, usd float, eur float )")

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS delegates (address varchar(64) )")

        self.connection.commit()


    def update_prices(self, prices):
        newPrices=[]

        for p in prices:
            self.cursor.execute("SELECT timestamp FROM prices WHERE timestamp = ?", (p[0],))

            if self.cursor.fetchone() is None:
                newPrices.append((p[0], p[1], p[2]))

        self.executemany("INSERT INTO prices VALUES (?,?,?)", newPrices)

        self.commit()


    def get_prices(self):
        return self.cursor.execute("SELECT * FROM prices")


    def single_price(self, ts):
        return self.cursor.execute("SELECT * FROM prices WHERE timestamp = '{ts}'")


    def update_delegates(self, delegates):
        newDelegates=[]

        for d in delegates:
            self.cursor.execute("SELECT address FROM delegates WHERE address = ?", (d,))

            if self.cursor.fetchone() is None:
                newDelegates.append((d,))

        self.executemany("INSERT INTO delegates VALUES (?)", newDelegates)

        self.commit()

    def get_delegates(self):
        return self.cursor.execute("SELECT * FROM delegates")


    def single_delegate(self, addr):
        return self.cursor.execute("SELECT * FROM delegates WHERE address = '{addr}'")
