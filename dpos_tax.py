#!/usr/bin/env python
from flask import Flask, jsonify, request
from flask_cors import CORS
from core.taxdb import TaxDB
from core.psql import DB
import csv
import datetime
from network.network import Network
from util.config import use_network
from crypto.identity.address import address_from_public_key
from crypto.configuration.network import set_custom_network


acct = [""]
exchange_acct = {"ark":["AUexKjGtgsSpVzPLs6jNMM6vJ6znEVTQWK", 
                        "AFrPtEmzu6wdVpa2CnRDEKGQQMWgq8nE9V",
                        "ARXhacG5MPdT1ehWPTPo8jtfC5NrS29eKS",
                        "AJbmGnDAx9y91MQCDApyaqZhn6fBvYX9iJ",
                        "AcVHEfEmFJkgoyuNczpgyxEA3MZ747DRAu",
                        "ANQftoXeWoa9ud9q9dd2ZrUpuKinpdejAJ",
                        "AdA5THjiVFAWhcMo5QyTKF1Y6d39bnPR2F"]}
exceptions = [""]
n = None
taxdb = None
psql = None
network = None
atomic = 100000000
year = 86400 * 365
app = Flask(__name__)
CORS(app)


@app.route("/api", methods=['POST'])
def tax():
    try:
        global acct
        global exceptions
        global n
        global network
        global taxdb
        global psql
               
        # get addresses and exceptions
        req_data = request.get_json()
        acct = [i for i in req_data['addresses']]
        exceptions = [i for i in req_data["exceptions"]]
        network = req_data['network']
        
        n = use_network(network)        
        net = Network(network)
        build_network(net)
        taxdb = TaxDB(n['dbuser'])
        psql = DB(n['database'], n['dbuser'], n['dbpassword'])
        out_buy, out_sell, out_summary = process_taxes(acct)
        quit()
        buy_cols = ['tax lot', 'timestamp', 'buy amount', 'price', 'market value', 'tx type', 'datetime', 'lot status', 'remaining_qty', 'senderId']
        sell_cols = ['timestamp', 'sell amount', 'price', 'market value', 'datetime', 'short term', 'long term', 'recipientId']
        summary_cols = ['year', 'income', 'short term', 'long term']
        acctDict = {"Buys": {"columns": buy_cols, "data":out_buy},
                    "Sells": {"columns": sell_cols, "data":out_sell},
                    "Summary": {"columns": summary_cols, "data":out_summary}
                   }
        return jsonify(acctDict)
    
    except Exception as e:
        print(e)
        error ={"success":False, "msg":"API Error"}
        return jsonify(Error=error)
    

def get_db_price(ts):
    p = taxdb.get_prices().fetchall()

    for counter, i in enumerate(p):
        if i[0] >= ts:
            break

    if (counter+1) == len(p):
        price = p[counter][1]
    else:
        price = p[counter + 1][1]

    return price


def buy(acct):
    s = "Income"
    buy_agg=[]
    for i in acct:
        buys = psql.get_transactions(address_from_public_key(i), s)
        buy_agg += buys
        
    buy_orders = create_buy_records(buy_agg)
    
    # sort and reorder lots
    buy_orders_sort = sorted(buy_orders, key=lambda x: x[1])
    lot = 1 
    for j in buy_orders_sort:
        j[0] = lot
        lot+=1
    
    return buy_orders_sort

def sell(acct):
    s = "sell"
    sell_agg=[]
    for i in acct:
        sells = psql.get_transactions(i, s)
        sell_agg += sells
    
    sell_orders = create_sell_records(sell_agg)
    
    #sort sells
    sell_orders_sort = sorted(sell_orders, key=lambda x: x[0])
   
    return sell_orders_sort


def create_buy_records(b):
    orders = []

    for counter, i in enumerate(b):
        if i[4] not in exceptions and i[3] not in acct:
            # add attributes timestamp, total amount, tax lot
            ts = i[0]
            # don't include fee in incoming records
            order_amt = i[1]
            tax_lot = counter+1
            price = get_db_price(ts+n['epoch'])
            market_value = round((price * (order_amt/atomic)),2)
            convert_ts = convert_timestamp((ts+n['epoch']))
            if i[3] in acct:
                classify = "Transfer in"
            else:
                classify = "Income"
            remain = order_amt
            sender = address_from_public_key(i[3])

            # create order record including
            t = [tax_lot, ts, order_amt, price, market_value, classify, convert_ts, "open", remain, sender]

            # append to buy_orders
            orders.append(t)

    return orders


def create_sell_records(s):
    sells = []
    #map pkeys in test_accouts to addresses so transfers check works
    tmp_list = map(address_from_public_key,acct)
    check = list(tmp_list)

    for i in s:
        if i[4] not in exceptions and i[3] not in check:
            # normal sell
            sell_amt = (i[1]+i[2])
        else:
            # transfer out to related acct or excluded tx out. Only count tx fee out
            sell_amt = (i[2])  
        
        ts = i[0]    
        price = get_db_price(ts+n['epoch'])
        market_value = round((price *(sell_amt/atomic)),2)
        convert_ts = convert_timestamp((ts + n['epoch']))
        receiver = i[3]

        # create sell record including
        t = [ts, sell_amt, price, market_value, convert_ts, 0, 0, receiver]

        # append to buy_orders
        sells.append(t)    

    return sells


