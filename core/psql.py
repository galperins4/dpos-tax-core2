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
            if side == "Income":
                self.cursor.execute(f"""SELECT "timestamp", "amount", "fee", "sender_public_key", "id" FROM transactions WHERE "recipient_id" = '{
                account}' AND "type" = {0} ORDER BY "timestamp" ASC""")
            else:
                self.cursor.execute(f"""SELECT "timestamp", "amount", "fee", "recipient_id", "id" FROM transactions WHERE "sender_public_key" = '{
                account}'ORDER BY "timestamp" ASC""")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)

    def get_all_multi(self):
        # get all multi-payments universe
        try:
            self.cursor.execute(f"""SELECT "timestamp", "fee", "sender_public_key", "asset", "id" FROM transactions WHERE "type" = 6 order by "timestamp" DESC""")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)
    
    def get_multi_tx(self, account, side, universe):
        try:
            acct_multi=[]
            if side == "Income":
                for i in universe:
                    for j in i[3]['payments']:
                        if j['recipientId'] == account:
                            tmp = (i[0], int(j['amount']), i[1], i[2], i[4])
                            acct_multi.append(tmp)
            else:
                # need to figure out how to get fee and divide across transactions
                for i in universe:
                    if i[2] == account:
                        multi_count = len(i[3]['payments'])
                        print("total fee", i[1])
                        fee = int(i[1] / multi_count)
                        print("fee per tx", fee)
                        quit()
                        for j in i[3]['payments']:
                            tmp = (i[0], int(j['amount']), i[1], j['recipientId'], i[4])
                            acct_multi.append(tmp)            
                quit()
            return acct_multi
        except Exception as e:
            print(e)
            
            
    def get_delegates(self):
        try:
            self.cursor.execute(f"""SELECT "address" from wallets WHERE "username" is NOT NULL""")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)
