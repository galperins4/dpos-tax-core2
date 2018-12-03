#!/usr/bin/env python
import psycopg2


class DB:
    def __init__(self, db, u, pw):
        self.connection = psycopg2.connect(
            dbname=db,
            user=u,
            password=pw,
            host='localhost',
            port='5432'
        )

        self.cursor = self.connection.cursor()

    def get_transactions(self, account, side):
        try:
            if side == "buy":
                self.cursor.execute(f"""SELECT "timestamp", "amount", "fee", "sender_public_key", "id" FROM transactions WHERE "recipient_id" = '{
                account}' AND "type" = {0} ORDER BY "timestamp" ASC""")
            else:
                self.cursor.execute(f"""SELECT "timestamp", "amount", "fee", "recipient_id", "id" FROM transactions WHERE "sender_public_key" = '{
                account}'ORDER BY "timestamp" ASC""")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)

    def get_delegates(self):
        try:
            self.cursor.execute(f"""SELECT "address" from wallets WHERE "username" is NOT NULL""")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)