def convert_timestamp(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def lotting(b,s):

    for i in s:
        # initialize cap gains
        short_cap_gain = 0
        long_cap_gain = 0
        sold_quantity = i[1]
        sold_price = i[2]

        for j in b:
            lot_quantity = j[8]
            # check if lot has been used up to skip and move to next lot
            if lot_quantity == 0:
                pass

            # check to see if another lot needs relief
            elif sold_quantity > lot_quantity:
                cap_gain = ((sold_price - j[3]) * (lot_quantity/atomic))
                gain_type = gain_classification(i[0], j[1])
                if gain_type == "st":
                    short_cap_gain += cap_gain
                else:
                    long_cap_gain += cap_gain

                # update lot - zero out and status
                j[8] -= lot_quantity
                j[7] = "Lot sold"

                # update remaining sell amount
                sold_quantity -= lot_quantity

            # this executes on the final lot to relieve for the sell
            else:
                cap_gain = ((sold_price - j[3]) * (sold_quantity/atomic))

                gain_type = gain_classification(i[0], j[1])
                if gain_type == "st":
                    short_cap_gain += cap_gain
                else:
                    long_cap_gain += cap_gain

                # update lot and status
                j[8] -= sold_quantity
                if j[8] == 0:
                    j[7] = "Lot sold"
                else:
                    j[7] = "Lot partially sold"
                break

        # update capital gains for sell record
        i[5] += round(short_cap_gain,2)
        i[6] += round(long_cap_gain,2)


def gain_classification(sts, bts):
    if (sts - bts) >= year:
        gain = "lt"
    else:
        gain = "st"

    return gain


def write_csv(b,s, a):
    # buy file
    b_file = "buys.csv"
    with open(b_file, "w") as output:
        fieldnames = ['tax lot', 'timestamp', 'buy amount', 'price', 'market value', 'tx type', 'datetime', 'lot status', 'remaining_qty', 'senderId']
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(fieldnames)
        writer.writerows(b)

    s_file = "sells.csv"
    with open(s_file, "w") as output:
        fieldnames = ['timestamp', 'sell amount', 'price', 'market value', 'datetime', 'st-gain', 'lt-gain', 'receipientId']
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(fieldnames)
        writer.writerows(s)
        
    a_file = "summary.csv"
    with open(a_file,"w") as output:
        fieldnames = ['year', 'income', 'short term', 'long term']
        writer = csv.writer(output, lineterminator='\n')
        writer.writerow(fieldnames)
        writer.writerows(a)

        
def buy_convert(b):
    for i in b:
        i[2] = i[2]/atomic
        i[8] = i[8]/atomic

        
def sell_convert(s):
    for i in s:
        i[1] = i[1]/atomic

def staking_test(d, b):
    for i in b:
        addr = i[9]
        result = delegate_check(d, addr)

        if result == "Yes":
            i[5] = "Staking Reward"

            
def exchange_test(b):
    for i in b:
        addr = i[9]
        if addr in exchange_acct[network]:
            i[5] = "Buy - From Exchange"
            

def delegate_check(d, check):
   test = "No"

   for i in d:
       if check == i[0]:
           test = "Yes"
           break

   return test


def summarize(b,s):
    year1 = {"income":0, "short":0, "long":0}
    year2 = {"income":0, "short":0, "long":0}
    year3 = {"income":0, "short":0, "long":0}
    income = ['Staking Reward','Income']
    twoeighteen = 1514786400
    twonineteen = 1546322400
    
    for i in b:
        if (i[1]+n['epoch']) < twoeighteen:
            #2017 income
            if i[5] in income:
                year1['income']+=i[4] 
        elif (i[1]+n['epoch']) < twonineteen:
            if i[5] in income:
                year2['income']+=i[4]
        else:
            if i[5] in income:
                year3['income']+=i[4]
      
    for j in s:
        if (j[0]+n['epoch']) < twoeighteen:
            #2017 trading
            year1['short']+=j[5]
            year1['long']+=j[6]
        elif (j[0]+n['epoch']) < twonineteen:
            year2['short']+=j[5]
            year2['long']+=j[6]
        else:
            year3['short']+=j[5]
            year3['long']+=j[6]  
           
    
    sum_year1 = ["2017",round(year1['income'],2),round(year1['short'],2),round(year1['long'],2)]
    sum_year2 = ["2018",round(year2['income'],2),round(year2['short'],2),round(year2['long'],2)]
    sum_year3 = ["2019",round(year3['income'],2),round(year3['short'],2),round(year3['long'],2)]
    
    years = [sum_year1, sum_year2, sum_year3]
    return years
      
      
def process_taxes(acct):
    delegates = taxdb.get_delegates().fetchall()
    # do processing
    buys = buy(acct)
    quit()
    sells = sell(acct)
    quit()
    lotting(buys, sells)
    buy_convert(buys)
    sell_convert(sells)
    staking_test(delegates, buys)
    exchange_test(buys)
    agg_years = summarize(buys,sells)
    

    # output to buy and sell csv
    # write_csv(buys, sells, agg_years)

    return buys, sells, agg_years

  
def build_network(c_net):
    e = c_net.epoch
    t = [int(i) for i in e]
    epoch = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
    version = c_net.version
    wif = c_net.wif
    set_custom_network(epoch, version, wif)
    
    
if __name__ == '__main__':
    app.run(host="127.0.0.1", threaded=False)

